import asyncio

import pytest

from claim_trace import stages
from claim_trace.manifest import load_experiment
from claim_trace.constants import ONTOLOGY_FILE
from tests.conftest import DEFINITION, STRICT_DEFINITION


def test_documents_follow_the_four_arm_design():
    experiment = load_experiment(DEFINITION)
    assert stages.documents_for(experiment, "control", "base")[-1] == experiment.control
    assert stages.documents_for(experiment, "single", "base") == [
        *experiment.background, experiment.claim]
    assert stages.documents_for(experiment, "copies", "expanded") == [experiment.claim] * 3
    assert stages.documents_for(experiment, "distinct", "expanded") == (
        experiment.supporting_claims)
    with pytest.raises(ValueError):
        stages.documents_for(experiment, "single", "expanded")
    assert stages.final_stage("single") == "base"
    assert stages.final_stage("distinct") == "expanded"


def test_client_uses_the_definition_and_no_language_model(settings, tmp_path):
    experiment = load_experiment(DEFINITION)
    config = stages.client_settings(settings, experiment, "single", tmp_path)
    assert config.schema_config.ontology_path is None
    assert config.llm is None
    assert config.neo4j.uri == "bolt://localhost:8001"
    assert config.schema_config.validation_mode == experiment.validation_mode
    assert config.extraction.gliner_schema == experiment.gliner_schema
    assert config.extraction.enable_llm_fallback is False


def test_embedding_hash_is_stable_and_absent_without_a_vector():
    assert stages.embedding_sha256(None) is None
    assert stages.embedding_sha256([0.5, 0.25]) == stages.embedding_sha256([0.5, 0.25])
    assert stages.embedding_sha256([0.5, 0.25]) != stages.embedding_sha256([0.25, 0.5])


class UsedDatabase:
    class query:
        @staticmethod
        async def cypher(_query):
            return [{"messages": 4}]


def test_base_ingestion_refuses_a_database_that_already_holds_messages():
    experiment = load_experiment(DEFINITION)
    with pytest.raises(RuntimeError, match="not empty"):
        asyncio.run(stages.ingest(UsedDatabase(), experiment, "single", "base"))


def test_saved_records_are_never_overwritten(tmp_path):
    experiment = load_experiment(DEFINITION)
    path = tmp_path / "record.json"
    stages.save(path, experiment)
    with pytest.raises(FileExistsError):
        stages.save(path, experiment)


def test_strict_client_loads_the_frozen_ontology_and_names_no_schema(settings, tmp_path):
    experiment = load_experiment(STRICT_DEFINITION)
    config = stages.client_settings(settings, experiment, "single", tmp_path)
    assert config.schema_config.ontology_path == str(tmp_path / ONTOLOGY_FILE)
    assert config.schema_config.validation_mode == "strict"
    assert config.extraction.gliner_schema is None


class RecordingClient:
    """Stands in for the memory client: one stored mention, and a log of provenance writes."""

    def __init__(self):
        self.linked = []
        self.query = self
        self.long_term = self

    async def cypher(self, _query, params):
        assert params == {"message_id": "m-1"}
        return [{"id": "e-1", "metadata": '{"extracted_by": "gliner2"}',
                 "confidence": 0.9, "start_pos": 4, "end_pos": 20}]

    async def link_entity_to_message(self, entity, message_id, **values):
        self.linked.append(("message", entity, message_id, values))

    async def link_entity_to_extractor(self, entity, extractor, **values):
        self.linked.append(("extractor", entity, extractor, values))


def test_provenance_links_pass_on_only_what_the_library_stored():
    client = RecordingClient()
    assert asyncio.run(stages.link_provenance(client, "m-1")) == 1
    assert client.linked == [
        ("message", "e-1", "m-1", {"confidence": 0.9, "start_pos": 4, "end_pos": 20}),
        ("extractor", "e-1", "gliner2", {"confidence": 0.9}),
    ]
