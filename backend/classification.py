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


_BL = r"\b(?:b/?l|bills? of lading)\b"
_SI = r"\b(?:si|shipping instructions?)\b"


def _request_categories(text: str) -> set[EmailCategory]:
    """Recognize bounded action phrases before considering topic keywords.

    This remains an English heuristic: indirect requests, negation and unusual
    wording may require a richer classifier later.
    """
    result: set[EmailCategory] = set()
    clauses = re.split(r"[.!?;]|\bbut\b", text)
    for clause in clauses:
        bl = re.search(_BL, clause)
        # Action must precede the BL reference within the same clause.
        if bl and re.search(
            r"\b(?:compare|check|review|verify|confirm)\b.{0,100}" + _BL,
            clause,
        ):
            result.add(EmailCategory.BL_COMPARISON)
        if re.search(
            r"\b(?:send|provide|prepare|create|update|submit|issue)\b"
            r"(?:\s+(?:me|us|the|a|new|updated|your))*\s+" + _SI,
            clause,
        ):
            result.add(EmailCategory.SI_REQUEST)
        if re.search(
            r"\b(?:clarify|explain|query|dispute|cancel|correct)\b.{0,80}"
            r"\b(?:invoice|billing|charges|payment|amount due)\b",
            clause,
        ):
            result.add(EmailCategory.INVOICE_QUERY)
    # A short follow-up can refer back to documents in the current message.
    if (re.search(_BL, text) and re.search(_SI, text)
            and re.search(r"\battached\b", text)
            and re.search(r"\b(?:check|review|verify) the (?:details|documents|docs)\b", text)):
        result.add(EmailCategory.BL_COMPARISON)
    return result


def classify_email(email: EmailRecord) -> ClassifiedEmail:
    """Prefer current body requests, then body topics, then subject evidence."""
    subject = _current_request(email.subject)
    body = _current_request(email.body)
    selected = EmailCategory.GENERAL
    explanation = "No distinctive current-request category evidence was found."

    for source, text in (("body", body), ("subject", subject)):
        requests = _request_categories(text)
        if requests:
            if len(requests) == 1:
                selected = next(iter(requests))
                explanation = f"Explicit {source} request indicates {selected.value}."
            else:
                explanation = f"Conflicting explicit {source} requests; classified as GENERAL."
            break

        evidence = {category: _matches(text, phrases)
                    for category, phrases in _CATEGORY_RULES}
        best = max((len(matches) for matches in evidence.values()), default=0)
        if not best:
            continue
        winners = [category for category, matches in evidence.items()
                   if len(matches) == best]
        if len(winners) == 1:
            selected = winners[0]
            explanation = f"Classified from {source} phrases: " + ", ".join(evidence[selected]) + "."
        else:
            explanation = f"Ambiguous {source} category evidence; classified as GENERAL."
        break

    return ClassifiedEmail(email=email, category=selected, explanation=explanation)
