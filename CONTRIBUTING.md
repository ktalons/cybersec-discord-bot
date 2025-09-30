# Contributing to Cybersec Discord Bot

Thanks for your interest in contributing! This guide helps you get set up and submit effective contributions.

## Getting started
- Make sure you have Python 3.10+.
- Create a virtual environment and install deps:
  ```bash
  python3 -m venv .venv
  . .venv/bin/activate
  pip install -r requirements.txt
  cp .env.example .env
  # Fill in .env values
  ```
- Run locally:
  ```bash
  python -m src.main
  ```

## Branching
- Fork the repo (if outside the org) and create a feature branch:
  - feature/<short-description>
  - bugfix/<short-description>
  - docs/<short-description>

## Commits
- Keep commits focused and descriptive (imperative mood, e.g., "Add verification cog tests").
- Reference related issues (e.g., "Fixes #123").

## Pull Requests
- Ensure the description explains the change and rationale.
- Include screenshots or logs when helpful.
- Update docs (README, examples) if behavior changes.
- Keep PRs small and focused when possible.

## Issues
- Use the provided templates for bug reports and feature requests.
- For bugs, include reproduction steps, expected/actual results, and environment details.

## Code style & tests
- No strict linter/formatter is enforced by CI yet. You may use tools like `ruff` and `black` locally.
- If you add tests in the future, describe how to run them in the PR.

Thanks again for contributing!
