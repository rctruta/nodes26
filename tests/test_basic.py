"""The first test in a new project, and deliberately not `assert True`.

A suite whose only test cannot fail is a gate that passes forever. The
pre-commit hook runs `pytest tests/`, so `assert True` here meant every new
project shipped with a green gate protecting nothing.

These two can fail, and check the only thing that exists before any project
code does: that the workspace's own protections are installed and wired.

Replace them when there is something real to test. Do not delete them
without replacing them -- an empty tests/ makes the hook pass vacuously.
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# A gate that reads a named file instead of the git index is given one.
FILE_ARGS = {"check_outbound.py": ["--no-private", "README.md"]}


def test_gates_are_installed_and_runnable():
    """Every gate exists and runs. Exit 1 is a finding; a crash is a defect."""
    gates = sorted((ROOT / ".gates").glob("check_*.py"))
    assert gates, "no gates in .gates/ -- this workspace is not protected"
    for g in gates:
        r = subprocess.run([sys.executable, str(g), *FILE_ARGS.get(g.name, [])], cwd=ROOT,
                           capture_output=True, text=True, timeout=60)
        assert r.returncode in (0, 1), (
            f"{g.name} crashed with exit {r.returncode}: {r.stderr[-200:]}")


def test_hooks_are_wired():
    """A hook git does not know about is a file, not a gate."""
    r = subprocess.run(["git", "config", "core.hooksPath"], cwd=ROOT,
                       capture_output=True, text=True)
    assert r.stdout.strip() == ".githooks", (
        "core.hooksPath is not .githooks, so the pre-commit gate never runs")
