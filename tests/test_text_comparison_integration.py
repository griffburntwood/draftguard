"""Test plain-text extraction connected to the comparison engine."""

from backend.extraction import extract_text_document
from backend.comparison import compare_shipments


SI_TEXT = """Shipper: ABC Trading
Consignee: XYZ Ltd
Notify Party: XYZ Ltd
Port of Loading: Singapore
Port of Discharge: Mersin
Container Count: 3
Gross Weight: 22,000 KG
"""


def compare_text(bl_text):
    return compare_shipments(
        si=extract_text_document(SI_TEXT, "test_si"),
        bl=extract_text_document(bl_text, "test_bl"),
        email_id="test_email",
        comparison_id="test_comparison",
    )


def test_matching_documents():
    result = compare_text(SI_TEXT)
    assert result["status"] == "OK"
    assert result["defect_fields"] == []
    assert len(result["field_results"]) == 7
    assert all(
        field["outcome"] == "MATCH"
        for field in result["field_results"]
    )


def test_container_mismatch():
    text = SI_TEXT.replace("Container Count: 3", "Container Count: 4")
    result = compare_text(text)
    assert result["status"] == "MISMATCH"
    assert result["defect_fields"] == ["container_count"]


def test_missing_weight_preserves_confirmed_defect():
    text = SI_TEXT.replace("Container Count: 3", "Container Count: 4")
    text = text.replace("Gross Weight: 22,000 KG\n", "")
    result = compare_text(text)

    assert result["status"] == "NEEDS_REVIEW"
    assert result["defect_fields"] == ["container_count"]
    assert result["review_reasons"]

    weight = next(
        field for field in result["field_results"]
        if field["field"] == "gross_weight_kg"
    )
    assert weight["outcome"] == "UNKNOWN"
    assert weight["bl"]["normalized_value"] is None


def test_source_evidence_survives_comparison():
    text = SI_TEXT.replace("Container Count: 3", "Container Count: 4")
    result = compare_text(text)
    container = next(
        field for field in result["field_results"]
        if field["field"] == "container_count"
    )

    si_source = container["si"]["evidence"][0]
    bl_source = container["bl"]["evidence"][0]
    assert si_source["document_id"] == "test_si"
    assert bl_source["document_id"] == "test_bl"
    assert "Container Count: 3" in si_source["text"]
    assert "Container Count: 4" in bl_source["text"]
    assert si_source["location"]
    assert bl_source["location"]
