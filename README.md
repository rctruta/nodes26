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

Agent trials then give a fresh agent one read-only tool, the library's own `search_memory`, restricted to one memory type per trial. The agent has no other tool and cannot execute anything.

The definition in `experiments/catalog_lamp.json` selects strict validation and the library's built-in POLE+O GLiNER schema. These are **type checks**, not evidence that the catalog claim is true. Extraction and embedding run locally; no language model takes part in ingestion or search.

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

To run a different claim, copy `experiments/catalog_lamp.json` and change the texts, entities, queries, models, schema, thresholds, or trial count. The definition is validated before anything starts, and an unknown key stops the run.

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

- One library at one commit, one schema, one embedding model, one fabricated claim. Nothing here generalizes without a new run.
- Similarity scores measure wording overlap with the query. They are not a measure of truth.
- Agent answers vary between trials. The number of trials is small and is stated wherever a count is given.
- The GLiNER and embedding-model loaders emit compatibility warnings. They are left visible in the logs. Identical embedding hashes across runs show the setup is repeatable; they do not show the warnings are harmless.
- Agent trial files contain input text and provider metadata. Read them before publishing a new run.

## License and citation

Copyright 2026 Ramona C. Truta. The code is licensed under the [Apache License 2.0](LICENSE). The written results and the records under `results/` are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/): reuse requires attribution. To cite this work, use [CITATION.cff](CITATION.cff).
