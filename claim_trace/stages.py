"""Ingestion and retrieval through the memory library's public API."""
import hashlib
import json
from pathlib import Path

from neo4j_agent_memory import Neo4jConfig, connect
from neo4j_agent_memory.config.settings import (
    BoltSettings,
    ExtractionConfig,
    ExtractorType,
    SchemaConfig,
)
from pydantic import BaseModel

from claim_trace import databases
from claim_trace.config import Settings
from claim_trace.constants import (
    ARM_CONTROL,
    ARM_COPIES,
    COUNT_MESSAGES_QUERY,
    ENTITY_NODES_QUERY,
    ENTITY_SEARCH_FILE,
    EXPANSION_ARMS,
    INGEST_FILE,
    MESSAGE_ROLE,
    MESSAGE_SEARCH_FILE,
    NEO4J_USERNAME,
    SESSION_ID,
    STAGE_BASE,
    STAGE_EXPANDED,
)
from claim_trace.logger import get_logger
from claim_trace.models import (
    EntityHit,
    EntityNode,
    EntitySearchRecord,
    Experiment,
    IngestedMessage,
    IngestRecord,
    MessageHit,
    MessageSearchRecord,
    SourceMessage,
)

log = get_logger(__name__)


def client_settings(settings: Settings, experiment: Experiment, arm: str) -> BoltSettings:
    """Local extraction and embedding only: no language model takes part in ingestion."""
    return BoltSettings(
        neo4j=Neo4jConfig(uri=databases.bolt_uri(settings, arm), username=NEO4J_USERNAME,
                          password=settings.neo4j_password),
        llm=None,
        embedding=experiment.embedding_model,
        schema_config=SchemaConfig(ontology_path=None,
                                   validation_mode=experiment.validation_mode),
        extraction=ExtractionConfig(extractor_type=ExtractorType.PIPELINE,
                                    enable_spacy=False, enable_gliner=True,
                                    enable_llm_fallback=False,
                                    gliner_schema=experiment.gliner_schema),
    )


def stages_for(arm: str) -> tuple[str, ...]:
    return (STAGE_BASE, STAGE_EXPANDED) if arm in EXPANSION_ARMS else (STAGE_BASE,)


def final_stage(arm: str) -> str:
    return stages_for(arm)[-1]


def documents_for(experiment: Experiment, arm: str, stage: str) -> list[str]:
    if stage == STAGE_BASE:
        subject = experiment.control if arm == ARM_CONTROL else experiment.claim
        return [*experiment.background, subject]
    if arm not in EXPANSION_ARMS:
        raise ValueError(f"Arm {arm} has no {stage} stage")
    if arm == ARM_COPIES:
        return [experiment.claim] * len(experiment.supporting_claims)
    return list(experiment.supporting_claims)


def save(path: Path, record: BaseModel) -> None:
    """Write once. An existing file is a finished stage and is never overwritten."""
    with path.open("x") as stream:
        stream.write(record.model_dump_json(indent=2) + "\n")


async def ingest(client, experiment: Experiment, arm: str, stage: str) -> IngestRecord:
    if stage == STAGE_BASE:
        existing = (await client.query.cypher(COUNT_MESSAGES_QUERY))[0]["messages"]
        if existing:
            raise RuntimeError(f"Arm {arm} database is not empty: {existing} messages")
    messages = []
    for index, document in enumerate(documents_for(experiment, arm, stage)):
        session = SESSION_ID.format(experiment_id=experiment.experiment_id, arm=arm,
                                    stage=stage, index=index)
        message = await client.short_term.add_message(session, MESSAGE_ROLE, document)
        messages.append(IngestedMessage(id=str(message.id), session=session, text=document))
    return IngestRecord(arm=arm, stage=stage, validation=str(client.validation_mode),
                        messages=messages)


def embedding_sha256(embedding: list[float] | None) -> str | None:
    if not embedding:
        return None
    return hashlib.sha256(json.dumps(embedding).encode()).hexdigest()


async def search_entities(client, experiment: Experiment, arm: str,
                          stage: str) -> EntitySearchRecord:
    nodes = [
        EntityNode(
            id=row["id"], name=row["name"], type=row["type"], labels=row["labels"],
            sources=[SourceMessage(**source) for source in row["sources"] if source["id"]],
            embedding_sha256=embedding_sha256(row["embedding"]),
        )
        for row in await client.query.cypher(ENTITY_NODES_QUERY)
    ]
    searches: dict[str, dict[str, list[EntityHit]]] = {}
    for query in experiment.queries:
        searches[query] = {}
        for threshold in experiment.search_thresholds:
            hits = await client.long_term.search_entities(query, threshold=threshold)
            searches[query][str(threshold)] = [
                EntityHit(rank=rank, id=str(hit.id), name=hit.name,
                          similarity=hit.metadata["similarity"])
                for rank, hit in enumerate(hits, 1)
            ]
    return EntitySearchRecord(arm=arm, stage=stage, validation=str(client.validation_mode),
                              nodes=nodes, searches=searches)


async def search_messages(client, experiment: Experiment, arm: str,
                          stage: str) -> MessageSearchRecord:
    searches: dict[str, dict[str, list[MessageHit]]] = {}
    for query in experiment.queries:
        searches[query] = {}
        for threshold in experiment.search_thresholds:
            hits = await client.short_term.search_messages(query, threshold=threshold)
            searches[query][str(threshold)] = [
                MessageHit(rank=rank, id=str(hit.id), content=hit.content,
                           similarity=hit.metadata["similarity"])
                for rank, hit in enumerate(hits, 1)
            ]
    return MessageSearchRecord(arm=arm, stage=stage, searches=searches)


async def run_arm(settings: Settings, experiment: Experiment, arm: str, run_dir: Path) -> None:
    """Ingest and search every stage of one arm on its own database."""
    client = await connect(client_settings(settings, experiment, arm))
    try:
        for stage in stages_for(arm):
            names = {"arm": arm, "stage": stage}
            log.info("ingest arm=%s stage=%s", arm, stage)
            save(run_dir / INGEST_FILE.format(**names),
                 await ingest(client, experiment, arm, stage))
            log.info("entity search arm=%s stage=%s", arm, stage)
            save(run_dir / ENTITY_SEARCH_FILE.format(**names),
                 await search_entities(client, experiment, arm, stage))
            log.info("message search arm=%s stage=%s", arm, stage)
            save(run_dir / MESSAGE_SEARCH_FILE.format(**names),
                 await search_messages(client, experiment, arm, stage))
    finally:
        await client.close()
