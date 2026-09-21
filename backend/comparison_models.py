"""Shared response structures for document comparisons."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .models import ExtractedField, ExtractionState, ShipmentField


class FieldOutcome(str, Enum):
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    UNKNOWN = "UNKNOWN"


class ComparisonStatus(str, Enum):
    OK = "OK"
    MISMATCH = "MISMATCH"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class FieldComparison(BaseModel):
    """The result of checking one SI field against its BL counterpart."""

    model_config = ConfigDict(extra="forbid")

    field: ShipmentField
    si: ExtractedField
    bl: ExtractedField
    outcome: FieldOutcome
    explanation: str = Field(min_length=1)


    @model_validator(mode="after")
    def validate_extraction_outcome(self):
        uncertain = (
            self.si.state != ExtractionState.EXTRACTED
            or self.bl.state != ExtractionState.EXTRACTED
        )
        if uncertain and self.outcome != FieldOutcome.UNKNOWN:
            raise ValueError(
                "Missing, unreadable, or ambiguous values require UNKNOWN."
            )
        return self


class ComparisonResult(BaseModel):
    """A comparison response following docs/DATA_CONTRACT.md."""

    model_config = ConfigDict(extra="forbid")

    comparison_id: str = Field(min_length=1)
    email_id: str = Field(min_length=1)
    si_document_id: str | None
    bl_document_id: str | None
    status: ComparisonStatus
    field_results: list[FieldComparison] = Field(min_length=7, max_length=7)
    defect_fields: list[ShipmentField]
    review_reasons: list[str]
    review_codes: list[Literal["wrong_doc_type", "missing_attachment", "unreadable", "missing_value"]] = Field(default_factory=list)


    @model_validator(mode="after")
    def validate_consistency(self):
        fields = [item.field for item in self.field_results]
        if len(set(fields)) != 7:
            raise ValueError("Each of the seven fields must appear exactly once.")

        defects = [
            item.field for item in self.field_results
            if item.outcome == FieldOutcome.MISMATCH
        ]
        if len(set(self.defect_fields)) != len(self.defect_fields):
            raise ValueError("defect_fields cannot contain duplicates.")
        if set(self.defect_fields) != set(defects):
            raise ValueError("defect_fields must match the field outcomes.")

        unknown = any(
            item.outcome == FieldOutcome.UNKNOWN
            for item in self.field_results
        )
        missing_document = (
            self.si_document_id is None or self.bl_document_id is None
        )
        if any(not reason.strip() for reason in self.review_reasons):
            raise ValueError("Review reasons cannot be blank.")

        if unknown or missing_document or self.review_reasons:
            expected = ComparisonStatus.NEEDS_REVIEW
        elif defects:
            expected = ComparisonStatus.MISMATCH
        else:
            expected = ComparisonStatus.OK

        if self.status != expected:
            raise ValueError(f"Comparison status must be {expected.value}.")

        if self.status == ComparisonStatus.NEEDS_REVIEW:
            if not self.review_reasons:
                raise ValueError("NEEDS_REVIEW requires an explanation.")

        return self


class DemoComparisonResult(ComparisonResult):
    """Adds the existing demo endpoint's presentation metadata."""

    is_demo: bool
    notice: str = Field(min_length=1)
