from decimal import Decimal, InvalidOperation
from rapidfuzz import fuzz, process
from invoice_db.assistant.schemas import InvoiceStatus, ResultType
from pydantic import ValidationError
from invoice_db.assistant.schemas import (
    AssistantIntent,
    IntentParameters,
    IntentPrediction,
    unknown_intent,
)

STATUS_WORDS: set[InvoiceStatus] = {"draft", "sent", "paid", "void"}

COUNT_PHRASES = [
    "how many",
    "count",
    "number of",
    "total number",
]


def extract_status(message: str) -> InvoiceStatus | None:
    cleaned = (
        message.lower()
        .replace("?", " ")
        .replace(".", " ")
        .replace(",", " ")
    )

    words = set(cleaned.split())
    matches = words & STATUS_WORDS

    if len(matches) == 1:
        return matches.pop()

    return None


def infer_result_type(message: str) -> ResultType:
    normalized = message.lower()

    if any(phrase in normalized for phrase in COUNT_PHRASES):
        return "count"

    return "list"


def extract_money_values(message: str) -> list[int]:
    values = []

    cleaned = (
        message.lower()
        .replace(",", "")
        .replace("$", " $")
    )

    for raw_token in cleaned.split():
        token = raw_token.strip(" $?!;:()[]{}\"'")

        try:
            amount = Decimal(token)
        except InvalidOperation:
            continue

        cents = amount * 100

        if cents == cents.to_integral_value():
            values.append(int(cents))

    return values


def extract_total_range(message: str) -> tuple[int | None, int | None]:
    normalized = message.lower()
    amounts = extract_money_values(message)

    if not amounts:
        return None, None

    if "between" in normalized or "from" in normalized:
        if len(amounts) >= 2:
            return min(amounts[0], amounts[1]), max(amounts[0], amounts[1])

    if any(
        phrase in normalized
        for phrase in ["over", "above", "greater than", "more than"]
    ):
        return amounts[0], None

    if any(
        phrase in normalized
        for phrase in ["under", "below", "less than"]
    ):
        return None, amounts[0]

    return None, None


def extract_customer_name(
    message: str,
    customer_names: list[str],
    min_score: int = 80,
) -> str | None:
    if not customer_names:
        return None

    match = process.extractOne(
        message,
        customer_names,
        scorer=fuzz.partial_ratio,
    )

    if match is None:
        return None

    name, score, _ = match

    if score < min_score:
        return None

    return name

def build_assistant_intent(
    message: str,
    prediction: IntentPrediction,
    customer_names: list[str] | None = None,
) -> AssistantIntent:
    """Build a fully validated assistant intent from a classifier prediction."""

    customer_names = customer_names or []

    try:
        if prediction.intent == "unknown":
            return unknown_intent(confidence=prediction.confidence)

        if prediction.intent == "invoices_by_status":
            status = extract_status(message)

            if status is None:
                return unknown_intent(confidence=prediction.confidence)

            return AssistantIntent(
                intent="invoices_by_status",
                confidence=prediction.confidence,
                parameters=IntentParameters(
                    status=status,
                    result_type=infer_result_type(message),
                ),
            )

        if prediction.intent == "list_overdue_invoices":
            return AssistantIntent(
                intent="list_overdue_invoices",
                confidence=prediction.confidence,
                parameters=IntentParameters(),
            )

        if prediction.intent == "list_invoices_by_customer":
            customer_name = extract_customer_name(
                message=message,
                customer_names=customer_names,
            )

            if customer_name is None:
                return unknown_intent(confidence=prediction.confidence)

            return AssistantIntent(
                intent="list_invoices_by_customer",
                confidence=prediction.confidence,
                parameters=IntentParameters(customer_name=customer_name),
            )

        if prediction.intent == "list_invoices_by_total_range":
            min_total_cents, max_total_cents = extract_total_range(message)

            if min_total_cents is None and max_total_cents is None:
                return unknown_intent(confidence=prediction.confidence)

            return AssistantIntent(
                intent="list_invoices_by_total_range",
                confidence=prediction.confidence,
                parameters=IntentParameters(
                    min_total_cents=min_total_cents,
                    max_total_cents=max_total_cents,
                ),
            )

        return unknown_intent(confidence=prediction.confidence)

    except ValidationError:
        return unknown_intent(confidence=prediction.confidence)