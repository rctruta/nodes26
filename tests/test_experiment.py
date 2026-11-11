import json

import pytest
from pydantic import ValidationError

from claim_trace.manifest import load_experiment
from claim_trace.models import Experiment
from tests.conftest import DEFINITION


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
