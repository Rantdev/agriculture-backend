"""
preprocess_train.py
Loads data, preprocesses, trains classification (Suitability) and regression (Yield) pipelines,
saves pipelines and metadata.

Usage:
    python preprocess_train.py --input data/agriculture_suitability.csv --out_dir models

Outputs:
    models/suitability_pipeline.joblib
    models/yield_pipeline.joblib
    models/metadata.json
"""
import argparse
import json
from pathlib import Path
import math

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import (
    accuracy_score,
    mean_squared_error,
    r2_score,
    classification_report,
    confusion_matrix,
)

RANDOM_STATE = 42


def detect_columns(df: pd.DataFrame):
    """Try to auto-detect suitability and yield target columns."""
    # detect suitability and yield columns
    suit_col = next((c for c in df.columns if "suit" in c.lower()), None)
    yield_col = next((c for c in df.columns if "yield" in c.lower()), None)

    if suit_col is None:
        # fallback: any low-cardinality object column
        candidates = [
            c for c in df.columns
            if df[c].dtype == object and df[c].nunique() <= 3
        ]
        suit_col = candidates[0] if candidates else None

    if yield_col is None:
        numeric_cols = [
            c for c in df.columns
            if pd.api.types.is_numeric_dtype(df[c])
        ]
        yield_col = max(numeric_cols, key=lambda x: df[x].mean()) if numeric_cols else None

    return suit_col, yield_col


def build_pipelines(numeric_cols, categorical_cols):
    """Create preprocessing + model pipelines."""
    numeric_transformer = Pipeline([("scaler", StandardScaler())])

    # Use sparse=False for broader sklearn compatibility
    categorical_transformer = OneHotEncoder(
        handle_unknown="ignore",
        sparse=False
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_cols),
            ("cat", categorical_transformer, categorical_cols),
        ],
        remainder="drop",
    )

    clf_pipeline = Pipeline([
        ("pre", preprocessor),
        ("clf", RandomForestClassifier(
            n_estimators=200,
            random_state=RANDOM_STATE
        )),
    ])

    reg_pipeline = Pipeline([
        ("pre", preprocessor),
        ("reg", RandomForestRegressor(
            n_estimators=200,
            random_state=RANDOM_STATE
        )),
    ])

    return clf_pipeline, reg_pipeline


def main(input_csv: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(input_csv)

    suit_col, yield_col = detect_columns(df)
    if suit_col is None or yield_col is None:
        raise ValueError(
            f"Could not detect columns. Suitability: {suit_col}, Yield: {yield_col}"
        )

    exclude = ["Farm_ID", suit_col, yield_col]
    categorical_cols = [
        c for c in df.columns
        if df[c].dtype == object and c not in exclude
    ]
    numeric_cols = [
        c for c in df.columns
        if c not in categorical_cols + exclude
    ]

    # Create binary label for suitability
    if df[suit_col].dtype == object:
        df["Suitability_Label"] = df[suit_col].apply(
            lambda x: 1
            if str(x).strip().lower() in ("suitable", "yes", "y", "1", "true")
            else 0
        )
    else:
        df["Suitability_Label"] = df[suit_col].astype(int)

    # Fill missing numerical
    for col in numeric_cols:
        if df[col].isnull().any():
            df[col] = df[col].fillna(df[col].median())

    # Fill missing categorical
    for col in categorical_cols:
        if df[col].isnull().any():
            df[col] = df[col].fillna(df[col].mode().iloc[0])

    clf_pipeline, reg_pipeline = build_pipelines(numeric_cols, categorical_cols)

    # Train classification model
    X = df[numeric_cols + categorical_cols]
    y = df["Suitability_Label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        stratify=y,
        test_size=0.2,
        random_state=RANDOM_STATE,
    )

    clf_pipeline.fit(X_train, y_train)
    y_pred = clf_pipeline.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    print("Classification accuracy:", acc)
    print(classification_report(y_test, y_pred, zero_division=0))
    print("Confusion matrix:\n", confusion_matrix(y_test, y_pred))

    # Train regression model
    Xr = df[numeric_cols + categorical_cols]
    yr = df[yield_col].astype(float)

    Xr_train, Xr_test, yr_train, yr_test = train_test_split(
        Xr,
        yr,
        test_size=0.2,
        random_state=RANDOM_STATE,
    )

    reg_pipeline.fit(Xr_train, yr_train)
    yr_pred = reg_pipeline.predict(Xr_test)

    rmse = math.sqrt(mean_squared_error(yr_test, yr_pred))
    r2 = r2_score(yr_test, yr_pred)
    print("Regression RMSE:", rmse, "R2:", r2)

    # Save models and metadata
    joblib.dump(clf_pipeline, out_dir / "suitability_pipeline.joblib")
    joblib.dump(reg_pipeline, out_dir / "yield_pipeline.joblib")

    meta = {
        "input_csv": str(input_csv),
        "suitability_column": suit_col,
        "yield_column": yield_col,
        "numeric_features": numeric_cols,
        "categorical_features": categorical_cols,
        "classification_accuracy": float(acc),
        "regression_rmse": float(rmse),
        "regression_r2": float(r2),
    }

    with open(out_dir / "metadata.json", "w") as f:
        json.dump(meta, f, indent=2)

    print(f"Saved artifacts to {out_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default="data/agriculture_suitability.csv",
        help="Input CSV path",
    )
    parser.add_argument(
        "--out_dir",
        "-o",
        type=str,
        default="models",
        help="Output models directory",
    )
    args = parser.parse_args()
    main(Path(args.input), Path(args.out_dir))
