"""Fresh agent trials that can reach memory only through one read-only search tool."""
import dataclasses
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from neo4j_agent_memory import connect
from neo4j_agent_memory.integrations.pydantic_ai import create_memory_tools
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits

from claim_trace.config import Settings
from claim_trace.constants import AGENT_FILE, AGENT_TOOL_NAME, MEMORY_TYPES
from claim_trace.logger import get_logger
from claim_trace.models import AgentTrial, Experiment, ToolCall
from claim_trace.stages import client_settings, final_stage, save

log = get_logger(__name__)


def trial_path(run_dir: Path, arm: str, stage: str, memory_type: str, trial: int) -> Path:
    return run_dir / AGENT_FILE.format(arm=arm, stage=stage, memory_type=memory_type,
                                       trial=trial)


def trial_record(*, arm: str, stage: str, memory_type: str, trial: int, model: str,
                 started: datetime, elapsed_ms: int, calls: list[ToolCall],
                 result) -> AgentTrial:
    return AgentTrial(
        arm=arm, stage=stage, memory_type=memory_type, trial=trial, model=model,
        started_utc=started.isoformat(), elapsed_ms=elapsed_ms, calls=calls,
        output=result.output, usage=dataclasses.asdict(result.usage()),
        messages=json.loads(result.all_messages_json()),
    )


async def run_trial(upstream_search, model, experiment: Experiment, *, arm: str, stage: str,
                    memory_type: str, trial: int) -> AgentTrial:
    calls: list[ToolCall] = []

    async def search_memory(query: str) -> str:
        """Search saved memory for relevant catalog products."""
        call_started = time.monotonic()
        result = await upstream_search(query, memory_types=[memory_type])
        calls.append(ToolCall(query=query, result=result,
                              elapsed_ms=round((time.monotonic() - call_started) * 1000)))
        return result

    agent = Agent(model, instructions=experiment.agent_instructions, tools=[search_memory])
    started = datetime.now(timezone.utc)
    clock = time.monotonic()
    result = await agent.run(
        experiment.primary_query,
        usage_limits=UsageLimits(request_limit=experiment.agent_request_limit),
    )
    return trial_record(arm=arm, stage=stage, memory_type=memory_type, trial=trial,
                        model=experiment.agent_model, started=started,
                        elapsed_ms=round((time.monotonic() - clock) * 1000),
                        calls=calls, result=result)


async def run_arm(settings: Settings, experiment: Experiment, arm: str, run_dir: Path) -> None:
    """Run every planned trial for one arm against its final-stage graph."""
    if settings.openai_api_key is None:
        raise RuntimeError("Set OPENAI_API_KEY in .env to run agent trials")
    stage = final_stage(arm)
    planned = [(memory_type, trial) for memory_type in MEMORY_TYPES
               for trial in range(1, experiment.trials_per_stage + 1)]
    for memory_type, trial in planned:
        path = trial_path(run_dir, arm, stage, memory_type, trial)
        if path.exists():
            raise FileExistsError(path)
    model = OpenAIChatModel(experiment.agent_model, provider=OpenAIProvider(
        api_key=settings.openai_api_key.get_secret_value()))
    client = await connect(client_settings(settings, experiment, arm))
    try:
        upstream = next(tool for tool in create_memory_tools(client)
                        if tool.__name__ == AGENT_TOOL_NAME)
        for memory_type, trial in planned:
            log.info("agent trial arm=%s memory=%s trial=%s", arm, memory_type, trial)
            record = await run_trial(upstream, model, experiment, arm=arm, stage=stage,
                                     memory_type=memory_type, trial=trial)
            save(trial_path(run_dir, arm, stage, memory_type, trial), record)
    finally:
        await client.close()
