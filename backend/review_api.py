"""Explicit human corrections, preserving original extraction and an audit trail.

Stateless API: the browser keeps session history; no identity/authentication claim.
"""
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from .comparison import compare_shipments
from .models import ExtractedField, ExtractionState, ShipmentField, ShipmentRecord, SourceEvidence
from .processing_models import TextProcessingResponse
from .submission import build_submission_entry
from typing import Literal

router = APIRouter()


class Correction(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    side: Literal['si', 'bl']
    field: ShipmentField = Field(strict=False)
    value: str | int | float


class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    original: TextProcessingResponse
    reviewer: str = Field(min_length=1, max_length=120)
    reason: str = Field(min_length=1, max_length=2000)
    corrections: list[Correction] = Field(min_length=1, max_length=14)


@router.post('/process/review', response_model=TextProcessingResponse)
def apply_corrections(request: ReviewRequest):
    original = request.original
    comparison = original.comparison
    if not comparison or not comparison.si_document_id or not comparison.bl_document_id:
        raise HTTPException(422, 'Select both source documents before correcting fields.')
    if 'wrong_doc_type' in comparison.review_codes:
        raise HTTPException(422, 'Replace the incorrect document before reviewing values.')
    if not request.reviewer.strip() or not request.reason.strip():
        raise HTTPException(422, 'Reviewer and reason must not be blank.')
    if len({(c.side, c.field) for c in request.corrections}) != len(request.corrections):
        raise HTTPException(422, 'Each field can be corrected only once per request.')
    values = {side: {field.field.value: getattr(field, side).model_copy(deep=True) for field in comparison.field_results} for side in ['si', 'bl']}
    audit = list(original.review_audit)
    timestamp = datetime.now(timezone.utc).isoformat()
    for correction in request.corrections:
        field = values[correction.side][correction.field.value]
        audit.append({
            'side': correction.side, 'field': correction.field.value,
            'previous_value': field.normalized_value, 'value': correction.value,
            'reviewer': request.reviewer.strip(), 'reason': request.reason.strip(),
            'timestamp': timestamp, 'original_comparison_id': comparison.comparison_id,
        })
        field.normalized_value = correction.value
        field.state = ExtractionState.EXTRACTED
        # Source raw_value and evidence stay intact; manual evidence is explicitly separate.
        field.evidence.append(SourceEvidence(
            document_id=getattr(comparison, f'{correction.side}_document_id'),
            location=f'Human correction by {request.reviewer.strip()} at {timestamp}',
            text=f'{correction.value} — {request.reason.strip()}',
        ))
    try:
        records = [ShipmentRecord.model_validate({'document_id': getattr(comparison, f'{side}_document_id'), **{name: ExtractedField.model_validate(value.model_dump()) for name, value in values[side].items()}}) for side in ['si', 'bl']]
        result = compare_shipments(*records, comparison.email_id, f'comparison_{uuid4().hex}')
    except ValueError:
        raise HTTPException(422, 'Correction has an invalid type or value. Counts must be non-negative integers; weights must be finite non-negative numbers.')
    return {
        'classification': original.classification,
        'comparison': result,
        'document_hashes': original.document_hashes,
        'review_audit': audit,
        'submission_entry': build_submission_entry(original.classification, result),
    }
