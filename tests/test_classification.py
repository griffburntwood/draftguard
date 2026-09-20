from backend.classification import classify_email
from backend.models import EmailCategory, EmailRecord


def make_email(subject: str, body: str, attachments: list[str] | None = None):
    return EmailRecord(
        email_id="synthetic-email",
        **{
            "from": "synthetic@example.test",
            "subject": subject,
            "body": body,
            "attachments": attachments or [],
        },
    )


def assert_category(subject: str, body: str, expected: EmailCategory, attachments=None):
    result = classify_email(make_email(subject, body, attachments))
    assert result.category is expected
    assert result.explanation.strip()


def test_classifies_bl_comparison_without_attachments():
    assert_category(
        "Document review",
        "Please compare the draft BL against the shipping instructions.",
        EmailCategory.BL_COMPARISON,
    )


def test_classifies_si_request():
    assert_category(
        "Shipping instructions needed",
        "Please send the SI for the next shipment.",
        EmailCategory.SI_REQUEST,
    )


def test_classifies_invoice_query():
    assert_category(
        "Accounts question",
        "Could you clarify the invoice charges for this shipment?",
        EmailCategory.INVOICE_QUERY,
    )


def test_classifies_spam():
    assert_category(
        "Important account notice",
        "Congratulations, you are a lottery winner. Claim your prize now.",
        EmailCategory.SPAM,
    )


def test_classifies_general():
    assert_category(
        "Schedule update",
        "The vessel is expected to arrive on Tuesday afternoon.",
        EmailCategory.GENERAL,
    )


def test_current_body_overrides_misleading_subject():
    assert_category(
        "Invoice query from last week",
        "Please send the SI for booking 42 so we can prepare the shipment.",
        EmailCategory.SI_REQUEST,
    )


def test_quoted_history_does_not_override_current_request():
    assert_category(
        "Re: shipment update",
        "Please clarify the invoice total.\n\n> Please compare the draft BL against the SI.",
        EmailCategory.INVOICE_QUERY,
    )


def test_checks_attached_pair_with_followup_request():
    assert_category("Documents", "Attached are the SI and draft BL. Please check the details and confirm.", EmailCategory.BL_COMPARISON)


def test_comparison_wording_with_si_first():
    assert_category("Documents", "Please compare the SI and draft BL; attachments were dropped.", EmailCategory.BL_COMPARISON)


def test_wrong_attachment_does_not_change_request_category():
    assert_category("Invoice enclosed", "Attached are the SI and Commercial Invoice. Kindly confirm the BL is in order.", EmailCategory.BL_COMPARISON)


def test_many_subject_keywords_cannot_override_body_request():
    assert_category("Invoice billing payment charges amount due", "Please review the BL.", EmailCategory.BL_COMPARISON)


def test_si_preparation_with_bl_subject():
    assert_category("Draft bill of lading", "Please prepare the shipping instructions and send the SI.", EmailCategory.SI_REQUEST)


def test_conflicting_requests_fall_back_to_general():
    assert_category("Documents", "Please review the BL and send the SI.", EmailCategory.GENERAL)


def test_equal_topic_scores_fall_back_to_general():
    assert_category("", "Invoice and shipping instructions.", EmailCategory.GENERAL)


def test_forwarded_request_does_not_override_body():
    assert_category("Shipment", "Please send the SI.\nFrom: old@example.test\nPlease review the BL.", EmailCategory.SI_REQUEST)


def test_attachments_do_not_determine_category():
    assert_category("Schedule update", "The vessel arrives Tuesday.", EmailCategory.GENERAL, ["SI.txt", "BL.txt"])


def test_subject_used_when_body_has_no_category_evidence():
    assert_category("Please review the BL", "Thank you.", EmailCategory.BL_COMPARISON)
