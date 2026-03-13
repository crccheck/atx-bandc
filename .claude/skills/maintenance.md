---
name: running-maintenance
description: Runs the full maintenance workflow for the atx-bandc project: install dependencies, run tests, build Docker image, and test WebP thumbnail generation. Use when user asks to "run maintenance", "do a maintenance run", or "check the build".
allowed-tools: Bash
---

## Workflow

Run each step in order. Stop and report if any step fails.

1. `make install` — sync dependencies
2. `source .venv/bin/activate && make test` — run test suite (bare `python` in Makefile requires venv activated)
3. `make docker/build` — build production and test Docker images
4. `make docker/webptest` — test WebP thumbnail generation in Docker

Report a summary of which steps passed or failed.
