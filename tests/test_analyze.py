import pytest

from claim_trace import analyze, manifest
from claim_trace.agents import trial_path
from claim_trace.constants import (
    ARMS,
    ENTITY_SEARCH_FILE,
    INGEST_FILE,
    MESSAGE_SEARCH_FILE,
)
from claim_trace.models import (
    AgentTrial,
    EntityHit,
    EntityNode,
    EntitySearchRecord,
    IngestedMessage,
    IngestRecord,
    MessageHit,
    MessageSearchRecord,
    SourceMessage,
    ToolCall,
)
from claim_trace.stages import save, stages_for
from tests.conftest import DEFINITION


def write_core(run_dir, experiment, *, skip=()):
    for arm in ARMS:
        subject = analyze.subject_for(experiment, arm)
        for stage in stages_for(arm):
            names = {"arm": arm, "stage": stage}
            sources = 4 if stage == "expanded" else 1
            nodes = [
                EntityNode(id=f"{arm}-subject", name=subject, type="OBJECT",
                           labels=["Entity", "Object"], embedding_sha256="same-hash",
                           sources=[SourceMessage(id=str(i), content="text")
                                    for i in range(sources)]),
                EntityNode(id=f"{arm}-other", name="desk lamp", type="OBJECT",
                           labels=["Entity", "Object"], embedding_sha256="other", sources=[]),
            ]
            if (arm, stage) == ("distinct", "expanded"):
                nodes.append(EntityNode(id="new", name="task light", type="OBJECT",
                                        labels=["Entity"], embedding_sha256="n", sources=[]))
            hits = [EntityHit(rank=1, id=f"{arm}-other", name="desk lamp", similarity=0.9),
                    EntityHit(rank=2, id=f"{arm}-subject", name=subject, similarity=0.75)]
            messages = [MessageHit(rank=1, id="m", content=f"The {subject} is a lamp.",
                                   similarity=0.87)]
            records = {
                INGEST_FILE: IngestRecord(
                    arm=arm, stage=stage, validation="strict",
                    messages=[IngestedMessage(id="m", session="s", text="t")]),
                ENTITY_SEARCH_FILE: EntitySearchRecord(
                    arm=arm, stage=stage, validation="strict", nodes=nodes,
                    searches={q: {"0.7": hits, "0.0": hits} for q in experiment.queries}),
                MESSAGE_SEARCH_FILE: MessageSearchRecord(
                    arm=arm, stage=stage,
                    searches={q: {"0.7": messages, "0.0": messages}
                              for q in experiment.queries}),
            }
            for template, record in records.items():
                if template not in skip:
                    save(run_dir / template.format(**names), record)


@pytest.fixture
def run_dir(tmp_path, settings):
    manifest.freeze(DEFINITION, tmp_path, settings)
    return tmp_path


def test_rows_follow_each_arms_subject_and_count_target_nodes(run_dir):
    experiment, _ = manifest.load_frozen(run_dir)
    write_core(run_dir, experiment)
    report = analyze.analyze(run_dir)
    assert report.core_complete and not report.agents_complete
    rows = {(row.arm, row.stage): row for row in report.rows}
    control = rows["control", "base"]
    assert control.subject == experiment.control_entity
    assert control.target_nodes == 0 and control.entity_hit.rank == 2
    single = rows["single", "base"]
    assert single.subject == experiment.target_entity and single.target_nodes == 1
    assert single.node.source_count == 1 and single.message_hit.rank == 1
    assert report.expansions["copies"].sources_after == 4
    assert report.expansions["copies"].same_embedding
    assert report.expansions["copies"].new_entities == []
    assert report.expansions["distinct"].new_entities == ["task light"]


def test_missing_stage_is_reported_as_not_run(run_dir):
    experiment, _ = manifest.load_frozen(run_dir)
    write_core(run_dir, experiment, skip=(MESSAGE_SEARCH_FILE,))
    report = analyze.analyze(run_dir)
    assert not report.core_complete
    assert "single-base-message_search.json" in report.missing_files
    text = analyze.markdown(report)
    assert "not run" in text


def test_trial_rows_separate_tool_exposure_from_the_answer(run_dir):
    experiment, _ = manifest.load_frozen(run_dir)
    write_core(run_dir, experiment)
    common = {"stage": "base", "model": "m", "started_utc": "t", "elapsed_ms": 1,
              "usage": {"input_tokens": 3, "output_tokens": 2}, "messages": []}
    save(trial_path(run_dir, "single", "base", "long_term", 1), AgentTrial(
        arm="single", memory_type="long_term", trial=1, output="Choose any LED lamp.",
        calls=[ToolCall(query="q", result="[OBJECT] Meadowlight Lamp", elapsed_ms=1)],
        **common))
    save(trial_path(run_dir, "control", "base", "short_term", 2), AgentTrial(
        arm="control", memory_type="short_term", trial=2,
        output="Consider the Harbor Task Lamp.", calls=[], **common))
    report = analyze.write(run_dir)
    trials = {(t.arm, t.memory_type): t for t in report.trials}
    exposed = trials["single", "long_term"]
    assert exposed.subject_in_tool_result and not exposed.subject_in_answer
    named = trials["control", "short_term"]
    assert named.subject == "Harbor Task Lamp"
    assert named.subject_in_answer and not named.subject_in_tool_result
    assert (run_dir / "analysis.md").read_text().count("| single | long_term | 1 |") == 1
