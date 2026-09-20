# DraftGuard — Developer Setup

## Current State

Implemented:
- Shared email and extraction models in backend/models.py
- Seven-field shipment record with validation
- GET /health
- GET /demo/comparison with explicitly synthetic data

Not yet implemented:
- Real email classification or document extraction
- Real comparison pipeline
- Dashboard
- Human-review workflow
- Revision tracking
- Submission exporter

The demo endpoint does not process documents.

## Prerequisites

- Git and access to the private repository
- Python 3.13 recommended to match the initial setup
- Node.js and npm will be needed for frontend development

The current Python dependency file was generated on macOS.
Windows users should use WSL for this initial setup because the
dependency list includes uvloop.

## Initial Setup — macOS / Linux / WSL

Clone the repository once:

    git clone https://github.com/griffburntwood/draftguard.git
    cd draftguard

Create and activate an isolated Python environment:

    python3 -m venv .venv
    source .venv/bin/activate

Install backend dependencies:

    python -m pip install -r backend/requirements.txt

Run the backend from the repository root:

    python -m uvicorn backend.main:app --reload

Open:
- Health: http://127.0.0.1:8000/health
- API documentation: http://127.0.0.1:8000/docs
- Demo comparison: http://127.0.0.1:8000/demo/comparison

Stop the server with Control + C.

## Starting Work Later

From the repository root:

    source .venv/bin/activate

Before creating a new task branch, ensure your working tree is clean:

    git status
    git switch main
    git pull --ff-only

Create a branch with a descriptive name, for example:

    git switch -c feature/email-classification

Do not discard uncommitted work to switch branches.
Commit your work or ask the team lead for help.

## Required Reading

- docs/PROJECT_SCOPE.md
- docs/TEAM.md
- docs/DATA_CONTRACT.md
- backend/models.py

## Working With an AI Coding Tool

Give it your assigned task and the required reading above.

Ask it to:
1. Inspect the existing code before making changes.
2. Work only on the assigned component.
3. Follow the shared data contract.
4. Coordinate proposed contract changes with the team lead.
5. Keep mock data visibly labelled.
6. Add meaningful checks for the behavior implemented.
7. Explain changed files and how to verify the result.
8. Never claim a test passed unless it actually ran.

Do not paste API keys or the organizer answer key into prompts.

## Sharing Changes

Stage only the files you intend to include.
Commit and push your feature branch.
Open a pull request targeting main.

Include:
- What changed
- How to run or verify it
- Checks actually performed
- Known limitations

Have another teammate review before merging.

## Dataset and Secrets

Do not commit:
- .venv or node_modules
- .env files containing secrets
- The supplied dataset ZIPs
- The organizer Docker package
- ground_truth.json

Coordinate local dataset setup with the team lead.
Use clearly labelled synthetic examples for shareable demos.
