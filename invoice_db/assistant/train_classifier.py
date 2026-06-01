import json
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from invoice_db.assistant.text_preprocessing import normalize_text

BASE_DIR = Path(__file__).resolve().parent
TRAINING_DATA_PATH = BASE_DIR / "training_data" / "train_intents.json"
ARTIFACT_PATH = BASE_DIR / "artifacts" / "intent_classifier.joblib"

def load_training_data() -> tuple[list[str], list[str]]:
    with TRAINING_DATA_PATH.open("r", encoding="utf-8") as file:
        examples = json.load(file)

    texts = [example['text'] for example in examples]
    labels = [example['intent'] for example in examples]

    return texts, labels

def train_classifier() -> Pipeline:
    texts, labels = load_training_data()

    model = Pipeline(
        steps = [
            (
                "tfidf",
                TfidfVectorizer(
                    preprocessor=normalize_text,
                    lowercase=True,
                    ngram_range=(1, 2),
                    sublinear_tf=True,
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=1000,
                    C=5.0,
                    # class_weight="balanced",
                )
            ),
        ]
    )

    model.fit(texts, labels)
    return model


def main() -> None:
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)

    model = train_classifier()
    joblib.dump(model, ARTIFACT_PATH)

    print(f"Saved classifier to: {ARTIFACT_PATH}")

if __name__ == "__main__":
    main()