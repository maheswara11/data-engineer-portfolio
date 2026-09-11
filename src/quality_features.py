from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from src.quality_engine import (
    SEVERITY_ORDER,
    SEVERITY_WEIGHTS,
    run_quality_checks,
)


CUSTOM_RULE_TYPES = (
    "Required",
    "Unique",
    "Minimum Value",
    "Maximum Value",
    "Allowed Values",
    "Regex Pattern",
)


def infer_column_roles(df: pd.DataFrame) -> dict:
    """
    Infer useful data-quality roles from names, values, and cardinality.

    A likely primary key is allowed to contain some duplicates/missing values.
    That is intentional: duplicate/missing key values are exactly the quality
    problems the application should detect.
    """
    roles = {
        "primary_key": None,
        "primary_key_confidence": None,
        "email_columns": [],
        "phone_columns": [],
        "date_columns": [],
        "numeric_columns": [],
        "amount_columns": [],
        "quantity_columns": [],
    }

    if not isinstance(df, pd.DataFrame) or df.empty:
        return roles

    pk_candidates = []

    for column in df.columns:
        name = str(column)
        lower = name.lower().strip()
        series = df[column]

        if pd.api.types.is_numeric_dtype(series):
            roles["numeric_columns"].append(name)

        if "email" in lower:
            roles["email_columns"].append(name)

        if any(
            token in lower
            for token in ("phone", "mobile", "telephone")
        ):
            roles["phone_columns"].append(name)

        if (
            "date" in lower
            or "timestamp" in lower
            or lower.endswith("_at")
        ):
            roles["date_columns"].append(name)

        if any(
            token in lower
            for token in (
                "amount",
                "price",
                "cost",
                "revenue",
                "salary",
                "balance",
            )
        ):
            roles["amount_columns"].append(name)

        if any(
            token in lower
            for token in (
                "quantity",
                "qty",
                "count",
                "units",
            )
        ):
            roles["quantity_columns"].append(name)

        nonblank_mask = (
            series.notna()
            & series.astype(str)
            .str.strip()
            .ne("")
        )

        nonblank_ratio = (
            float(nonblank_mask.mean())
            if len(series)
            else 0.0
        )

        nonblank_values = series[
            nonblank_mask
        ]

        unique_ratio = (
            float(
                nonblank_values.nunique(
                    dropna=True
                )
                / len(nonblank_values)
            )
            if len(nonblank_values)
            else 0.0
        )

        name_score = 0

        if lower == "id":
            name_score = 5
        elif lower.endswith("_id"):
            name_score = 5
        elif lower.endswith("id"):
            name_score = 4
        elif "key" in lower:
            name_score = 4
        elif any(
            token in lower
            for token in (
                "customer",
                "account",
                "order",
                "transaction",
                "record",
            )
        ):
            name_score = 2

        if (
            name_score > 0
            and nonblank_ratio >= 0.70
            and unique_ratio >= 0.70
        ):
            pk_candidates.append(
                (
                    name_score,
                    unique_ratio,
                    nonblank_ratio,
                    name,
                )
            )

    if pk_candidates:
        pk_candidates.sort(
            reverse=True
        )

        (
            _,
            unique_ratio,
            nonblank_ratio,
            best_column,
        ) = pk_candidates[0]

        roles["primary_key"] = (
            best_column
        )

        roles[
            "primary_key_confidence"
        ] = round(
            (
                unique_ratio
                * 0.75
                + nonblank_ratio
                * 0.25
            )
            * 100,
            1,
        )

    return roles


def generate_schema_contract(
    df: pd.DataFrame,
    primary_key: str | None = None,
) -> dict:
    """Create a reusable schema contract from a DataFrame."""
    columns = []

    for column in df.columns:
        series = df[column]

        columns.append(
            {
                "name": str(column),
                "dtype": str(series.dtype),
                "nullable": bool(series.isna().any()),
            }
        )

    return {
        "version": 1,
        "created_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "primary_key": (
            primary_key
            if primary_key
            and primary_key != "None"
            else None
        ),
        "columns": columns,
    }


def _dtype_family(dtype_text: str) -> str:
    value = str(dtype_text).lower()

    if any(
        token in value
        for token in (
            "int",
            "float",
            "double",
            "decimal",
        )
    ):
        return "numeric"

    if "datetime" in value:
        return "datetime"

    if "bool" in value:
        return "boolean"

    if any(
        token in value
        for token in (
            "object",
            "string",
            "str",
        )
    ):
        return "string"

    return value


