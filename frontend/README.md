# DraftGuard comparison screen

This React + TypeScript + Vite frontend implements DraftGuard's first comparison screen.

## Prerequisites

- Node.js and npm
- The DraftGuard FastAPI backend running locally on port `8000`

## Run locally

From the repository root, start the backend:

```bash
source .venv/bin/activate
python -m uvicorn backend.main:app --reload
```

In a second Terminal window, start the frontend:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, normally `http://localhost:5173`.

The frontend requests `/api/demo/comparison`. Vite proxies that path to the local backend endpoint `/demo/comparison`, so no backend changes are needed.

## Checks performed

- `npm run lint` passed.
- `npm run build` passed.
- The screen was checked against the running local backend.
- The returned synthetic-demo notice, comparison status, all seven fields, container-count mismatch, and expandable evidence were verified.
- The unavailable-backend error state and Retry recovery were verified.

## Current limitation

This screen displays only the synthetic demo comparison endpoint. It does not yet include an inbox, revision timeline, or human approval workflow.
