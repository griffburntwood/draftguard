"""Tests for the seven-field shipment comparator."""

import unittest

from backend.comparison import compare_shipments
from backend.models import (
    ExtractedField,
    ExtractionState,
    ShipmentRecord,
    SourceEvidence,
)


def extracted(value, document_id: str) -> ExtractedField:
    return ExtractedField(
        raw_value=str(value),
        normalized_value=value,
        state=ExtractionState.EXTRACTED,
        evidence=[
            SourceEvidence(
                document_id=document_id,
                location="Synthetic test source",
                text=str(value),
            )
        ],
    )


def uncertain(state: ExtractionState) -> ExtractedField:
    return ExtractedField(
        raw_value=None,
        normalized_value=None,
        state=state,
        evidence=[],
    )


def shipment(document_id: str, **overrides) -> ShipmentRecord:
    values = {
        "shipper": "Acme Trading",
        "consignee": "Northstar Imports",
        "notify_party": "Northstar Imports",
        "port_of_loading": "Singapore",
        "port_of_discharge": "Mersin",
        "container_count": 3,
        "gross_weight_kg": 22000,
    }
    values.update(overrides)
    fields = {
        name: value if isinstance(value, ExtractedField) else extracted(value, document_id)
        for name, value in values.items()
    }
    return ShipmentRecord(document_id=document_id, **fields)


class CompareShipmentsTests(unittest.TestCase):
    def compare(self, si: ShipmentRecord, bl: ShipmentRecord) -> dict:
        return compare_shipments(si, bl, "email_001", "comparison_001")

    def outcomes(self, result: dict) -> dict[str, str]:
        return {item["field"]: item["outcome"] for item in result["field_results"]}

    def test_matching_records_return_ok_and_preserve_evidence(self):
        result = self.compare(shipment("si_001"), shipment("bl_001"))

        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["defect_fields"], [])
        self.assertEqual(set(self.outcomes(result).values()), {"MATCH"})
        self.assertEqual(
            result["field_results"][0]["si"]["evidence"][0]["document_id"],
            "si_001",
        )

    def test_one_mismatch_returns_mismatch(self):
        result = self.compare(
            shipment("si_001"),
            shipment("bl_001", container_count=4),
        )

        self.assertEqual(result["status"], "MISMATCH")
        self.assertEqual(result["defect_fields"], ["container_count"])
        self.assertEqual(self.outcomes(result)["container_count"], "MISMATCH")

    def test_multiple_mismatches_are_all_reported(self):
        result = self.compare(
            shipment("si_001"),
            shipment(
                "bl_001",
                consignee="Different consignee",
                port_of_discharge="Izmir",
                gross_weight_kg=22001,
            ),
        )

        self.assertEqual(result["status"], "MISMATCH")
        self.assertEqual(
            result["defect_fields"],
            ["consignee", "port_of_discharge", "gross_weight_kg"],
        )

    def test_text_formatting_differences_match(self):
        result = self.compare(
            shipment(
                "si_001",
                shipper="  ACME\nTrading  ",
                port_of_loading="SINGAPORE",
            ),
            shipment(
                "bl_001",
                shipper="acme trading",
                port_of_loading=" singapore ",
            ),
        )

        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["defect_fields"], [])

    def test_mismatch_and_uncertainty_need_review_but_keep_defect(self):
        result = self.compare(
            shipment("si_001", shipper=uncertain(ExtractionState.MISSING)),
            shipment("bl_001", container_count=4),
        )

        self.assertEqual(result["status"], "NEEDS_REVIEW")
        self.assertEqual(result["defect_fields"], ["container_count"])
        self.assertEqual(self.outcomes(result)["shipper"], "UNKNOWN")
        self.assertEqual(self.outcomes(result)["container_count"], "MISMATCH")
        self.assertEqual(result["review_reasons"], ["SI shipper is missing."])


if __name__ == "__main__":
    unittest.main()
