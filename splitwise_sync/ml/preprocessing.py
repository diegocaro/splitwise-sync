from typing import Optional

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.pipeline import FeatureUnion, make_pipeline

from .feature_extractor import DateFeatureExtractor, DescriptionFeatureExtractor


def joined_words(text: str) -> str:
    return "_".join([word for word in text.split(" ") if len(word) > 0]).strip("_")


def build_preprocess(
    verbose: bool = True, stop_words: Optional[list[str]] = None
) -> FeatureUnion:
    stop_words = ["sumup", "merpago", "mercadopago", "spa"]

    # Text vectorization
    text_vectorizer = ColumnTransformer(
        transformers=[
            # (
            #     "description",
            #     CountVectorizer(
            #         max_features=200, ngram_range=(2, 10), stop_words=stop_words
            #     ),
            #     "transaction_description",
            # ),
            # (
            #     "merchant",
            #     CountVectorizer(
            #         max_features=200, ngram_range=(1, 10), stop_words=stop_words
            #     ),
            #     "description_merchant",
            # ),
            (
                "memorized_merchant",
                CountVectorizer(
                    max_features=10000,
                    ngram_range=(1, 1),
                    binary=True,
                    preprocessor=joined_words,
                ),
                "description_merchant",
            ),
            # (
            #     "municipality",
            #     CountVectorizer(max_features=200, ngram_range=(1, 10)),
            #     "description_municipality",
            # ),
            # (
            #     "country",
            #     CountVectorizer(max_features=200, ngram_range=(1, 10)),
            #     "description_country",
            # ),
        ],
        verbose=verbose,
    )

    # Text preprocessing pipeline
    text_preprocessor = make_pipeline(DescriptionFeatureExtractor(), text_vectorizer)

    # Numeric features
    numeric_features = ColumnTransformer(
        transformers=[
            ("transaction_cost", "passthrough", ["transaction_cost"]),
            ("transaction_date", DateFeatureExtractor(), ["transaction_date"]),
        ],
        verbose=verbose,
    )

    # Combine feature extraction pipelines
    combiner = FeatureUnion(
        [("text_features", text_preprocessor), ("numeric_features", numeric_features)],
        verbose=verbose,
    )
    return combiner


if __name__ == "__main__":
    df = pd.read_pickle("processed/matched_transactions_locs.pkl")

    preprocess = build_preprocess()
    transformed = preprocess.fit_transform(df)
    transformed = pd.DataFrame(
        transformed.toarray(), columns=preprocess.get_feature_names_out()
    )
    print(transformed.head())
