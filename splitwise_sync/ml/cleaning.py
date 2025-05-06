import pandas as pd


def clean_datetime_series(
    serie: pd.Series, timezone: str = "America/Santiago"
) -> pd.Series:
    """
    Cleans a datetime column by converting it to a standard format.
    """
    new = pd.to_datetime(
        serie, format="ISO8601", utc=True, errors="coerce"
    ).dt.tz_convert(timezone)
    return new


from typing import Optional

EXPENSES_CLEANED_COLUMNS = [
    "id",
    "date",
    "category_name",
    "description",
    "cost",
    "details",
    "created_at",
    "updated_at",
    "deleted_at",
    "created_by_name",
    "updated_by_name",
    "deleted_by_name",
]


def is_duplicated_expense(expenses: pd.DataFrame) -> pd.Series:
    # Un expense se considera duplicado si tiene la misma fecha, costo y descripción
    # Marcaremos como duplicados a los que tienen una fecha de deleted_at no nula (que fueron eliminados)
    # cols = ["date", "cost", "description"]
    cols = [
        "date",
        "cost",
    ]  # I changed the description of some expenses when testing, but they are the same in the end...
    duplicated = (
        expenses.groupby(cols)
        .agg(cnt=("id", "count"), ids=("id", list))
        .pipe(lambda df: df[df.cnt > 1])
    )
    duplicated_ids = duplicated["ids"].explode().unique()
    is_duplicated = expenses["id"].isin(duplicated_ids) & ~expenses["deleted_at"].isna()
    return is_duplicated


def read_expenses(
    file_name: str,
    keep_all_columns: Optional[bool] = False,
    keep_duplicated: Optional[bool] = True,
) -> pd.DataFrame:
    assert file_name.endswith(".json"), "File must be a JSON file"

    df = pd.read_json(file_name)
    df["id"] = df["id"].astype("Int64")
    for col in ["date", "created_at", "updated_at", "deleted_at"]:
        df[col] = clean_datetime_series(df[col])

    for col in ["created_by", "updated_by", "deleted_by"]:
        df[f"{col}_id"] = df[col].str["id"]
        df[f"{col}_name"] = df[col].str["first_name"]

    df["category_id"] = df["category"].str["id"]
    df["category_name"] = df["category"].str["name"]

    if not keep_all_columns:
        df = df[EXPENSES_CLEANED_COLUMNS]

    is_duplicated = is_duplicated_expense(df)
    if keep_duplicated:
        df["is_duplicated"] = is_duplicated
    else:
        df = df[~is_duplicated]

    df = df.rename(columns=lambda x: f"expense_{x}")
    return df