def _issue(
    *,
    rule: str,
    column: str,
    severity: str,
    failed_rows: int,
    total_rows: int,
    affected_records: list[int],
    examples: list[str],
    suggestion: str,
    fix_options: list[str],
) -> dict:
    failure_rate = (
        round(
            (
                failed_rows
                / total_rows
            )
            * 100,
            2,
        )
        if total_rows
        else 0
    )

    return {
        "rule": rule,
        "column": column,
        "severity": severity,
        "failed_rows": int(
            failed_rows
        ),
        "failure_rate": (
            f"{failure_rate}%"
        ),
        "affected_records": (
            affected_records
        ),
        "examples": examples[:5],
        "suggestion": suggestion,
        "fix_options": fix_options,
    }


def evaluate_schema_contract(
    df: pd.DataFrame,
    contract: dict | None,
) -> tuple[list[dict], list[dict]]:
    """
    Compare a DataFrame with a saved schema contract.

    Contract failures are dataset-level. Missing/type-changed required
    structure is considered to affect every row because downstream
    consumers cannot safely rely on the dataset shape.
    """
    if not contract:
        return [], []

    expected = {
        str(item.get("name")): item
        for item
        in contract.get(
            "columns",
            [],
        )
        if item.get("name")
    }

    actual = {
        str(column): str(
            df[column].dtype
        )
        for column
        in df.columns
    }

    total_rows = len(df)
    all_records = list(
        range(
            1,
            total_rows + 1,
        )
    )

    issues = []
    rows = []

    for column, config in expected.items():

        if column not in actual:

            issue = _issue(
                rule="SCHEMA_MISSING_COLUMN",
                column=column,
                severity="CRITICAL",
                failed_rows=total_rows,
                total_rows=total_rows,
                affected_records=all_records,
                examples=[],
                suggestion=(
                    f"Expected column '{column}' is missing. "
                    "Restore it from the source or update the approved contract."
                ),
                fix_options=[
                    "Correct from source system",
                    "Keep for manual review",
                ],
            )

            issues.append(issue)

            continue

        expected_family = _dtype_family(
            config.get(
                "dtype",
                "",
            )
        )

        actual_family = _dtype_family(
            actual[column]
        )

        if (
            expected_family
            != actual_family
        ):

            issue = _issue(
                rule="SCHEMA_TYPE_MISMATCH",
                column=column,
                severity="HIGH",
                failed_rows=total_rows,
                total_rows=total_rows,
                affected_records=all_records,
                examples=[
                    f"expected={config.get('dtype')}",
                    f"actual={actual[column]}",
                ],
                suggestion=(
                    f"Column '{column}' changed type from "
                    f"{config.get('dtype')} to {actual[column]}. "
                    "Verify the upstream schema before downstream processing."
                ),
                fix_options=[
                    "Correct from source system",
                    "Keep for manual review",
                ],
            )

            issues.append(issue)

    for column in actual:

        if column not in expected:

            issue = _issue(
                rule="SCHEMA_EXTRA_COLUMN",
                column=column,
                severity="LOW",
                failed_rows=total_rows,
                total_rows=total_rows,
                affected_records=all_records,
                examples=[],
                suggestion=(
                    f"Column '{column}' is not present in the saved contract. "
                    "Review whether the contract should be updated."
                ),
                fix_options=[
                    "Keep for manual review",
                ],
            )

            issues.append(issue)

    for issue in issues:
        for record in issue.get(
            "affected_records",
            [],
        )[:250]:
            rows.append(
                {
                    "record": record,
                    "column": issue[
                        "column"
                    ],
                    "rule": issue[
                        "rule"
                    ],
                    "severity": issue[
                        "severity"
                    ],
                    "current_value": (
                        "Schema-level issue"
                    ),
                    "suggestion": issue[
                        "suggestion"
                    ],
                }
            )

    return issues, rows


