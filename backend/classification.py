"""Deterministic email classification baseline.

This baseline relies on phrase matching and simple text cleanup, so it cannot
reliably understand every wording, language, or business context. It is not a
machine-learning classifier or a production-grade spam detector. In
particular, ambiguous messages intentionally fall back to GENERAL for a
predictable result.
"""

from __future__ import annotations

import re

from .models import ClassifiedEmail, EmailCategory, EmailRecord


_REPLY_SEPARATOR = re.compile(
    r"(?im)^\s*(?:-+\s*original message\s*-+|on .+ wrote:|from:\s+.+$)"
)
_WHITESPACE = re.compile(r"\s+")

_CATEGORY_RULES: tuple[tuple[EmailCategory, tuple[str, ...]], ...] = (
    (
        EmailCategory.BL_COMPARISON,
        (
            "compare the bl",
            "compare bl",
            "review the bl",
            "review bl",
            "draft bill of lading",
            "bill of lading against",
            "bl against",
            "bl discrepancy",
            "bl discrepancies",
            "bill of lading discrepancy",
            "bill of lading discrepancies",
            "shipping instructions against the bl",
        ),
    ),
    (
        EmailCategory.SI_REQUEST,
        (
            "shipping instructions",
            "shipping instruction",
            "send the si",
            "provide the si",
            "update the si",
            "confirm the si",
        ),
    ),
    (
        EmailCategory.INVOICE_QUERY,
        (
            "invoice",
            "invoicing",
            "billing",
            "payment",
            "amount due",
            "charges",
            "charge query",
        ),
    ),
    (
        EmailCategory.SPAM,
        (
            "unsubscribe",
            "winner",
            "you have won",
            "lottery",
            "prize",
            "free money",
            "wire transfer",
            "limited time offer",
        ),
    ),
)


def _current_request(text: str) -> str:
    """Return normalized text before common quoted or replied history."""

    without_quotes = "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith(">")
    )
    current = _REPLY_SEPARATOR.split(without_quotes, maxsplit=1)[0]
    return _WHITESPACE.sub(" ", current).strip().lower()


def _matches(text: str, phrases: tuple[str, ...]) -> list[str]:
    matched: list[str] = []
    for phrase in sorted(phrases, key=lambda item: (-len(item), item)):
        if phrase in text and not any(phrase in existing for existing in matched):
            matched.append(phrase)
    return [phrase for phrase in phrases if phrase in matched]


def classify_email(email: EmailRecord) -> ClassifiedEmail:
    """Classify an email using current-request subject and body evidence."""

    subject = _current_request(email.subject)
    body = _current_request(email.body)
    scores: dict[EmailCategory, int] = {
        category: 0 for category, _ in _CATEGORY_RULES
    }
    evidence: dict[EmailCategory, list[str]] = {
        category: [] for category, _ in _CATEGORY_RULES
    }

    for category, phrases in _CATEGORY_RULES:
        body_matches = _matches(body, phrases)
        subject_matches = _matches(subject, phrases)
        scores[category] = len(body_matches) * 3 + len(subject_matches)
        evidence[category] = [
            f"body phrase '{phrase}'" for phrase in body_matches
        ] + [f"subject phrase '{phrase}'" for phrase in subject_matches]

    category_order = [category for category, _ in _CATEGORY_RULES]
    selected = max(
        category_order,
        key=lambda category: (scores[category], -category_order.index(category)),
    )
    if scores[selected] == 0:
        selected = EmailCategory.GENERAL
        explanation = "No distinctive current-request category evidence was found."
    else:
        explanation = (
            "Classified from current-request evidence: "
            + "; ".join(evidence[selected])
            + "."
        )

    return ClassifiedEmail(
        email=email,
        category=selected,
        explanation=explanation,
    )