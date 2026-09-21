"""Build evaluator submission entries from DraftGuard's internal results."""

from __future__ import annotations

from typing import Any

from .comparison_models import ComparisonResult, ComparisonStatus
from .models import ClassifiedEmail, EmailCategory, ExtractionState


def _as_comparison_result(
    comparison: ComparisonResult | dict[str, Any],
) -> ComparisonResult:
    if isinstance(comparison, ComparisonResult):
        return comparison
    return ComparisonResult.model_validate(comparison)


def _review_reason(comparison: ComparisonResult) -> str | None:
    """Map richer internal uncertainty to the evaluator's four allowed values."""

    reasons = " ".join(comparison.review_reasons).casefold()

    if "wrong document type" in reasons or "wrong doc type" in reasons:
        return "wrong_doc_type"
    if "missing attachment" in reasons or "attachment is missing" in reasons:
        return "missing_attachment"

    states = {
        field.state
        for result in comparison.field_results
        for field in (result.si, result.bl)
    }
    if ExtractionState.UNREADABLE in states or "unreadable" in reasons:
        return "unreadable"
    if ExtractionState.MISSING in states or "missing" in reasons:
        return "missing_value"

    # The evaluator has no category for ambiguous or other free-text review
    # reasons. Treat them as missing_value: a dependable value is unavailable
    # and human input is required, without inventing a new evaluator enum.
    if ExtractionState.AMBIGUOUS in states or comparison.review_reasons:
        return "missing_value"
    return None


def build_submission_entry(
    classification: ClassifiedEmail,
    comparison: ComparisonResult | dict[str, Any] | None,
) -> dict:
    """Return one evaluator-format entry without changing either input object."""

    category = classification.category.value
    if classification.category != EmailCategory.BL_COMPARISON:
        return {
            "category": category,
            "status": None,
            "review_reason": None,
            "has_defect": False,
            "defect_fields": [],
        }

    if comparison is None:
        raise ValueError("A BL_COMPARISON email requires a comparison result.")

    result = _as_comparison_result(comparison)
    review_reason = (
        _review_reason(result)
        if result.status == ComparisonStatus.NEEDS_REVIEW
        else None
    )

    return {
        "category": category,
        "status": result.status.value,
        "review_reason": review_reason,
        "has_defect": bool(result.defect_fields),
        "defect_fields": [field.value for field in result.defect_fields],
    }
