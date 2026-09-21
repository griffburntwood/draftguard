"""Seven-field comparison for extracted shipment records."""

from __future__ import annotations

import re

from .comparison_models import (
    ComparisonResult,
    ComparisonStatus,
    FieldComparison,
    FieldOutcome,
)
from .models import ExtractionState, ShipmentField, ShipmentRecord


_TEXT_FIELDS = {
    ShipmentField.SHIPPER,
    ShipmentField.CONSIGNEE,
    ShipmentField.NOTIFY_PARTY,
    ShipmentField.PORT_OF_LOADING,
    ShipmentField.PORT_OF_DISCHARGE,
}


def _normalized_text(value: str) -> str:
    """Collapse harmless whitespace and compare text without case differences."""

    return " ".join(re.sub(r"[;|]", " ", value).split()).casefold()


def _values_match(field: ShipmentField, si_value: object, bl_value: object) -> bool:
    if field in _TEXT_FIELDS:
        left, right = str(si_value), str(bl_value)
        if field in {ShipmentField.PORT_OF_LOADING, ShipmentField.PORT_OF_DISCHARGE}:
            code_pattern = r"\s*\(([A-Z]{2}[A-Z0-9]{3})\)\s*$"
            left_code, right_code = re.search(code_pattern, left, re.I), re.search(code_pattern, right, re.I)
            if left_code and right_code and left_code.group(1).casefold() != right_code.group(1).casefold():
                return False
            left = re.sub(code_pattern, "", left, flags=re.I)
            right = re.sub(code_pattern, "", right, flags=re.I)
        return _normalized_text(left) == _normalized_text(right)
    return si_value == bl_value


def _uncertainty_reason(
    field: ShipmentField,
    si_state: ExtractionState,
    bl_state: ExtractionState,
) -> str:
    sides: list[str] = []
    if si_state != ExtractionState.EXTRACTED:
        sides.append(f"SI {field.value} is {si_state.value}.")
    if bl_state != ExtractionState.EXTRACTED:
        sides.append(f"Draft BL {field.value} is {bl_state.value}.")
    return " ".join(sides)


def compare_shipments(
    si: ShipmentRecord,
    bl: ShipmentRecord,
    email_id: str,
    comparison_id: str,
) -> dict:
    """Compare all required shipment fields and return the data-contract payload.

    Text comparison normalizes case, whitespace, address separators, and optional
    port-code suffixes (conflicting explicit codes still differ). Numeric values are
    compared exactly: this function deliberately does not apply aliases,
    geographic equivalences, or weight tolerances.
    """

    field_results: list[FieldComparison] = []
    defect_fields: list[ShipmentField] = []
    review_reasons: list[str] = []

    for field in ShipmentField:
        si_field = getattr(si, field.value)
        bl_field = getattr(bl, field.value)

        if (
            si_field.state != ExtractionState.EXTRACTED
            or bl_field.state != ExtractionState.EXTRACTED
        ):
            reason = _uncertainty_reason(field, si_field.state, bl_field.state)
            field_results.append(
                FieldComparison(
                    field=field,
                    si=si_field,
                    bl=bl_field,
                    outcome=FieldOutcome.UNKNOWN,
                    explanation=reason,
                )
            )
            review_reasons.append(reason)
            continue

        if _values_match(
            field,
            si_field.normalized_value,
            bl_field.normalized_value,
        ):
            explanation = "Values match."
            outcome = FieldOutcome.MATCH
        else:
            explanation = "SI and draft BL values differ."
            outcome = FieldOutcome.MISMATCH
            defect_fields.append(field)

        field_results.append(
            FieldComparison(
                field=field,
                si=si_field,
                bl=bl_field,
                outcome=outcome,
                explanation=explanation,
            )
        )

    if review_reasons:
        status = ComparisonStatus.NEEDS_REVIEW
    elif defect_fields:
        status = ComparisonStatus.MISMATCH
    else:
        status = ComparisonStatus.OK

    result = ComparisonResult(
        comparison_id=comparison_id,
        email_id=email_id,
        si_document_id=si.document_id,
        bl_document_id=bl.document_id,
        status=status,
        field_results=field_results,
        defect_fields=defect_fields,
        review_reasons=review_reasons,
        review_codes=(
            ["unreadable"] if any(f.si.state == ExtractionState.UNREADABLE or f.bl.state == ExtractionState.UNREADABLE for f in field_results)
            else ["missing_value"] if review_reasons else []
        ),
    )
    return result.model_dump(mode="json")
