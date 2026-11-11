# nodes26-graph-memory

An agent-safe workspace: humans and AI coding agents share this repository.
The rules of engagement
live in `AGENTS.md` — and they are **enforced by git hooks**, not merely
written down.

## Guardrails
- The pre-push hook refuses a dirty working tree — including untracked
  files — (and, for Python, a red test suite).
- `main` is the source of truth: work on branches, open PRs; never commit
  to `main` directly.

## Getting started
- **Fresh clone? Hooks do NOT clone.** Run this once per clone or the
  guardrails above are silently absent:
  `git config core.hooksPath .githooks`
- Python: open a new terminal and run `source .venv/bin/activate`.
- Copy `.env.example` to `.env` and set your keys. If you run more than
  one agent, give each process its own `AGENT_ID` (export it in that
  agent's environment — one shared `.env` can only hold one value).

## License
Add a LICENSE file of your choice (MIT is a common, permissive default).
