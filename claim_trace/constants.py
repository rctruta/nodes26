"""Fixed names and formats. Values that vary per machine live in `.env`."""

ARM_CONTROL = "control"
ARM_SINGLE = "single"
ARM_COPIES = "copies"
ARM_DISTINCT = "distinct"
ARMS = (ARM_CONTROL, ARM_SINGLE, ARM_COPIES, ARM_DISTINCT)
EXPANSION_ARMS = (ARM_COPIES, ARM_DISTINCT)

STAGE_BASE = "base"
STAGE_EXPANDED = "expanded"

# The library's own names for its two searchable stores.
MEMORY_ENTITY = "long_term"
MEMORY_MESSAGE = "short_term"
MEMORY_TYPES = (MEMORY_ENTITY, MEMORY_MESSAGE)

EXPERIMENT_FILE = "experiment.json"
MANIFEST_FILE = "manifest.json"
ONTOLOGY_FILE = "ontology.yaml"
COMPARISON_FILE = "comparison-with-{base_run_id}.md"
ANALYSIS_JSON_FILE = "analysis.json"
ANALYSIS_MARKDOWN_FILE = "analysis.md"
INGEST_FILE = "{arm}-{stage}-ingest.json"
ENTITY_SEARCH_FILE = "{arm}-{stage}-entity_search.json"
MESSAGE_SEARCH_FILE = "{arm}-{stage}-message_search.json"
AGENT_FILE = "{arm}-{stage}-agent-{memory_type}-{trial}.json"

RUN_ID_FORMAT = "%Y%m%dT%H%M%SZ"
SESSION_ID = "{experiment_id}-{arm}-{stage}-{index}"
MESSAGE_ROLE = "user"

NEO4J_USERNAME = "neo4j"
BOLT_URI = "bolt://{host}:{port}"
BOLT_WAIT_SECONDS = 120
BOLT_CONNECT_TIMEOUT_SECONDS = 4
BOLT_RETRY_SECONDS = 1

DOCKER = "docker"
COMPOSE_FILE = "compose.yaml"
COMPOSE_PROJECT = "{prefix}-{run_id}-{arm}"

LOCKFILE = "uv.lock"
MEMORY_DISTRIBUTION = "neo4j-agent-memory"
AGENT_DISTRIBUTION = "pydantic-ai-slim"
AGENT_SEARCH_TOOL = "search_memory"
TOOL_ERROR_PREFIX = "ERROR: "
STOPPED_REQUEST_LIMIT = "request_limit"
EXTRACTOR_METADATA_KEY = "extracted_by"

COUNT_MESSAGES_QUERY = "MATCH (m:Message) RETURN count(m) AS messages"
MESSAGE_MENTIONS_QUERY = """MATCH (m:Message {id: $message_id})-[r:MENTIONS]->(e:Entity)
RETURN e.id AS id, e.metadata AS metadata, r.confidence AS confidence,
       r.start_pos AS start_pos, r.end_pos AS end_pos
ORDER BY id"""
ENTITY_NODES_QUERY = """MATCH (e:Entity) OPTIONAL MATCH (m:Message)-[:MENTIONS]->(e)
RETURN e.id AS id, e.name AS name, e.type AS type, e.subtype AS subtype,
       labels(e) AS labels, e.embedding AS embedding,
       collect(DISTINCT {id: m.id, content: m.content}) AS sources
ORDER BY name, id"""

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
ANSWER_EXCERPT_CHARS = 450

# Decoration only: download progress bars, a vendor banner, and a tokenizer
# fork notice. Warnings and library log output are left visible.
DISPLAY_ENV_DEFAULTS = {
    "HF_HUB_DISABLE_PROGRESS_BARS": "1",
    "PYDANTIC_AI_NO_BANNER": "1",
    "TOKENIZERS_PARALLELISM": "false",
}

# What a version 1 definition always did. Version 2 definitions state each one.
V1_FIXED_SETTINGS = {
    "ontology_path": None,
    "provenance_links": False,
    "agent_tools": [AGENT_SEARCH_TOOL],
}
