"""Request models for processing email and plain-text attachments."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .models import EmailRecord


class TextDocumentInput(BaseModel):
    """Text from one attachment, explicitly selected as SI or BL."""

    model_config = ConfigDict(extra="forbid")

    document_id: str = Field(min_length=1)
    attachment_path: str = Field(min_length=1)
    text: str


class TextProcessingRequest(BaseModel):
    """An email and its caller-selected SI and draft BL."""

    model_config = ConfigDict(extra="forbid")

    email: EmailRecord
    si: TextDocumentInput | None = None
    bl: TextDocumentInput | None = None

    @model_validator(mode="after")
    def validate_document_selection(self):
        for document in (self.si, self.bl):
            if document is None:
                continue
            if not document.document_id.strip():
                raise ValueError("Document IDs cannot be blank.")
            if document.attachment_path not in self.email.attachments:
                raise ValueError(
                    "Selected documents must belong to the email attachments."
                )

        if self.si is not None and self.bl is not None:
            if self.si.document_id == self.bl.document_id:
                raise ValueError("SI and BL must have different document IDs.")
            if self.si.attachment_path == self.bl.attachment_path:
                raise ValueError("Select separate SI and BL attachments.")

        return self


from .comparison_models import ComparisonResult
from .models import ClassifiedEmail, EmailCategory


class TextProcessingResponse(BaseModel):
    """Classification plus comparison results when applicable."""

    model_config = ConfigDict(extra="forbid")

    classification: ClassifiedEmail
    comparison: ComparisonResult | None

    @model_validator(mode="after")
    def validate_routing(self):
        needs_comparison = (
            self.classification.category == EmailCategory.BL_COMPARISON
        )
        if needs_comparison != (self.comparison is not None):
            raise ValueError("Comparison results must follow email routing.")
        if self.comparison is not None:
            if self.comparison.email_id != self.classification.email.email_id:
                raise ValueError("Comparison must belong to the classified email.")
        return self