def evaluate_custom_rules(
    df: pd.DataFrame,
    custom_rules: list[dict] | None,
) -> tuple[list[dict], list[dict]]:
    """Evaluate user-defined deterministic rules."""
    if not custom_rules:
        return [], []

    issues = []
    rows = []
    total_rows = len(df)

    for index, config in enumerate(
        custom_rules,
        start=1,
    ):
        column = str(
            config.get(
                "column",
                "",
            )
        )

        if column not in df.columns:
            continue

        rule_type = str(
            config.get(
                "type",
                "",
            )
        )

        name = str(
            config.get(
                "name",
                "",
            )
            or f"Custom Rule {index}"
        )

        severity = str(
            config.get(
                "severity",
                "MEDIUM",
            )
        ).upper()

        if severity not in SEVERITY_ORDER:
            severity = "MEDIUM"

        series = df[column]

        mask = pd.Series(
            False,
            index=df.index,
        )

        suggestion = (
            f"Review records failing custom rule '{name}'."
        )

        options = [
            "Keep for manual review",
            "Set affected values to NULL after approval",
        ]

        if rule_type == "Required":
            blank = (
                series.notna()
                & series.astype(str)
                .str.strip()
                .eq("")
            )

            mask = (
                series.isna()
                | blank
            )

            suggestion = (
                f"'{column}' is required by custom rule '{name}'. "
                "Provide a verified value or remove the invalid record."
            )

            options = [
                "Retrieve value from trusted source",
                "Keep for manual review",
                "Remove affected rows after approval",
            ]

        elif rule_type == "Unique":

            nonblank = (
                series.notna()
                & series.astype(str)
                .str.strip()
                .ne("")
            )

            mask = (
                nonblank
                & series.duplicated(
                    keep=False
                )
            )

            suggestion = (
                f"'{column}' must be unique under custom rule '{name}'."
            )

            options = [
                "Keep first occurrence",
                "Keep last occurrence",
                "Keep for manual review",
                "Merge duplicate records",
            ]

        elif rule_type in (
            "Minimum Value",
            "Maximum Value",
        ):

            numeric = pd.to_numeric(
                series,
                errors="coerce",
            )

            nonblank = (
                series.notna()
                & series.astype(str)
                .str.strip()
                .ne("")
            )

            threshold = float(
                config.get(
                    "value",
                    0,
                )
            )

            if rule_type == "Minimum Value":
                mask = (
                    nonblank
                    & (
                        numeric.isna()
                        | (
                            numeric
                            < threshold
                        )
                    )
                )

                suggestion = (
                    f"'{column}' must be at least {threshold}."
                )

            else:
                mask = (
                    nonblank
                    & (
                        numeric.isna()
                        | (
                            numeric
                            > threshold
                        )
                    )
                )

                suggestion = (
                    f"'{column}' must be no greater than {threshold}."
                )

        elif rule_type == "Allowed Values":

            raw_values = config.get(
                "value",
                [],
            )

            if isinstance(
                raw_values,
                str,
            ):
                allowed = [
                    item.strip()
                    for item
                    in raw_values.split(",")
                    if item.strip()
                ]
            else:
                allowed = [
                    str(item)
                    for item
                    in raw_values
                ]

            values = series.astype(str)

            nonblank = (
                series.notna()
                & values.str.strip()
                .ne("")
            )

            mask = (
                nonblank
                & ~values.isin(
                    allowed
                )
            )

            suggestion = (
                f"'{column}' must contain one of: "
                + ", ".join(
                    allowed[:12]
                )
            )

        elif rule_type == "Regex Pattern":

            pattern = str(
                config.get(
                    "value",
                    "",
                )
            )

            try:
                compiled = re.compile(
                    pattern
                )
            except re.error:
                continue

            values = (
                series.astype(str)
                .str.strip()
            )

            nonblank = (
                series.notna()
                & values.ne("")
            )

            mask = (
                nonblank
                & ~values.str.match(
                    compiled,
                    na=False,
                )
            )

            suggestion = (
                f"'{column}' must match regex pattern: {pattern}"
            )

        else:
            continue

        failed = int(
            mask.fillna(
                False
            ).sum()
        )

        if failed == 0:
            continue

        records = [
            int(position) + 1
            for position
            in df.index[
                mask.fillna(
                    False
                )
            ]
        ]

        examples = (
            df.loc[
                mask.fillna(
                    False
                ),
                column,
            ]
            .astype(str)
            .head(5)
            .tolist()
        )

        issue = _issue(
            rule=(
                "CUSTOM_"
                + re.sub(
                    r"[^A-Z0-9]+",
                    "_",
                    rule_type.upper(),
                ).strip("_")
            ),
            column=column,
            severity=severity,
            failed_rows=failed,
            total_rows=total_rows,
            affected_records=records,
            examples=examples,
            suggestion=suggestion,
            fix_options=options,
        )

        issue["custom_rule_name"] = name

        issues.append(
            issue
        )

        for position in df.index[
            mask.fillna(
                False
            )
        ]:
            rows.append(
                {
                    "record": (
                        int(position)
                        + 1
                    ),
                    "column": column,
                    "rule": issue[
                        "rule"
                    ],
                    "severity": severity,
                    "current_value": (
                        None
                        if pd.isna(
                            df.at[
                                position,
                                column,
                            ]
                        )
                        else df.at[
                            position,
                            column,
                        ]
                    ),
                    "suggestion": suggestion,
                }
            )

    return issues, rows


