"""Print the figures a results summary quotes, derived from one run's saved records.

Standard library only, so a fact check can run it without the project environment:

    python3 -m claim_trace.facts results/RUN_ID "phrase to count in answers"
"""
import json
import sys
from pathlib import Path

from claim_trace.constants import (
    AGENT_PROVENANCE_TOOL,
    AGENT_SEARCH_TOOL,
    ANALYSIS_JSON_FILE,
    ARM_CONTROL,
    ARM_SINGLE,
    ENTITY_SEARCH_FILE,
    MANIFEST_FILE,
    MEMORY_ENTITY,
    MEMORY_MESSAGE,
    PROVENANCE_EMPTY_MARKER,
    STAGE_BASE,
)


def derive(run_dir: Path, phrase: str) -> dict[str, str]:
    analysis = json.loads((run_dir / ANALYSIS_JSON_FILE).read_text())
    manifest = json.loads((run_dir / MANIFEST_FILE).read_text())
    rows = {(row["arm"], row["stage"]): row for row in analysis["rows"]}
    target = rows[ARM_SINGLE, STAGE_BASE]["entity_hit"]["similarity"]
    control = rows[ARM_CONTROL, STAGE_BASE]["entity_hit"]["similarity"]
    search = json.loads((run_dir / ENTITY_SEARCH_FILE.format(
        arm=ARM_SINGLE, stage=STAGE_BASE)).read_text())["searches"]
    hits = search[analysis["primary_query"]][str(analysis["primary_threshold"])]
    above = [hit["name"] for hit in hits if hit["name"] != analysis["target"]
             and hit["similarity"] > target]
    facts = {
        "library_version": manifest["memory_library_version"],
        "score_gap": f"{target - control:.3f}",
        "ranked_above": ", ".join(above),
    }
    trials = analysis["trials"]
    for memory_type in (MEMORY_ENTITY, MEMORY_MESSAGE):
        chosen = [trial for trial in trials if trial["memory_type"] == memory_type]
        both = sum(t["subject_in_tool_result"] and t["subject_in_answer"] for t in chosen)
        either = sum(t["subject_in_tool_result"] or t["subject_in_answer"] for t in chosen)
        facts[f"{memory_type}_trials"] = f"{both} of {len(chosen)} in tool result and answer, " \
                                         f"{either} in either"
    facts["trial_files"] = str(len(trials))
    outputs = [json.loads((run_dir / trial["file"]).read_text()) for trial in trials]
    claim_answers = [o["output"] for o in outputs
                     if o["memory_type"] == MEMORY_MESSAGE and o["arm"] != ARM_CONTROL]
    facts["phrase_in_claim_arm_message_answers"] = (
        f"{sum(phrase.casefold() in answer.casefold() for answer in claim_answers)} "
        f"of {len(claim_answers)}")
    facts["tokens"] = (f"{sum(o['usage']['input_tokens'] for o in outputs)} input, "
                       f"{sum(o['usage']['output_tokens'] for o in outputs)} output")
    facts.update(_provenance_facts(run_dir, analysis, outputs))
    return facts


def _provenance_facts(run_dir: Path, analysis: dict, outputs: list[dict]) -> dict[str, str]:
    """What the library's provenance call held per subject, and how the agent's calls fared."""
    stored_ids: set[str] = set()
    held = []
    for row in analysis["rows"]:
        record = json.loads((run_dir / ENTITY_SEARCH_FILE.format(
            arm=row["arm"], stage=row["stage"])).read_text())
        stored_ids.update(node["id"] for node in record["nodes"])
        node = row["node"]
        # An analysis written before provenance was read back has no such key.
        count = None if node is None else node.get("provenance_sources")
        held.append(f"{row['arm']}-{row['stage']} "
                    f"{'not recorded' if count is None else count}")
    calls = [call for output in outputs for call in output["calls"]]
    by_tool: dict[str, int] = {}
    for call in calls:
        name = call.get("tool", AGENT_SEARCH_TOOL)
        by_tool[name] = by_tool.get(name, 0) + 1
    provenance = [call for call in calls if call.get("tool") == AGENT_PROVENANCE_TOOL]
    given_id = sum(json.loads(call["query"])["kwargs"].get("entity_id") in stored_ids
                   for call in provenance)
    empty = sum(PROVENANCE_EMPTY_MARKER in call["result"] for call in provenance)
    return {
        "subject_provenance_sources": ", ".join(held),
        "tool_calls": ", ".join(f"{name} {count}" for name, count in sorted(by_tool.items())),
        "provenance_tool_calls": f"{len(provenance)} calls, {empty} returned no sources, "
                                 f"{given_id} given a stored entity id",
    }


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    for name, value in derive(Path(sys.argv[1]), sys.argv[2]).items():
        sys.stdout.write(f"{name}: {value}\n")
