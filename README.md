# Graph memory: a false catalog claim

This is a controlled, reproducible case study of one graph-backed agent-memory pipeline. A fictional catalog entry describes a nonexistent lamp. The experiment asks whether the official extractor persists it as a typed entity, whether a later semantic search retrieves it, and whether a fresh agent uses it in an answer. It does **not** claim a vulnerability in every graph-memory product.

The library under test is [neo4j-labs/agent-memory](https://github.com/neo4j-labs/agent-memory), pinned to one upstream commit in `pyproject.toml` and `uv.lock`. A related report, [issue 155](https://github.com/neo4j-labs/agent-memory/issues/155), describes poisoning that attaches false claims to entities already present in trusted memory. This experiment differs in what it measures: the entity is new, a matched control entry goes through the same pipeline, and repetition is compared with independently worded support.

Observed results are in [RESULTS.md](RESULTS.md), with the raw records for that run under `results/`.

## Design

Four arms, each on its own disposable Neo4j instance:

| Arm | Base stage | Expanded stage |
| --- | --- | --- |
| control | background notes + a comparison entry for a different product | none |
| single | background notes + the fabricated entry | none |
| copies | same as single | the fabricated entry repeated |
| distinct | same as single | independently worded statements naming the same product |

Every document is ingested with `short_term.add_message()` and its default arguments. Entity nodes are never seeded by hand. After each stage the same queries are run two ways: `long_term.search_entities()` over extracted **entities**, and `short_term.search_messages()` over stored **messages**. Here "short-term" is the library's API name; the messages are persisted in Neo4j, so this is not an ephemeral context window.

Agent trials then give a fresh agent the library's own read-only tools named in the definition, with `search_memory` restricted to one memory type per trial. The agent cannot write to memory or execute anything.

Extraction and embedding run locally; no language model takes part in ingestion or search.

## Settings a definition controls

How strictly memory is stored and exposed is set in the definition, frozen with the run, and printed at the top of its analysis.

| Setting | What it does |
| --- | --- |
| `validation_mode` | `strict` drops extracted entities whose type and subtype the ontology does not declare. |
| `gliner_schema` or `ontology_path` | Exactly one. A built-in schema name, or an ontology document that the extractor and validation both use. A schema name would override an ontology, so setting both is refused. |
| `provenance_links` | After each ingested message, write the library's `EXTRACTED_FROM` and `EXTRACTED_BY` links. The library stores each mention's position, confidence and extractor but writes these links only when the application asks. |
| `agent_tools` | Which of the library's agent tools the agent may call: `search_memory`, `get_entity_provenance`, `cypher_query` (read-only). |

Two definitions are included. They ingest the same documents and ask the same queries.

- `experiments/catalog_lamp.json` — the library's defaults plus strict validation: built-in POLE+O schema, no provenance links, `search_memory` only. A version 1 definition; those settings are fixed for version 1.
- `experiments/catalog_lamp_strict.json` — the procurement ontology in `ontologies/`, strict validation, provenance links written, and the agent given the provenance and query tools.
- `experiments/catalog_lamp_upstream_ontology.json` — the same as the strict definition, with the library's own example ontology, unmodified, in place of the procurement one.

The client settings are those of the library's ontology example, `SchemaConfig(ontology_path=...)` with the GLiNER extractor and no language model, plus the validation mode. Where each ontology comes from is recorded in [ontologies/README.md](ontologies/README.md).

Type checks and source links are not evidence that a claim is true. An ontology declares which kinds of thing may be stored; it holds no list of which things exist.

## Requirements

- macOS or Linux, Docker, and [uv](https://docs.astral.sh/uv/)
- Four free consecutive HTTP ports and four free consecutive Bolt ports
- An OpenAI API key only for the agent trials

## Setup and run

```bash
cp .env.example .env
# Edit .env: set a local Neo4j password and, if needed, different base ports.
uv sync --frozen
git config core.hooksPath .githooks
make test
make run EXPERIMENT=experiments/catalog_lamp.json
```

The run logs its progress and ends with the `results/RUN_ID` directory it wrote. The run ID is a UTC timestamp. Before the first database write, the definition is copied to `results/RUN_ID/experiment.json` and a `manifest.json` records its SHA-256, the Git commit and whether the tree was clean, the lockfile hash, library versions, image digest, and ports. No secret is recorded. Every later step reads the frozen copy and refuses it if the hash no longer matches.

For the agent trials, add `OPENAI_API_KEY` to `.env`, then:

```bash
make agents RUN=results/RUN_ID
```

Each arm gets `trials_per_stage` fresh trials with entity memory and the same number with message memory. Each trial file holds the complete model and tool messages, every memory query with its result, elapsed time, and token usage.

`analysis.json` and `analysis.md` are rewritten after each step. They report the subject node and its source links, entity and message search positions, the before/after comparison for the two expansion arms, and whether the subject's name appears in each trial's tool results and answer. They deliberately do not label an answer as a recommendation; that needs a person reading the trial file. To rewrite the analysis for an existing run:

```bash
make analyze RUN=results/RUN_ID
```

To put two runs side by side, with every setting and what each run recorded:

```bash
make compare BASE=results/RUN_ID RUN=results/OTHER_RUN_ID
```

The comparison is written beside the second run. It reads both runs' saved records and changes neither.

To run a different claim, copy a definition and change the texts, entities, queries, models, settings, thresholds, or trial count. The definition is validated before anything starts, and an unknown key stops the run.

## Inspect the graph

Open Neo4j Browser at the HTTP port for the arm: `BASE_HTTP_PORT` for control, then +1 for single, +2 for copies, +3 for distinct. Log in as `neo4j` with the password in `.env`, and run:

```cypher
MATCH p=(m:Message)-[:MENTIONS]->(e:Entity)
WHERE e.name = 'Meadowlight Lamp'
RETURN p
```

Match the entity ID and source-message count to that arm's `entity_search` file. A source link shows where a claim came from; it does not certify the claim.

## Stop and clean up

```bash
make stop RUN=results/RUN_ID
```

This removes the run's containers and volumes. The saved records are untouched.

## Limits

- One library at one commit, one embedding model, one fabricated claim, and the two settings profiles above. Nothing here generalizes without a new run.
- The procurement ontology was written for this experiment and committed before the run that uses it. A different ontology may extract differently.
- With one extractor driven by the ontology, strict validation has nothing to reject: the extractor emits only the types the ontology declares. Strict validation acts when another extractor or a direct write supplies a type.
- Similarity scores measure wording overlap with the query. They are not a measure of truth.
- Agent answers vary between trials. The number of trials is small and is stated wherever a count is given.
- The GLiNER and embedding-model loaders emit compatibility warnings. They are left visible in the logs. Identical embedding hashes across runs show the setup is repeatable; they do not show the warnings are harmless.
- Agent trial files contain input text and provider metadata. Read them before publishing a new run.

## Repository scaffolding

This repository was started with `init-agent-project` from [ai-agent-utils](https://github.com/rctruta/ai-agent-utils), which installs checks more usual in production code than in an experiment. None of them is needed to run the experiment. They are here because a result is only worth as much as the record behind it.

| Path | What it does |
| --- | --- |
| `.gates/FACTS.yaml`, `.gates/verify.py` | Each figure and quotation in `RESULTS.md` is registered with a file search or a command that reads it back from the run records. A commit is refused if one no longer matches. |
| `claim_trace/facts.py` | Derives the counts those checks compare against, using the standard library only. |
| other scripts in `.gates/` | Refuse a script with a literal URL or home path, a module that only its tests import, a notes folder git can reach, and a publishing file whose rules were never written. `.gates/tests/prove_gates.sh` shows each one firing on a planted violation. |
| `.pre-commit-config.yaml`, `.gitleaks.toml`, `ruff.toml` | Standard checks: files parse, lint is clean, no secret or home-directory path is committed. |
| `.githooks/` | `pre-commit` runs everything above; `pre-push` refuses a dirty tree or a failing test. Hooks do not come with a clone, hence `git config core.hooksPath .githooks` in the setup. |
| `.github/workflows/ci.yml` | Runs the tests and the same gates on every pull request, where a local hook cannot be skipped. |
| `AGENTS.md`, `.claude/`, `.cursor/` | Describe these rules to coding agents working in the repository. The hooks enforce them; these files only explain. |

To check the registered facts yourself:

```bash
python3 .gates/verify.py
```

## License and citation

Copyright 2026 Ramona C. Truta. The code is licensed under the [Apache License 2.0](LICENSE). The written results and the records under `results/` are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/): reuse requires attribution. To cite this work, use [CITATION.cff](CITATION.cff).
