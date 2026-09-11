from __future__ import annotations

import re
from typing import Iterable

import pandas as pd

from src.industry_rules import run_industry_rules


SEVERITY_ORDER = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
SEVERITY_WEIGHTS = {"CRITICAL": 35, "HIGH": 20, "MEDIUM": 10, "LOW": 5}


def _record_numbers(mask: pd.Series) -> list[int]:
    return [position + 1 for position, failed in enumerate(mask.tolist()) if bool(failed)]


def _safe_value(value):
    if pd.isna(value):
        return None
    return value


def _parse_failure_rate(value) -> float:
    try:
        return float(str(value).replace("%", "").strip()) / 100
    except (TypeError, ValueError):
        return 0.0


def run_quality_checks(
    df: pd.DataFrame,
    industry: str = "General",
    primary_key: str | None = None,
) -> dict:
    """Run deterministic, non-destructive data-quality checks."""

    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")

    data = df.reset_index(drop=True)
    total_rows = len(data)
    issues: list[dict] = []
    row_issues: list[dict] = []
    unique_bad_records: set[int] = set()

    def add_issue(
        *,
        rule: str,
        column: str,
        severity: str,
        mask: pd.Series,
        suggestion: str,
        fix_options: list[str],
        examples: Iterable | None = None,
    ) -> None:
        normalized_mask = pd.Series(mask, index=data.index).fillna(False).astype(bool)
        failed_rows = int(normalized_mask.sum())
        if failed_rows == 0:
            return

        severity_normalized = str(severity).upper()
        if severity_normalized not in SEVERITY_ORDER:
            severity_normalized = "LOW"

        failure_rate = round((failed_rows / total_rows) * 100, 2) if total_rows else 0
        affected_records = _record_numbers(normalized_mask)
        unique_bad_records.update(affected_records)

        if examples is None:
            if column in data.columns:
                example_values = data.loc[normalized_mask, column].astype(str).head(5).tolist()
            else:
                example_values = []
        else:
            example_values = [str(value) for value in list(examples)[:5]]

        issues.append(
            {
                "rule": rule,
                "column": column,
                "severity": severity_normalized,
                "failed_rows": failed_rows,
                "failure_rate": f"{failure_rate}%",
                "affected_records": affected_records,
                "examples": example_values,
                "suggestion": suggestion,
                "fix_options": fix_options,
            }
        )

        for position in data.index[normalized_mask]:
            current_value = data.at[position, column] if column in data.columns else "N/A"
            row_issues.append(
                {
                    "record": int(position) + 1,
                    "column": column,
                    "rule": rule,
                    "severity": severity_normalized,
                    "current_value": _safe_value(current_value),
                    "suggestion": suggestion,
                }
            )

    # 1) Missing values.
    for column in data.columns:
        add_issue(
            rule="MISSING_VALUES",
            column=column,
            severity="MEDIUM",
            mask=data[column].isna(),
            suggestion="Review missing values before changing them. Use a trusted source or a business-approved rule.",
            fix_options=[
                "Keep as NULL",
                "Retrieve value from trusted source",
                "Remove affected rows after approval",
            ],
        )

    # 2) Empty strings.
    for column in data.select_dtypes(include=["object", "string"]).columns:
        mask = data[column].notna() & data[column].astype(str).str.strip().eq("")
        add_issue(
            rule="EMPTY_STRING",
            column=column,
            severity="MEDIUM",
            mask=mask,
            suggestion="Review blank strings and decide whether they should remain blank or become NULL.",
            fix_options=[
                "Convert blank to NULL",
                "Retrieve value from trusted source",
                "Keep blank if valid",
            ],
        )

    # 3) Full-row duplicates.
    duplicate_mask = data.duplicated(keep=False)
    add_issue(
        rule="DUPLICATE_ROWS",
        column="ALL",
        severity="HIGH",
        mask=duplicate_mask,
        suggestion="Review duplicate records before removal. Confirm whether they are true duplicates or valid repeated business events.",
        fix_options=[
            "Keep first occurrence",
            "Keep last occurrence",
            "Keep all if duplicates are valid",
            "Merge duplicate records",
        ],
        examples=[],
    )

    # 4) User-selected primary key.
    valid_primary_key = (
        primary_key
        and primary_key != "None"
        and primary_key in data.columns
    )
    if valid_primary_key:
        pk_series = data[primary_key]
        blank_pk = pk_series.notna() & pk_series.astype(str).str.strip().eq("")
        missing_pk = pk_series.isna() | blank_pk
        add_issue(
            rule="MISSING_PRIMARY_KEY",
            column=primary_key,
            severity="CRITICAL",
            mask=missing_pk,
            suggestion="Primary-key values must identify records reliably. Investigate missing or blank keys before downstream processing.",
            fix_options=[
                "Retrieve correct ID from source",
                "Keep for manual review",
                "Remove affected rows after approval",
            ],
        )

        duplicate_pk = pk_series.notna() & ~blank_pk & pk_series.duplicated(keep=False)
        add_issue(
            rule="DUPLICATE_PRIMARY_KEY",
            column=primary_key,
            severity="CRITICAL",
            mask=duplicate_pk,
            suggestion="The selected primary key should uniquely identify each record. Investigate duplicate keys before downstream processing.",
            fix_options=[
                "Keep first occurrence",
                "Keep last occurrence",
                "Keep for manual review",
                "Merge duplicate records",
            ],
        )

    # 5) Date validation.
    date_columns = [
        column
        for column in data.columns
        if (
            "date" in column.lower()
            or column.lower().endswith("_at")
            or "timestamp" in column.lower()
        )
    ]
    parsed_dates: dict[str, pd.Series] = {}
    for column in date_columns:
        parsed = pd.to_datetime(data[column], errors="coerce", utc=True)
        parsed_dates[column] = parsed
        nonblank = data[column].notna() & data[column].astype(str).str.strip().ne("")
        mask = nonblank & parsed.isna()
        add_issue(
            rule="INVALID_DATE",
            column=column,
            severity="HIGH",
            mask=mask,
            suggestion="The date cannot be parsed reliably. Confirm the correct value from the source system.",
            fix_options=[
                "Correct from source system",
                "Keep for manual review",
                "Set affected values to NULL after approval",
            ],
        )

    # 6) Future dates only for event fields that normally describe completed events.
    future_sensitive_keywords = {
        "order_date",
        "transaction_date",
        "purchase_date",
        "payment_date",
        "created_at",
        "updated_at",
        "event_date",
    }
    now_utc = pd.Timestamp.now(tz="UTC")
    for column, parsed in parsed_dates.items():
        if not any(keyword in column.lower() for keyword in future_sensitive_keywords):
            continue
        mask = parsed.notna() & (parsed > now_utc)
        add_issue(
            rule="FUTURE_DATE",
            column=column,
            severity="HIGH",
            mask=mask,
            suggestion="This completed-event date occurs in the future. Verify whether the value is valid for the business process.",
            fix_options=[
                "Correct from source system",
                "Keep for manual review",
                "Set affected values to NULL after approval",
            ],
        )

    # 7) Email validation.
    email_pattern = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
    for column in [c for c in data.columns if "email" in c.lower()]:
        values = data[column].astype(str).str.strip()
        nonblank = data[column].notna() & values.ne("")
        mask = nonblank & ~values.str.match(email_pattern, na=False)
        add_issue(
            rule="INVALID_EMAIL",
            column=column,
            severity="MEDIUM",
            mask=mask,
            suggestion="The email address does not match a standard format. Verify it before changing customer information.",
            fix_options=[
                "Correct from trusted source",
                "Keep for manual review",
                "Set affected values to NULL after approval",
            ],
        )

    # 8) Phone validation: practical international range, 7-15 digits.
    phone_columns = [
        c for c in data.columns
        if any(token in c.lower() for token in ("phone", "mobile", "telephone"))
    ]
    for column in phone_columns:
        raw_phone = data[column].astype(str).str.strip()
        digits = raw_phone.str.replace(r"\D", "", regex=True)
        nonblank = data[column].notna() & raw_phone.ne("")
        mask = nonblank & ((digits.str.len() < 7) | (digits.str.len() > 15))
        add_issue(
            rule="INVALID_PHONE",
            column=column,
            severity="MEDIUM",
            mask=mask,
            suggestion="The phone number appears incomplete or incorrectly formatted. Verify it against a trusted source.",
            fix_options=[
                "Correct from trusted source",
                "Keep for manual review",
                "Set affected values to NULL after approval",
            ],
        )

    # 9) Industry-specific rules.
    for industry_issue in run_industry_rules(data, industry):
        issues.append(industry_issue)
        affected_records = industry_issue.get("affected_records", [])
        unique_bad_records.update(affected_records)
        column = industry_issue.get("column", "N/A")
        suggestion = industry_issue.get("suggestion", "Review this issue.")
        severity = industry_issue.get("severity", "LOW")
        rule = industry_issue.get("rule", "INDUSTRY_RULE")

        for record_number in affected_records:
            position = int(record_number) - 1
            value = data.at[position, column] if column in data.columns and position in data.index else "N/A"
            row_issues.append(
                {
                    "record": int(record_number),
                    "column": column,
                    "rule": rule,
                    "severity": severity,
                    "current_value": _safe_value(value),
                    "suggestion": suggestion,
                }
            )

    # Sort the report so the most important issues appear first.
    issues.sort(
        key=lambda item: (
            SEVERITY_ORDER.get(item.get("severity", "LOW"), 0),
            int(item.get("failed_rows", 0) or 0),
        ),
        reverse=True,
    )
    row_issues.sort(
        key=lambda item: (
            -SEVERITY_ORDER.get(item.get("severity", "LOW"), 0),
            int(item.get("record", 0)),
        )
    )

    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for issue in issues:
        severity = issue.get("severity", "LOW")
        if severity in severity_counts:
            severity_counts[severity] += 1

    total_penalty = sum(
        SEVERITY_WEIGHTS.get(issue.get("severity", "LOW"), 5)
        * _parse_failure_rate(issue.get("failure_rate", "0%"))
        for issue in issues
    )
    quality_score = round(max(0.0, min(100.0, 100.0 - total_penalty)), 2)

    total_failed_checks = sum(int(issue.get("failed_rows", 0)) for issue in issues)
    unique_bad_rows = len(unique_bad_records)
    clean_rows = max(0, total_rows - unique_bad_rows)
    bad_row_rate = round((unique_bad_rows / total_rows) * 100, 2) if total_rows else 0

    return {
        "rows": total_rows,
        "columns": len(data.columns),
        "industry": industry,
        "primary_key": primary_key if valid_primary_key else None,
        "quality_score": quality_score,
        "score_method": "severity-weighted failure-rate heuristic",
        "weighted_penalty": round(total_penalty, 4),
        "total_issues": len(issues),
        "total_failed_checks": total_failed_checks,
        "unique_bad_rows": unique_bad_rows,
        "clean_rows": clean_rows,
        "bad_row_rate": bad_row_rate,
        "severity_counts": severity_counts,
        "column_names": [str(column) for column in data.columns],
        "schema": [
            {
                "column": str(column),
                "dtype": str(data[column].dtype),
                "null_count": int(data[column].isna().sum()),
                "unique_values": int(data[column].nunique(dropna=True)),
            }
            for column in data.columns
        ],
        "issues": issues,
        "row_issues": row_issues,
    }
