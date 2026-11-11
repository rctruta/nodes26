"""Summarize a run's saved records. Reports observations; judges nothing."""
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from claim_trace.agents import trial_path
from claim_trace.constants import (
    ANALYSIS_JSON_FILE,
    ANALYSIS_MARKDOWN_FILE,
    ANSWER_EXCERPT_CHARS,
    ARM_CONTROL,
    ARMS,
    ENTITY_SEARCH_FILE,
    EXPANSION_ARMS,
    INGEST_FILE,
    MEMORY_TYPES,
    MESSAGE_SEARCH_FILE,
    STAGE_BASE,
    STAGE_EXPANDED,
)
from claim_trace.manifest import load_frozen
from claim_trace.models import (
    AgentTrial,
    Analysis,
    EntitySearchRecord,
    Expansion,
    Experiment,
    IngestRecord,
    MessageSearchRecord,
    SearchPosition,
    StageRow,
    SubjectNode,
    TrialRow,
)
from claim_trace.stages import final_stage, stages_for

RecordT = TypeVar("RecordT", bound=BaseModel)


def _load(path: Path, model: type[RecordT], missing: list[str]) -> RecordT | None:
    if not path.is_file():
        missing.append(path.name)
        return None
    return model.model_validate_json(path.read_bytes())


def subject_for(experiment: Experiment, arm: str) -> str:
    """The entity an arm is about: the comparison product in control, the target elsewhere."""
    return experiment.control_entity if arm == ARM_CONTROL else experiment.target_entity


def _stage_row(experiment: Experiment, arm: str, stage: str, ingest: IngestRecord | None,
               entities: EntitySearchRecord | None,
               messages: MessageSearchRecord | None) -> StageRow:
    subject = subject_for(experiment, arm)
    query, threshold = experiment.primary_query, experiment.primary_threshold
    node = entity_hit = message_hit = None
    if entities is not None:
        matches = [n for n in entities.nodes if n.name == subject]
        if len(matches) > 1:
            raise ValueError(f"Multiple {subject} nodes in {arm}-{stage}")
        if matches:
            node = SubjectNode(id=matches[0].id, type=matches[0].type,
                               labels=matches[0].labels,
                               source_count=len(matches[0].sources),
                               embedding_sha256=matches[0].embedding_sha256)
        entity_hit = next((SearchPosition(rank=h.rank, similarity=h.similarity, id=h.id)
                           for h in entities.searches[query][threshold]
                           if h.name == subject), None)
    if messages is not None:
        message_hit = next((SearchPosition(rank=h.rank, similarity=h.similarity, id=h.id)
                            for h in messages.searches[query][threshold]
                            if subject.casefold() in h.content.casefold()), None)
    return StageRow(
        arm=arm, stage=stage, subject=subject,
        ingested_messages=None if ingest is None else len(ingest.messages),
        entity_count=None if entities is None else len(entities.nodes),
        target_nodes=None if entities is None else sum(
            n.name == experiment.target_entity for n in entities.nodes),
        node=node, entity_hit=entity_hit, message_hit=message_hit,
        entity_search_ran=entities is not None, message_search_ran=messages is not None,
    )


def _expansion(before: StageRow, after: StageRow, base: EntitySearchRecord | None,
               expanded: EntitySearchRecord | None) -> Expansion | None:
    if not (before.node and after.node and base and expanded):
        return None
    return Expansion(
        same_node_id=before.node.id == after.node.id,
        sources_before=before.node.source_count,
        sources_after=after.node.source_count,
        same_embedding=before.node.embedding_sha256 == after.node.embedding_sha256,
        same_score=bool(before.entity_hit and after.entity_hit
                        and before.entity_hit.similarity == after.entity_hit.similarity),
        same_rank=bool(before.entity_hit and after.entity_hit
                       and before.entity_hit.rank == after.entity_hit.rank),
        new_entities=sorted({n.name for n in expanded.nodes} - {n.name for n in base.nodes}),
    )


def _trial_row(experiment: Experiment, path: Path, trial: AgentTrial) -> TrialRow:
    subject = subject_for(experiment, trial.arm).casefold()
    return TrialRow(
        file=path.name, arm=trial.arm, stage=trial.stage, memory_type=trial.memory_type,
        trial=trial.trial, subject=subject_for(experiment, trial.arm),
        tool_calls=len(trial.calls),
        subject_in_tool_result=any(subject in call.result.casefold() for call in trial.calls),
        subject_in_answer=subject in trial.output.casefold(),
        answer_excerpt=trial.output[:ANSWER_EXCERPT_CHARS],
        input_tokens=trial.usage.get("input_tokens"),
        output_tokens=trial.usage.get("output_tokens"),
    )


