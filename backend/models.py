"""Shared data models used by DraftGuard components."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EmailCategory(str, Enum):
    BL_COMPARISON = "BL_COMPARISON"
    SI_REQUEST = "SI_REQUEST"
    INVOICE_QUERY = "INVOICE_QUERY"
    GENERAL = "GENERAL"
    SPAM = "SPAM"


class EmailRecord(BaseModel):
    """An input email using the organizer's JSON structure."""

    model_config = ConfigDict(extra="forbid")

    email_id: str = Field(min_length=1)
    sender: str = Field(alias="from")
    subject: str
    body: str
    attachments: list[str]


class ClassifiedEmail(BaseModel):
    """An email together with our classification decision."""

    model_config = ConfigDict(extra="forbid")

    email: EmailRecord
    category: EmailCategory
    explanation: str = Field(min_length=1)


class ShipmentField(str, Enum):
    SHIPPER = "shipper"
    CONSIGNEE = "consignee"
    NOTIFY_PARTY = "notify_party"
    PORT_OF_LOADING = "port_of_loading"
    PORT_OF_DISCHARGE = "port_of_discharge"
    CONTAINER_COUNT = "container_count"
    GROSS_WEIGHT_KG = "gross_weight_kg"


class ExtractionState(str, Enum):
    EXTRACTED = "extracted"
    MISSING = "missing"
    UNREADABLE = "unreadable"
    AMBIGUOUS = "ambiguous"


class SourceEvidence(BaseModel):
    """The source supporting an extracted value."""

    model_config = ConfigDict(extra="forbid")

    document_id: str = Field(min_length=1)
    location: str = Field(min_length=1)
    text: str | None


class ExtractedField(BaseModel):
    """A document value and its supporting evidence."""

    model_config = ConfigDict(extra="forbid", strict=True)

    raw_value: str | None
    normalized_value: str | int | float | None
    state: ExtractionState
    evidence: list[SourceEvidence]

    @model_validator(mode="after")
    def validate_extraction_state(self):
        if self.state == ExtractionState.EXTRACTED:
            if self.normalized_value is None:
                raise ValueError("An extracted field must have a value.")
            if isinstance(self.normalized_value, str):
                if not self.normalized_value.strip():
                    raise ValueError("An extracted value cannot be blank.")
            if not self.evidence:
                raise ValueError("An extracted field must have source evidence.")
        elif self.normalized_value is not None:
            raise ValueError(
                "Uncertain fields must have a null normalized value."
            )
        return self
