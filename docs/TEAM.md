# DraftGuard — Team Responsibilities

## Member 1 — Project Lead, Integration & Revisions (Qinyi)

Owns:
- Initial project setup and shared data contracts
- Backend API foundation and storage
- Integration of teammates' components
- Document versions and correction history
- Detecting when a previous review becomes outdated

First deliverable:
A running backend with a sample comparison endpoint that the
frontend can display.

Later deliverable:
Track new, unresolved, and fixed discrepancies across manually
selected revisions.

## Member 2 — Email Intake & Classification

Owns:
- Loading emails from the participant dataset
- Preserving email IDs and attachment references
- Classification into the five required categories
- Routing comparison requests to document processing

First deliverable:
A function that accepts an email record and returns its category
with an explanation.

Coordinate with Member 1 on the shared email schema.

## Member 3 — Attachment Reading & Extraction

Owns:
- TXT, PDF, DOCX, and XLSX readers
- Document-type identification
- Extraction of the seven required fields
- Source evidence for each extracted field
- Explicit missing/unreadable states
- OCR fallback after the initial extraction flow works

First deliverable:
Extract the seven fields and source evidence from one real
plain-text SI–BL pair.

Coordinate with Member 4 on the extracted-field schema.

## Member 4 — Comparison & Evaluation

Owns:
- Normalization of extracted values
- Seven-field comparison
- Mismatch and human-review logic
- Required submission JSON export
- Comparison tests and evaluation reporting

First deliverable:
Compare two structured shipment records and return field-level
results with OK, MISMATCH, or NEEDS_REVIEW.

Do not add arbitrary weight tolerances or guess missing values.

## Member 5 — Dashboard & Human Review

Owns:
- Inbox and action queue
- Side-by-side comparison and source evidence
- Human correction form
- Revision timeline interface
- Clear loading, failure, and retry states

First deliverable:
Display a sample comparison returned by the backend.

Coordinate with Member 1 on API responses and review actions.

## Shared First Milestone

One email completes:
Intake → Classification → Extraction → Comparison →
Dashboard → Submission export.

Each member adds checks for their own component.
Member 4 does not own all testing.

## Validation

Members 1 and 5:
- Show the proposed workflow to a mentor or shipping employee.
- Ask how revisions and corrections are handled today.
- Record findings in docs/VALIDATION.md.
- Share any scope changes with the whole team.

Required baseline development can proceed while validation is pending.

## Collaboration Rules

- Agree on shared schemas before implementing integrations.
- Each member works on a separate feature branch.
- Open a pull request for changes to main.
- Ask another teammate to review before merging.
- Coordinate changes to shared files and dependencies.
- Keep passwords, API keys, and answer keys out of Git.
- Label mock data and synthetic revision examples clearly.
