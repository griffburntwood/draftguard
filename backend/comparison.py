"""Seven-field comparison for extracted shipment records."""

from __future__ import annotations

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

    return " ".join(value.split()).casefold()


def _values_match(field: ShipmentField, si_value: object, bl_value: object) -> bool:
    if field in _TEXT_FIELDS:
        return _normalized_text(str(si_value)) == _normalized_text(str(bl_value))
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

    Text comparison ignores case and repeated whitespace only. Numeric values are
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
    )
    return result.model_dump(mode="json")
