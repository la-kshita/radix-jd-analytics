# RADIX JD Analytics

Standalone Windows build of RADIX Module 1 using the PDF's `TEAM-V1` contract. The app accepts a job description as pasted text or a text-based PDF/DOCX, proposes an extraction, lets a person review and correct it, and downloads the reviewed result as JSON.

## Current status

- Backend, React screen, upload/paste paths, TEAM-V1 validation, review route, and JSON download are implemented.
- Offline extraction is available without a Groq key. Hosted extraction is opt-in and requires the backend's local `.env`.
- JD A, B, and C fictional text, DOCX, and PDF inputs are in `samples/`. The full hand-labelled expected JD A object is `samples/jd_reviewed.json`; it is a fixture, not a live model response.
- The user reported 20 backend tests passing and the production frontend build passing. The acceptance record distinguishes reported results from checks rerun in this environment.
- The UI was checked at a 390 px responsive width after the text-size update: no horizontal overflow, helper text at 16 px, and visible keyboard focus while tabbing.
- The PDFs generated for JD B/C are selectable and visually checked. Their DOCX files' text matches the TXT fixtures, but DOCX rendering could not be visually verified because the bundled LibreOffice renderer was unavailable.

See [`docs/acceptance-record.md`](docs/acceptance-record.md) for the observed results, test caveats, and pending items.

## Scope and limitations

- This is a standalone local module. It is not connected to the main RADIX application. The Git remote is `https://github.com/la-kshita/radix-jd-analytics.git`; the current `master` branch has been pushed.
- Extracted records are kept in backend memory only. Restarting the backend clears them; there is no database or durable storage.
- Scanned/image-only PDFs are unsupported; the reader needs selectable text. OCR is not included.
- The live unfamiliar-skill Groq case has not passed after the requirement-to-skill mapping fix. Its mocked regression test is present, but live semantic acceptance remains pending.
- Organizer-provided official samples/benchmarks were unavailable. The supplied examples are fictional.
- This is a local development build, not a production authentication, privacy, or deployment design.

## Project layout

| Path | Purpose |
| --- | --- |
| `backend/models.py` | TEAM-V1 Skill, Requirement, and Extraction models and validation |
| `backend/reader.py` | Selectable-text extraction from PDF and DOCX; type, size, and empty-text checks |
| `backend/extractor.py` | Consent-gated Groq proposal path and offline manual-review fallback |
| `backend/review.py` | Review validation, stable IDs, quote checks, and revision increment |
| `backend/app.py` | FastAPI health, JD extraction, review routes, and in-memory storage |
| `backend/tests/` | Reader, extractor, and review tests |
| `frontend/src/App.jsx`, `frontend/src/App.css` | Paste/upload, extraction preview, human review, and JSON download UI |
| `samples/` | Fictional JD A-C TXT/PDF/DOCX inputs and the hand-labelled JD A TEAM-V1 fixture |
| `docs/acceptance-record.md` | Acceptance evidence and pending checks |

## Requirements

- Windows PowerShell
- Python 3.12
- Node.js 24 with npm
- Git for local version history

## First-time setup

Open PowerShell in the project root (the directory containing `backend`, `frontend`, and `samples`):

```powershell
python --version
node --version
npm.cmd --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
cd frontend
npm.cmd ci
cd ..
```

The Python packages are pinned in `backend/requirements.txt`; the frontend lockfile is `frontend/package-lock.json`. Do not copy `.venv` or `frontend/node_modules` when handing the project to a teammate.

## Run locally

Use two PowerShell terminals, both starting at the project root.

Terminal 1, start the backend:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2, start the frontend:

```powershell
cd frontend
npm.cmd run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Open <http://127.0.0.1:5173/>. The API health check is <http://127.0.0.1:8000/api/team/v1/health>; interactive API forms are at <http://127.0.0.1:8000/docs>.

Leave both server terminals running while using the app. Stop a server with Ctrl+C in its own terminal.

## API routes

The API base is `http://127.0.0.1:8000`. Routes use the PDF's TEAM-V1 prefix and exact field names.

