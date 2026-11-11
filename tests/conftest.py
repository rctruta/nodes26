import json
from pathlib import Path

import pytest

from claim_trace.config import ROOT, Settings

DEFINITION = ROOT / "experiments" / "catalog_lamp.json"


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(_env_file=None, neo4j_password="test-password", neo4j_host="localhost",
                    neo4j_image="neo4j:test", base_http_port=7000, base_bolt_port=8000,
                    results_dir=tmp_path, compose_project_prefix="trace", log_level="INFO")


@pytest.fixture
def definition() -> dict:
    return json.loads(DEFINITION.read_text())
