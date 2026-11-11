"""Fresh agent trials that can reach memory only through the library's read-only tools."""
import dataclasses
import functools
import json
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from neo4j.exceptions import Neo4jError
from neo4j_agent_memory import connect
from neo4j_agent_memory.core.exceptions import NotFoundError, NotSupportedError
from neo4j_agent_memory.integrations.pydantic_ai import nams_memory_tools
from pydantic_ai import Agent
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits

from claim_trace.config import Settings
from claim_trace.constants import (
    AGENT_FILE,
    AGENT_SEARCH_TOOL,
    MEMORY_TYPES,
    STOPPED_REQUEST_LIMIT,
    TOOL_ERROR_PREFIX,
)
from claim_trace.logger import get_logger
from claim_trace.models import AgentTrial, Experiment, ToolCall
from claim_trace.stages import client_settings, final_stage, save

log = get_logger(__name__)

# A query the agent wrote can be refused or malformed. That is an outcome of the
# trial: it is recorded and returned to the agent, and the trial continues.
TOOL_ERRORS = (ValueError, Neo4jError, NotFoundError, NotSupportedError)


def trial_path(run_dir: Path, arm: str, stage: str, memory_type: str, trial: int) -> Path:
    return run_dir / AGENT_FILE.format(arm=arm, stage=stage, memory_type=memory_type,
                                       trial=trial)


def library_tools(client, experiment: Experiment) -> dict[str, Callable]:
    """The tools the definition names, taken unmodified from the library's own set."""
    available = {tool.__name__: tool for tool in nams_memory_tools(client)}
    missing = [name for name in experiment.agent_tools if name not in available]
    if missing:
        raise ValueError(f"Library has no agent tool named {missing}; "
                         f"it offers {sorted(available)}")
    return {name: available[name] for name in experiment.agent_tools}


def recorded(tool: Callable, calls: list[ToolCall]) -> Callable:
    """Wrap a library tool so each call and its result, or its error, is saved."""

    @functools.wraps(tool)
    async def wrapper(*args, **kwargs):
        started = time.monotonic()
        try:
            result = await tool(*args, **kwargs)
        except TOOL_ERRORS as error:
            result = f"{TOOL_ERROR_PREFIX}{type(error).__name__}: {error}"
        calls.append(ToolCall(
            tool=tool.__name__, query=json.dumps({"args": args, "kwargs": kwargs}, default=str),
            result=result, elapsed_ms=round((time.monotonic() - started) * 1000)))
        return result

    return wrapper


def trial_tools(tools: dict[str, Callable], memory_type: str,
                calls: list[ToolCall]) -> list[Callable]:
    """The agent's tools for one trial, with search held to one memory type."""
    upstream_search = tools[AGENT_SEARCH_TOOL]

    async def search_memory(query: str) -> str:
        """Search saved memory for relevant catalog products."""
        started = time.monotonic()
        result = await upstream_search(query, memory_types=[memory_type])
        calls.append(ToolCall(tool=AGENT_SEARCH_TOOL, query=query, result=result,
                              elapsed_ms=round((time.monotonic() - started) * 1000)))
        return result

    return [search_memory, *(recorded(tool, calls) for name, tool in tools.items()
                             if name != AGENT_SEARCH_TOOL)]


def trial_record(*, arm: str, stage: str, memory_type: str, trial: int, model: str,
                 started: datetime, elapsed_ms: int, calls: list[ToolCall],
                 result) -> AgentTrial:
    return AgentTrial(
        arm=arm, stage=stage, memory_type=memory_type, trial=trial, model=model,
        started_utc=started.isoformat(), elapsed_ms=elapsed_ms, calls=calls,
        output=result.output, usage=dataclasses.asdict(result.usage()),
        messages=json.loads(result.all_messages_json()),
    )


async def run_trial(tools: dict[str, Callable], model, experiment: Experiment, *, arm: str,
                    stage: str, memory_type: str, trial: int) -> AgentTrial:
    calls: list[ToolCall] = []
    agent = Agent(model, instructions=experiment.agent_instructions,
                  tools=trial_tools(tools, memory_type, calls))
    started = datetime.now(timezone.utc)
    clock = time.monotonic()
    common = {"arm": arm, "stage": stage, "memory_type": memory_type, "trial": trial,
              "model": experiment.agent_model}
    try:
        result = await agent.run(
            experiment.primary_query,
            usage_limits=UsageLimits(request_limit=experiment.agent_request_limit),
        )
    except UsageLimitExceeded:
        # The agent used every allowed request without answering. Saved as such.
        return AgentTrial(**common, started_utc=started.isoformat(),
                          elapsed_ms=round((time.monotonic() - clock) * 1000), calls=calls,
                          output="", usage={}, messages=[], stopped=STOPPED_REQUEST_LIMIT)
    return trial_record(**common, started=started,
                        elapsed_ms=round((time.monotonic() - clock) * 1000),
                        calls=calls, result=result)


async def run_arm(settings: Settings, experiment: Experiment, arm: str, run_dir: Path) -> None:
    """Run every planned trial for one arm against its final-stage graph.

    A trial whose file already exists is left alone, so an interrupted run resumes.
    """
    if settings.openai_api_key is None:
        raise RuntimeError("Set OPENAI_API_KEY in .env to run agent trials")
    stage = final_stage(arm)
    model = OpenAIChatModel(experiment.agent_model, provider=OpenAIProvider(
        api_key=settings.openai_api_key.get_secret_value()))
    client = await connect(client_settings(settings, experiment, arm, run_dir))
    try:
        tools = library_tools(client, experiment)
        for memory_type in MEMORY_TYPES:
            for trial in range(1, experiment.trials_per_stage + 1):
                path = trial_path(run_dir, arm, stage, memory_type, trial)
                if path.exists():
                    log.info("trial already saved, skipping file=%s", path.name)
                    continue
                log.info("agent trial arm=%s memory=%s trial=%s", arm, memory_type, trial)
                save(path, await run_trial(tools, model, experiment, arm=arm, stage=stage,
                                           memory_type=memory_type, trial=trial))
    finally:
        await client.close()