def _parse_rate(
    value: Any,
) -> float:
    try:
        return float(
            str(value)
            .replace(
                "%",
                "",
            )
            .strip()
        ) / 100
    except (
        TypeError,
        ValueError,
    ):
        return 0.0


def augment_report(
    report: dict,
    df: pd.DataFrame,
    extra_issues: list[dict],
    extra_row_issues: list[dict],
) -> dict:
    """Merge custom/schema issues into the normal deterministic report."""
    result = dict(
        report
    )

    issues = list(
        result.get(
            "issues",
            [],
        )
    ) + list(
        extra_issues
    )

    row_issues = list(
        result.get(
            "row_issues",
            [],
        )
    ) + list(
        extra_row_issues
    )

    issues.sort(
        key=lambda item: (
            SEVERITY_ORDER.get(
                str(
                    item.get(
                        "severity",
                        "LOW",
                    )
                ).upper(),
                0,
            ),
            int(
                item.get(
                    "failed_rows",
                    0,
                )
                or 0
            ),
        ),
        reverse=True,
    )

    row_issues.sort(
        key=lambda item: (
            -SEVERITY_ORDER.get(
                str(
                    item.get(
                        "severity",
                        "LOW",
                    )
                ).upper(),
                0,
            ),
            int(
                item.get(
                    "record",
                    0,
                )
                or 0
            ),
        )
    )

    bad_records = {
        int(record)
        for issue in issues
        for record
        in issue.get(
            "affected_records",
            [],
        )
        if isinstance(
            record,
            int,
        )
    }

    total_rows = len(
        df
    )

    severity_counts = {
        "CRITICAL": 0,
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0,
    }

    for issue in issues:
        severity = str(
            issue.get(
                "severity",
                "LOW",
            )
        ).upper()

        if severity in severity_counts:
            severity_counts[
                severity
            ] += 1

    penalty = sum(
        SEVERITY_WEIGHTS.get(
            str(
                issue.get(
                    "severity",
                    "LOW",
                )
            ).upper(),
            5,
        )
        * _parse_rate(
            issue.get(
                "failure_rate",
                "0%",
            )
        )
        for issue in issues
    )

    result.update(
        {
            "quality_score": round(
                max(
                    0.0,
                    min(
                        100.0,
                        100.0
                        - penalty,
                    ),
                ),
                2,
            ),
            "weighted_penalty": round(
                penalty,
                4,
            ),
            "total_issues": len(
                issues
            ),
            "total_failed_checks": sum(
                int(
                    issue.get(
                        "failed_rows",
                        0,
                    )
                    or 0
                )
                for issue
                in issues
            ),
            "unique_bad_rows": len(
                bad_records
            ),
            "clean_rows": max(
                0,
                total_rows
                - len(
                    bad_records
                ),
            ),
            "bad_row_rate": round(
                (
                    len(
                        bad_records
                    )
                    / total_rows
                    * 100
                )
                if total_rows
                else 0,
                2,
            ),
            "severity_counts": (
                severity_counts
            ),
            "issues": issues,
            "row_issues": row_issues,
        }
    )

    return result


