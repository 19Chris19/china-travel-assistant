# Agent Engineering Rules

This repository uses evidence-backed, recoverable Git workflows.

- Start each change from a clean `main` in a dedicated `codex/<change-id>` branch and worktree.
- Record the objective, risks, acceptance criteria, commits, and verification in `.planning/changes/`.
- Stage explicit paths only. Never use `git add .` or `git add -A`.
- Keep commits atomic and include `Change-ID`, verification, rollout, and rollback details in the commit body.
- Never commit credentials, local configuration, generated user itineraries, browser state, or private conversation data.
- Merge `main` through a reviewed GitHub pull request after required CI checks pass. Never force-push or rewrite published history.
- Tag releases only from a verified `main` commit and retain checksums for release artifacts.

