# GitHub Collaboration Repository Design

## Goal

Create a private GitHub repository and local project scaffold for the insurance product recommendation coursework project, so the team can collaborate through branches, Pull Requests, shared documentation, and a consistent FastAPI project structure.

## Repository Structure

The repository uses a lightweight FastAPI layout with separate folders for application code, raw and generated data, saved models, documents, and tests. Generated databases, processed data, exported results, virtual environments, and trained model artifacts are ignored by Git.

## Collaboration Model

The team uses `main` as the stable branch. Each working area has a feature branch: `feature/data-model`, `feature/backend`, `feature/frontend`, and `feature/docs`. Group members develop on their own branches and submit Pull Requests for review before merging to `main`.

## First Version Scope

The initial repository includes a minimal FastAPI app with a health check, dependency list, `.gitignore`, collaboration documentation, planned API notes, a development task board, and a Pull Request template. The full recommendation workflow will be implemented in later tasks by the assigned group members.

## Verification

The first executable behavior is the `/health` endpoint. It is covered by `tests/test_app.py` and should pass with `python -m pytest tests/test_app.py -q`.
