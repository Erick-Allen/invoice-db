# invoice_db/assistant/text_preprocessing.py

import re

MONEY_PATTERN = re.compile(r"\$?\d+(?:,\d{3})*(?:\.\d+)?")

POSSESSIVE_CUSTOMER_PATTERN = re.compile(
    r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*'s\s+invoices\b"
)

CUSTOMER_PATTERNS = [
    re.compile(r"\bfor\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b"),
    re.compile(r"\bconnected to\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b"),
    re.compile(r"\bbilled to\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b"),
    re.compile(r"\bbelonging to\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b"),
    re.compile(r"\btied to\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b"),
]


def normalize_text(text: str) -> str:
    normalized = text

    normalized = POSSESSIVE_CUSTOMER_PATTERN.sub(
        "customer_name invoices",
        normalized,
    )

    for pattern in CUSTOMER_PATTERNS:
        normalized = pattern.sub(
            lambda match: _replace_customer_phrase(match.group(0)),
            normalized,
        )

    normalized = MONEY_PATTERN.sub("money_amount", normalized)

    return normalized.lower()


def _replace_customer_phrase(phrase: str) -> str:
    lowered = phrase.lower()

    if lowered.startswith("billed to"):
        return "billed to customer_name"

    if lowered.startswith("connected to"):
        return "connected to customer_name"

    if lowered.startswith("belonging to"):
        return "belonging to customer_name"

    if lowered.startswith("tied to"):
        return "tied to customer_name"

    if lowered.startswith("for"):
        return "for customer_name"

    return "customer_name"