def run_extended_quality_checks(
    df: pd.DataFrame,
    industry: str = "General",
    primary_key: str | None = None,
    custom_rules: list[dict] | None = None,
    schema_contract: dict | None = None,
) -> dict:
    """Run built-in + custom + contract checks in one report."""
    base = run_quality_checks(
        df,
        industry,
        primary_key,
    )

    custom_issues, custom_rows = (
        evaluate_custom_rules(
            df,
            custom_rules,
        )
    )

    schema_issues, schema_rows = (
        evaluate_schema_contract(
            df,
            schema_contract,
        )
    )

    return augment_report(
        base,
        df,
        custom_issues
        + schema_issues,
        custom_rows
        + schema_rows,
    )


def get_safe_fix_plan(
    issues: list[dict],
) -> list[dict]:
    """
    Build a deterministic bulk-cleaning plan.

    These actions never invent replacement values. Some NULL conversions
    may intentionally reveal a MISSING_VALUES issue on the next validation.
    """
    plan = []

    for issue in issues:
        rule = str(
            issue.get(
                "rule",
                "",
            )
        ).upper()

        options = issue.get(
            "fix_options",
            [],
        )

        action = None

        if (
            rule
            == "DUPLICATE_ROWS"
            and "Merge duplicate records"
            in options
        ):
            action = (
                "Merge duplicate records"
            )

        elif (
            rule
            == "EMPTY_STRING"
            and "Convert blank to NULL"
            in options
        ):
            action = (
                "Convert blank to NULL"
            )

        elif (
            rule.startswith(
                (
                    "INVALID_",
                    "FUTURE_DATE",
                    "CUSTOM_MINIMUM",
                    "CUSTOM_MAXIMUM",
                    "CUSTOM_ALLOWED",
                    "CUSTOM_REGEX",
                )
            )
            and (
                "Set affected values to NULL after approval"
                in options
            )
        ):
            action = (
                "Set affected values to NULL after approval"
            )

        if action:
            plan.append(
                {
                    "rule": issue.get(
                        "rule"
                    ),
                    "column": issue.get(
                        "column"
                    ),
                    "severity": issue.get(
                        "severity"
                    ),
                    "failed_rows": issue.get(
                        "failed_rows",
                        0,
                    ),
                    "action": action,
                }
            )

    return plan


def build_cleaning_recipe(
    *,
    name: str,
    industry: str,
    primary_key: str,
    custom_rules: list[dict],
    schema_contract: dict | None,
    remediation_history: list[dict] | None = None,
) -> dict:
    """
    Create a portable cleaning configuration.

    Only generic automatic actions are saved as reusable action policies.
    Direct row edits and bulk replacement values are intentionally excluded
    because they may not be correct for a future dataset.
    """
    reusable_actions = {
        "Convert blank to NULL",
        "Set affected values to NULL after approval",
        "Remove affected rows after approval",
        "Keep first occurrence",
        "Keep last occurrence",
        "Merge duplicate records",
    }

    action_policies = []
    seen = set()

    for item in remediation_history or []:
        action = str(
            item.get(
                "action",
                "",
            )
        )

        if action not in reusable_actions:
            continue

        policy = (
            str(
                item.get(
                    "rule",
                    "",
                )
            ),
            str(
                item.get(
                    "column",
                    "",
                )
            ),
            action,
        )

        if policy in seen:
            continue

        seen.add(
            policy
        )

        action_policies.append(
            {
                "rule": policy[0],
                "column": policy[1],
                "action": policy[2],
            }
        )

    return {
        "version": 1,
        "name": (
            name.strip()
            or "Cleaning Recipe"
        ),
        "created_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "industry": industry,
        "primary_key": (
            None
            if primary_key
            == "None"
            else primary_key
        ),
        "custom_rules": list(
            custom_rules
        ),
        "schema_contract": (
            schema_contract
        ),
        "safe_fix_policy": (
            "deterministic_no_invented_values"
        ),
        "action_policies": action_policies,
    }


def recipe_to_json(
    recipe: dict,
) -> str:
    return json.dumps(
        recipe,
        indent=2,
        default=str,
    )


def parse_recipe(
    raw: str | bytes,
) -> dict:
    if isinstance(
        raw,
        bytes,
    ):
        raw = raw.decode(
            "utf-8"
        )

    data = json.loads(
        raw
    )

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            "Recipe must be a JSON object."
        )

    return data


def contract_to_json(
    contract: dict,
) -> str:
    return json.dumps(
        contract,
        indent=2,
        default=str,
    )


