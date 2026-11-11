# AGENTS.md — Agent Contract & Workspace Policy

You are a delegate; the human owns this repository. This file documents what
the repo ENFORCES. It does not enforce anything itself — the hooks do.

Prose that an agent re-reads every turn is expensive and does not reliably
change behavior. So this file is minimal, and every rule below is backed by a
mechanism. **You do not need to memorize this: if you cross a boundary, a gate
stops you.**

## The gates (enforced)
- **Push a clean tree.** The `pre-push` hook refuses a dirty working tree (and,
  for Python, a red test suite). `git status` must be clean at end of turn.
- **Stage files by name.** Never `git add -A` or `git add .`. Review `git status`
  and `git diff --staged` before committing to confirm each path is meant to be public.
- **Agents do not publish.** No `git push` unless the owner explicitly requests
  it in the current session, and never directly to `main`. Work on feature branches.
- **Private material stays outside the repository.** Personal notes and unpublished
  work must never enter tracked files.
- **Commit messages are public writing.** Use standard Conventional Commits
  (`feat: ...`, `fix: ...`, `chore: ...`). Keep subjects concise and technical.
- **Branch protection.** Remote branch protection (Require PR + Include administrators)
  is the true multi-agent boundary. Structure keeps agents from colliding.

## The rules a hook can't enforce (on your honor — and watched)
- **No bypass.** Never `git push --no-verify`, `git commit --no-verify`, or
  `gh pr merge --admin` to route around a gate.
- **No agent attribution.** The human owns the commit history.

## Claim integrity (enforced)
- Every load-bearing number is registered in .gates/FACTS.yaml with a source,
  and pre-commit re-checks it. A number you have not verified does not go into
  an outward-facing document.
- Fabricated claims are banned by pattern. When a wrong number is found in the
  wild, add it to the banned list so it cannot return.
- Third-party attribution is verified against the source system - the issue
  tracker, the log, the registry - never against an earlier draft.

## Change safety
- Before mutating a working system, tag the known-good commit and put the
  command that proves it in the tag message:
  git tag -a known-good-<name> -m "<command that proves it works>"
  Then "it worked before" is a recorded command rather than a memory.

## What else is enforced here

This file does not list the gates. A prose list goes stale the moment a gate
is added or removed, which is the failure the gates exist to prevent. Ask the
repository instead:

    ls .gates/*.py                  what is installed
    python3 .gates/check_version.py whether it is current with the registry
    sh .gates/gates_report.sh       what each one has found
    cat .gates/NOT_ADOPTED          what this repo declines, if anything does

Read a gate's docstring for what it refuses and the incident that produced it.
Every one of them was a rule stated in prose first, and broken anyway.

## Proving the gates
Run .gates/tests/prove_gates.sh - it demonstrates each gate firing.
An untested gate is theatre.

## If you write a check

- Wire it into .githooks/pre-commit in the SAME change. A check nothing runs
  is a file, not a gate.
- Use the standard library only. This repo may have nothing installed.
- Prove it both ways: it fires on a planted violation AND stays quiet on a
  clean tree.
- A gate may not exempt its own file unless there is genuinely nothing there
  to find, and then say so in the code.

## If a gate fires and you think it is wrong

Check its premise before changing anything. A finding can be about the checker
rather than the code - the wrong interpreter, a trigger that means something
narrower than it looks, a probe asserting an old meaning. Establish which,
then fix that.

Never route around it: no `--no-verify`, no `--admin`, no deleting the check.
If the gate is genuinely wrong, fix the gate and prove the fix.

## Documentation Triggers (When to Update README)
Do NOT update the README for internal bug fixes, refactorings, or minor code edits.
Review and update README and agent instructions ONLY when a change crosses an external boundary:
1. CLI / Entrypoints: A command, CLI flag, or runner script is added, renamed, or removed.
2. Dependencies & Toolchain: A dependency, interpreter version, or external tool requirement is changed in pyproject.toml / package.json.
3. Environment & Configuration: A new environment variable, configuration table, or setup prerequisite is introduced.
4. Repository Layout: A top-level directory or primary data pipeline is added, moved, or removed.
If none of these boundaries was crossed, leave the README untouched.
