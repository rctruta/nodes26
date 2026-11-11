import json

import pytest
from pydantic import ValidationError

from claim_trace.manifest import load_experiment
from claim_trace.models import Experiment
from tests.conftest import DEFINITION, STRICT_DEFINITION


def test_shipped_definition_is_valid():
    experiment = load_experiment(DEFINITION)
    assert experiment.primary_query == experiment.queries[0]
    assert experiment.target_entity in experiment.claim
    assert experiment.control_entity in experiment.control


@pytest.mark.parametrize("change", [
    {"control": None},                      # control equal to claim
    {"unknown_key": "x"},                   # a typo must stop the run
    {"search_thresholds": [1.5]},
    {"trials_per_stage": 0},
    {"supporting_claims": ["A sentence naming no product."]},
    {"schema_version": 2},
])
def test_invalid_definitions_are_refused(definition, change):
    if change == {"control": None}:
        change = {"control": definition["claim"]}
    with pytest.raises(ValidationError):
        Experiment.model_validate({**definition, **change})


def test_definition_file_with_bad_json_is_refused(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text(json.dumps({"schema_version": 1}))
    with pytest.raises(ValidationError):
        load_experiment(path)


def test_version_1_definition_gets_the_fixed_baseline_settings():
    experiment = load_experiment(DEFINITION)
    assert experiment.ontology_path is None
    assert experiment.provenance_links is False
    assert experiment.agent_tools == ["search_memory"]


def test_version_1_definition_cannot_set_a_later_field(definition):
    with pytest.raises(ValidationError, match="schema_version 2"):
        Experiment.model_validate({**definition, "provenance_links": True})


def test_strict_definition_states_every_setting_and_differs_only_in_them():
    baseline, strict = load_experiment(DEFINITION), load_experiment(STRICT_DEFINITION)
    assert strict.ontology_path and strict.gliner_schema is None
    assert strict.provenance_links is True
    assert "get_entity_provenance" in strict.agent_tools
    settings = {"schema_version", "experiment_id", "gliner_schema", "ontology_path",
                "provenance_links", "agent_tools"}
    assert baseline.model_dump(exclude=settings) == strict.model_dump(exclude=settings)


@pytest.mark.parametrize("change", [
    {"provenance_links": None},                      # every setting must be stated
    {"gliner_schema": "poleo"},                      # a schema name would override the ontology
    {"ontology_path": None},                         # neither schema nor ontology
    {"agent_tools": ["get_entity_provenance"]},      # search is required
    {"agent_tools": ["search_memory", "search_memory"]},
    {"validation_mode": "lenient"},
])
def test_inconsistent_version_2_settings_are_refused(strict_definition, change):
    with pytest.raises(ValidationError):
        Experiment.model_validate({**strict_definition, **change})


def test_version_2_definition_missing_a_setting_is_refused(strict_definition):
    del strict_definition["agent_tools"]
    with pytest.raises(ValidationError):
        Experiment.model_validate(strict_definition)
