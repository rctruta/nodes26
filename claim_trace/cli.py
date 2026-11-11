"""Command line entry: run, agents, analyze, stop."""
import argparse
import asyncio
from pathlib import Path

from claim_trace import databases, manifest
from claim_trace.config import Settings
from claim_trace.constants import ARMS
from claim_trace.logger import configure, get_logger

log = get_logger(__name__)


def run(settings: Settings, source: Path) -> Path:
    """Freeze the definition, then ingest and search each arm on a fresh database."""
    from claim_trace import analyze, stages

    run_dir = settings.results_path / manifest.new_run_id()
    run_dir.mkdir(parents=True)
    experiment = manifest.freeze(source, run_dir, settings)
    for arm in ARMS:
        databases.start(settings, run_dir.name, arm)
        asyncio.run(databases.wait_for_bolt(settings, arm))
        asyncio.run(stages.run_arm(settings, experiment, arm, run_dir))
    report = analyze.write(run_dir)
    log.info("run complete dir=%s core_complete=%s", run_dir, report.core_complete)
    return run_dir


def run_agents(settings: Settings, run_dir: Path) -> None:
    """Run the planned agent trials against a run's live databases."""
    from claim_trace import agents, analyze

    experiment, _ = manifest.load_frozen(run_dir)
    for arm in ARMS:
        asyncio.run(databases.wait_for_bolt(settings, arm))
        asyncio.run(agents.run_arm(settings, experiment, arm, run_dir))
    report = analyze.write(run_dir)
    log.info("agent trials complete dir=%s trials=%s", run_dir, len(report.trials))


def run_analyze(run_dir: Path) -> None:
    from claim_trace import analyze

    report = analyze.write(run_dir)
    log.info("analysis written dir=%s missing_files=%s", run_dir, len(report.missing_files))


def stop(settings: Settings, run_dir: Path) -> None:
    for arm in ARMS:
        databases.stop(settings, run_dir.name, arm)


def main() -> None:
    parser = argparse.ArgumentParser(prog="claim_trace", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("run", help=run.__doc__).add_argument("experiment", type=Path)
    for name, helper in (("agents", run_agents.__doc__),
                         ("analyze", "Rewrite a run's analysis from its saved records."),
                         ("stop", "Remove a run's databases and volumes.")):
        commands.add_parser(name, help=helper).add_argument("run_dir", type=Path)
    args = parser.parse_args()
    settings = Settings()
    configure(settings.log_level)
    if args.command == "run":
        run(settings, args.experiment.resolve(strict=True))
        return
    run_dir = args.run_dir.resolve(strict=True)
    if args.command == "agents":
        run_agents(settings, run_dir)
    elif args.command == "analyze":
        run_analyze(run_dir)
    else:
        stop(settings, run_dir)
