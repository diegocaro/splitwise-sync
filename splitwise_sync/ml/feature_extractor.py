import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


class DateFeatureExtractor(BaseEstimator, TransformerMixin):
    def __init__(self, date_column: str = "transaction_date"):
        self.date_column = date_column
        self._feature_names_out = [
            # "month",
            "hour",
            "dayofweek",
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
            # "is_weekend",
        ]

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        assert self.date_column in X.columns, f"{self.date_column} not in input columns"

        date_col = pd.to_datetime(X[self.date_column])
        X_new = pd.DataFrame(
            {
                # "month": date_col.dt.month,
                "hour": date_col.dt.hour,
                "dayofweek": date_col.dt.dayofweek,
                "monday": (date_col.dt.dayofweek == 0).astype(int),
                "tuesday": (date_col.dt.dayofweek == 1).astype(int),
                "wednesday": (date_col.dt.dayofweek == 2).astype(int),
                "thursday": (date_col.dt.dayofweek == 3).astype(int),
                "friday": (date_col.dt.dayofweek == 4).astype(int),
                "saturday": (date_col.dt.dayofweek == 5).astype(int),
                "sunday": (date_col.dt.dayofweek == 6).astype(int),
                # "is_weekend": (date_col.dt.dayofweek >= 5).astype(int),
            },
            index=X.index,
        )

        return X_new

    def get_feature_names_out(self, input_features=None):
        return self._feature_names_out


class DescriptionFeatureExtractor(BaseEstimator, TransformerMixin):
    def __init__(self, description_column: str = "transaction_description"):
        self.description_column = description_column
        self._feature_names_out = [
            "description_municipality",
            "description_country",
            "description_merchant",
            "transaction_description",
        ]

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        assert (
            self.description_column in X.columns
        ), f"{self.description_column} not in input columns {X.columns}"

        description_col = X[self.description_column].fillna("")
        X_new = pd.DataFrame(
            {
                "description_municipality": description_col.str[23:37].str.strip(),
                "description_country": description_col.str[37:45].str.strip(),
                "description_merchant": description_col.str[0:23].str.strip(),
                "transaction_description": description_col.str.strip(),
            },
            index=X.index,
        )

        return X_new

    def get_feature_names_out(self, input_features=None):
        return self._feature_names_out


if __name__ == "__main__":
    df = pd.read_pickle("processed/matched_transactions_locs.pkl")
    col = "transaction_date"
    print(pd.concat([df[col], DateFeatureExtractor().transform(df)], axis=1))

    col = "transaction_description"
    print(pd.concat([df[col], DescriptionFeatureExtractor().transform(df)], axis=1))
