from invoice_db.assistant.parameter_extractor import build_assistant_intent
from invoice_db.assistant.schemas import IntentPrediction


def test_builds_status_count_intent():
    prediction = IntentPrediction(
        intent="invoices_by_status",
        confidence=0.9,
    )

    result = build_assistant_intent(
        "How many paid invoices do I have?",
        prediction,
    )

    assert result.intent == "invoices_by_status"
    assert result.confidence == 0.9
    assert result.parameters.status == "paid"
    assert result.parameters.result_type == "count"


def test_builds_status_list_intent():
    prediction = IntentPrediction(
        intent="invoices_by_status",
        confidence=0.85,
    )

    result = build_assistant_intent(
        "Show draft invoices",
        prediction,
    )

    assert result.intent == "invoices_by_status"
    assert result.parameters.status == "draft"
    assert result.parameters.result_type == "list"


def test_returns_unknown_when_status_missing():
    prediction = IntentPrediction(
        intent="invoices_by_status",
        confidence=0.8,
    )

    result = build_assistant_intent(
        "Show invoices",
        prediction,
    )

    assert result.intent == "unknown"


def test_builds_overdue_intent():
    prediction = IntentPrediction(
        intent="list_overdue_invoices",
        confidence=0.92,
    )

    result = build_assistant_intent(
        "Show overdue invoices",
        prediction,
    )

    assert result.intent == "list_overdue_invoices"
    assert result.parameters.model_dump(exclude_none=True) == {}


def test_builds_customer_intent_with_known_customer():
    prediction = IntentPrediction(
        intent="list_invoices_by_customer",
        confidence=0.88,
    )

    result = build_assistant_intent(
        "Show invoices for John Smith",
        prediction,
        customer_names=["John Smith", "Alice Johnson"],
    )

    assert result.intent == "list_invoices_by_customer"
    assert result.parameters.customer_name == "John Smith"


def test_returns_unknown_when_customer_not_found():
    prediction = IntentPrediction(
        intent="list_invoices_by_customer",
        confidence=0.88,
    )

    result = build_assistant_intent(
        "Show invoices for Michael Brown",
        prediction,
        customer_names=["John Smith", "Alice Johnson"],
    )

    assert result.intent == "unknown"


def test_builds_min_total_range_intent():
    prediction = IntentPrediction(
        intent="list_invoices_by_total_range",
        confidence=0.86,
    )

    result = build_assistant_intent(
        "Show invoices over $500",
        prediction,
    )

    assert result.intent == "list_invoices_by_total_range"
    assert result.parameters.min_total_cents == 50000
    assert result.parameters.max_total_cents is None


def test_builds_max_total_range_intent():
    prediction = IntentPrediction(
        intent="list_invoices_by_total_range",
        confidence=0.86,
    )

    result = build_assistant_intent(
        "Find invoices below $300",
        prediction,
    )

    assert result.intent == "list_invoices_by_total_range"
    assert result.parameters.min_total_cents is None
    assert result.parameters.max_total_cents == 30000


def test_builds_between_total_range_intent():
    prediction = IntentPrediction(
        intent="list_invoices_by_total_range",
        confidence=0.86,
    )

    result = build_assistant_intent(
        "Show invoices between $100 and $500",
        prediction,
    )

    assert result.intent == "list_invoices_by_total_range"
    assert result.parameters.min_total_cents == 10000
    assert result.parameters.max_total_cents == 50000


def test_builds_decimal_total_range_intent():
    prediction = IntentPrediction(
        intent="list_invoices_by_total_range",
        confidence=0.86,
    )

    result = build_assistant_intent(
        "Show invoices over $100.25",
        prediction,
    )

    assert result.intent == "list_invoices_by_total_range"
    assert result.parameters.min_total_cents == 10025


def test_returns_unknown_when_total_range_missing():
    prediction = IntentPrediction(
        intent="list_invoices_by_total_range",
        confidence=0.86,
    )

    result = build_assistant_intent(
        "Show expensive invoices",
        prediction,
    )

    assert result.intent == "unknown"


def test_unknown_prediction_stays_unknown():
    prediction = IntentPrediction(
        intent="unknown",
        confidence=0.7,
    )

    result = build_assistant_intent(
        "Tell me a joke",
        prediction,
    )

    assert result.intent == "unknown"
    assert result.confidence == 0.7