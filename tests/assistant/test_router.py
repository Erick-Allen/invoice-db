from invoice_db.assistant.router import AssistantRouter
from invoice_db.assistant.schemas import IntentPrediction


class FakeClassifier:
    def predict(self, message: str) -> IntentPrediction:
        return IntentPrediction(
            intent="invoices_by_status",
            confidence=0.9,
        )


def test_routes_status_count_request():
    router = AssistantRouter(classifier=FakeClassifier())

    result = router.route("How many paid invoices do I have?")

    assert result.intent == "invoices_by_status"
    assert result.confidence == 0.9
    assert result.parameters.status == "paid"
    assert result.parameters.result_type == "count"

class LowConfidenceClassifier:
    def predict(self, message: str) -> IntentPrediction:
        return IntentPrediction(
            intent="invoices_by_status",
            confidence=0.40,
        )


def test_routes_low_confidence_prediction_to_unknown():
    router = AssistantRouter(
        classifier=LowConfidenceClassifier(),
        min_confidence=0.60,
    )

    result = router.route("Show paid invoices")

    assert result.intent == "unknown"
    assert result.confidence == 0.40