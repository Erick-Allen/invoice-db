# Assistant Classifier Evaluation Runs

The v0.9 assistant classifier uses a local scikit-learn intent classifier to route natural-language invoice questions into predefined intents.

Current baseline:
- Five supported intents
- Balanced training data
- 50 test examples
- 10 test examples per intent
- 100% accuracy on current test set
- Overdue invoice intent improved after balancing training data

This baseline should be preserved before adding parameter extraction and Qwen/Ollama fallback behavior.