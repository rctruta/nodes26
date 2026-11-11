from datetime import datetime, timezone

from pydantic_ai.usage import RunUsage

from claim_trace import agents
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