def analyze(run_dir: Path) -> Analysis:
    experiment, manifest = load_frozen(run_dir)
    core_missing: list[str] = []
    rows: dict[tuple[str, str], StageRow] = {}
    entity_records: dict[tuple[str, str], EntitySearchRecord | None] = {}
    for arm in ARMS:
        for stage in stages_for(arm):
            names = {"arm": arm, "stage": stage}
            entities = _load(run_dir / ENTITY_SEARCH_FILE.format(**names),
                             EntitySearchRecord, core_missing)
            entity_records[arm, stage] = entities
            rows[arm, stage] = _stage_row(
                experiment, arm, stage,
                _load(run_dir / INGEST_FILE.format(**names), IngestRecord, core_missing),
                entities,
                _load(run_dir / MESSAGE_SEARCH_FILE.format(**names), MessageSearchRecord,
                      core_missing),
            )
    agent_missing: list[str] = []
    trials = []
    for arm in ARMS:
        for memory_type in MEMORY_TYPES:
            for number in range(1, experiment.trials_per_stage + 1):
                path = trial_path(run_dir, arm, final_stage(arm), memory_type, number)
                trial = _load(path, AgentTrial, agent_missing)
                if trial is not None:
                    trials.append(_trial_row(experiment, path, trial))
    return Analysis(
        run_id=manifest.run_id, experiment_id=experiment.experiment_id,
        experiment_sha256=manifest.experiment_sha256, git_commit=manifest.git_commit,
        git_dirty=manifest.git_dirty, target=experiment.target_entity,
        control_entity=experiment.control_entity, primary_query=experiment.primary_query,
        primary_threshold=float(experiment.primary_threshold),
        core_complete=not core_missing, agents_complete=not agent_missing,
        missing_files=sorted(core_missing + agent_missing), rows=list(rows.values()),
        expansions={arm: _expansion(rows[arm, STAGE_BASE], rows[arm, STAGE_EXPANDED],
                                    entity_records[arm, STAGE_BASE],
                                    entity_records[arm, STAGE_EXPANDED])
                    for arm in EXPANSION_ARMS},
        trials=trials,
    )


def _position(hit: SearchPosition | None, ran: bool) -> str:
    if not ran:
        return "not run"
    return "absent" if hit is None else f"{hit.rank} / {hit.similarity:.4f}"


def markdown(report: Analysis) -> str:
    lines = [
        "# Run analysis", "",
        f"Run: `{report.run_id}`",
        f"Experiment: `{report.experiment_id}` (SHA-256 `{report.experiment_sha256}`)",
        f"Code: commit `{report.git_commit}`"
        f"{' with uncommitted changes' if report.git_dirty else ', clean tree'}",
        f"Target: `{report.target}`. Control entity: `{report.control_entity}`",
        f"Primary query: {report.primary_query}",
        f"Primary search threshold: {report.primary_threshold}",
        f"Core ingestion and retrieval complete: **{'yes' if report.core_complete else 'no'}**",
        f"Agent trials complete: **{'yes' if report.agents_complete else 'no'}**", "",
        "## Graph and retrieval", "",
        "Each row follows the arm's subject entity: the control entity in the control arm,",
        "the target in the others. `Target nodes` counts nodes named after the target.", "",
        "| Arm | Stage | Subject | Type | Sources | Entities | Target nodes "
        "| Entity rank / score | Message rank / score |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in report.rows:
        lines.append(
            f"| {row.arm} | {row.stage} | {row.subject} | "
            f"{row.node.type if row.node else 'absent'} | "
            f"{row.node.source_count if row.node else 0} | "
            f"{'not run' if row.entity_count is None else row.entity_count} | "
            f"{'not run' if row.target_nodes is None else row.target_nodes} | "
            f"{_position(row.entity_hit, row.entity_search_ran)} | "
            f"{_position(row.message_hit, row.message_search_ran)} |")
    lines += ["", "## Expansion comparison", ""]
    for arm, expansion in report.expansions.items():
        if expansion is None:
            lines.append(f"- {arm}: target absent or stage not run.")
            continue
        lines.append(
            f"- {arm}: sources {expansion.sources_before} to {expansion.sources_after}; "
            f"same node: {expansion.same_node_id}; same embedding: {expansion.same_embedding}; "
            f"same score: {expansion.same_score}; same rank: {expansion.same_rank}; "
            f"new entities: {', '.join(expansion.new_entities) or 'none'}.")
    lines += [
        "", "## Agent trials", "",
        "A name in a tool result or an answer is not a recommendation. Read the full trial",
        "file before labeling one.", "",
        "| Arm | Memory | Trial | Subject | Tool calls | In tool result | In answer |",
        "| --- | --- | ---: | --- | ---: | --- | --- |",
    ]
    for trial in report.trials:
        lines.append(
            f"| {trial.arm} | {trial.memory_type} | {trial.trial} | {trial.subject} | "
            f"{trial.tool_calls} | {'yes' if trial.subject_in_tool_result else 'no'} | "
            f"{'yes' if trial.subject_in_answer else 'no'} |")
    lines += ["", "## Missing planned files", ""]
    lines += [f"- `{name}`" for name in report.missing_files] or ["None."]
    return "\n".join(lines) + "\n"


def write(run_dir: Path) -> Analysis:
    report = analyze(run_dir)
    (run_dir / ANALYSIS_JSON_FILE).write_text(report.model_dump_json(indent=2) + "\n")
    (run_dir / ANALYSIS_MARKDOWN_FILE).write_text(markdown(report))
    return report
