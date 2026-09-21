"""Connect email classification, text extraction, and comparison."""

from uuid import uuid4

from .classification import classify_email
from .comparison import compare_shipments
from .comparison_models import ComparisonResult, FieldComparison
from .extraction import extract_text_document
from .models import EmailCategory, ExtractedField, ExtractionState, ShipmentField
from .processing_models import TextProcessingRequest


def process_text_email(request: TextProcessingRequest) -> dict:
    classified = classify_email(request.email)
    response = {
        "classification": classified.model_dump(mode="json", by_alias=True),
        "comparison": None,
    }

    if classified.category != EmailCategory.BL_COMPARISON:
        return response

    si = (
        extract_text_document(request.si.text, request.si.document_id)
        if request.si is not None
        else None
    )
    bl = (
        extract_text_document(request.bl.text, request.bl.document_id)
        if request.bl is not None
        else None
    )
    comparison_id = f"comparison_{uuid4().hex}"

    if si is not None and bl is not None:
        response["comparison"] = compare_shipments(
            si=si,
            bl=bl,
            email_id=request.email.email_id,
            comparison_id=comparison_id,
        )
        return response

    reasons = []
    if si is None:
        reasons.append("SI text was not supplied; select and provide the SI.")
    if bl is None:
        reasons.append(
            "Draft BL text was not supplied; select and provide the draft BL."
        )

    def missing_field():
        return ExtractedField(
            raw_value=None,
            normalized_value=None,
            state=ExtractionState.MISSING,
            evidence=[],
        )

    fields = [
        FieldComparison(
            field=field,
            si=getattr(si, field.value) if si is not None else missing_field(),
            bl=getattr(bl, field.value) if bl is not None else missing_field(),
            outcome="UNKNOWN",
            explanation=" ".join(reasons),
        )
        for field in ShipmentField
    ]

    comparison = ComparisonResult(
        comparison_id=comparison_id,
        email_id=request.email.email_id,
        si_document_id=si.document_id if si is not None else None,
        bl_document_id=bl.document_id if bl is not None else None,
        status="NEEDS_REVIEW",
        field_results=fields,
        defect_fields=[],
        review_reasons=reasons,
    )
    response["comparison"] = comparison.model_dump(mode="json")
    return response
