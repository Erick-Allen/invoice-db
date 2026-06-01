import json
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from invoice_db.assistant.train_classifier import ARTIFACT_PATH

BASE_DIR = Path(__file__).resolve().parent
TEST_DATA_PATH = BASE_DIR / "training_data" / "test_intents.json"
EVALUATION_DIR = BASE_DIR / "evaluation_runs"

def load_test_data() -> tuple[list[str], list[str]]:
    with TEST_DATA_PATH.open("r", encoding="utf-8") as file:
        examples = json.load(file)

    texts = [example["text"] for example in examples]
    labels = [example["intent"] for example in examples]

    return texts, labels

def evaluate_classifier() -> dict[str, Any]:
    if not ARTIFACT_PATH.exists():
        raise FileNotFoundError(
            "Intent classifier artifact was not found."
            "Run: uv run python -m invoice_db.assistant.train_classifier"
        )
    
    model = joblib.load(ARTIFACT_PATH)

    texts, expected_labels = load_test_data()

    predicted_labels = model.predict(texts)
    probabilities = model.predict_proba(texts)
    classes = list(model.classes_)

    predictions = []

    labels = sorted(set(expected_labels) | set(predicted_labels))

    report_dict = classification_report(
    expected_labels,
    predicted_labels,
    labels=labels,
    output_dict=True,
    zero_division=0,
)
    
    rounded_report = {
    key: (
        {sub_key: round(sub_val, 2) for sub_key, sub_val in val.items()}
        if isinstance(val, dict)
        else round(val, 2)
    )
    for key, val in report_dict.items()
}

    for text, expected, predicted, probability_row in zip(
        texts,
        expected_labels,
        predicted_labels,
        probabilities,
        strict=True,
    ):
        confidence = float(max(probability_row))

        top_predictions = sorted(
            zip(model.classes_, probability_row, strict=True),
            key=lambda item: item[1],
            reverse=True,
        )[:3]

        predictions.append(
            {
                "text": text,
                "expected_intent": expected,
                "predicted_intent": predicted,
                "confidence": round(confidence, 2),
                "correct": expected == predicted,
                "top_predictions": [
                    {
                        "intent": intent,
                        "confidence": round(float(score), 2),
                    }
                    for intent, score in top_predictions
                ],
            }
        )


    report = {
        "run_at": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M"),
        "total_examples": len(texts),
        "accuracy": round(float(accuracy_score(expected_labels, predicted_labels)), 2),
        "classification_report": rounded_report,
        "confusion_matrix": {
            "labels": labels,
            "matrix": confusion_matrix(
                expected_labels,
                predicted_labels,
                labels=labels
            ).tolist(),
        },
        "predictions": predictions,
    }

    return report

def save_evaluation_report(report: dict[str, Any]) -> Path:
    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    output_path = EVALUATION_DIR / f"intent_eval_{timestamp}.json"

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    return output_path

def main() -> None:
    report = evaluate_classifier()
    output_path = save_evaluation_report(report)

    print(f"Accuracy: {report['accuracy']:.2%}")
    print(f"Saved evaluation report to: {output_path}")

if __name__ == "__main__":
    main()