import asyncio

import pytest

from claim_trace import stages
from claim_trace.manifest import load_experiment
from tests.conftest import DEFINITION


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


def test_client_uses_the_definition_and_no_language_model(settings):
    experiment = load_experiment(DEFINITION)
    config = stages.client_settings(settings, experiment, "single")
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