| Method and route | Request | Result |
| --- | --- | --- |
| `GET /api/team/v1/health` | None | `{"status":"ok"}` |
| `POST /api/team/v1/jd/extract` | `multipart/form-data`: `file` (PDF/DOCX), optional `hosted_consent` (defaults to `false`) | TEAM-V1 JD extraction |
| `POST /api/team/v1/jd/extract-text` | JSON: `text` (15-100,000 characters), `source_file` ending in `.txt`, optional `hosted_consent` (defaults to `false`) | TEAM-V1 JD extraction |
| `POST /api/team/v1/jd/review` | Complete corrected TEAM-V1 Extraction JSON | Validated reviewed Extraction with next revision |

Extraction responses begin as `needs_review`. The offline path is `manual`, makes no provider call, and starts without proposed skills. Review verifies that quotes still exist in the original stored source and that IDs/groups are valid. Errors use a safe JSON envelope: `{"error":{"code":"...","message":"..."}}`.

## Offline and Groq behavior

For offline use, leave the consent checkbox unchecked. A result is marked `needs_review` with `extraction_method: "manual"`; add/correct claims in the review UI, then save and download the JSON.

For an authorized live test only, keep `GROQ_API_KEY` in a private `.env` at the project root. The server loads it; React never receives the key. The configured default model is `openai/gpt-oss-20b`, and the default model timeout is 45 seconds. Do not put keys or personal documents in this README, React, logs, screenshots, Git, or messages. Never use a real person's document without permission. Hosted processing requires explicit consent for that input.

The live unfamiliar-JD scenario still needs a successful rerun after the mapper fix. The prior authorized request returned an unknown-skill group error; a mocked regression test now covers that case. No further live request is claimed here.

## Tests and production build

Run the backend suite from the project root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Build the frontend:

```powershell
cd frontend
npm.cmd run build
cd ..
```

The last full backend result reported by the user was `20 passed` with one Starlette/httpx TestClient deprecation warning. A rerun during handoff preparation did not finish in this environment, so it is not presented as a fresh pass. The frontend build was reported by the user and also completed successfully during handoff preparation. See the acceptance record for detail.

## Sample inputs

| JD | Expected meaning from the manual | Files |
| --- | --- | --- |
| A | Python mandatory; SQL preferred | `samples/jd_a.txt`, `samples/jd_a.docx`, `samples/jd_a.pdf` |
| B | SQL mandatory; Python preferred | `samples/jd_b.txt`, `samples/jd_b.docx`, `samples/jd_b.pdf` |
| C | Python AND SQL mandatory; AWS OR GCP preferred | `samples/jd_c.txt`, `samples/jd_c.docx`, `samples/jd_c.pdf` |

`samples/jd_reviewed.json` is the hand-labelled expected JD A object. It is not a real Groq response. Generated IDs and model confidence can differ; check meaning, exact quotes, and group links.

## Teammate handoff

Before sharing a tested snapshot:

1. Review `git status` and commit the intended source, tests, fixtures, README, acceptance record, `backend/requirements.txt`, and `frontend/package-lock.json` to local Git.
2. Run the setup, backend tests, and frontend build above from a clean copy. Record the actual output in the acceptance record.
3. Add safe screenshots of a successful fictional-data review/export and an error-recovery case if image evidence is needed. Do not use personal data or show `.env`.
4. Keep `.env`, `.venv/`, `frontend/node_modules/`, `frontend/dist/`, `samples/jd_a-Lakshita.pdf`, and `tmp/` out of the handoff.
5. The GitHub repository and initial push are complete. Add the Scrum Master and other teammates as collaborators through GitHub before they try to clone it; collaborator access has not been configured here. Do not call it integrated with RADIX until the separate adapter and integration checks are completed.

The current acceptance record lists the remaining live Groq check, screenshot evidence, fresh-copy verification, and sharing steps. The larger RADIX integration is outside this module's standalone build.
