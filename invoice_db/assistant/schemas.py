from typing import Literal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


IntentName = Literal[
    "invoices_by_status",
    "list_overdue_invoices",
    "list_invoices_by_customer",
    "list_invoices_by_total_range",
    "unknown",
]

ResultType = Literal["count", "list"]

InvoiceStatus = Literal["draft", "sent", "paid", "void"]


class IntentParameters(BaseModel):
    """Validated parameters extracted from the user's message."""

    model_config = ConfigDict(extra="forbid")

    status: InvoiceStatus | None = None
    result_type: ResultType | None = None
    customer_name: str | None = Field(default=None, min_length=1, max_length=100)
    min_total_cents: int | None = Field(default=None, ge=0)
    max_total_cents: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_total_range(self) -> "IntentParameters":
        if (
            self.min_total_cents is not None
            and self.max_total_cents is not None
            and self.min_total_cents > self.max_total_cents
        ):
            raise ValueError("min_total_cents cannot be greater than max_total_cents")

        return self


class AssistantIntent(BaseModel):
    """The single contract every assistant router must return."""

    model_config = ConfigDict(extra="forbid")

    intent: IntentName
    confidence: float = Field(ge=0.0, le=1.0)
    parameters: IntentParameters = Field(default_factory=IntentParameters)

    @model_validator(mode="after")
    def validate_parameters_for_intent(self) -> "AssistantIntent":
        params = self.parameters.model_dump(exclude_none=True)
        provided = set(params.keys())

        allowed_params_by_intent: dict[IntentName, set[str]] = {
            "invoices_by_status": {"status", "result_type"},
            "list_overdue_invoices": set(),
            "list_invoices_by_customer": {"customer_name"},
            "list_invoices_by_total_range": {
                "min_total_cents",
                "max_total_cents",
            },
            "unknown": set(),
        }

        required_params_by_intent: dict[IntentName, set[str]] = {
            "invoices_by_status": {"status", "result_type"},
            "list_overdue_invoices": set(),
            "list_invoices_by_customer": {"customer_name"},
            "list_invoices_by_total_range": set(),
            "unknown": set(),
        }

        at_least_one_params_by_intent: dict[IntentName, set[str]] = {
            "list_invoices_by_total_range": {
                "min_total_cents",
                "max_total_cents",
            }
        }

        allowed = allowed_params_by_intent[self.intent]
        required = required_params_by_intent[self.intent]

        extra = provided - allowed
        if extra:
            raise ValueError(
                f"Intent '{self.intent}' does not accept parameters: {sorted(extra)}"
            )

        missing = required - provided
        if missing:
            raise ValueError(
                f"Intent '{self.intent}' requires parameters: {sorted(missing)}"
            )

        required_any = at_least_one_params_by_intent.get(self.intent, set())
        if required_any and not provided.intersection(required_any):
            raise ValueError(
                "list_invoices_by_total_range requires at least one total range parameter"
            )

        return self


class IntentPrediction(BaseModel):
    """Raw classifier output before parameter extraction."""

    model_config = ConfigDict(extra="forbid")

    intent: IntentName
    confidence: float = Field(ge=0.0, le=1.0)

class AssistantResponse(BaseModel):
    """Response returned after dispatching an assistant intent."""

    model_config = ConfigDict(extra="forbid")

    message: str
    intent: IntentName
    data: Any = None


def unknown_intent(confidence: float = 0.0) -> AssistantIntent:
    """Return a safe fallback intent."""

    return AssistantIntent(
        intent="unknown",
        confidence=confidence,
        parameters=IntentParameters(),
    )


def infer_result_type(message: str) -> ResultType:
    """Infer whether the user wants a count or list response."""

    normalized = message.lower()

    count_phrases = [
        "how many",
        "count",
        "number of",
        "total number",
    ]

    if any(phrase in normalized for phrase in count_phrases):
        return "count"

    return "list"