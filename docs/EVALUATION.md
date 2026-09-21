# Coverage and evaluation

Measured locally on 2026-09-22 against the organizer participant ZIP. No answer key, generator, or scoring labels were read. Counts below are **predictions and processing coverage, not accuracy**. A passing test suite also does not establish dataset accuracy.

## Full participant run

520 input email IDs produced 520 submission entries, with exact ID coverage against `sample_submission.json`. Every detailed response passed the shared Pydantic response model. Every submission entry contained the five required keys and allowed enum values. The sample submission is a format template, not expected labels.

| Predicted category | Count |
| --- | ---: |
| BL_COMPARISON | 220 |
| SI_REQUEST | 132 |
| INVOICE_QUERY | 83 |
| GENERAL | 58 |
| SPAM | 27 |

| Comparison result | Count |
| --- | ---: |
| OK | 61 |
| MISMATCH | 49 |
| NEEDS_REVIEW | 110 |

Review exports: missing_attachment 96; wrong_doc_type 5; unreadable 5; missing_value 4. The participant archive contains 192 TXT, 28 PDF, 22 XLSX, and 8 DOCX attachments. Attachment counts are not category labels: some comparison requests have no usable document pair.

The previously inspected `email_004` still reports consignee and notify_party mismatches, with no unresolved values. This is a spot check against source text, not an official expected result.

## Improvements grounded in input inspection

- Recognize alternate consignee, loading-port, and gross-weight labels; prevent a later labeled field from being absorbed into a party address.
- Parse complete equipment expressions such as `6 x 40 HC`; reject unclear numeric strings rather than taking their first digit.
- Read Word tables, Excel label/value cells, and machine-readable PDF text with source locations.
- Treat duplicate labels, placeholders, unknown weight units, formulas, corrupt files, and empty/image-only PDFs conservatively.
- Separate operational updates from historical BL subjects; trim common reply/signature text; recognize attached SI/BL “for checking” phrasing and supplied shipping instructions.
- Preserve confirmed defects even when another field requires review.

## Reproduce

```sh
python -m pytest -q
python -m backend.batch /path/to/sdoc-hackathon-bundle.zip
npm --prefix frontend run lint
npm --prefix frontend run build
```

100 backend tests plus 4 unittest subtests passed locally at the initial completion checkpoint. Tests cover the existing models/classifier/comparison and new readers, upload routes, export, correction validation, and bounded participant ZIP handling. Two installed-library deprecation warnings remain; they do not fail the suite.

## Remaining uncertainty

English phrase rules can misclassify unusual wording, mixed requests, negation, and other languages. Document readers handle known label/table layouts, not every carrier template. No fuzzy company equivalence or port database is used; normalization is deliberately limited. “Send a draft BL for checking” is currently routed to BL_COMPARISON even before attachments arrive; the missing-document review is intentional but the organizer's expected category for such wording should be confirmed.

For official evaluation, run the organizer's prescribed evaluator separately when authorized, record its exact version/input split, and report measured scores. Do not tune against a hidden answer key or advertise these coverage counts as accuracy.
