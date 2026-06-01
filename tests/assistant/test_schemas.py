import pytest
from pydantic import ValidationError

from invoice_db.assistant.schemas import (AssistantIntent, IntentParameters, unknown_intent)

def test_accepts_valid_count_by_status_intent():
    result = AssistantIntent(
        intent="invoices_by_status",
        confidence=0.95,
        parameters=IntentParameters(status="paid", result_type="count"),
    )

    assert result.intent == "invoices_by_status"
    assert result.confidence == 0.95
    assert result.parameters.status == "paid"
    assert result.parameters.result_type == "count"

def test_accepts_valid_list_overdue_intent_without_parameters():
    result = AssistantIntent(
        intent="list_overdue_invoices",
        confidence=0.9,
    )

    assert result.intent == "list_overdue_invoices"
    assert result.parameters.status is None

def test_accepts_valid_customer_intent():
    result = AssistantIntent(
        intent="list_invoices_by_customer",
        confidence=0.88,
        parameters=IntentParameters(customer_name="John Smith"),
    )

    assert result.intent == "list_invoices_by_customer"
    assert result.parameters.customer_name == "John Smith"

def test_accepts_valid_total_range_with_min_only():
    result = AssistantIntent(
        intent="list_invoices_by_total_range",
        confidence=0.81,
        parameters=IntentParameters(min_total_cents=50000)
    )

    assert result.intent == "list_invoices_by_total_range"
    assert result.parameters.min_total_cents == 50000

def test_accepts_valid_total_range_with_max_only():
    result = AssistantIntent(
        intent="list_invoices_by_total_range",
        confidence=0.81,
        parameters=IntentParameters(max_total_cents=50000)
    )

    assert result.intent == "list_invoices_by_total_range"
    assert result.parameters.max_total_cents == 50000

def test_rejects_invalid_status():
    with pytest.raises(ValidationError):
        AssistantIntent(
            intent="count_invoices_by_status",
            confidence=0.95,
            parameters={"status": "unpaid"},
        )

def test_rejects_confidence_below_zero():
    with pytest.raises(ValidationError):
        AssistantIntent(
            intent="list_overdue_invoices",
            confidence=-0.1,
        )

def test_rejects_confidence_above_one():
    with pytest.raises(ValidationError):
        AssistantIntent(
            intent="list_overdue_invoices",
            confidence=1.1,
        )

def test_rejects_extra_field_on_parameters():
    with pytest.raises(ValidationError):
        AssistantIntent(
            intent="list_overdue_invoices",
            confidence=0.9,
            parameters={"status": "paid", "random": "not allowed"}
        )

def test_rejects_status_parameter_for_overdue_intent():
    with pytest.raises(ValidationError):
        AssistantIntent(
            intent="list_overdue_invoices",
            confidence=0.9,
            parameters=IntentParameters(status="paid"),
        )

def test_rejects_missing_status_for_count_intent():
    with pytest.raises(ValidationError):
        AssistantIntent(
            intent="count_invoices_by_status",
            confidence=0.9,
        )

def test_rejects_total_range_without_min_or_max():
    with pytest.raises(ValidationError):
        AssistantIntent(
            intent="list_invoices_by_total_range",
            confidence=0.9,
        )

def test_rejects_min_total_greater_than_max_total():
    with pytest.raises(ValidationError):
        AssistantIntent(
            intent="list_invoices_by_total_range",
            confidence=0.9,
            parameters=IntentParameters(
                min_total_cents=100000,
                max_total_cents=50000,
            ),
        )

def test_unknown_intent_helper_returns_safe_unknown_intent():
    result = unknown_intent()

    assert result.intent == "unknown"
    assert result.confidence == 0.0
    assert result.parameters.model_dump(exclude_none=True) == {}