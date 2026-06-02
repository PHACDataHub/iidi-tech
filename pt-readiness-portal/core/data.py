"""
core/data.py
────────────
File ingestion and data preparation for the PT Readiness Dashboard.

Public API
──────────
parse_upload(contents, filename)  → raw DataFrame
try_load_default()                → raw DataFrame (from SURVEY_CSV env var)
prepare_data(raw_df)              → (clean_df, scores_df)
"""

import base64
import io
import os

import pandas as pd

from core.scoring import deduplicate, calculate_scores


# ─────────────────────────── FILE PARSING ────────────────────────────

def parse_upload(contents: str, filename: str) -> pd.DataFrame:
    """
    Decode a base64-encoded Dash upload payload and return a DataFrame.
    Supports .xlsx, .xls, and .csv files.
    """
    _, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    if filename.lower().endswith(('.xlsx', '.xls')):
        return pd.read_excel(io.BytesIO(decoded))

    try:
        return pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    except UnicodeDecodeError:
        return pd.read_csv(io.StringIO(decoded.decode('latin-1')))


def try_load_default() -> pd.DataFrame:
    """
    Attempt to load a survey file from the SURVEY_CSV environment variable.
    Returns an empty DataFrame if the variable is unset or the file is unreadable.

    Usage:
        SURVEY_CSV=/path/to/survey.xlsx python app.py
    """
    path = os.environ.get('SURVEY_CSV', '')
    if not path or not os.path.exists(path):
        return pd.DataFrame()

    try:
        if path.lower().endswith(('.xlsx', '.xls')):
            return pd.read_excel(path)
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


# ─────────────────────────── PREPARATION PIPELINE ────────────────────

def prepare_data(raw_df: pd.DataFrame):
    """
    Run the full data preparation pipeline:
      1. Deduplicate (keep most recent per respondent × jurisdiction)
      2. Calculate DCC / OC scores for each row

    Returns:
        clean_df  : deduplicated survey DataFrame
        scores_df : scored DataFrame ready for the dashboard tables and chart
    """
    if raw_df.empty:
        empty_scores = pd.DataFrame(columns=[
            'Jurisdiction', 'Short', 'Respondent',
            'Data Connection Complexity', 'Operational Complexity',
            'DCC (normalized)', 'OC (normalized)',
            'Readiness Band', '_color_idx', '_dcc_norm', '_oc_norm',
        ])
        return raw_df, empty_scores

    clean_df  = deduplicate(raw_df)
    scores_df = calculate_scores(clean_df)
    return clean_df, scores_df