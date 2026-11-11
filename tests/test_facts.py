from claim_trace import analyze, facts, manifest
from claim_trace.agents import trial_path
from claim_trace.models import AgentTrial, ToolCall
from claim_trace.stages import save
from tests.conftest import DEFINITION
from tests.test_analyze import write_core


def test_derived_figures_come_from_the_saved_records(tmp_path, settings):
    manifest.freeze(DEFINITION, tmp_path, settings)
    experiment, _ = manifest.load_frozen(tmp_path)
    write_core(tmp_path, experiment)
    common = {"stage": "base", "model": "m", "started_utc": "t", "elapsed_ms": 1,
              "usage": {"input_tokens": 3, "output_tokens": 2}, "messages": []}
    save(trial_path(tmp_path, "single", "base", "short_term", 1), AgentTrial(
        arm="single", memory_type="short_term", trial=1,
        output="The Meadowlight Lamp is Independently Certified.",
        calls=[ToolCall(query="q", result="The Meadowlight Lamp is a lamp.", elapsed_ms=1)],
        **common))
    save(trial_path(tmp_path, "control", "base", "short_term", 1), AgentTrial(
        arm="control", memory_type="short_term", trial=1,
        output="independently certified, says nobody.", calls=[], **common))
    analyze.write(tmp_path)
    derived = facts.derive(tmp_path, "independently certified")
    assert derived["score_gap"] == "0.000"
    assert derived["ranked_above"] == "desk lamp"
    assert derived["short_term_trials"] == "1 of 2 in tool result and answer, 1 in either"
    assert derived["long_term_trials"] == "0 of 0 in tool result and answer, 0 in either"
    assert derived["phrase_in_claim_arm_message_answers"] == "1 of 1"
    assert derived["tokens"] == "6 input, 4 output"
    assert derived["trial_files"] == "2"
