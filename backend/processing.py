"""Shared processing path for pasted text, uploaded files, and inbox batches."""
from uuid import uuid4

from .classification import classify_email
from .comparison import compare_shipments
from .comparison_models import ComparisonResult
from .documents import ParsedDocument, parse_document
from .extraction import empty_record, extract_text_document  # retained public import for callers
from .models import EmailCategory, ExtractionState
from .processing_models import TextProcessingRequest
from .submission import build_submission_entry


def process_selected(classified, si: ParsedDocument | None, bl: ParsedDocument | None):
    response = {
        'classification': classified.model_dump(mode='json', by_alias=True),
        'comparison': None,
        'document_hashes': {role: doc.content_hash for role, doc in [('si', si), ('bl', bl)] if doc},
    }
    comparison = None
    if classified.category == EmailCategory.BL_COMPARISON:
        records = [doc.record if doc else empty_record(f'missing_{role}', ExtractionState.MISSING)
                   for role, doc in [('si', si), ('bl', bl)]]
        data = compare_shipments(*records, classified.email.email_id, f'comparison_{uuid4().hex}')
        for role, doc in [('si', si), ('bl', bl)]:
            if doc is None:
                data[f'{role}_document_id'] = None
                data['review_reasons'].insert(0, f'{role.upper()} attachment is missing or was not selected.')
                data['review_codes'].append('missing_attachment')
            elif doc.issue:
                data['review_codes'].append(doc.issue)
                message = 'has the wrong document type' if doc.issue == 'wrong_doc_type' else 'could not be read; use a supported text-based file or review manually'
                data['review_reasons'].insert(0, f'{role.upper()} attachment {message}.')
        if data['review_reasons']:
            data['status'] = 'NEEDS_REVIEW'
        data['review_codes'] = list(dict.fromkeys(data['review_codes']))
        comparison = ComparisonResult.model_validate(data)
        response['comparison'] = comparison.model_dump(mode='json')
    response['submission_entry'] = build_submission_entry(classified, comparison)
    return response


def process_text_email(request: TextProcessingRequest) -> dict:
    classified = classify_email(request.email)
    if classified.category != EmailCategory.BL_COMPARISON:
        return process_selected(classified, None, None)
    docs = [parse_document(doc.text.encode('utf-8'), 'input.txt', doc.document_id, role)
            if doc is not None else None for role, doc in [('SI', request.si), ('BL', request.bl)]]
    return process_selected(classified, *docs)
