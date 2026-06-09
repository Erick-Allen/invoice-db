from typing import Protocol
from invoice_db.assistant.classifier_router import SklearnIntentClassifier
from invoice_db.assistant.parameter_extractor import build_assistant_intent
from invoice_db.assistant.qwen_router import QwenIntentRouter, QwenRouterUnavailableError
from invoice_db.assistant.schemas import AssistantIntent, IntentPrediction, unknown_intent

DEFAULT_MIN_CONFIDENCE = 0.60

class IntentClassifier(Protocol):
    def predict(self, message: str) -> IntentPrediction:
        ...


class AssistantRouter:
    def __init__(
        self,
        classifier: IntentClassifier | None = None,
        min_confidence: float = DEFAULT_MIN_CONFIDENCE,
        use_qwen: bool = False,
        qwen_router: QwenIntentRouter | None = None,
    ):
        self.classifier = classifier or SklearnIntentClassifier()
        self.min_confidence = min_confidence
        self.use_qwen = use_qwen
        self.qwen_router = qwen_router or (QwenIntentRouter() if use_qwen else None)

    def route(
        self,
        message: str,
        customer_names: list[str] | None = None,
    ) -> AssistantIntent:
        prediction = self.classifier.predict(message)

        if prediction.confidence >= self.min_confidence:
            assistant_intent = build_assistant_intent(
                message=message,
                prediction=prediction,
                customer_names=customer_names,
            )

            if assistant_intent.intent != "unknown":
                return assistant_intent

            if self.use_qwen and self.qwen_router is not None:
                # print("ROUTER: trying Qwen because classifier returned unknown")
                try:
                    return self.qwen_router.route(message)
                except QwenRouterUnavailableError:
                    return assistant_intent

            return assistant_intent

        if self.use_qwen and self.qwen_router is not None:
            # print("ROUTER: trying Qwen because classifier confidence was low")
            try:
                return self.qwen_router.route(message)
            except QwenRouterUnavailableError:
                return unknown_intent(confidence=prediction.confidence)

        return unknown_intent(confidence=prediction.confidence)