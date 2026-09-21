"""Tests for email classification through document comparison."""

from unittest.mock import patch

from backend.processing import process_text_email
from backend.processing_models import TextProcessingRequest


TEXT = """Shipper: ABC Trading
Consignee: XYZ Ltd
Notify Party: XYZ Ltd
Port of Loading: Singapore
Port of Discharge: Mersin
Container Count: 3
Gross Weight: 22,000 KG
"""


def request(body="Please compare the BL against the SI.", bl_text=TEXT):
    return TextProcessingRequest.model_validate({
        "email": {
            "email_id": "test_email",
            "from": "demo@example.com",
            "subject": "",
            "body": body,
            "attachments": ["si.txt", "bl.txt"],
        },
        "si": {
            "document_id": "test_si",
            "attachment_path": "si.txt",
            "text": TEXT,
        },
        "bl": {
            "document_id": "test_bl",
            "attachment_path": "bl.txt",
            "text": bl_text,
        },
    })


def test_matching_documents():
    result = process_text_email(request())
    assert result["classification"]["category"] == "BL_COMPARISON"
    comparison = result["comparison"]
    assert comparison["status"] == "OK"
    assert comparison["defect_fields"] == []
    assert comparison["email_id"] == "test_email"
    assert comparison["si_document_id"] == "test_si"
    assert comparison["bl_document_id"] == "test_bl"
    assert len(comparison["field_results"]) == 7


def test_container_mismatch():
    text = TEXT.replace("Container Count: 3", "Container Count: 4")
    result = process_text_email(request(bl_text=text))
    assert result["comparison"]["status"] == "MISMATCH"
    assert result["comparison"]["defect_fields"] == ["container_count"]


def test_missing_value_preserves_confirmed_mismatch():
    text = TEXT.replace("Container Count: 3", "Container Count: 4")
    text = text.replace("Gross Weight: 22,000 KG\n", "")
    result = process_text_email(request(bl_text=text))
    comparison = result["comparison"]
    assert comparison["status"] == "NEEDS_REVIEW"
    assert comparison["defect_fields"] == ["container_count"]
    assert comparison["review_reasons"]


def test_missing_bl_preserves_si_evidence():
    payload = request().model_dump(by_alias=True)
    payload["bl"] = None
    result = process_text_email(
        TextProcessingRequest.model_validate(payload)
    )
    comparison = result["comparison"]
    assert comparison["status"] == "NEEDS_REVIEW"
    assert comparison["bl_document_id"] is None
    assert comparison["defect_fields"] == []
    assert all(
        field["outcome"] == "UNKNOWN"
        for field in comparison["field_results"]
    )
    assert comparison["field_results"][0]["si"]["evidence"]
    assert comparison["field_results"][0]["bl"]["evidence"] == []


def test_invoice_skips_extraction():
    invoice = request(body="Please explain the invoice charges.")
    with patch("backend.processing.extract_text_document") as extract:
        result = process_text_email(invoice)
    extract.assert_not_called()
    assert result["classification"]["category"] == "INVOICE_QUERY"
    assert result["comparison"] is None


def test_empty_bl_requires_review():
    result = process_text_email(request(bl_text=""))
    comparison = result["comparison"]
    assert comparison["status"] == "NEEDS_REVIEW"
    assert comparison["defect_fields"] == []
    assert all(
        field["outcome"] == "UNKNOWN"
        for field in comparison["field_results"]
    )
