import asyncio
from datetime import datetime, timezone

import pytest
from pydantic_ai.usage import RunUsage

from claim_trace import agents
from claim_trace.manifest import load_experiment
from tests.conftest import STRICT_DEFINITION
from claim_trace.models import AgentTrial, ToolCall


class FinishedRun:
    output = "An answer."

    def usage(self):
        return RunUsage(input_tokens=11, output_tokens=7, requests=2)

    def all_messages_json(self):
        return b'[{"kind": "request"}]'


def test_trial_record_round_trips_the_library_usage_object():
    record = agents.trial_record(
        arm="single", stage="base", memory_type="long_term", trial=1, model="m",
        started=datetime.now(timezone.utc), elapsed_ms=5,
        calls=[ToolCall(query="q", result="[OBJECT] Lamp", elapsed_ms=1)],
        result=FinishedRun())
    restored = AgentTrial.model_validate_json(record.model_dump_json())
    assert restored.usage["input_tokens"] == 11
    assert restored.usage["requests"] == 2
    assert restored.messages == [{"kind": "request"}]


def test_trial_files_are_named_by_arm_stage_memory_and_number(tmp_path):
    path = agents.trial_path(tmp_path, "copies", "expanded", "short_term", 2)
    assert path.name == "copies-expanded-agent-short_term-2.json"


async def get_entity_provenance(entity_id: str) -> str:
    """Get the provenance for an entity."""
    return f"Sources (1): {entity_id}"


async def cypher_query(query: str) -> str:
    """Run a read-only query."""
    raise ValueError("Only read-only Cypher queries are allowed.")


async def search_memory(query: str, memory_types: list[str] | None = None) -> str:
    """Search memory."""
    return f"{memory_types}: {query}"


def test_each_tool_call_is_recorded_and_search_is_held_to_one_memory_type():
    calls = []
    tools = {"search_memory": search_memory, "get_entity_provenance": get_entity_provenance}
    search, provenance = agents.trial_tools(tools, "short_term", calls)
    assert asyncio.run(search("lamp")) == "['short_term']: lamp"
    assert asyncio.run(provenance(entity_id="e-1")) == "Sources (1): e-1"
    assert [(c.tool, c.result) for c in calls] == [
        ("search_memory", "['short_term']: lamp"),
        ("get_entity_provenance", "Sources (1): e-1")]
    assert provenance.__name__ == "get_entity_provenance" and provenance.__doc__


def test_a_refused_query_is_recorded_and_returned_instead_of_ending_the_trial():
    calls = []
    result = asyncio.run(agents.recorded(cypher_query, calls)(query="CREATE (n)"))
    assert result.startswith("ERROR: ValueError")
    assert calls[0].tool == "cypher_query" and calls[0].result == result


def test_a_tool_the_library_does_not_offer_stops_the_run(monkeypatch):
    monkeypatch.setattr(agents, "nams_memory_tools", lambda _client: [search_memory])
    with pytest.raises(ValueError, match="no agent tool named"):
        agents.library_tools(object(), load_experiment(STRICT_DEFINITION))
