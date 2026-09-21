"""Tests for evaluator-format submission entries."""

import unittest

from backend.comparison_models import DemoComparisonResult
from backend.main import demo_comparison
from backend.models import (
    ClassifiedEmail,
    EmailCategory,
    EmailRecord,
    ExtractionState,
)
from backend.submission import build_submission_entry


def classified(category: EmailCategory) -> ClassifiedEmail:
    return ClassifiedEmail(
        email=EmailRecord(
            email_id="email_001",
            **{
                "from": "ops@example.com",
                "subject": "Test",
                "body": "Test body",
                "attachments": [],
            },
        ),
        category=category,
        explanation="Synthetic test classification.",
    )


def payload() -> dict:
    return demo_comparison()


def matching_payload() -> dict:
    result = payload()
    container = result["field_results"][5]
    container["bl"] = {
        **container["bl"],
        "raw_value": "3",
        "normalized_value": 3,
        "evidence": [
            {
                **container["bl"]["evidence"][0],
                "text": "container_count: 3",
            }
        ],
    }
    container["outcome"] = "MATCH"
    container["explanation"] = "Values match."
    result["status"] = "OK"
    result["defect_fields"] = []
    return result


def review_payload(reason: str, state: ExtractionState | None = None) -> dict:
    result = matching_payload()
    result["status"] = "NEEDS_REVIEW"
    result["review_reasons"] = [reason]
    if state is not None:
        result["field_results"][0]["si"] = {
            "raw_value": None,
            "normalized_value": None,
            "state": state.value,
            "evidence": [],
        }
        result["field_results"][0]["outcome"] = "UNKNOWN"
        result["field_results"][0]["explanation"] = reason
    return result


class SubmissionTests(unittest.TestCase):
    def entry(self, result: dict) -> dict:
        comparison = DemoComparisonResult.model_validate(result)
        return build_submission_entry(
            classified(EmailCategory.BL_COMPARISON), comparison
        )

    def test_ok_entry(self):
        entry = self.entry(matching_payload())

        self.assertEqual(entry["status"], "OK")
        self.assertIsNone(entry["review_reason"])
        self.assertFalse(entry["has_defect"])
        self.assertEqual(entry["defect_fields"], [])

    def test_mismatch_entry(self):
        entry = self.entry(payload())

        self.assertEqual(entry["status"], "MISMATCH")
        self.assertIsNone(entry["review_reason"])
        self.assertTrue(entry["has_defect"])
        self.assertEqual(entry["defect_fields"], ["container_count"])

    def test_wrong_document_type_reason(self):
        entry = self.entry(
            review_payload("SI attachment has the wrong document type.")
        )

        self.assertEqual(entry["review_reason"], "wrong_doc_type")

    def test_missing_attachment_reason(self):
        entry = self.entry(review_payload("Draft BL attachment is missing."))

        self.assertEqual(entry["review_reason"], "missing_attachment")

    def test_unreadable_reason(self):
        entry = self.entry(
            review_payload("SI shipper is unreadable.", ExtractionState.UNREADABLE)
        )

        self.assertEqual(entry["review_reason"], "unreadable")

    def test_missing_value_reason(self):
        entry = self.entry(
            review_payload("SI shipper is missing.", ExtractionState.MISSING)
        )

        self.assertEqual(entry["review_reason"], "missing_value")

    def test_non_comparison_categories_have_empty_comparison_values(self):
        for category in (
            EmailCategory.SI_REQUEST,
            EmailCategory.INVOICE_QUERY,
            EmailCategory.GENERAL,
            EmailCategory.SPAM,
        ):
            with self.subTest(category=category):
                entry = build_submission_entry(classified(category), None)
                self.assertEqual(entry["category"], category.value)
                self.assertEqual(entry["status"], "OK")
                self.assertIsNone(entry["review_reason"])
                self.assertFalse(entry["has_defect"])
                self.assertEqual(entry["defect_fields"], [])


if __name__ == "__main__":
    unittest.main()
