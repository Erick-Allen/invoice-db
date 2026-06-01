from typing import Protocol
from invoice_db.assistant.classifier_router import SklearnIntentClassifier
from invoice_db.assistant.parameter_extractor import build_assistant_intent
from invoice_db.assistant.schemas import AssistantIntent, IntentPrediction


class IntentClassifier(Protocol):
    def predict(self, message: str) -> IntentPrediction:
        ...


class AssistantRouter:
    def __init__(self, classifier: IntentClassifier | None = None):
        self.classifier = classifier or SklearnIntentClassifier()

    def route(
        self,
        message: str,
        customer_names: list[str] | None = None,
    ) -> AssistantIntent:
        prediction = self.classifier.predict(message)

        return build_assistant_intent(
            message=message,
            prediction=prediction,
            customer_names=customer_names,
        )