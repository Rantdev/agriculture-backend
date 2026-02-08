"""
utils.py
Small helpers used by the project (optional)
"""
from typing import List
import pandas as pd

def check_required_columns(df: pd.DataFrame, required: List[str]) -> List[str]:
    """Return list of missing columns (empty if none)."""
    return [c for c in required if c not in df.columns]
