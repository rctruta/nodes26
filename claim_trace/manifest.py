"""Freeze the experiment definition and record what produced a run."""
import hashlib
import subprocess
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from claim_trace import databases
from claim_trace.config import ROOT, Settings
from claim_trace.constants import (
    AGENT_DISTRIBUTION,
    ARMS,
    EXPERIMENT_FILE,
    LOCKFILE,
    MANIFEST_FILE,
    MEMORY_DISTRIBUTION,
    ONTOLOGY_FILE,
    RUN_ID_FORMAT,
)
from claim_trace.models import Experiment, Manifest


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def new_run_id() -> str:
    return datetime.now(timezone.utc).strftime(RUN_ID_FORMAT)


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                          check=True).stdout.strip()


def load_experiment(path: Path) -> Experiment:
    return Experiment.model_validate_json(path.read_bytes())


def freeze(source: Path, run_dir: Path, settings: Settings) -> Experiment:
    """Copy the definition into an empty run directory before any database write."""
    experiment = load_experiment(source)
    if any(run_dir.iterdir()):
        raise FileExistsError(f"Run directory must be empty: {run_dir}")
    # Read before the frozen copy exists, so the run's own files never count as changes.
    git_commit, git_dirty = _git("rev-parse", "HEAD"), bool(_git("status", "--porcelain"))
    frozen = run_dir / EXPERIMENT_FILE
    frozen.write_bytes(source.read_bytes())
    ontology_source = ontology_sha256 = None
    if experiment.ontology_path is not None:
        ontology_source = ROOT / experiment.ontology_path
        (run_dir / ONTOLOGY_FILE).write_bytes(ontology_source.read_bytes())
        ontology_sha256 = sha256(run_dir / ONTOLOGY_FILE)
    manifest = Manifest(
        run_id=run_dir.name,
        captured_at_utc=datetime.now(timezone.utc).isoformat(),
        experiment_id=experiment.experiment_id,
        experiment_source_name=source.name,
        experiment_sha256=sha256(frozen),
        git_commit=git_commit,
        git_dirty=git_dirty,
        lockfile_sha256=sha256(ROOT / LOCKFILE),
        python_version=sys.version.split()[0],
        memory_library_version=version(MEMORY_DISTRIBUTION),
        agent_library_version=version(AGENT_DISTRIBUTION),
        neo4j_image=settings.neo4j_image,
        neo4j_host=settings.neo4j_host,
        http_ports=[databases.ports(settings, arm)[0] for arm in ARMS],
        bolt_ports=[databases.ports(settings, arm)[1] for arm in ARMS],
        ontology_source_name=None if ontology_source is None else ontology_source.name,
        ontology_sha256=ontology_sha256,
    )
    (run_dir / MANIFEST_FILE).write_text(manifest.model_dump_json(indent=2) + "\n")
    return experiment


def load_frozen(run_dir: Path) -> tuple[Experiment, Manifest]:
    """Read a run's definition, refusing one that changed after it was frozen."""
    manifest = Manifest.model_validate_json((run_dir / MANIFEST_FILE).read_bytes())
    frozen = run_dir / EXPERIMENT_FILE
    if sha256(frozen) != manifest.experiment_sha256:
        raise ValueError(f"Frozen experiment hash differs from manifest: {run_dir}")
    experiment = load_experiment(frozen)
    if (experiment.ontology_path is None) != (manifest.ontology_sha256 is None):
        raise ValueError(f"Definition and manifest disagree about an ontology: {run_dir}")
    if (manifest.ontology_sha256 is not None
            and manifest.ontology_sha256 != sha256(run_dir / ONTOLOGY_FILE)):
        raise ValueError(f"Frozen ontology hash differs from manifest: {run_dir}")
    return experiment, manifest
