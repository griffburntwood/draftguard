# Processing API

Open `/docs` on the running backend for generated request schemas. Existing `GET /health`, `GET /demo/comparison`, and `POST /process/text` remain available. The demo is explicitly synthetic.

## POST /process/files

Multipart form fields:

| Field | Value |
| --- | --- |
| `email` | JSON string with `email_id`, `from`, `subject`, `body`, `attachments` |
| `si_file` | Optional selected SI file |
| `bl_file` | Optional selected draft BL file |

Accepted suffixes: TXT, PDF, DOCX, XLSX. Maximum 10 MiB per file. Documents are processed temporarily; filenames are never used as disk destinations. The uploaded files are the explicitly selected sources. The frontend supplies their names in the email attachment list.

Example (macOS/Linux shell):

```sh
curl http://127.0.0.1:8000/process/files \
  -F 'email={"email_id":"demo_1","from":"demo@example.com","subject":"Check draft BL","body":"Please compare the BL against the SI.","attachments":["si.txt","bl.txt"]}' \
  -F 'si_file=@si.txt' -F 'bl_file=@bl.txt'
```

Response: `classification`, nullable `comparison`, `document_hashes`, `submission_entry`, `review_audit`. Missing files produce NEEDS_REVIEW for comparison emails. Non-comparison emails skip extraction. Unreadable/corrupt/scan-only supported files produce review results rather than server errors. Clear conflicting document headings produce `wrong_doc_type`; unknown layouts without clear headings can instead produce missing values.

Errors: 413 size exceeded; 415 unsupported suffix; 422 malformed email/request. Parser limits include 50 PDF pages, 20 worksheets, 10,000 rows and 100 columns per sheet, 1,000,000 extracted characters, and bounded expanded Office archives. Formulas are not executed or guessed.

## POST /process/inbox

Multipart field `bundle`: participant ZIP with `inbox/email_*.json` and referenced attachments. Maximum 30 MiB compressed, 100 MiB expanded, 3,000 members, 1,000 emails. Returns `submission` keyed by email ID, `results` for the action queue, and `summary` prediction counts. No bundled Python is executed. Absolute/traversal attachment paths are rejected. Duplicate email IDs or malformed emails reject the batch with 422.

CLI equivalent: `python -m backend.batch /path/to/participant.zip`.

## POST /process/review

JSON fields:

- `original`: a complete processing response.
- `reviewer`, `reason`: nonblank strings.
- `corrections`: objects with `side` (`si`/`bl`), `field`, and `value`.

Counts must be nonnegative integers; weights finite nonnegative numbers in kilograms. Text cannot be blank. The API validates, retains original raw text/evidence, appends explicitly human-supplied evidence and audit entries, and reruns comparison. Missing/wrong source documents must be replaced, not overridden. Response uses the same processing schema.

This endpoint is stateless. Client-supplied history is not an authenticated audit record; do not treat it as legal approval or an independently verified source.

## Submission mapping

One entry per email ID, exactly `category`, `status`, `review_reason`, `has_defect`, `defect_fields`. Non-comparison entries use status `OK`, null review reason, false has_defect, and an empty defect list, matching the supplied sample's placeholder convention; this does not assert document verification.

For NEEDS_REVIEW, explicit reasons take precedence: wrong_doc_type, missing_attachment, unreadable, missing_value. Repeated/ambiguous values map to missing_value because a dependable value is unavailable. Missing or non-unique SI/BL selection maps to missing_attachment: an authoritative pair has not been selected. Confirmed defects remain present alongside uncertainty.
