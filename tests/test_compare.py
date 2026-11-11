from claim_trace import analyze, compare, manifest
from tests.conftest import DEFINITION, STRICT_DEFINITION
from tests.test_analyze import write_core


def build(run_dir, definition, settings, *, provenance):
    run_dir.mkdir()
    manifest.freeze(definition, run_dir, settings)
    experiment, _ = manifest.load_frozen(run_dir)
    write_core(run_dir, experiment, provenance=provenance)
    return run_dir


def test_comparison_shows_which_settings_differ_and_what_each_run_recorded(tmp_path, settings):
    base = build(tmp_path / "20260101T000000Z", DEFINITION, settings, provenance=None)
    strict = build(tmp_path / "20260102T000000Z", STRICT_DEFINITION, settings, provenance=1)
    path = compare.write(base, strict)
    assert path.name == "comparison-with-20260101T000000Z.md"
    text = path.read_text()
    assert "| Provenance links written | no | yes | **no** |" in text
    assert "| Validation mode | strict | strict | yes |" in text
    assert "none; built-in schema `poleo`" in text and "procurement_catalog.yaml" in text
    assert "search_memory, get_entity_provenance, cypher_query" in text
    assert "OBJECT; 1; not recorded; 2;" in text
    assert "OBJECT:PRODUCT; 1; 1; 2;" in text
    assert "| single | long_term | not run; not run; not run |" in text


def test_analysis_header_states_the_settings(tmp_path, settings):
    strict = build(tmp_path / "20260102T000000Z", STRICT_DEFINITION, settings, provenance=1)
    report = analyze.write(strict)
    assert report.settings.provenance_links and report.settings.ontology_sha256
    text = (strict / "analysis.md").read_text()
    assert "- Provenance links written at ingestion: yes" in text
    assert "- Validation mode: strict" in text
    assert "- Agent tools: search_memory, get_entity_provenance, cypher_query" in text


def test_saved_records_stay_untouched_by_a_comparison(tmp_path, settings):
    base = build(tmp_path / "20260101T000000Z", DEFINITION, settings, provenance=None)
    strict = build(tmp_path / "20260102T000000Z", STRICT_DEFINITION, settings, provenance=1)
    before = sorted(path.name for path in base.iterdir())
    compare.write(base, strict)
    assert sorted(path.name for path in base.iterdir()) == before
