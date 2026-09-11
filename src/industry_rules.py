from __future__ import annotations

import pandas as pd


def _record_numbers(mask: pd.Series) -> list[int]:
    return [position + 1 for position, failed in enumerate(mask.tolist()) if bool(failed)]


def _make_issue(
    df: pd.DataFrame,
    *,
    rule: str,
    column: str,
    severity: str,
    mask: pd.Series,
    suggestion: str,
    fix_options: list[str],
) -> dict | None:
    failed_rows = int(mask.sum())
    if failed_rows == 0:
        return None

    total_rows = len(df)
    failure_rate = round((failed_rows / total_rows) * 100, 2) if total_rows else 0
    affected_records = _record_numbers(mask)

    examples = (
        df.loc[mask, column].astype(str).head(5).tolist()
        if column in df.columns
        else []
    )

    return {
        "rule": rule,
        "column": column,
        "severity": severity,
        "failed_rows": failed_rows,
        "failure_rate": f"{failure_rate}%",
        "affected_records": affected_records,
        "examples": examples,
        "suggestion": suggestion,
        "fix_options": fix_options,
    }


def run_industry_rules(df: pd.DataFrame, industry: str = "General") -> list[dict]:
    """Return optional domain-specific quality issues.

    These rules are intentionally conservative. They flag suspicious values but
    avoid silently changing business data.
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")

    data = df.reset_index(drop=True)
    industry = str(industry or "General").strip().title()
    issues: list[dict] = []

    if industry == "General":
        return issues

    if industry == "Retail":
        if "quantity" in data.columns:
            raw = data["quantity"]
            nonblank = raw.notna() & raw.astype(str).str.strip().ne("")
            numeric = pd.to_numeric(raw, errors="coerce")
            # Zero and non-numeric quantities are suspicious. Negative quantities
            # can legitimately represent returns, so they are not flagged generically.
            mask = nonblank & (numeric.isna() | (numeric == 0))
            issue = _make_issue(
                data,
                rule="INVALID_QUANTITY",
                column="quantity",
                severity="HIGH",
                mask=mask,
                suggestion=(
                    "Quantity is zero or non-numeric. Verify the source transaction. "
                    "Negative quantities are not flagged generically because they may represent returns."
                ),
                fix_options=[
                    "Correct from source system",
                    "Keep for manual review",
                    "Set affected values to NULL after approval",
                ],
            )
            if issue:
                issues.append(issue)

        for price_column in ("price", "unit_price"):
            if price_column not in data.columns:
                continue
            raw = data[price_column]
            nonblank = raw.notna() & raw.astype(str).str.strip().ne("")
            numeric = pd.to_numeric(raw, errors="coerce")
            mask = nonblank & (numeric.isna() | (numeric <= 0))
            issue = _make_issue(
                data,
                rule="INVALID_PRICE",
                column=price_column,
                severity="HIGH",
                mask=mask,
                suggestion="Price should normally be greater than zero. Verify the trusted product or transaction source.",
                fix_options=[
                    "Correct from trusted source",
                    "Keep for manual review",
                    "Set affected values to NULL after approval",
                ],
            )
            if issue:
                issues.append(issue)

    elif industry == "Healthcare":
        if "age" in data.columns:
            raw = data["age"]
            nonblank = raw.notna() & raw.astype(str).str.strip().ne("")
            numeric = pd.to_numeric(raw, errors="coerce")
            mask = nonblank & (numeric.isna() | (numeric < 0) | (numeric > 120))
            issue = _make_issue(
                data,
                rule="INVALID_AGE",
                column="age",
                severity="HIGH",
                mask=mask,
                suggestion="Age is outside a realistic range. Verify the date of birth or trusted source record.",
                fix_options=[
                    "Correct from source system",
                    "Keep for manual review",
                    "Set affected values to NULL after approval",
                ],
            )
            if issue:
                issues.append(issue)

        if "claim_amount" in data.columns:
            raw = data["claim_amount"]
            nonblank = raw.notna() & raw.astype(str).str.strip().ne("")
            numeric = pd.to_numeric(raw, errors="coerce")
            mask = nonblank & (numeric.isna() | (numeric <= 0))
            issue = _make_issue(
                data,
                rule="INVALID_CLAIM_AMOUNT",
                column="claim_amount",
                severity="HIGH",
                mask=mask,
                suggestion="Claim amount should normally be greater than zero. Verify it against the billing or claims source.",
                fix_options=[
                    "Correct from billing source",
                    "Keep for manual review",
                    "Set affected values to NULL after approval",
                ],
            )
            if issue:
                issues.append(issue)

        if {"admission_date", "discharge_date"}.issubset(data.columns):
            admission = pd.to_datetime(data["admission_date"], errors="coerce", utc=True)
            discharge = pd.to_datetime(data["discharge_date"], errors="coerce", utc=True)
            mask = admission.notna() & discharge.notna() & (discharge < admission)
            issue = _make_issue(
                data,
                rule="INVALID_DATE_SEQUENCE",
                column="discharge_date",
                severity="CRITICAL",
                mask=mask,
                suggestion="Discharge occurs before admission. Verify both dates with the source system.",
                fix_options=[
                    "Correct admission/discharge dates from source",
                    "Keep for manual review",
                ],
            )
            if issue:
                issues.append(issue)

    elif industry == "Banking":
        amount_column = next((c for c in ("amount", "transaction_amount") if c in data.columns), None)
        if amount_column:
            raw = data[amount_column]
            nonblank = raw.notna() & raw.astype(str).str.strip().ne("")
            numeric = pd.to_numeric(raw, errors="coerce")
            # Negative values can be legitimate credits/reversals, so only zero
            # and non-numeric nonblank values are treated as generic quality failures.
            mask = nonblank & (numeric.isna() | (numeric == 0))
            issue = _make_issue(
                data,
                rule="INVALID_TRANSACTION_AMOUNT",
                column=amount_column,
                severity="HIGH",
                mask=mask,
                suggestion="Transaction amount is zero or non-numeric. Verify whether the record is valid before downstream processing.",
                fix_options=[
                    "Correct from transaction source",
                    "Keep for manual review",
                    "Set affected values to NULL after approval",
                ],
            )
            if issue:
                issues.append(issue)

    return issues
