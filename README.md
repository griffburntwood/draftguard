# DraftGuard

DraftGuard compares Shipping Instructions (SI) with a draft Bill of Lading (BL). It routes incoming emails, extracts seven shipment fields, highlights differences with source evidence, and sends uncertain cases to a human action queue.

The revision workflow answers **“Did the new draft fix the problem, and did anything else change?”** Previous checks remain visible and a recorded review becomes outdated when source content or reviewed values change.

## Run locally

Use Python 3.13+ and Node 24. From the repository root:

```sh
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt pytest
python -m uvicorn backend.main:app --reload
```

In another terminal:

```sh
npm --prefix frontend ci
npm --prefix frontend run dev
```

Open the frontend URL printed by Vite. The backend provides `/health` and `/docs`; `/` is not a website. Default development frontend origin is localhost:5173. See [setup](docs/SETUP.md) for beginner instructions.

## Included workflow

- Classify email into BL comparison, SI request, invoice query, general, or spam.
- Paste text or select TXT, text-based PDF, DOCX, or XLSX documents.
- Compare shipper, consignee, notify party, loading/discharge ports, container count, and gross weight in kilograms.
- Distinguish confirmed differences from missing, ambiguous, unreadable, or wrong documents.
- Inspect text-line, PDF-page, DOCX-table/paragraph, or XLSX-cell evidence.
- Correct extraction with reviewer/reason/time while preserving original evidence.
- Recheck revised sources, see fixed/new/unresolved differences, and identify outdated reviews.
- Process a participant inbox ZIP and download one evaluator entry per email.

## Participant data and submission

Obtain the **participant bundle** directly from the organizer and share it privately with teammates. The data and organizer loader are not prerequisites in Git. Our runner reads JSON and referenced attachments directly; it does not execute bundled code or read an answer key.

```sh
python -m backend.batch /path/to/sdoc-hackathon-bundle.zip
# Or an extracted folder containing inbox/ and attachments/
python -m backend.batch /path/to/participant-folder --output data/results/submission.json
```

Outputs are `submission.json`, `processing_details.json`, and `coverage_summary.json`. The default `data/results/` directory is ignored by Git. The dashboard also accepts the participant ZIP and offers the same submission format, plus an action queue. Correcting a selected queue item updates its export entry.

## Checks

```sh
python -m pytest -q
npm --prefix frontend run lint
npm --prefix frontend run build
```

Backend CI runs on Windows, macOS, and Linux. Frontend CI checks lint and production build. Synthetic regression fixtures live in tests; private participant documents stay outside Git.

## Deployment

Existing baseline URLs: [dashboard](https://draftguard-weld.vercel.app) and [backend health](https://draftguard-api.onrender.com/health). A local feature branch is not live until merged and deployed.

Render: repository root, build `pip install -r backend/requirements.txt`, start `python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT`. Set `CORS_ALLOWED_ORIGINS=https://draftguard-weld.vercel.app` without a trailing slash.

Vercel: root `frontend`, build `npm run build`, output `dist`, `VITE_API_BASE_URL=https://draftguard-api.onrender.com`. Redeploy after changing this build-time variable. Free backend instances can take about a minute to wake.

## Practical boundaries

This is a hackathon prototype. Classification and extraction are deterministic English/label-based heuristics, not a trained model. No OCR, mailbox integration, automatic authoritative-version selection, or shared server database is included. Scans and unsupported layouts require review. The user explicitly selects SI/BL roles. A review records acknowledgment; it never releases or approves a shipping document.

History is stored only in the current browser (up to 10 checks), with self-reported reviewer names. It is not an authenticated or tamper-proof audit record. Download history before switching browsers or clearing site data. Full inbox results stay in memory until downloaded.

See [API contract](docs/API.md), [evaluation coverage](docs/EVALUATION.md), [demo script](docs/DEMO.md), and [validation plan](docs/VALIDATION.md).
