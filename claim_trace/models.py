"""Validated shapes for the experiment definition and every saved record."""
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, StringConstraints, model_validator

Text = Annotated[str, StringConstraints(min_length=1, pattern=r"\S")]
Threshold = Annotated[float, Field(ge=0, le=1)]


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Experiment(Record):
    schema_version: Literal[1]
    experiment_id: Text
    target_entity: Text
    control_entity: Text
    control: Text
    claim: Text
    background: Annotated[list[Text], Field(min_length=1)]
    supporting_claims: Annotated[list[Text], Field(min_length=1)]
    queries: Annotated[list[Text], Field(min_length=1)]
    agent_instructions: Text
    agent_model: Text
    embedding_model: Text
    validation_mode: Text
    gliner_schema: Text
    search_thresholds: Annotated[list[Threshold], Field(min_length=1)]
    agent_request_limit: PositiveInt
    trials_per_stage: PositiveInt

    @model_validator(mode="after")
    def entities_appear_in_their_documents(self) -> "Experiment":
        if self.control == self.claim:
            raise ValueError("control and claim must differ")
        if self.target_entity not in self.claim:
            raise ValueError("claim must name target_entity")
        if self.control_entity not in self.control:
            raise ValueError("control must name control_entity")
        if self.target_entity in self.control:
            raise ValueError("control must not name target_entity")
        if not all(self.target_entity in text for text in self.supporting_claims):
            raise ValueError("every supporting claim must name target_entity")
        return self

    @property
    def primary_query(self) -> str:
        return self.queries[0]

    @property
    def primary_threshold(self) -> str:
        return str(self.search_thresholds[0])


class IngestedMessage(Record):
    id: str
    session: str
    text: str


class IngestRecord(Record):
    arm: str
    stage: str
    validation: str
    messages: list[IngestedMessage]


class SourceMessage(Record):
    id: str
    content: str


class EntityNode(Record):
    id: str
    name: str
    type: str
    labels: list[str]
    sources: list[SourceMessage]
    embedding_sha256: str | None


class EntityHit(Record):
    rank: int
    id: str
    name: str
    similarity: float


class MessageHit(Record):
    rank: int
    id: str
    content: str
    similarity: float


class EntitySearchRecord(Record):
    arm: str
    stage: str
    validation: str
    nodes: list[EntityNode]
    # query -> threshold -> ordered hits
    searches: dict[str, dict[str, list[EntityHit]]]


class MessageSearchRecord(Record):
    arm: str
    stage: str
    searches: dict[str, dict[str, list[MessageHit]]]


class ToolCall(Record):
    query: str
    result: str
    elapsed_ms: int


class AgentTrial(Record):
    arm: str
    stage: str
    memory_type: str
    trial: int
    model: str
    started_utc: str
    elapsed_ms: int
    calls: list[ToolCall]
    output: str
    usage: dict[str, Any]
    messages: list[dict[str, Any]]


class Manifest(Record):
    run_id: str
    captured_at_utc: str
    experiment_id: str
    experiment_source_name: str
    experiment_sha256: str
    git_commit: str
    git_dirty: bool
    lockfile_sha256: str
    python_version: str
    memory_library_version: str
    agent_library_version: str
    neo4j_image: str
    neo4j_host: str
    http_ports: list[int]
    bolt_ports: list[int]


class SearchPosition(Record):
    rank: int
    similarity: float
    id: str


class SubjectNode(Record):
    id: str
    type: str
    labels: list[str]
    source_count: int
    embedding_sha256: str | None


class StageRow(Record):
    arm: str
    stage: str
    subject: str
    ingested_messages: int | None
    entity_count: int | None
    target_nodes: int | None
    node: SubjectNode | None
    entity_hit: SearchPosition | None
    message_hit: SearchPosition | None
    entity_search_ran: bool
    message_search_ran: bool


class Expansion(Record):
    same_node_id: bool
    sources_before: int
    sources_after: int
    same_embedding: bool
    same_score: bool
    same_rank: bool
    new_entities: list[str]


class TrialRow(Record):
    file: str
    arm: str
    stage: str
    memory_type: str
    trial: int
    subject: str
    tool_calls: int
    subject_in_tool_result: bool
    subject_in_answer: bool
    answer_excerpt: str
    input_tokens: int | None
    output_tokens: int | None


class Analysis(Record):
    run_id: str
    experiment_id: str
    experiment_sha256: str
    git_commit: str
    git_dirty: bool
    target: str
    control_entity: str
    primary_query: str
    primary_threshold: float
    core_complete: bool
    agents_complete: bool
    missing_files: list[str]
    rows: list[StageRow]
    expansions: dict[str, Expansion | None]
    trials: list[TrialRow]
