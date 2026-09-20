"""Regression tests for the shared comparison response."""

import unittest

from pydantic import ValidationError

from backend.main import demo_comparison
from backend.comparison_models import (
    ComparisonStatus,
    DemoComparisonResult,
)


class ComparisonModelTests(unittest.TestCase):
    def setUp(self):
        self.payload = demo_comparison()

    def test_valid_demo(self):
        result = DemoComparisonResult.model_validate(self.payload)
        self.assertEqual(len(result.field_results), 7)
        self.assertEqual(result.status, ComparisonStatus.MISMATCH)

    def test_rejects_ok_with_mismatch(self):
        self.payload["status"] = "OK"
        with self.assertRaises(ValidationError):
            DemoComparisonResult.model_validate(self.payload)

    def test_rejects_duplicate_field(self):
        self.payload["field_results"][1]["field"] = "shipper"
        with self.assertRaises(ValidationError):
            DemoComparisonResult.model_validate(self.payload)

    def test_rejects_missing_defect_entry(self):
        self.payload["defect_fields"] = []
        with self.assertRaises(ValidationError):
            DemoComparisonResult.model_validate(self.payload)

    def test_rejects_missing_value_reported_as_match(self):
        self.mark_shipper_missing()
        with self.assertRaises(ValidationError):
            DemoComparisonResult.model_validate(self.payload)

    def test_accepts_uncertainty_with_confirmed_mismatch(self):
        self.mark_shipper_missing()
        self.payload["field_results"][0]["outcome"] = "UNKNOWN"
        self.payload["status"] = "NEEDS_REVIEW"
        self.payload["review_reasons"] = ["SI shipper is missing."]

        result = DemoComparisonResult.model_validate(self.payload)
        self.assertEqual(result.status, ComparisonStatus.NEEDS_REVIEW)
        self.assertEqual(
            [field.value for field in result.defect_fields],
            ["container_count"],
        )

    def test_rejects_review_without_explanation(self):
        self.mark_shipper_missing()
        self.payload["field_results"][0]["outcome"] = "UNKNOWN"
        self.payload["status"] = "NEEDS_REVIEW"
        self.payload["review_reasons"] = []

        with self.assertRaises(ValidationError):
            DemoComparisonResult.model_validate(self.payload)

    def mark_shipper_missing(self):
        self.payload["field_results"][0]["si"] = {
            "raw_value": None,
            "normalized_value": None,
            "state": "missing",
            "evidence": [],
        }


if __name__ == "__main__":
    unittest.main()
