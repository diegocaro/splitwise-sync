import os

import joblib
import pandas as pd


class ExpenseModel:

    def __init__(self, model_path: str):
        assert os.path.exists(model_path), f"Model path {model_path} does not exist."
        self.model = joblib.load(model_path)

    def predict(self, X):
        return self.model.predict(X)

    def predict_proba(self, X):
        return self.model.predict_proba(X)

    def dump(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self.model, path)


if __name__ == "__main__":
    # Example usage
    import pandas as pd

    from splitwise_sync.config import MODELS_DIR, PROCESSED_DIR

    data_path = PROCESSED_DIR / "matched_transactions_locs.pkl"
    df = pd.read_pickle(data_path)
    print("Data loaded successfully from", data_path)

    # Split into features and target
    X = df.drop(columns=["is_shared"])
    y = df["is_shared"]

    # Create and train predictor
    model_path = MODELS_DIR / "decision_tree_model.pkl"
    predictor = ExpenseModel(str(model_path))
    print("Model loaded successfully from", model_path)

    # Make predictions on first 5 transactions
    sample = X.head(5)
    predictions = predictor.predict(sample)
    # predictions_proba = predictor.predict_proba(sample)

    # Display results
    for i, (prediction, actual) in enumerate(zip(predictions, y.head(5))):
        print(f"Transaction {i+1}: Predicted: {prediction}, Actual: {actual}")
