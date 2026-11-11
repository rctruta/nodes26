---
name: gates
description: What this repository enforces mechanically. Read before making a factual claim, citing a number, attributing work to someone, or changing a working configuration.
---

This repo has gates. They are git hooks and plain scripts in .gates/, so they
run regardless of which agent is driving. This file describes them; it does not
enforce anything.

## Before stating a number or attributing work

Every load-bearing claim must be registered in .gates/FACTS.yaml with a source.
Run: python3 .gates/verify.py

A claim you have not checked is not ready to write down. Attributions to third
parties — who filed an issue, who reviewed what — are verified against the
source system, never against an earlier draft.

## Before changing something that works

Tag the known-good commit, with the command that proves it in the message:

    git tag -a known-good-<name> -m "<command that proves it works>"

Then "it worked before" is a recorded command rather than a memory, and
nothing extra has to be installed or kept working.

## Declarative Gate Configuration

Gate engines in `.gates/` are immutable mechanism. Project paths, thresholds, and exclusions are configured in `pyproject.toml` (under `[tool.gates]`) or `.gates.toml`. Never edit the Python code in `.gates/` to change project behavior.

## Prove the gates still fire

    .gates/tests/prove_gates.sh
