# DraftGuard — Project Scope

## Purpose
Help shipping employees compare Shipping Instructions (SI) against
draft Bills of Lading (BL), resolve discrepancies, and track whether
a review remains valid after documents change.

The SI is the reference for comparison.

## Required MVP
1. Load the supplied JSON emails and their attachments.
2. Classify every email:
   - BL_COMPARISON
   - SI_REQUEST
   - INVOICE_QUERY
   - GENERAL
   - SPAM
3. Process document-comparison requests.
4. Extract and compare seven fields:
   - shipper
   - consignee
   - notify_party
   - port_of_loading
   - port_of_discharge
   - container_count
   - gross_weight_kg
5. Show SI and BL values alongside source evidence.
6. Return OK, MISMATCH, or NEEDS_REVIEW.
7. Let a person resolve extraction uncertainty and rerun the check.
8. Export results in the supplied sample_submission.json format.

## Standout Extension
- Record the exact SI and BL versions used in each comparison.
- Track discrepancies as new, unresolved, or fixed across revisions.
- Recheck all seven fields when a document changes.
- Mark previous reviews outdated when their accepted sources change.
- Initially, users select the authoritative document versions manually.

## First Integration Milestone
One email passes through classification, real attachment extraction,
comparison, dashboard display, and submission export.

Complete this before expanding the revision workflow.

## Out of Scope for the First Version
- Live Gmail or Outlook integration
- Automatically sending emails
- Carrier-system integration
- Customs or legal compliance certification
- Payment processing
- Autonomous selection of authoritative SI revisions

## Data and Evaluation
- Keep the official dataset unchanged.
- Do not commit the organizer Docker package or answer key.
- Do not hard-code decisions from email IDs or reference answers.
- Use separate, clearly labelled synthetic revision scenarios.
- Report official-dataset and revision-test results separately.
- Resolve missing-attachment and scanned-document scoring ambiguities
  with the organizers.

## Validation — Still Pending
Show the workflow to a shipping employee or hackathon mentor.
Ask how they manage corrections, document versions, and prior approvals.
Record feedback and resulting scope changes in docs/VALIDATION.md.
