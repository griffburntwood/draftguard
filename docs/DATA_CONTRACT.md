# DraftGuard — Shared Data Contract

Status: Initial MVP agreement.

All components must follow these names and meanings.
Coordinate changes with the project lead before changing this contract.

## 1. Email

Preserve the supplied dataset structure:
- email_id: string
- from: string
- subject: string
- body: string
- attachments: list of relative file paths

Category must be one of:
- BL_COMPARISON
- SI_REQUEST
- INVOICE_QUERY
- GENERAL
- SPAM

## 2. Compared Fields

Use these exact names:
- shipper
- consignee
- notify_party
- port_of_loading
- port_of_discharge
- container_count
- gross_weight_kg

Normalized party and port values are strings.
Normalized container_count is an integer.
Normalized gross_weight_kg is a number expressed in kilograms.

A missing or unreadable value is null, never zero or a guess.

## 3. Extracted Field

Each field contains:
- raw_value: original text, or null
- normalized_value: string, number, or null
- state: extracted, missing, unreadable, or ambiguous
- evidence: list of source references

Each source reference contains:
- document_id: string
- location: human-readable source location
- text: supporting source text, or null

Examples of location:
- TXT: lines 8–9
- PDF: page 1, gross weight section
- XLSX: Sheet1!B12
- DOCX: table 1, row 4, column 2

## 4. Comparison Result

Each comparison contains:
- comparison_id: string
- email_id: string
- si_document_id: string or null
- bl_document_id: string or null
- status: OK, MISMATCH, or NEEDS_REVIEW
- field_results: results for all seven fields
- defect_fields: list of confirmed mismatched field names
- review_reasons: list of explanations requiring human input

Each field result contains:
- field: one of the seven field names
- si: extracted SI field
- bl: extracted BL field
- outcome: MATCH, MISMATCH, or UNKNOWN
- explanation: short explanation

## 5. Status Rules

OK:
All seven fields were checked and match.

MISMATCH:
All seven fields were checked and at least one differs.

NEEDS_REVIEW:
A required document or value is missing, unreadable, wrong,
ambiguous, or otherwise prevents a dependable complete comparison.

If confirmed mismatches coexist with uncertainty:
- Use NEEDS_REVIEW.
- Preserve confirmed mismatches in the internal field results.
- Explain what still requires review.

Non-comparison emails are not displayed as verified documents.

## 6. Human Corrections

Preserve the original extraction.
Record the corrected value, reviewer, time, and reason separately.
Rerun the comparison after a correction.

Correcting an extracted value does not edit the source document.
It does not automatically approve a BL.

## 7. Document Versions and Reviews

Every document has its own document_id and content hash.
A comparison refers to the exact SI and BL documents used.

For the initial revision demo:
- A person selects which SI and BL are current.
- Do not infer authoritative versions from email arrival order.
- A changed accepted source requires a new comparison.
- Preserve previous comparisons and human reviews as history.
- Identical duplicate content is not a substantive revision.

Comparison results and human approval are separate states.

## 8. Submission Export

The evaluator JSON is separate from our richer internal records.

Export one entry for every email_id using the supplied template:
- category
- status
- review_reason
- has_defect
- defect_fields

Allowed evaluator review_reason values:
- wrong_doc_type
- missing_attachment
- unreadable
- missing_value

Follow the participant submission format.
Document unresolved mappings and organizer clarifications before
finalizing export behavior. Do not invent new evaluator categories.

## 9. Mock Data

Label mock responses and synthetic revision scenarios clearly.
Never present them as results from processing the official dataset.

## 10. Implemented API additions

Comparison responses also contain `review_codes`, a list of the four allowed
submission reason strings. Processing responses include SHA-256
`document_hashes`, `submission_entry`, and `review_audit` (default empty).
See [API.md](API.md) for upload, inbox, and correction request formats.

The current prototype stores up to 10 manually grouped shipment checks in the
browser. Names are self-reported; this is not authenticated approval. Export
history before clearing browser data. An unrelated shipment must start a new
history. Non-comparison submission entries use the sample template convention
`status: "OK"`, while their internal `comparison` remains null.
