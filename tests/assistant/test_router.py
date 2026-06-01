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