def build_audit_markdown(
    *,
    dataset_name: str,
    industry: str,
    primary_key: str,
    baseline_report: dict,
    final_report: dict,
    remediation_history: list[dict],
    custom_rules: list[dict],
    schema_contract: dict | None,
) -> str:
    """Build a human-readable audit report."""
    before_score = baseline_report.get(
        "quality_score",
        0,
    )

    final_score = final_report.get(
        "quality_score",
        0,
    )

    before_rows = baseline_report.get(
        "rows",
        0,
    )

    final_rows = final_report.get(
        "rows",
        0,
    )

    lines = [
        "# Data Quality Audit Report",
        "",
        f"- Dataset: **{dataset_name}**",
        f"- Generated (UTC): **{datetime.now(timezone.utc).isoformat()}**",
        f"- Industry rule pack: **{industry}**",
        f"- Primary key: **{primary_key if primary_key != 'None' else 'Not selected'}**",
        "",
        "## Validation Summary",
        "",
        f"- Quality score: **{before_score} → {final_score}**",
        f"- Rows: **{before_rows} → {final_rows}**",
        f"- Rows removed: **{max(0, int(before_rows) - int(final_rows))}**",
        f"- Issue rules: **{baseline_report.get('total_issues', 0)} → {final_report.get('total_issues', 0)}**",
        f"- Failed checks: **{baseline_report.get('total_failed_checks', 0)} → {final_report.get('total_failed_checks', 0)}**",
        f"- Rows with problems: **{baseline_report.get('unique_bad_rows', 0)} → {final_report.get('unique_bad_rows', 0)}**",
        "",
        "## Configuration",
        "",
        f"- Custom rules: **{len(custom_rules)}**",
        f"- Schema contract active: **{'Yes' if schema_contract else 'No'}**",
        "",
        "## Approved Actions",
        "",
    ]

    if remediation_history:
        lines.extend(
            [
                "| # | Rule | Column | Action | Status | Failed Before | Failed After |",
                "|---:|---|---|---|---|---:|---:|",
            ]
        )

        for index, item in enumerate(
            remediation_history,
            start=1,
        ):
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(index),
                        str(
                            item.get(
                                "rule",
                                "",
                            )
                        ).replace(
                            "|",
                            "/",
                        ),
                        str(
                            item.get(
                                "column",
                                "",
                            )
                        ).replace(
                            "|",
                            "/",
                        ),
                        str(
                            item.get(
                                "action",
                                "",
                            )
                        ).replace(
                            "|",
                            "/",
                        ),
                        str(
                            item.get(
                                "status",
                                "",
                            )
                        ),
                        str(
                            item.get(
                                "failed_before",
                                "",
                            )
                        ),
                        str(
                            item.get(
                                "failed_after",
                                "",
                            )
                        ),
                    ]
                )
                + " |"
            )
    else:
        lines.append(
            "No remediation actions were approved."
        )

    lines.extend(
        [
            "",
            "## Remaining Issues",
            "",
        ]
    )

    remaining = final_report.get(
        "issues",
        [],
    )

    if not remaining:
        lines.append(
            "✅ No detected quality issues remain."
        )
    else:
        lines.extend(
            [
                "| Severity | Rule | Column | Failed Rows | Failure Rate |",
                "|---|---|---|---:|---:|",
            ]
        )

        for issue in remaining:
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(
                            issue.get(
                                "severity",
                                "",
                            )
                        ),
                        str(
                            issue.get(
                                "rule",
                                "",
                            )
                        ),
                        str(
                            issue.get(
                                "column",
                                "",
                            )
                        ),
                        str(
                            issue.get(
                                "failed_rows",
                                0,
                            )
                        ),
                        str(
                            issue.get(
                                "failure_rate",
                                "",
                            )
                        ),
                    ]
                )
                + " |"
            )

    lines.extend(
        [
            "",
            "## Final Status",
            "",
        ]
    )

    fully_clean = (
        int(
            final_report.get(
                "total_issues",
                0,
            )
            or 0
        )
        == 0
        and int(
            final_report.get(
                "unique_bad_rows",
                0,
            )
            or 0
        )
        == 0
    )

    lines.append(
        "✅ CLEAN — final deterministic validation passed."
        if fully_clean
        else "⚠️ REVIEW REQUIRED — quality issues remain."
    )

    return "\n".join(
        lines
    )
