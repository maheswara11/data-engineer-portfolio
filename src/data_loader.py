from __future__ import annotations

import io
import json

import pandas as pd


SUPPORTED_EXTENSIONS = {"csv", "json"}
JSON_RECORD_KEYS = ("records", "data", "items", "rows")


def _load_json_bytes(raw_bytes: bytes, filename: str) -> pd.DataFrame:
    """Load standard JSON, wrapped record arrays, or JSON Lines."""
    try:
        payload = json.loads(raw_bytes.decode("utf-8-sig"))

        if isinstance(payload, list):
            return pd.json_normalize(payload)

        if isinstance(payload, dict):
            for key in JSON_RECORD_KEYS:
                records = payload.get(key)
                if isinstance(records, list):
                    return pd.json_normalize(records)

            # A single JSON object is treated as one record.
            if all(not isinstance(value, list) for value in payload.values()):
                return pd.json_normalize([payload])

            # Dict-of-lists / column-oriented JSON.
            return pd.DataFrame(payload)

    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError):
        pass

    # Fall back to JSON Lines / NDJSON.
    try:
        return pd.read_json(io.BytesIO(raw_bytes), lines=True)
    except Exception as exc:
        raise ValueError(f"Could not read '{filename}' as JSON or JSON Lines: {exc}") from exc


def load_data(uploaded_file) -> pd.DataFrame:
    """Load a Streamlit UploadedFile containing CSV or JSON data."""
    if uploaded_file is None:
        raise ValueError("No file was provided.")

    filename = str(getattr(uploaded_file, "name", "")).strip()
    if not filename:
        raise ValueError("The uploaded file has no filename.")

    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError("Only CSV and JSON files are supported.")

    raw_bytes = uploaded_file.getvalue()
    if not raw_bytes:
        raise ValueError("The uploaded file is empty.")

    try:
        if extension == "csv":
            df = pd.read_csv(io.BytesIO(raw_bytes))
        else:
            df = _load_json_bytes(raw_bytes, filename)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Could not read '{filename}': {exc}") from exc

    if df.shape[1] == 0:
        raise ValueError("The dataset does not contain any columns.")

    # Keep record numbering predictable throughout quality checks/remediation.
    return df.reset_index(drop=True)
