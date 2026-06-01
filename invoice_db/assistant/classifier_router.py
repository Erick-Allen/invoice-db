from pathlib import Path

import joblib

from invoice_db.assistant.schemas import IntentPrediction


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_ARTIFACT_PATH = BASE_DIR / "artifacts" / "intent_classifier.joblib"


class ClassifierNotTrainedError(Exception):
    pass


class SklearnIntentClassifier:
    def __init__(self, artifact_path: Path = DEFAULT_ARTIFACT_PATH):
        self.artifact_path = artifact_path
        self.model = self._load_model()

    def predict(self, message: str) -> IntentPrediction:
        cleaned_message = message.strip()

        if not cleaned_message:
            return IntentPrediction(intent="unknown", confidence=1.0)

        probabilities = self.model.predict_proba([cleaned_message])[0]
        classes = self.model.classes_

        best_index = probabilities.argmax()
        predicted_intent = classes[best_index]
        confidence = float(probabilities[best_index])

        return IntentPrediction(
            intent=predicted_intent,
            confidence=confidence,
        )

    def _load_model(self):
        if not self.artifact_path.exists():
            raise ClassifierNotTrainedError(
                "Intent classifier artifact was not found. "
                "Run: uv run python -m invoice_db.assistant.train_classifier"
            )

        return joblib.load(self.artifact_path)