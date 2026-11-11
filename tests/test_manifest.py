import pytest

from claim_trace import manifest
from claim_trace.constants import EXPERIMENT_FILE, MANIFEST_FILE, RUN_ID_FORMAT
from claim_trace.constants import ONTOLOGY_FILE
from tests.conftest import DEFINITION, STRICT_DEFINITION


def test_freeze_copies_definition_and_records_its_hash(tmp_path, settings):
    manifest.freeze(DEFINITION, tmp_path, settings)
    assert (tmp_path / EXPERIMENT_FILE).read_bytes() == DEFINITION.read_bytes()
    experiment, record = manifest.load_frozen(tmp_path)
    assert record.experiment_sha256 == manifest.sha256(DEFINITION)
    assert record.bolt_ports == [8000, 8001, 8002, 8003]
    assert record.neo4j_image == "neo4j:test"
    assert len(record.git_commit) == 40
    assert experiment.experiment_id == record.experiment_id


def test_freeze_refuses_a_directory_that_already_holds_a_run(tmp_path, settings):
    (tmp_path / "leftover.json").write_text("{}")
    with pytest.raises(FileExistsError):
        manifest.freeze(DEFINITION, tmp_path, settings)
    assert not (tmp_path / MANIFEST_FILE).exists()


def test_changed_frozen_definition_is_refused(tmp_path, settings):
    manifest.freeze(DEFINITION, tmp_path, settings)
    frozen = tmp_path / EXPERIMENT_FILE
    frozen.write_text(frozen.read_text().replace("Meadowlight", "Moonlight"))
    with pytest.raises(ValueError, match="hash differs"):
        manifest.load_frozen(tmp_path)


def test_run_id_is_a_utc_timestamp():
    from datetime import datetime
    datetime.strptime(manifest.new_run_id(), RUN_ID_FORMAT)


def test_git_state_is_read_before_the_run_writes_its_first_file(tmp_path, settings, monkeypatch):
    files_seen = []

    def fake_git(*args):
        files_seen.append(sorted(path.name for path in tmp_path.iterdir()))
        return "a" * 40 if args[0] == "rev-parse" else ""

    monkeypatch.setattr(manifest, "_git", fake_git)
    manifest.freeze(DEFINITION, tmp_path, settings)
    assert files_seen == [[], []]
    assert manifest.load_frozen(tmp_path)[1].git_dirty is False


def test_baseline_run_freezes_no_ontology(tmp_path, settings):
    manifest.freeze(DEFINITION, tmp_path, settings)
    assert not (tmp_path / ONTOLOGY_FILE).exists()
    assert manifest.load_frozen(tmp_path)[1].ontology_sha256 is None


def test_ontology_is_frozen_and_a_later_edit_is_refused(tmp_path, settings):
    experiment = manifest.freeze(STRICT_DEFINITION, tmp_path, settings)
    frozen = tmp_path / ONTOLOGY_FILE
    record = manifest.load_frozen(tmp_path)[1]
    assert record.ontology_sha256 == manifest.sha256(frozen)
    assert record.ontology_source_name == experiment.ontology_path.rsplit("/", 1)[-1]
    frozen.write_text(frozen.read_text() + "# edited\n")
    with pytest.raises(ValueError, match="ontology hash differs"):
        manifest.load_frozen(tmp_path)


def test_upstream_ontology_is_the_recorded_upstream_file():
    from claim_trace.config import ROOT

    recorded = (ROOT / "ontologies" / "README.md").read_text()
    assert manifest.sha256(ROOT / "ontologies" / "upstream_support_desk.yaml") in recorded
