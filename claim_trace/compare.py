"""Put two runs side by side: what was set differently, and what was observed."""
from pathlib import Path

from claim_trace.analyze import (
    analyze,
    describe_ontology,
    position,
    provenance_count,
    type_label,
)
from claim_trace.constants import ARMS, COMPARISON_FILE, MEMORY_TYPES
from claim_trace.models import Analysis


def _settings_rows(report: Analysis) -> dict[str, str]:
    settings = report.settings
    return {
        "Experiment": f"`{report.experiment_id}`",
        "Code": f"commit `{report.git_commit[:7]}`"
                f"{' with uncommitted changes' if report.git_dirty else ', clean tree'}",
        "Memory library": settings.memory_library_version,
        "Ontology": describe_ontology(settings),
        "Validation mode": settings.validation_mode,
        "Provenance links written": "yes" if settings.provenance_links else "no",
        "Agent tools": ", ".join(settings.agent_tools),
    }


def _stage_cells(report: Analysis) -> dict[tuple[str, str], list[str]]:
    return {
        (row.arm, row.stage): [
            type_label(row.node),
            str(row.node.source_count if row.node else 0),
            provenance_count(row.node),
            "not run" if row.entity_count is None else str(row.entity_count),
            position(row.entity_hit, row.entity_search_ran),
            position(row.message_hit, row.message_search_ran),
        ]
        for row in report.rows
    }


def _trial_cells(report: Analysis, arm: str, memory_type: str) -> list[str]:
    trials = [t for t in report.trials if (t.arm, t.memory_type) == (arm, memory_type)]
    if not trials:
        return ["not run", "not run", "not run"]
    tools = sorted({tool for trial in trials for tool in trial.tools_used})
    return [
        f"{sum(t.subject_in_tool_result for t in trials)} of {len(trials)}",
        f"{sum(t.subject_in_answer for t in trials)} of {len(trials)}",
        ", ".join(tools) or "none",
    ]


def markdown(base: Analysis, run: Analysis) -> str:
    """Observations only. Which run is stricter is read from the settings table."""
    lines = [
        f"# Run `{run.run_id}` compared with `{base.run_id}`", "",
        "Both runs ingest the same documents and ask the same queries unless the",
        "definitions say otherwise. The first table shows every setting; the rest",
        "show what each run recorded.", "",
        "## Settings", "",
        f"| Setting | `{base.run_id}` | `{run.run_id}` | Same |",
        "| --- | --- | --- | --- |",
    ]
    base_settings, run_settings = _settings_rows(base), _settings_rows(run)
    for name, value in base_settings.items():
        same = "yes" if value == run_settings[name] else "**no**"
        lines.append(f"| {name} | {value} | {run_settings[name]} | {same} |")
    for label, left, right in (("Target", base.target, run.target),
                               ("Control entity", base.control_entity, run.control_entity),
                               ("Primary query", base.primary_query, run.primary_query),
                               ("Search threshold", base.primary_threshold,
                                run.primary_threshold)):
        lines.append(f"| {label} | {left} | {right} | {'yes' if left == right else '**no**'} |")

    lines += [
        "", "## Graph and retrieval", "",
        "Each cell is `type`, linked messages, provenance sources, entities in the graph,",
        "entity rank / score, message rank / score, for the arm's subject entity.", "",
        f"| Arm | Stage | `{base.run_id}` | `{run.run_id}` |",
        "| --- | --- | --- | --- |",
    ]
    base_cells, run_cells = _stage_cells(base), _stage_cells(run)
    for key in base_cells:
        if key in run_cells:
            lines.append(f"| {key[0]} | {key[1]} | {'; '.join(base_cells[key])} | "
                         f"{'; '.join(run_cells[key])} |")

    lines += [
        "", "## Expansion", "",
        f"| Arm | `{base.run_id}` | `{run.run_id}` |", "| --- | --- | --- |",
    ]
    for arm in base.expansions:
        cells = []
        for report in (base, run):
            e = report.expansions.get(arm)
            cells.append("not available" if e is None else (
                f"sources {e.sources_before} to {e.sources_after}; same embedding "
                f"{e.same_embedding}; same score {e.same_score}; same rank {e.same_rank}; "
                f"new entities: {', '.join(e.new_entities) or 'none'}"))
        lines.append(f"| {arm} | {cells[0]} | {cells[1]} |")

    lines += [
        "", "## Agent trials", "",
        "Each cell is trials with the subject's name in a tool result, trials with it in",
        "the answer, and the tools the agent called. A name in an answer is not a",
        "recommendation; read the trial files.", "",
        f"| Arm | Memory | `{base.run_id}` | `{run.run_id}` |",
        "| --- | --- | --- | --- |",
    ]
    for arm in ARMS:
        for memory_type in MEMORY_TYPES:
            lines.append(f"| {arm} | {memory_type} | "
                         f"{'; '.join(_trial_cells(base, arm, memory_type))} | "
                         f"{'; '.join(_trial_cells(run, arm, memory_type))} |")
    return "\n".join(lines) + "\n"


def write(base_dir: Path, run_dir: Path) -> Path:
    """Analyze both runs from their saved records and write the comparison beside the second."""
    base, run = analyze(base_dir), analyze(run_dir)
    path = run_dir / COMPARISON_FILE.format(base_run_id=base.run_id)
    path.write_text(markdown(base, run))
    return path
