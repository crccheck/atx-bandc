---
name: maintenance
description: 'Runs the full maintenance workflow for the atx-bandc project: pull latest Docker base images, install dependencies, run tests, build Docker image, and test WebP thumbnail generation. Use when user asks to "run maintenance", "do a maintenance run", "check the build", or "check Dockerfile versions".'
allowed-tools: Bash
---

## Workflow

Run each step in order. Stop and report if any step fails.

1. Ensure on latest `main`: `git checkout main` then `git pull`
2. Create a maintenance branch: `git checkout -b chore/maintenance`
3. Pull the base image used in the Dockerfile — keeps the local cache current
4. `make install` — sync dependencies
5. `source .venv/bin/activate && make test` — run test suite (bare `python` in Makefile requires venv activated)
6. `make docker/build` — build production and test Docker images
7. `make docker/webptest` — test WebP thumbnail generation in Docker
8. Commit any changes (e.g. updated lock files, dependency bumps) to the branch

Report a summary of which steps passed or failed.
