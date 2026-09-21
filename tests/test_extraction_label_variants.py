"""Synthetic tests for label formats found in participant documents."""

from backend.extraction import extract_text_document


TEXT = """SHIPPING INSTRUCTION
Shipper: Example Exporter
  12 Example Road
Consignee (Non-Negotiable): Example Importer
  34 Sample Avenue
Notify: Example Notify
Port of Loading (POL): Singapore
POD: Mersin
Total Containers: 6 x 40'HC
Gross Wt (kgs): 131,058 KG
Vessel: Example Vessel
"""


def test_party_fields_stop_at_alternate_labels():
    record = extract_text_document(TEXT, "synthetic_si")
    assert record.shipper.normalized_value == (
        "Example Exporter\n12 Example Road"
    )
    assert record.consignee.normalized_value == (
        "Example Importer\n34 Sample Avenue"
    )
    assert record.notify_party.normalized_value == "Example Notify"
    assert record.port_of_loading.normalized_value == "Singapore"
    assert record.shipper.evidence[0].location == "TXT: lines 2-3"
    assert record.consignee.evidence[0].location == "TXT: lines 4-5"


def test_container_expression_and_weight_label():
    record = extract_text_document(TEXT, "synthetic_si")
    assert record.container_count.normalized_value == 6
    assert record.container_count.raw_value == "6 x 40'HC"
    assert record.gross_weight_kg.normalized_value == 131058
    assert record.gross_weight_kg.raw_value == "131,058 KG"


def test_bl_consignee_label():
    text = TEXT.replace(
        "Consignee (Non-Negotiable):", "To the Order of:"
    )
    record = extract_text_document(text, "synthetic_bl")
    assert record.consignee.normalized_value == (
        "Example Importer\n34 Sample Avenue"
    )
    assert record.shipper.normalized_value == (
        "Example Exporter\n12 Example Road"
    )
