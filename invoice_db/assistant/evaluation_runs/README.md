# Assistant Classifier Evaluation Runs

The assistant uses a local scikit-learn intent classifier to route natural-language invoice questions into supported intents. Parameter extraction and the optional Ollama/Qwen fallback both return the same validated assistant intent contract.

Current classifier baseline:

- Five supported intents
- Balanced training data
- 50 test examples
- 10 test examples per intent
- 100% accuracy on the current test set

Preserve or intentionally update this baseline when changing assistant routing, supported intents, or training data.
