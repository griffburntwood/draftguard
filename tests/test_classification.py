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