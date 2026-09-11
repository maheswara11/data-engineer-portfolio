from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.ai_widget import render_ai_copilot
from src.data_loader import load_data
from src.page_contexts import PAGE_CONTEXTS
from src.quality_features import (
    CUSTOM_RULE_TYPES,
    build_audit_markdown,
    build_cleaning_recipe,
    contract_to_json,
    generate_schema_contract,
    get_safe_fix_plan,
    infer_column_roles,
    parse_recipe,
    recipe_to_json,
    run_extended_quality_checks,
)
from src.remediation import apply_fix, is_automatic_fix
from src.ui import apply_theme, render_section_header, render_top_nav


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI Data Quality Copilot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_theme()
render_top_nav("Projects")


# ============================================================
# SETTINGS
# ============================================================

MAX_FILES = 3
MAX_FILE_SIZE_MB = 25
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

SEVERITY_RANK = {
    "CRITICAL": 4,
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1,
}

DATASET_STATE_KEYS = (
    "cleaned_df",
    "remediation_history",
    "undo_stack",
    "quality_report",
    "baseline_report",
    "analysis_signature",
    "last_fix_message",
    "last_change",
    "custom_rules",
    "schema_contract",
    "detected_roles",
    "recipe_action_policies",
)


# ============================================================
# PAGE STYLES
# ============================================================

st.html(
    """
    <style>
    .dq-intro {
        max-width: 1080px;
        color: #64748b;
        font-size: 1.03rem;
        line-height: 1.72;
        margin-top: 0.3rem;
    }

    .safety-card {
        padding: 20px;
        border: 1px solid #dce5f1;
        border-radius: 16px;
        background: #ffffff;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
        margin-bottom: 12px;
    }

    .safety-title {
        color: #14264d;
        font-size: 1rem;
        font-weight: 750;
        margin-bottom: 7px;
    }

    .safety-text {
        color: #64748b;
        font-size: 0.9rem;
        line-height: 1.58;
    }

    /* Persistent results navigation: visually behaves like tabs while
       preserving the selected section across st.rerun(). */
    .st-key-results_view [role="radiogroup"] {
        display: flex;
        gap: 4px;
        border-bottom: 1px solid var(--portfolio-border, #dce5f1);
        padding-bottom: 0;
        margin-bottom: 0.55rem;
        overflow-x: auto;
        flex-wrap: nowrap;
    }

    .st-key-results_view [role="radiogroup"] label {
        padding: 0.58rem 0.75rem 0.62rem 0.75rem;
        border-bottom: 3px solid transparent;
        white-space: nowrap;
        cursor: pointer;
        margin-bottom: -1px;
    }

    .st-key-results_view [role="radiogroup"] label:has(input:checked) {
        border-bottom-color: #1768f2;
        color: #1768f2 !important;
        font-weight: 700;
    }

    .st-key-results_view [role="radiogroup"] [data-testid="stMarkdownContainer"] p {
        font-size: 0.92rem;
    }
    </style>
    """
)


# ============================================================
# HELPERS
# ============================================================

def run_current_quality_checks(
    data: pd.DataFrame,
    industry: str,
    primary_key: str,
) -> dict:
    """Run built-in checks plus active custom rules and schema contract."""
    return run_extended_quality_checks(
        data,
        industry=industry,
        primary_key=primary_key,
        custom_rules=st.session_state.get(
            "custom_rules",
            [],
        ),
        schema_contract=st.session_state.get(
            "schema_contract",
        ),
    )


def _config_fingerprint() -> str:
    payload = {
        "custom_rules": st.session_state.get(
            "custom_rules",
            [],
        ),
        "schema_contract": st.session_state.get(
            "schema_contract",
        ),
    }

    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            default=str,
        ).encode(
            "utf-8"
        )
    ).hexdigest()


def uploaded_file_size(uploaded_file) -> int:
    size = getattr(uploaded_file, "size", None)

    if size is not None:
        return int(size)

    return len(uploaded_file.getbuffer())


def make_dataset_key(uploaded_file) -> str:
    digest = hashlib.sha256(
        uploaded_file.getbuffer()
    ).hexdigest()

    return f"{uploaded_file.name}:{digest}"


def _snapshot_current_dataset_state() -> dict:
    snapshot = {}

    for key in DATASET_STATE_KEYS:
        if key in st.session_state:
            snapshot[key] = st.session_state[key]

    return snapshot


def _clear_current_dataset_state() -> None:
    for key in DATASET_STATE_KEYS:
        st.session_state.pop(key, None)


def reset_dataset_state(
    df: pd.DataFrame,
    dataset_key: str,
) -> None:
    st.session_state["dataset_key"] = dataset_key
    st.session_state["cleaned_df"] = df.copy()
    st.session_state["remediation_history"] = []
    st.session_state["undo_stack"] = []
    st.session_state["custom_rules"] = []
    st.session_state["schema_contract"] = None
    st.session_state["detected_roles"] = {}
    st.session_state["recipe_action_policies"] = []

    for key in (
        "quality_report",
        "baseline_report",
        "analysis_signature",
        "last_fix_message",
    ):
        st.session_state.pop(key, None)


def activate_dataset_state(
    df: pd.DataFrame,
    dataset_key: str,
) -> None:
    """
    Preserve analysis/remediation independently for each uploaded dataset.

    This prevents work on dataset A from disappearing when the user
    temporarily switches to dataset B and then returns to A.
    """
    states = st.session_state.setdefault(
        "dataset_states",
        {},
    )

    current_key = st.session_state.get(
        "dataset_key"
    )

    if current_key == dataset_key:
        return

    if current_key:
        states[current_key] = (
            _snapshot_current_dataset_state()
        )

    _clear_current_dataset_state()

    saved_state = states.get(dataset_key)

    if saved_state:
        for key, value in saved_state.items():
            st.session_state[key] = value

        st.session_state["dataset_key"] = dataset_key
    else:
        reset_dataset_state(
            df,
            dataset_key,
        )


def invalidate_analysis(
    df: pd.DataFrame,
) -> None:
    st.session_state["cleaned_df"] = df.copy()
    st.session_state["remediation_history"] = []
    st.session_state["undo_stack"] = []

    for key in (
        "quality_report",
        "baseline_report",
        "last_fix_message",
    ):
        st.session_state.pop(key, None)


def suggest_primary_key(
    df: pd.DataFrame,
) -> str | None:
    """
    Suggest a likely primary key without automatically enforcing it.

    Preference:
    1. Unique + non-null columns named id / *_id / *key*
    2. Any unique + non-null column
    """
    if df.empty:
        return None

    strong_candidates = []
    fallback_candidates = []

    for column in df.columns:
        series = df[column]

        if series.isna().any():
            continue

        if int(series.nunique(dropna=False)) != len(df):
            continue

        name = str(column).strip().lower()

        if (
            name == "id"
            or name.endswith("_id")
            or "key" in name
            or name.endswith("id")
        ):
            strong_candidates.append(column)
        else:
            fallback_candidates.append(column)

    if strong_candidates:
        return str(strong_candidates[0])

    if fallback_candidates:
        return str(fallback_candidates[0])

    return None


def format_affected_records(
    records: list[int],
    limit: int = 20,
) -> str:
    shown = records[:limit]

    text = (
        ", ".join(map(str, shown))
        if shown
        else ""
    )

    if len(records) > limit:
        text += (
            f" (+{len(records) - limit} more)"
        )

    return text


def score_status(score: float) -> str:
    if score >= 90:
        return "🟢 Excellent"

    if score >= 75:
        return "🟡 Good"

    if score >= 50:
        return "🟠 Needs Attention"

    return "🔴 Critical"


def _affected_positions(
    df: pd.DataFrame,
    issue: dict,
) -> list[int]:
    positions: list[int] = []

    for record in issue.get(
        "affected_records",
        [],
    ):
        if (
            isinstance(record, int)
            and 1 <= record <= len(df)
        ):
            positions.append(
                record - 1
            )

    return positions


def _preview_before_rows(
    df: pd.DataFrame,
    issue: dict,
    limit: int = 25,
) -> pd.DataFrame:
    positions = _affected_positions(
        df,
        issue,
    )

    if not positions:
        return pd.DataFrame()

    preview = (
        df.iloc[
            positions[:limit]
        ]
        .copy()
    )

    preview.insert(
        0,
        "Record Before",
        [
            position + 1
            for position
            in positions[:limit]
        ],
    )

    return preview


def _matching_after_rows(
    before_df: pd.DataFrame,
    after_df: pd.DataFrame,
    issue: dict,
    limit: int = 25,
) -> pd.DataFrame:
    """
    Find the most relevant rows after a remediation.

    For row-preserving operations, use the same row positions.
    For duplicate operations, locate surviving rows by the duplicate
    column or exact row values.
    """
    if after_df.empty:
        return pd.DataFrame(
            columns=after_df.columns
        )

    rule = str(
        issue.get(
            "rule",
            "",
        )
    ).upper()

    column = issue.get(
        "column"
    )

    positions = _affected_positions(
        before_df,
        issue,
    )

    # Row count unchanged: same positions remain meaningful.
    if len(before_df) == len(after_df):

        valid_positions = [
            position
            for position in positions
            if position < len(after_df)
        ]

        if valid_positions:

            preview = (
                after_df.iloc[
                    valid_positions[:limit]
                ]
                .copy()
            )

            preview.insert(
                0,
                "Record After",
                [
                    position + 1
                    for position
                    in valid_positions[:limit]
                ],
            )

            return preview

    # Duplicate-key issue: show surviving rows for affected key values.
    if (
        "DUPLICATE" in rule
        and column
        and column != "ALL"
        and column in before_df.columns
        and column in after_df.columns
        and positions
    ):

        affected_values = (
            before_df.iloc[
                positions
            ][column]
            .drop_duplicates()
            .tolist()
        )

        mask = pd.Series(
            False,
            index=after_df.index,
        )

        for value in affected_values:

            if pd.isna(value):
                mask = (
                    mask
                    | after_df[
                        column
                    ].isna()
                )
            else:
                mask = (
                    mask
                    | after_df[
                        column
                    ].eq(value)
                )

        preview = (
            after_df.loc[
                mask
            ]
            .head(limit)
            .copy()
        )

        if not preview.empty:
            preview.insert(
                0,
                "Record After",
                [
                    int(index) + 1
                    for index
                    in preview.index
                ],
            )

        return preview

    # Exact duplicate rows: display any surviving copies of the
    # affected exact rows.
    if (
        "DUPLICATE" in rule
        and column == "ALL"
        and positions
    ):

        affected_rows = (
            before_df.iloc[
                positions
            ]
            .drop_duplicates()
        )

        matched_indices: list[int] = []

        for after_index, after_row in (
            after_df.iterrows()
        ):

            for _, target_row in (
                affected_rows.iterrows()
            ):

                try:
                    equal_mask = (
                        (
                            after_row.eq(
                                target_row
                            )
                        )
                        | (
                            after_row.isna()
                            & target_row.isna()
                        )
                    )

                    if bool(
                        equal_mask.all()
                    ):
                        matched_indices.append(
                            int(after_index)
                        )
                        break

                except Exception:
                    continue

            if len(matched_indices) >= limit:
                break

        if matched_indices:

            preview = (
                after_df.loc[
                    matched_indices
                ]
                .copy()
            )

            preview.insert(
                0,
                "Record After",
                [
                    index + 1
                    for index
                    in matched_indices
                ],
            )

            return preview

    # Fallback for row-changing operations.
    # Show nearby working data so the user can verify the result.
    return (
        after_df.head(limit)
        .reset_index(drop=False)
        .rename(
            columns={
                "index": "Record After"
            }
        )
        .assign(
            **{
                "Record After": lambda frame: (
                    frame[
                        "Record After"
                    ]
                    + 1
                )
            }
        )
    )


def _find_issue_after(
    report: dict,
    rule: str,
    column: str,
) -> dict | None:
    for candidate in report.get(
        "issues",
        [],
    ):
        if (
            str(
                candidate.get(
                    "rule",
                    "",
                )
            )
            == str(rule)
            and str(
                candidate.get(
                    "column",
                    "",
                )
            )
            == str(column)
        ):
            return candidate

    return None


def _build_change_summary(
    *,
    before_df: pd.DataFrame,
    after_df: pd.DataFrame,
    issue: dict,
    action: str,
    message: str,
    after_report: dict,
) -> dict:
    rule = str(
        issue.get(
            "rule",
            "Issue",
        )
    )

    column = str(
        issue.get(
            "column",
            "N/A",
        )
    )

    before_failed = int(
        issue.get(
            "failed_rows",
            0,
        )
        or 0
    )

    after_issue = _find_issue_after(
        after_report,
        rule,
        column,
    )

    after_failed = (
        int(
            after_issue.get(
                "failed_rows",
                0,
            )
            or 0
        )
        if after_issue
        else 0
    )

    before_preview = (
        _preview_before_rows(
            before_df,
            issue,
        )
    )

    after_preview = (
        _matching_after_rows(
            before_df,
            after_df,
            issue,
        )
    )

    return {
        "rule": rule,
        "column": column,
        "action": action,
        "message": message,
        "data_changed": (
            not after_df.equals(
                before_df
            )
        ),
        "before_rows": len(
            before_df
        ),
        "after_rows": len(
            after_df
        ),
        "row_delta": (
            len(after_df)
            - len(before_df)
        ),
        "before_failed": before_failed,
        "after_failed": after_failed,
        "resolved": (
            after_issue is None
        ),
        "after_failure_rate": (
            after_issue.get(
                "failure_rate",
                "0%",
            )
            if after_issue
            else "0%"
        ),
        "before_preview": before_preview,
        "after_preview": after_preview,
    }


def render_latest_change(
    change: dict | None,
    *,
    title: str = "Latest Approved Change",
) -> None:
    if not change:
        return

    st.markdown(
        f"### 🔄 {title}"
    )

    status_text = (
        "✅ CLEAN — issue no longer detected"
        if change.get(
            "resolved"
        )
        else "⚠️ STILL EXISTS — review remaining failures"
    )

    if not change.get(
        "data_changed"
    ):
        status_text = (
            "ℹ️ NO AUTOMATIC DATA CHANGE"
        )

    st.write(
        f"**{change.get('rule', 'Issue')} "
        f"→ {change.get('column', 'N/A')}**"
    )

    st.caption(
        f"Action: {change.get('action', '')}"
    )

    st.write(
        change.get(
            "message",
            "",
        )
    )

    m1, m2, m3, m4, m5 = (
        st.columns(5)
    )

    m1.metric(
        "Failed Before",
        change.get(
            "before_failed",
            0,
        ),
    )

    m2.metric(
        "Failed After",
        change.get(
            "after_failed",
            0,
        ),
        delta=(
            change.get(
                "after_failed",
                0,
            )
            - change.get(
                "before_failed",
                0,
            )
        ),
        delta_color="inverse",
    )

    m3.metric(
        "Rows Before",
        change.get(
            "before_rows",
            0,
        ),
    )

    m4.metric(
        "Rows After",
        change.get(
            "after_rows",
            0,
        ),
    )

    rows_removed = max(
        0,
        int(change.get("before_rows", 0))
        - int(change.get("after_rows", 0)),
    )

    m5.metric(
        "Rows Removed",
        rows_removed,
    )

    if change.get(
        "resolved"
    ):
        st.success(
            status_text
        )
    elif change.get(
        "data_changed"
    ):
        st.warning(
            status_text
            + f" · Remaining failure rate: "
            + str(
                change.get(
                    "after_failure_rate",
                    "0%",
                )
            )
        )
    else:
        st.info(
            status_text
        )

    before_preview = change.get(
        "before_preview"
    )

    after_preview = change.get(
        "after_preview"
    )

    left, right = st.columns(2)

    with left:
        st.markdown(
            "#### Before"
        )

        if (
            isinstance(
                before_preview,
                pd.DataFrame,
            )
            and not before_preview.empty
        ):
            st.dataframe(
                before_preview,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.caption(
                "No affected-record preview "
                "was available."
            )

    with right:
        st.markdown(
            "#### After"
        )

        if (
            isinstance(
                after_preview,
                pd.DataFrame,
            )
            and not after_preview.empty
        ):
            st.dataframe(
                after_preview,
                use_container_width=True,
                hide_index=True,
            )
        elif change.get(
            "data_changed"
        ):
            st.success(
                "Affected records were removed "
                "or no longer exist in the "
                "working copy."
            )
        else:
            st.caption(
                "Working data is unchanged."
            )


def sort_issues(
    issues: list[dict],
) -> list[dict]:
    return sorted(
        issues,
        key=lambda issue: (
            -SEVERITY_RANK.get(
                str(
                    issue.get(
                        "severity",
                        "LOW",
                    )
                ).upper(),
                0,
            ),
            -int(
                issue.get(
                    "failed_rows",
                    0,
                )
                or 0
            ),
            str(
                issue.get(
                    "rule",
                    "",
                )
            ),
        ),
    )



def render_clean_dataset_download(
    df: pd.DataFrame,
    quality_report: dict,
    base_name: str,
) -> None:
    """
    Show final validation and download buttons.

    A dataset is labeled CLEAN only when the deterministic
    quality engine reports zero issue rules and zero bad rows.
    """

    remaining_issues = int(
        quality_report.get(
            "total_issues",
            len(
                quality_report.get(
                    "issues",
                    [],
                )
            ),
        )
        or 0
    )

    bad_rows = int(
        quality_report.get(
            "unique_bad_rows",
            0,
        )
        or 0
    )

    score = float(
        quality_report.get(
            "quality_score",
            0,
        )
        or 0
    )

    fully_clean = (
        remaining_issues == 0
        and bad_rows == 0
    )

    st.markdown(
        (
            "### ✅ Final Clean Dataset"
            if fully_clean
            else "### 📦 Dataset Export"
        )
    )

    v1, v2, v3 = st.columns(3)

    v1.metric(
        "Quality Score",
        f"{score}/100",
    )

    v2.metric(
        "Remaining Issues",
        remaining_issues,
    )

    v3.metric(
        "Rows With Problems",
        bad_rows,
    )

    if fully_clean:

        st.success(
            "✅ Final validation passed. "
            "No detected quality issues remain. "
            "The cleaned dataset is ready to download."
        )

        d1, d2 = st.columns(2)

        with d1:
            st.download_button(
                "⬇️ Download Clean Dataset (CSV)",
                data=(
                    df.to_csv(
                        index=False
                    )
                    .encode(
                        "utf-8"
                    )
                ),
                file_name=(
                    f"{base_name}_cleaned.csv"
                ),
                mime="text/csv",
                use_container_width=True,
                key=(
                    f"download_clean_csv_"
                    f"{base_name}"
                ),
            )

        with d2:
            st.download_button(
                "⬇️ Download Clean Dataset (JSON)",
                data=(
                    df.to_json(
                        orient="records",
                        indent=2,
                    )
                    .encode(
                        "utf-8"
                    )
                ),
                file_name=(
                    f"{base_name}_cleaned.json"
                ),
                mime="application/json",
                use_container_width=True,
                key=(
                    f"download_clean_json_"
                    f"{base_name}"
                ),
            )

    else:

        st.warning(
            "⚠️ This working dataset is not fully clean yet. "
            f"{remaining_issues} issue rule(s) remain across "
            f"{bad_rows} row(s). Complete or review the remaining "
            "quality issues before downloading it as the final clean dataset."
        )

        if st.toggle(
            "Allow download of current working copy",
            value=False,
            key=f"allow_working_download_{base_name}",
            help=(
                "This copy may still contain detected quality issues. "
                "It will not be labeled as a clean dataset."
            ),
        ):

            w1, w2 = st.columns(2)

            with w1:
                st.download_button(
                    "⬇️ Download Working Copy (CSV)",
                    data=(
                        df.to_csv(
                            index=False
                        )
                        .encode(
                            "utf-8"
                        )
                    ),
                    file_name=(
                        f"{base_name}_working.csv"
                    ),
                    mime="text/csv",
                    use_container_width=True,
                    key=(
                        f"download_working_csv_"
                        f"{base_name}"
                    ),
                )

            with w2:
                st.download_button(
                    "⬇️ Download Working Copy (JSON)",
                    data=(
                        df.to_json(
                            orient="records",
                            indent=2,
                        )
                        .encode(
                            "utf-8"
                        )
                    ),
                    file_name=(
                        f"{base_name}_working.json"
                    ),
                    mime="application/json",
                    use_container_width=True,
                    key=(
                        f"download_working_json_"
                        f"{base_name}"
                    ),
                )



def _coerce_bulk_value(
    series: pd.Series,
    raw_value: str,
):
    """
    Convert a user-entered bulk replacement value to the
    current column's dtype where practical.

    String/object columns keep the user's exact text.
    """
    dtype = series.dtype
    raw_text = str(raw_value)

    if pd.api.types.is_bool_dtype(dtype):
        normalized = raw_text.strip().lower()

        if normalized in {
            "true",
            "1",
            "yes",
            "y",
        }:
            return True

        if normalized in {
            "false",
            "0",
            "no",
            "n",
        }:
            return False

        raise ValueError(
            "Enter true/false for this boolean column."
        )

    if pd.api.types.is_integer_dtype(dtype):
        return int(
            float(
                raw_text.strip()
            )
        )

    if pd.api.types.is_float_dtype(dtype):
        return float(
            raw_text.strip()
        )

    if pd.api.types.is_datetime64_any_dtype(dtype):
        parsed = pd.to_datetime(
            raw_text,
            errors="raise",
        )

        return parsed

    return raw_text


def _commit_direct_cleaning_change(
    *,
    before_df: pd.DataFrame,
    after_df: pd.DataFrame,
    issue: dict,
    action: str,
    message: str,
    industry: str,
    primary_key: str,
) -> bool:
    """
    Commit one user-approved direct edit to the protected working copy.

    Returns True when a real data change was committed.
    """
    data_changed = (
        not after_df.equals(
            before_df
        )
    )

    if not data_changed:
        st.warning(
            "No values changed. Edit at least one value "
            "before applying the correction."
        )
        return False

    after_report = run_current_quality_checks(
        after_df,
        industry,
        primary_key,
    )

    change_summary = (
        _build_change_summary(
            before_df=before_df,
            after_df=after_df,
            issue=issue,
            action=action,
            message=message,
            after_report=after_report,
        )
    )

    st.session_state.setdefault(
        "undo_stack",
        [],
    ).append(
        before_df.copy()
    )

    st.session_state[
        "cleaned_df"
    ] = after_df

    st.session_state[
        "quality_report"
    ] = after_report

    st.session_state[
        "last_change"
    ] = change_summary

    st.session_state.setdefault(
        "remediation_history",
        [],
    ).append(
        {
            "rule": issue.get(
                "rule"
            ),
            "column": issue.get(
                "column"
            ),
            "action": action,
            "data_changed": True,
            "failed_before": (
                change_summary[
                    "before_failed"
                ]
            ),
            "failed_after": (
                change_summary[
                    "after_failed"
                ]
            ),
            "status": (
                "CLEAN"
                if change_summary[
                    "resolved"
                ]
                else "UPDATED"
            ),
            "message": message,
        }
    )

    st.session_state[
        "last_fix_message"
    ] = (
        "✅ "
        + message
        + " Original uploaded data remains unchanged."
    )

    return True


def render_direct_cleaning_tools(
    *,
    issue: dict,
    issue_number: int,
    working_df: pd.DataFrame,
    industry: str,
    primary_key: str,
) -> None:
    """
    Provide user-controlled cleaning in addition to rule recommendations.

    Modes:
    1. Edit exact affected rows directly.
    2. Apply one replacement value to every affected record.

    Both modes modify only the protected working copy and then rerun
    deterministic quality checks.
    """
    affected_positions = _affected_positions(
        working_df,
        issue,
    )

    if not affected_positions:
        return

    rule = str(
        issue.get(
            "rule",
            "Issue",
        )
    )

    target_column = str(
        issue.get(
            "column",
            "",
        )
    )

    issue_key = (
        f"{issue_number}_"
        f"{rule}_"
        f"{target_column}"
    )

    st.divider()

    st.markdown(
        "#### ✏️ Direct Cleaning Tools"
    )

    st.caption(
        "Use these tools when the correct value is known. "
        "Edits are applied only to the protected working copy, "
        "then the quality checks run again automatically."
    )

    edit_tab, bulk_tab = st.tabs(
        [
            "✏️ Edit Affected Rows",
            "🧹 Bulk Correction",
        ]
    )

    # --------------------------------------------------------
    # DIRECT ROW EDITOR
    # --------------------------------------------------------

    with edit_tab:

        max_editor_rows = 100

        editor_positions = (
            affected_positions[
                :max_editor_rows
            ]
        )

        editor_df = (
            working_df.iloc[
                editor_positions
            ]
            .copy()
        )

        editor_df.insert(
            0,
            "Record",
            [
                position + 1
                for position
                in editor_positions
            ],
        )

        if (
            len(affected_positions)
            > max_editor_rows
        ):
            st.info(
                f"Showing the first {max_editor_rows} of "
                f"{len(affected_positions)} affected records. "
                "Apply these edits, rerun validation, then continue "
                "with the remaining records."
            )

        editable_target_exists = (
            target_column != "ALL"
            and target_column
            in working_df.columns
        )

        edit_all_columns = st.toggle(
            "Advanced: allow editing all columns in these rows",
            value=(
                not editable_target_exists
            ),
            key=(
                f"edit_all_columns_"
                f"{issue_key}"
            ),
            help=(
                "Normally only the problem column is editable. "
                "Enable this only when multiple fields in the "
                "affected records need correction."
            ),
        )

        if (
            editable_target_exists
            and not edit_all_columns
        ):
            disabled_columns = [
                "Record"
            ] + [
                column
                for column
                in working_df.columns
                if str(column)
                != target_column
            ]

            st.info(
                f"🎯 Editing only **{target_column}**. "
                "Other columns are locked for safety."
            )

        else:
            disabled_columns = [
                "Record"
            ]

            st.warning(
                "Advanced editing is enabled. Review every changed "
                "field before applying."
            )

        edited_df = st.data_editor(
            editor_df,
            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            disabled=disabled_columns,
            key=(
                f"direct_editor_"
                f"{issue_key}"
            ),
        )

        if st.button(
            "💾 Apply Direct Edits & Revalidate",
            use_container_width=True,
            key=(
                f"apply_direct_edits_"
                f"{issue_key}"
            ),
        ):

            before_df = (
                st.session_state[
                    "cleaned_df"
                ].copy()
            )

            after_df = (
                before_df.copy()
            )

            editable_columns = [
                column
                for column
                in working_df.columns
                if (
                    edit_all_columns
                    or str(column)
                    == target_column
                )
            ]

            changed_cells = 0

            for row_number in range(
                len(edited_df)
            ):

                record_number = int(
                    edited_df.iloc[
                        row_number
                    ][
                        "Record"
                    ]
                )

                position = (
                    record_number - 1
                )

                if (
                    position
                    not in after_df.index
                ):
                    continue

                for column in editable_columns:

                    new_value = (
                        edited_df.iloc[
                            row_number
                        ][
                            column
                        ]
                    )

                    old_value = (
                        after_df.at[
                            position,
                            column,
                        ]
                    )

                    values_equal = False

                    try:
                        values_equal = bool(
                            (
                                pd.isna(
                                    old_value
                                )
                                and pd.isna(
                                    new_value
                                )
                            )
                            or (
                                old_value
                                == new_value
                            )
                        )
                    except Exception:
                        values_equal = (
                            repr(
                                old_value
                            )
                            == repr(
                                new_value
                            )
                        )

                    if values_equal:
                        continue

                    after_df.at[
                        position,
                        column,
                    ] = new_value

                    changed_cells += 1

            if changed_cells == 0:

                st.warning(
                    "No edited values were detected."
                )

            else:

                committed = (
                    _commit_direct_cleaning_change(
                        before_df=before_df,
                        after_df=after_df,
                        issue=issue,
                        action=(
                            "Direct row edit"
                        ),
                        message=(
                            f"{changed_cells} cell value(s) "
                            "were manually corrected in the "
                            "affected records."
                        ),
                        industry=industry,
                        primary_key=primary_key,
                    )
                )

                if committed:
                    st.rerun()

    # --------------------------------------------------------
    # BULK CORRECTION
    # --------------------------------------------------------

    with bulk_tab:

        if (
            target_column == "ALL"
            or target_column
            not in working_df.columns
        ):

            st.info(
                "Bulk replacement is available for issues "
                "that target one specific column. "
                "For this issue, use the direct row editor "
                "or one of the recommended duplicate actions."
            )

        else:

            st.write(
                f"Apply one approved value to all "
                f"**{len(affected_positions)}** affected "
                f"record(s) in **{target_column}**."
            )

            st.warning(
                "Use Bulk Correction only when the same value "
                "is correct for every affected record."
            )

            replacement_value = (
                st.text_input(
                    f"Replacement value for {target_column}",
                    key=(
                        f"bulk_value_"
                        f"{issue_key}"
                    ),
                    placeholder=(
                        "Enter the verified value"
                    ),
                )
            )

            confirm_bulk = st.checkbox(
                (
                    "I confirm this value is correct for "
                    f"all {len(affected_positions)} "
                    "affected records."
                ),
                key=(
                    f"bulk_confirm_"
                    f"{issue_key}"
                ),
            )

            if st.button(
                "🧹 Apply Bulk Correction & Revalidate",
                use_container_width=True,
                disabled=(
                    not confirm_bulk
                    or replacement_value
                    == ""
                ),
                key=(
                    f"apply_bulk_"
                    f"{issue_key}"
                ),
            ):

                before_df = (
                    st.session_state[
                        "cleaned_df"
                    ].copy()
                )

                after_df = (
                    before_df.copy()
                )

                valid_positions = [
                    position
                    for position
                    in affected_positions
                    if position
                    in after_df.index
                ]

                try:
                    converted_value = (
                        _coerce_bulk_value(
                            after_df[
                                target_column
                            ],
                            replacement_value,
                        )
                    )

                except (
                    ValueError,
                    TypeError,
                ) as error:

                    st.error(
                        f"Could not apply that value: {error}"
                    )

                else:

                    after_df.loc[
                        valid_positions,
                        target_column,
                    ] = converted_value

                    committed = (
                        _commit_direct_cleaning_change(
                            before_df=before_df,
                            after_df=after_df,
                            issue=issue,
                            action=(
                                f"Bulk correction: "
                                f"{target_column}"
                            ),
                            message=(
                                f"{len(valid_positions)} affected "
                                f"value(s) in '{target_column}' "
                                "were replaced with the "
                                "user-approved value."
                            ),
                            industry=industry,
                            primary_key=primary_key,
                        )
                    )

                    if committed:
                        st.rerun()


# ============================================================
# HERO
# ============================================================

st.html(
    '<div class="hello-pill">🤖 Live Project</div>'
)

st.html(
    '<h1 class="hero-title" style="font-size:3.25rem">'
    'AI Data Quality Copilot'
    '</h1>'
)

st.html(
    """
    <div class="dq-intro">
        Deterministic data-quality analysis, exact problem records,
        human-approved remediation, before/after validation, and local
        AI explanations grounded in the quality report.
    </div>
    """
)

st.write("")

st.html(
    """
    <div class="safety-card">
        <div class="safety-title">
            🔒 Safe by design
        </div>
        <div class="safety-text">
            The original uploaded dataset is never modified.
            Approved remediation is applied only to a protected working copy.
            The deterministic quality engine remains the source of truth,
            while AI is used only for explanation and recommendations.
        </div>
    </div>
    """
)

with st.expander(
    "🏗 How it works"
):
    st.code(
        """
CSV / JSON
    ↓
Data Loader
    ↓
Deterministic Quality Engine
    ↓
Industry Rules
    ↓
Quality Score + Exact Issues
    ↓
Human Approval
    ↓
Protected Working Copy
    ↓
Re-run Checks
    ↓
Before / After Validation
    ↓
AI Explanation
        """.strip()
    )


# ============================================================
# ANALYSIS SETTINGS
# ============================================================

_pending_recipe = st.session_state.get(
    "pending_cleaning_recipe"
)

if _pending_recipe:
    _pending_industry = _pending_recipe.get(
        "industry",
        "General",
    )

    if _pending_industry in (
        "General",
        "Retail",
        "Healthcare",
        "Banking",
    ):
        st.session_state[
            "dq_industry"
        ] = _pending_industry

render_section_header(
    "Analysis Settings",
    "⚙️",
)

settings1, settings2 = st.columns(
    [1, 2]
)

with settings1:
    industry = st.selectbox(
        "Industry",
        [
            "General",
            "Retail",
            "Healthcare",
            "Banking",
        ],
        key="dq_industry",
        help=(
            "General checks always run. "
            "Industry selection adds domain-specific rules."
        ),
    )

with settings2:
    st.info(
        "🤖 The AI assistant explains the deterministic report. "
        "It does not create, replace, or override quality checks."
    )


# ============================================================
# UPLOAD
# ============================================================

render_section_header(
    "Upload Datasets",
    "📂",
)

uploaded_files = (
    st.file_uploader(
        "Upload up to 3 CSV or JSON datasets",
        type=[
            "csv",
            "json",
        ],
        accept_multiple_files=True,
        help=(
            f"Maximum {MAX_FILES} files; "
            f"{MAX_FILE_SIZE_MB} MB per file."
        ),
    )
    or []
)

if len(uploaded_files) > MAX_FILES:
    st.error(
        f"Please upload a maximum of "
        f"{MAX_FILES} files at a time."
    )
    st.stop()

oversized = [
    file.name
    for file in uploaded_files
    if uploaded_file_size(file)
    > MAX_FILE_SIZE_BYTES
]

if oversized:
    st.error(
        f"These files are larger than "
        f"{MAX_FILE_SIZE_MB} MB: "
        + ", ".join(oversized)
    )
    st.stop()


# ============================================================
# MAIN APP
# ============================================================

if not uploaded_files:

    st.info(
        "👆 Upload one or more CSV/JSON "
        "datasets to begin."
    )

else:

    st.success(
        f"✅ {len(uploaded_files)} "
        f"dataset(s) uploaded."
    )

    selected_index = st.selectbox(
        "📁 Select Dataset to Analyze",
        options=range(
            len(uploaded_files)
        ),
        format_func=lambda i: (
            f"{uploaded_files[i].name} "
            f"({uploaded_file_size(uploaded_files[i]) / 1024:.1f} KB)"
        ),
    )

    uploaded_file = (
        uploaded_files[selected_index]
    )

    try:

        # ====================================================
        # LOAD DATA
        # ====================================================

        dataset_key = make_dataset_key(
            uploaded_file
        )

        uploaded_file.seek(0)

        df = load_data(
            uploaded_file
        )

        report_columns = {
            "Issue",
            "Column",
            "Severity",
            "Failed Rows",
            "Failure Rate",
            "Affected Records",
        }

        if report_columns.issubset(
            set(df.columns)
        ):
            st.warning(
                "This appears to be a generated "
                "quality report. Upload the original "
                "source dataset instead."
            )
            st.stop()

        activate_dataset_state(
            df,
            dataset_key,
        )


        # ====================================================
        # APPLY PENDING CLEANING RECIPE
        # ====================================================

        pending_recipe = st.session_state.get(
            "pending_cleaning_recipe"
        )

        if pending_recipe:

            pending_pk = pending_recipe.get(
                "primary_key"
            )

            st.session_state[
                f"primary_key_{dataset_key}"
            ] = (
                pending_pk
                if pending_pk
                in df.columns
                else "None"
            )

            st.session_state[
                "custom_rules"
            ] = [
                rule
                for rule
                in pending_recipe.get(
                    "custom_rules",
                    [],
                )
                if rule.get(
                    "column"
                )
                in df.columns
            ]

            st.session_state[
                "schema_contract"
            ] = pending_recipe.get(
                "schema_contract"
            )

            st.session_state[
                "recipe_action_policies"
            ] = pending_recipe.get(
                "action_policies",
                [],
            )

            st.session_state.pop(
                "pending_cleaning_recipe",
                None,
            )

            invalidate_analysis(
                df
            )

            st.session_state[
                "last_fix_message"
            ] = (
                "✅ Cleaning recipe loaded. "
                "Review the configuration and run analysis."
            )

        # ====================================================
        # DATASET SETUP
        # ====================================================

        render_section_header(
            "Dataset Setup",
            "🔑",
        )

        detected_roles = infer_column_roles(
            df
        )

        st.session_state[
            "detected_roles"
        ] = detected_roles

        suggested_pk = (
            detected_roles.get(
                "primary_key"
            )
            or suggest_primary_key(
                df
            )
        )

        pk_options = [
            "None"
        ] + list(df.columns)

        default_pk_index = 0

        if (
            suggested_pk
            and suggested_pk in pk_options
        ):
            default_pk_index = (
                pk_options.index(
                    suggested_pk
                )
            )

        setup1, setup2 = st.columns(
            [1, 2]
        )

        with setup1:

            primary_key = st.selectbox(
                "Primary Key",
                pk_options,
                index=default_pk_index,
                key=f"primary_key_{dataset_key}",
                help=(
                    "A likely unique key is suggested "
                    "when one can be detected. "
                    "You remain in control of the selection."
                ),
            )

            if suggested_pk:
                st.caption(
                    f"💡 Suggested key: "
                    f"**{suggested_pk}**"
                )
            else:
                st.caption(
                    "💡 No safe primary-key "
                    "candidate was auto-detected."
                )

        with setup2:

            overview1, overview2, overview3 = (
                st.columns(3)
            )

            overview1.metric(
                "Rows",
                f"{len(df):,}",
            )

            overview2.metric(
                "Columns",
                f"{len(df.columns):,}",
            )

            overview3.metric(
                "File Type",
                Path(
                    uploaded_file.name
                )
                .suffix
                .lstrip(".")
                .upper(),
            )

            overview4, overview5 = (
                st.columns(2)
            )

            overview4.metric(
                "Industry",
                industry,
            )

            overview5.metric(
                "Primary Key",
                (
                    primary_key
                    if primary_key != "None"
                    else "Not selected"
                ),
            )

        current_signature = (
            dataset_key,
            industry,
            primary_key,
            _config_fingerprint(),
        )

        previous_signature = (
            st.session_state.get(
                "analysis_signature"
            )
        )

        if (
            previous_signature is not None
            and previous_signature
            != current_signature
        ):
            invalidate_analysis(
                df
            )

            st.session_state.pop(
                "analysis_signature",
                None,
            )

        with st.expander(
            "👀 Preview Original Dataset"
        ):
            st.dataframe(
                df.head(25),
                use_container_width=True,
                hide_index=True,
            )



        # ====================================================
        # QUALITY CONFIGURATION
        # ====================================================

        render_section_header(
            "Quality Configuration",
            "🧩",
        )

        config_tab1, config_tab2, config_tab3 = st.tabs(
            [
                "🪄 Smart Detection",
                "📐 Custom Rules",
                "🧬 Contract + Recipe",
            ]
        )

        # ----------------------------------------------------
        # SMART COLUMN DETECTION
        # ----------------------------------------------------

        with config_tab1:

            st.caption(
                "The app suggests column roles from names, uniqueness, "
                "and data types. Suggestions never change the dataset."
            )

            role_rows = []

            if detected_roles.get(
                "primary_key"
            ):
                role_rows.append(
                    {
                        "Role": "Primary Key",
                        "Detected Columns": (
                            detected_roles[
                                "primary_key"
                            ]
                        ),
                    }
                )

            role_map = [
                (
                    "Email",
                    "email_columns",
                ),
                (
                    "Phone",
                    "phone_columns",
                ),
                (
                    "Date / Timestamp",
                    "date_columns",
                ),
                (
                    "Amount / Price",
                    "amount_columns",
                ),
                (
                    "Quantity",
                    "quantity_columns",
                ),
                (
                    "Numeric",
                    "numeric_columns",
                ),
            ]

            for label, key in role_map:

                values = detected_roles.get(
                    key,
                    [],
                )

                if values:
                    role_rows.append(
                        {
                            "Role": label,
                            "Detected Columns": (
                                ", ".join(
                                    values
                                )
                            ),
                        }
                    )

            if role_rows:
                st.dataframe(
                    pd.DataFrame(
                        role_rows
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info(
                    "No strong semantic column roles were detected."
                )

            if (
                detected_roles.get(
                    "primary_key"
                )
                and primary_key
                == detected_roles.get(
                    "primary_key"
                )
            ):
                st.success(
                    f"✅ Primary-key suggestion accepted: "
                    f"{primary_key}"
                )

        # ----------------------------------------------------
        # CUSTOM RULE BUILDER
        # ----------------------------------------------------

        with config_tab2:

            st.session_state.setdefault(
                "custom_rules",
                [],
            )

            st.write(
                "**Create deterministic business rules without editing Python.**"
            )

            rule_c1, rule_c2, rule_c3 = st.columns(
                [1.3, 1.2, 0.8]
            )

            with rule_c1:
                custom_rule_column = st.selectbox(
                    "Column",
                    list(
                        df.columns
                    ),
                    key=(
                        f"custom_rule_column_"
                        f"{dataset_key}"
                    ),
                )

            with rule_c2:
                custom_rule_type = st.selectbox(
                    "Rule Type",
                    list(
                        CUSTOM_RULE_TYPES
                    ),
                    key=(
                        f"custom_rule_type_"
                        f"{dataset_key}"
                    ),
                )

            with rule_c3:
                custom_rule_severity = st.selectbox(
                    "Severity",
                    [
                        "CRITICAL",
                        "HIGH",
                        "MEDIUM",
                        "LOW",
                    ],
                    index=2,
                    key=(
                        f"custom_rule_severity_"
                        f"{dataset_key}"
                    ),
                )

            custom_rule_name = st.text_input(
                "Rule Name",
                value=(
                    f"{custom_rule_type} - "
                    f"{custom_rule_column}"
                ),
                key=(
                    f"custom_rule_name_"
                    f"{dataset_key}_"
                    f"{custom_rule_type}_"
                    f"{custom_rule_column}"
                ),
            )

            custom_rule_value = None

            if custom_rule_type in (
                "Minimum Value",
                "Maximum Value",
            ):
                custom_rule_value = st.number_input(
                    "Threshold",
                    value=0.0,
                    key=(
                        f"custom_rule_value_"
                        f"{dataset_key}_"
                        f"{custom_rule_type}_"
                        f"{custom_rule_column}"
                    ),
                )

            elif custom_rule_type == "Allowed Values":
                custom_rule_value = st.text_input(
                    "Allowed values (comma-separated)",
                    placeholder=(
                        "Active, Pending, Closed"
                    ),
                    key=(
                        f"custom_rule_allowed_"
                        f"{dataset_key}_"
                        f"{custom_rule_column}"
                    ),
                )

            elif custom_rule_type == "Regex Pattern":
                custom_rule_value = st.text_input(
                    "Regex pattern",
                    placeholder=(
                        r"^[A-Z]{2}$"
                    ),
                    key=(
                        f"custom_rule_regex_"
                        f"{dataset_key}_"
                        f"{custom_rule_column}"
                    ),
                )

            if st.button(
                "➕ Add Custom Rule",
                use_container_width=True,
                key=(
                    f"add_custom_rule_"
                    f"{dataset_key}"
                ),
            ):

                rule_config = {
                    "name": (
                        custom_rule_name.strip()
                        or (
                            f"{custom_rule_type} - "
                            f"{custom_rule_column}"
                        )
                    ),
                    "type": custom_rule_type,
                    "column": (
                        custom_rule_column
                    ),
                    "severity": (
                        custom_rule_severity
                    ),
                }

                if custom_rule_value not in (
                    None,
                    "",
                ):
                    rule_config[
                        "value"
                    ] = custom_rule_value

                st.session_state[
                    "custom_rules"
                ].append(
                    rule_config
                )

                invalidate_analysis(
                            df
                        )

                st.success(
                    "Custom rule added."
                )

                st.rerun()

            rules = st.session_state.get(
                "custom_rules",
                [],
            )

            if rules:

                st.markdown(
                    "#### Active Custom Rules"
                )

                rules_table = []

                for index, rule in enumerate(
                    rules,
                    start=1,
                ):
                    rules_table.append(
                        {
                            "#": index,
                            "Name": rule.get(
                                "name"
                            ),
                            "Column": rule.get(
                                "column"
                            ),
                            "Type": rule.get(
                                "type"
                            ),
                            "Severity": rule.get(
                                "severity"
                            ),
                            "Value": rule.get(
                                "value",
                                "",
                            ),
                        }
                    )

                st.dataframe(
                    pd.DataFrame(
                        rules_table
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

                remove_c1, remove_c2 = st.columns(
                    [2, 1]
                )

                with remove_c1:
                    remove_rule_index = st.selectbox(
                        "Select rule to remove",
                        options=range(
                            len(
                                rules
                            )
                        ),
                        format_func=lambda i: (
                            f"{i + 1}. "
                            f"{rules[i].get('name')}"
                        ),
                        key=(
                            f"remove_rule_"
                            f"{dataset_key}"
                        ),
                    )

                with remove_c2:
                    st.write("")
                    st.write("")

                    if st.button(
                        "🗑 Remove Rule",
                        use_container_width=True,
                        key=(
                            f"remove_rule_button_"
                            f"{dataset_key}"
                        ),
                    ):
                        st.session_state[
                            "custom_rules"
                        ].pop(
                            remove_rule_index
                        )

                        invalidate_analysis(
                            df
                        )

                        st.rerun()

            else:
                st.info(
                    "No custom business rules are active."
                )

        # ----------------------------------------------------
        # SCHEMA CONTRACT + CLEANING RECIPE
        # ----------------------------------------------------

        with config_tab3:

            contract_col, recipe_col = st.columns(
                2
            )

            with contract_col:

                st.markdown(
                    "### 🧬 Data Contract / Schema Drift"
                )

                st.caption(
                    "Save the expected columns and data types, then compare "
                    "future uploads against the contract."
                )

                if st.button(
                    "📌 Create Contract From This Dataset",
                    use_container_width=True,
                    key=(
                        f"create_contract_"
                        f"{dataset_key}"
                    ),
                ):

                    contract = (
                        generate_schema_contract(
                            df,
                            primary_key,
                        )
                    )

                    st.session_state[
                        "schema_contract"
                    ] = contract

                    st.session_state[
                        "last_schema_contract"
                    ] = contract

                    invalidate_analysis(
                            df
                        )

                    st.success(
                        "Schema contract created."
                    )

                    st.rerun()

                if (
                    st.session_state.get(
                        "last_schema_contract"
                    )
                    and not st.session_state.get(
                        "schema_contract"
                    )
                ):
                    if st.button(
                        "♻️ Use Last Saved Contract",
                        use_container_width=True,
                        key=(
                            f"use_last_contract_"
                            f"{dataset_key}"
                        ),
                    ):
                        st.session_state[
                            "schema_contract"
                        ] = st.session_state[
                            "last_schema_contract"
                        ]

                        invalidate_analysis(
                            df
                        )

                        st.rerun()

                contract_upload = st.file_uploader(
                    "Load Contract JSON",
                    type=[
                        "json"
                    ],
                    key=(
                        f"contract_upload_"
                        f"{dataset_key}"
                    ),
                )

                if (
                    contract_upload
                    is not None
                ):

                    if st.button(
                        "📥 Apply Uploaded Contract",
                        use_container_width=True,
                        key=(
                            f"apply_contract_"
                            f"{dataset_key}"
                        ),
                    ):

                        try:
                            loaded_contract = (
                                json.loads(
                                    contract_upload
                                    .getvalue()
                                    .decode(
                                        "utf-8"
                                    )
                                )
                            )

                            if not isinstance(
                                loaded_contract,
                                dict,
                            ):
                                raise ValueError(
                                    "Contract must be a JSON object."
                                )

                        except Exception as error:
                            st.error(
                                f"Could not load contract: {error}"
                            )
                        else:
                            st.session_state[
                                "schema_contract"
                            ] = loaded_contract

                            st.session_state[
                                "last_schema_contract"
                            ] = loaded_contract

                            invalidate_analysis(
                            df
                        )

                            st.rerun()

                active_contract = (
                    st.session_state.get(
                        "schema_contract"
                    )
                )

                if active_contract:

                    st.success(
                        f"✅ Contract active · "
                        f"{len(active_contract.get('columns', []))} "
                        "expected columns"
                    )

                    contract_buttons = st.columns(
                        2
                    )

                    with contract_buttons[0]:
                        st.download_button(
                            "⬇️ Download Contract",
                            data=contract_to_json(
                                active_contract
                            ).encode(
                                "utf-8"
                            ),
                            file_name=(
                                f"{Path(uploaded_file.name).stem}"
                                "_schema_contract.json"
                            ),
                            mime="application/json",
                            use_container_width=True,
                            key=(
                                f"download_contract_"
                                f"{dataset_key}"
                            ),
                        )

                    with contract_buttons[1]:
                        if st.button(
                            "✖ Remove Contract",
                            use_container_width=True,
                            key=(
                                f"remove_contract_"
                                f"{dataset_key}"
                            ),
                        ):
                            st.session_state[
                                "schema_contract"
                            ] = None

                            invalidate_analysis(
                            df
                        )

                            st.rerun()

                else:
                    st.info(
                        "No schema contract is active."
                    )

            with recipe_col:

                st.markdown(
                    "### 💾 Cleaning Recipe"
                )

                st.caption(
                    "Save the industry, primary key, custom rules, and "
                    "schema contract as a reusable JSON recipe."
                )

                recipe_name = st.text_input(
                    "Recipe Name",
                    value=(
                        f"{Path(uploaded_file.name).stem} "
                        "Quality Recipe"
                    ),
                    key=(
                        f"recipe_name_"
                        f"{dataset_key}"
                    ),
                )

                current_recipe = (
                    build_cleaning_recipe(
                        name=recipe_name,
                        industry=industry,
                        primary_key=primary_key,
                        custom_rules=(
                            st.session_state.get(
                                "custom_rules",
                                [],
                            )
                        ),
                        schema_contract=(
                            st.session_state.get(
                                "schema_contract"
                            )
                        ),
                        remediation_history=(
                            st.session_state.get(
                                "remediation_history",
                                [],
                            )
                        ),
                    )
                )

                recipe_actions = st.columns(
                    2
                )

                with recipe_actions[0]:
                    if st.button(
                        "💾 Save Recipe in Session",
                        use_container_width=True,
                        key=(
                            f"save_recipe_"
                            f"{dataset_key}"
                        ),
                    ):
                        library = (
                            st.session_state.setdefault(
                                "recipe_library",
                                {},
                            )
                        )

                        library[
                            current_recipe[
                                "name"
                            ]
                        ] = current_recipe

                        st.success(
                            "Recipe saved for this session."
                        )

                with recipe_actions[1]:
                    st.download_button(
                        "⬇️ Export Recipe JSON",
                        data=recipe_to_json(
                            current_recipe
                        ).encode(
                            "utf-8"
                        ),
                        file_name=(
                            f"{Path(uploaded_file.name).stem}"
                            "_cleaning_recipe.json"
                        ),
                        mime="application/json",
                        use_container_width=True,
                        key=(
                            f"download_recipe_"
                            f"{dataset_key}"
                        ),
                    )

                recipe_upload = st.file_uploader(
                    "Load Recipe JSON",
                    type=[
                        "json"
                    ],
                    key=(
                        f"recipe_upload_"
                        f"{dataset_key}"
                    ),
                )

                if (
                    recipe_upload
                    is not None
                ):

                    if st.button(
                        "📥 Apply Uploaded Recipe",
                        use_container_width=True,
                        key=(
                            f"apply_recipe_upload_"
                            f"{dataset_key}"
                        ),
                    ):

                        try:
                            recipe = parse_recipe(
                                recipe_upload.getvalue()
                            )
                        except Exception as error:
                            st.error(
                                f"Could not load recipe: {error}"
                            )
                        else:
                            st.session_state[
                                "pending_cleaning_recipe"
                            ] = recipe

                            st.rerun()

                recipe_library = (
                    st.session_state.get(
                        "recipe_library",
                        {},
                    )
                )

                if recipe_library:

                    saved_name = st.selectbox(
                        "Saved Session Recipes",
                        list(
                            recipe_library.keys()
                        ),
                        key=(
                            f"saved_recipe_select_"
                            f"{dataset_key}"
                        ),
                    )

                    if st.button(
                        "♻️ Apply Saved Recipe",
                        use_container_width=True,
                        key=(
                            f"apply_saved_recipe_"
                            f"{dataset_key}"
                        ),
                    ):

                        st.session_state[
                            "pending_cleaning_recipe"
                        ] = recipe_library[
                            saved_name
                        ]

                        st.rerun()



        # ====================================================
        # ANALYSIS BUTTON
        # ====================================================

        if st.button(
            "🚀 Run Data Quality Analysis",
            type="primary",
            use_container_width=True,
            key=f"run_analysis_{dataset_key}",
        ):

            with st.status(
                "Running deterministic "
                "data-quality checks...",
                expanded=True,
            ) as status:

                st.write(
                    "🔍 Missing and blank values"
                )

                st.write(
                    "♻️ Duplicate rows and "
                    "primary-key checks"
                )

                st.write(
                    "📅 Dates and future-event dates"
                )

                st.write(
                    "📧 Email and phone formats"
                )

                st.write(
                    f"🏢 {industry} rule pack"
                )

                baseline_report = (
                    run_current_quality_checks(
                        df,
                        industry,
                        primary_key,
                    )
                )

                st.session_state[
                    "cleaned_df"
                ] = df.copy()

                st.session_state[
                    "baseline_report"
                ] = baseline_report

                st.session_state[
                    "quality_report"
                ] = baseline_report

                st.session_state[
                    "analysis_signature"
                ] = current_signature

                st.session_state[
                    "remediation_history"
                ] = []

                st.session_state[
                    "undo_stack"
                ] = []

                st.session_state.pop(
                    "last_change",
                    None,
                )

                # A fresh analysis starts on Overview. Remediation actions
                # later preserve the currently selected section automatically.
                st.session_state["results_view"] = "📊 Overview"

                status.update(
                    label=(
                        "✅ Data quality "
                        "analysis completed"
                    ),
                    state="complete",
                )


        # ====================================================
        # MESSAGES
        # ====================================================

        last_fix_message = (
            st.session_state.pop(
                "last_fix_message",
                None,
            )
        )

        if last_fix_message:
            st.success(
                last_fix_message
            )


        # ====================================================
        # RESULTS
        # ====================================================

        report = st.session_state.get(
            "quality_report"
        )

        if report:

            baseline_report = (
                st.session_state.get(
                    "baseline_report",
                    report,
                )
            )

            history = (
                st.session_state.get(
                    "remediation_history",
                    [],
                )
            )

            issues = sort_issues(
                report.get(
                    "issues",
                    [],
                )
            )

            row_issues = report.get(
                "row_issues",
                [],
            )

            working_df = (
                st.session_state.get(
                    "cleaned_df",
                    df,
                )
            )

            score = float(
                report.get(
                    "quality_score",
                    0,
                )
            )

            render_section_header(
                "Data Quality Results",
                "📈",
            )

            if issues:
                top_issue = issues[0]

                st.info(
                    f"🎯 **Top priority:** "
                    f"{top_issue.get('rule', 'Issue')} "
                    f"→ {top_issue.get('column', 'N/A')} "
                    f"· {top_issue.get('severity', 'LOW')} "
                    f"· {top_issue.get('failed_rows', 0)} "
                    f"failed check(s)"
                )

            # Keep the selected results section across Streamlit reruns.
            # Native st.tabs() returns to the first tab after st.rerun(),
            # which is disruptive during remediation. A horizontal radio
            # provides tab-style navigation while persisting its value in
            # session_state automatically.
            result_views = [
                "📊 Overview",
                "🔍 Issues",
                "🛠 Remediation",
                "✨ Working Data",
                "🧬 Schema",
                "✅ Final Summary",
            ]

            if "results_view" not in st.session_state:
                st.session_state["results_view"] = "📊 Overview"

            active_results_view = st.radio(
                "Results View",
                result_views,
                horizontal=True,
                key="results_view",
                label_visibility="collapsed",
            )


            # ====================================================
            # OVERVIEW
            # ====================================================

            if active_results_view == "📊 Overview":

                s1, s2 = st.columns(
                    [1, 2]
                )

                with s1:

                    st.metric(
                        "Current Quality Score",
                        f"{score}/100",
                    )

                    st.write(
                        f"**Status:** "
                        f"{score_status(score)}"
                    )

                with s2:

                    st.write(
                        "**Overall Data Health**"
                    )

                    st.progress(
                        min(
                            max(
                                score / 100,
                                0.0,
                            ),
                            1.0,
                        )
                    )

                if history:

                    before_score = float(
                        baseline_report.get(
                            "quality_score",
                            0,
                        )
                    )

                    improvement = round(
                        score - before_score,
                        2,
                    )

                    b1, b2, b3 = (
                        st.columns(3)
                    )

                    b1.metric(
                        "Before",
                        f"{before_score}/100",
                    )

                    b2.metric(
                        "Current",
                        f"{score}/100",
                    )

                    b3.metric(
                        "Improvement",
                        f"{improvement:+}",
                    )

                q1, q2, q3, q4 = (
                    st.columns(4)
                )

                q1.metric(
                    "🎯 Score",
                    f"{report.get('quality_score', 0)}/100",
                )

                q2.metric(
                    "📋 Issue Rules",
                    report.get(
                        "total_issues",
                        0,
                    ),
                    help=(
                        "Number of detected "
                        "rule/column issue entries."
                    ),
                )

                q3.metric(
                    "⚠️ Failed Checks",
                    report.get(
                        "total_failed_checks",
                        0,
                    ),
                    help=(
                        "Total rule failures. "
                        "One row can fail more than "
                        "one quality check."
                    ),
                )

                q4.metric(
                    "🚨 Bad Rows",
                    report.get(
                        "unique_bad_rows",
                        0,
                    ),
                    help=(
                        "Unique rows containing at "
                        "least one detected problem."
                    ),
                )

                h1, h2, h3 = (
                    st.columns(3)
                )

                h1.metric(
                    "✅ Clean Rows",
                    report.get(
                        "clean_rows",
                        0,
                    ),
                )

                h2.metric(
                    "🚨 Rows With Problems",
                    report.get(
                        "unique_bad_rows",
                        0,
                    ),
                )

                h3.metric(
                    "📉 Bad Row Rate",
                    (
                        f"{report.get('bad_row_rate', 0)}%"
                    ),
                )

                severity = report.get(
                    "severity_counts",
                    {},
                )

                v1, v2, v3, v4 = (
                    st.columns(4)
                )

                v1.metric(
                    "🔴 Critical",
                    severity.get(
                        "CRITICAL",
                        0,
                    ),
                )

                v2.metric(
                    "🟠 High",
                    severity.get(
                        "HIGH",
                        0,
                    ),
                )

                v3.metric(
                    "🟡 Medium",
                    severity.get(
                        "MEDIUM",
                        0,
                    ),
                )

                v4.metric(
                    "🟢 Low",
                    severity.get(
                        "LOW",
                        0,
                    ),
                )


            # ====================================================
            # ISSUES
            # ====================================================

            if active_results_view == "🔍 Issues":

                if not issues:

                    st.success(
                        "🎉 No major data-quality "
                        "issues detected."
                    )

                else:

                    filter1, filter2 = (
                        st.columns(2)
                    )

                    with filter1:

                        severity_filter = (
                            st.multiselect(
                                "Severity",
                                [
                                    "CRITICAL",
                                    "HIGH",
                                    "MEDIUM",
                                    "LOW",
                                ],
                                default=[
                                    "CRITICAL",
                                    "HIGH",
                                    "MEDIUM",
                                    "LOW",
                                ],
                            )
                        )

                    with filter2:

                        issue_columns = sorted(
                            {
                                str(
                                    issue.get(
                                        "column",
                                        "N/A",
                                    )
                                )
                                for issue in issues
                            }
                        )

                        column_filter = (
                            st.multiselect(
                                "Column",
                                issue_columns,
                                default=issue_columns,
                            )
                        )

                    filtered_issues = [
                        issue
                        for issue in issues
                        if (
                            str(
                                issue.get(
                                    "severity",
                                    "LOW",
                                )
                            )
                            in severity_filter
                            and str(
                                issue.get(
                                    "column",
                                    "N/A",
                                )
                            )
                            in column_filter
                        )
                    ]

                    issue_rows = []

                    for issue in filtered_issues:

                        issue_rows.append(
                            {
                                "Issue": issue.get(
                                    "rule",
                                    "",
                                ),
                                "Column": issue.get(
                                    "column",
                                    "",
                                ),
                                "Severity": issue.get(
                                    "severity",
                                    "",
                                ),
                                "Failed Rows": issue.get(
                                    "failed_rows",
                                    0,
                                ),
                                "Failure Rate": issue.get(
                                    "failure_rate",
                                    "",
                                ),
                                "Affected Records": (
                                    format_affected_records(
                                        issue.get(
                                            "affected_records",
                                            [],
                                        )
                                    )
                                ),
                            }
                        )

                    issues_df = pd.DataFrame(
                        issue_rows
                    )

                    st.caption(
                        f"Showing "
                        f"{len(filtered_issues)} "
                        f"of {len(issues)} "
                        f"issue entries."
                    )

                    st.dataframe(
                        issues_df,
                        use_container_width=True,
                        hide_index=True,
                    )

                    st.download_button(
                        "⬇️ Download Quality Report",
                        data=(
                            pd.DataFrame(
                                [
                                    {
                                        "Issue": issue.get(
                                            "rule",
                                            "",
                                        ),
                                        "Column": issue.get(
                                            "column",
                                            "",
                                        ),
                                        "Severity": issue.get(
                                            "severity",
                                            "",
                                        ),
                                        "Failed Rows": issue.get(
                                            "failed_rows",
                                            0,
                                        ),
                                        "Failure Rate": issue.get(
                                            "failure_rate",
                                            "",
                                        ),
                                        "Affected Records": (
                                            format_affected_records(
                                                issue.get(
                                                    "affected_records",
                                                    [],
                                                )
                                            )
                                        ),
                                    }
                                    for issue in issues
                                ]
                            )
                            .to_csv(
                                index=False
                            )
                            .encode(
                                "utf-8"
                            )
                        ),
                        file_name=(
                            "data_quality_report.csv"
                        ),
                        mime="text/csv",
                        use_container_width=True,
                    )

                if row_issues:

                    st.markdown(
                        "### 📍 Exact Problem Records"
                    )

                    row_issues_df = (
                        pd.DataFrame(
                            row_issues
                        )
                    )

                    st.dataframe(
                        row_issues_df,
                        use_container_width=True,
                        hide_index=True,
                    )

                    st.download_button(
                        "⬇️ Download Exact Problem Records",
                        data=(
                            row_issues_df
                            .to_csv(
                                index=False
                            )
                            .encode(
                                "utf-8"
                            )
                        ),
                        file_name=(
                            "problem_records.csv"
                        ),
                        mime="text/csv",
                        use_container_width=True,
                    )


            # ====================================================
            # REMEDIATION
            # ====================================================

            if active_results_view == "🛠 Remediation":

                st.caption(
                    "Nothing changes until you "
                    "approve an action. The original "
                    "uploaded file remains unchanged."
                )

                recipe_policies = (
                    st.session_state.get(
                        "recipe_action_policies",
                        [],
                    )
                )

                matching_recipe_actions = []

                for policy in recipe_policies:

                    matching_issue = next(
                        (
                            candidate
                            for candidate
                            in issues
                            if (
                                str(
                                    candidate.get(
                                        "rule"
                                    )
                                )
                                == str(
                                    policy.get(
                                        "rule"
                                    )
                                )
                                and str(
                                    candidate.get(
                                        "column"
                                    )
                                )
                                == str(
                                    policy.get(
                                        "column"
                                    )
                                )
                                and policy.get(
                                    "action"
                                )
                                in candidate.get(
                                    "fix_options",
                                    [],
                                )
                                and is_automatic_fix(
                                    policy.get(
                                        "action",
                                        "",
                                    )
                                )
                            )
                        ),
                        None,
                    )

                    if matching_issue:
                        matching_recipe_actions.append(
                            {
                                "rule": policy.get(
                                    "rule"
                                ),
                                "column": policy.get(
                                    "column"
                                ),
                                "action": policy.get(
                                    "action"
                                ),
                                "failed_rows": (
                                    matching_issue.get(
                                        "failed_rows",
                                        0,
                                    )
                                ),
                            }
                        )

                if matching_recipe_actions:

                    with st.expander(
                        "♻️ Apply Saved Recipe Actions",
                        expanded=False,
                    ):

                        st.write(
                            "These are reusable automatic actions saved "
                            "from a previous approved cleaning recipe."
                        )

                        st.dataframe(
                            pd.DataFrame(
                                matching_recipe_actions
                            ),
                            use_container_width=True,
                            hide_index=True,
                        )

                        recipe_action_confirm = st.checkbox(
                            "I reviewed these recipe actions and approve them.",
                            key=(
                                f"recipe_action_confirm_"
                                f"{dataset_key}"
                            ),
                        )

                        if st.button(
                            "♻️ Apply Recipe Actions & Revalidate",
                            use_container_width=True,
                            disabled=(
                                not recipe_action_confirm
                            ),
                            key=(
                                f"apply_recipe_actions_"
                                f"{dataset_key}"
                            ),
                        ):

                            recipe_before_df = (
                                st.session_state[
                                    "cleaned_df"
                                ].copy()
                            )

                            recipe_before_report = (
                                st.session_state[
                                    "quality_report"
                                ]
                            )

                            current_df = (
                                recipe_before_df.copy()
                            )

                            current_report = (
                                recipe_before_report
                            )

                            recipe_history = []

                            for policy in matching_recipe_actions:

                                current_issue = next(
                                    (
                                        candidate
                                        for candidate
                                        in current_report.get(
                                            "issues",
                                            [],
                                        )
                                        if (
                                            str(
                                                candidate.get(
                                                    "rule"
                                                )
                                            )
                                            == str(
                                                policy[
                                                    "rule"
                                                ]
                                            )
                                            and str(
                                                candidate.get(
                                                    "column"
                                                )
                                            )
                                            == str(
                                                policy[
                                                    "column"
                                                ]
                                            )
                                        )
                                    ),
                                    None,
                                )

                                if not current_issue:
                                    continue

                                before_failed = int(
                                    current_issue.get(
                                        "failed_rows",
                                        0,
                                    )
                                    or 0
                                )

                                candidate_df, message = (
                                    apply_fix(
                                        current_df,
                                        current_issue,
                                        policy[
                                            "action"
                                        ],
                                    )
                                )

                                if candidate_df.equals(
                                    current_df
                                ):
                                    continue

                                current_df = candidate_df

                                current_report = (
                                    run_current_quality_checks(
                                        current_df,
                                        industry,
                                        primary_key,
                                    )
                                )

                                after_issue = next(
                                    (
                                        candidate
                                        for candidate
                                        in current_report.get(
                                            "issues",
                                            [],
                                        )
                                        if (
                                            str(
                                                candidate.get(
                                                    "rule"
                                                )
                                            )
                                            == str(
                                                policy[
                                                    "rule"
                                                ]
                                            )
                                            and str(
                                                candidate.get(
                                                    "column"
                                                )
                                            )
                                            == str(
                                                policy[
                                                    "column"
                                                ]
                                            )
                                        )
                                    ),
                                    None,
                                )

                                after_failed = (
                                    int(
                                        after_issue.get(
                                            "failed_rows",
                                            0,
                                        )
                                        or 0
                                    )
                                    if after_issue
                                    else 0
                                )

                                recipe_history.append(
                                    {
                                        "rule": policy[
                                            "rule"
                                        ],
                                        "column": policy[
                                            "column"
                                        ],
                                        "action": policy[
                                            "action"
                                        ],
                                        "data_changed": True,
                                        "failed_before": (
                                            before_failed
                                        ),
                                        "failed_after": (
                                            after_failed
                                        ),
                                        "status": (
                                            "CLEAN"
                                            if after_failed
                                            == 0
                                            else "UPDATED"
                                        ),
                                        "message": message,
                                    }
                                )

                            if current_df.equals(
                                recipe_before_df
                            ):
                                st.info(
                                    "The saved recipe actions did not require "
                                    "any changes on this dataset."
                                )
                            else:

                                st.session_state.setdefault(
                                    "undo_stack",
                                    [],
                                ).append(
                                    recipe_before_df
                                )

                                st.session_state[
                                    "cleaned_df"
                                ] = current_df

                                st.session_state[
                                    "quality_report"
                                ] = current_report

                                st.session_state.setdefault(
                                    "remediation_history",
                                    [],
                                ).extend(
                                    recipe_history
                                )

                                st.session_state[
                                    "last_change"
                                ] = {
                                    "rule": (
                                        "RECIPE_ACTION_BATCH"
                                    ),
                                    "column": (
                                        "Multiple"
                                    ),
                                    "action": (
                                        "Apply Saved Recipe Actions"
                                    ),
                                    "message": (
                                        f"{len(recipe_history)} saved "
                                        "automatic action(s) were applied "
                                        "and revalidated."
                                    ),
                                    "data_changed": True,
                                    "before_rows": len(
                                        recipe_before_df
                                    ),
                                    "after_rows": len(
                                        current_df
                                    ),
                                    "row_delta": (
                                        len(current_df)
                                        - len(recipe_before_df)
                                    ),
                                    "before_failed": (
                                        recipe_before_report.get(
                                            "total_failed_checks",
                                            0,
                                        )
                                    ),
                                    "after_failed": (
                                        current_report.get(
                                            "total_failed_checks",
                                            0,
                                        )
                                    ),
                                    "resolved": (
                                        current_report.get(
                                            "total_issues",
                                            0,
                                        )
                                        == 0
                                    ),
                                    "after_failure_rate": (
                                        f"{current_report.get('bad_row_rate', 0)}%"
                                    ),
                                    "before_preview": (
                                        pd.DataFrame()
                                    ),
                                    "after_preview": (
                                        pd.DataFrame()
                                    ),
                                }

                                st.session_state[
                                    "last_fix_message"
                                ] = (
                                    "✅ Saved recipe actions were applied "
                                    "and revalidated."
                                )

                                st.rerun()

                safe_plan = get_safe_fix_plan(
                    issues
                )

                with st.expander(
                    "🪄 Fix All Safe Issues",
                    expanded=False,
                ):

                    st.write(
                        "Preview deterministic fixes that do not invent "
                        "replacement values. Invalid values may be converted "
                        "to NULL, which can intentionally surface a missing-value "
                        "issue during the next validation."
                    )

                    if safe_plan:

                        st.dataframe(
                            pd.DataFrame(
                                safe_plan
                            ),
                            use_container_width=True,
                            hide_index=True,
                        )

                        safe_confirm = st.checkbox(
                            (
                                "I reviewed the safe-fix plan "
                                "and approve these changes."
                            ),
                            key=(
                                f"safe_fix_confirm_"
                                f"{dataset_key}"
                            ),
                        )

                        if st.button(
                            "🪄 Apply All Safe Fixes & Revalidate",
                            type="primary",
                            use_container_width=True,
                            disabled=(
                                not safe_confirm
                            ),
                            key=(
                                f"apply_all_safe_"
                                f"{dataset_key}"
                            ),
                        ):

                            batch_before_df = (
                                st.session_state[
                                    "cleaned_df"
                                ].copy()
                            )

                            batch_before_report = (
                                st.session_state[
                                    "quality_report"
                                ]
                            )

                            current_df = (
                                batch_before_df.copy()
                            )

                            current_report = (
                                batch_before_report
                            )

                            batch_history = []

                            for plan_item in safe_plan:

                                current_issue = next(
                                    (
                                        candidate
                                        for candidate
                                        in current_report.get(
                                            "issues",
                                            [],
                                        )
                                        if (
                                            str(
                                                candidate.get(
                                                    "rule"
                                                )
                                            )
                                            == str(
                                                plan_item[
                                                    "rule"
                                                ]
                                            )
                                            and str(
                                                candidate.get(
                                                    "column"
                                                )
                                            )
                                            == str(
                                                plan_item[
                                                    "column"
                                                ]
                                            )
                                        )
                                    ),
                                    None,
                                )

                                if not current_issue:
                                    continue

                                before_failed = int(
                                    current_issue.get(
                                        "failed_rows",
                                        0,
                                    )
                                    or 0
                                )

                                candidate_df, message = (
                                    apply_fix(
                                        current_df,
                                        current_issue,
                                        plan_item[
                                            "action"
                                        ],
                                    )
                                )

                                if candidate_df.equals(
                                    current_df
                                ):
                                    continue

                                current_df = (
                                    candidate_df
                                )

                                current_report = (
                                    run_current_quality_checks(
                                        current_df,
                                        industry,
                                        primary_key,
                                    )
                                )

                                after_issue = next(
                                    (
                                        candidate
                                        for candidate
                                        in current_report.get(
                                            "issues",
                                            [],
                                        )
                                        if (
                                            str(
                                                candidate.get(
                                                    "rule"
                                                )
                                            )
                                            == str(
                                                plan_item[
                                                    "rule"
                                                ]
                                            )
                                            and str(
                                                candidate.get(
                                                    "column"
                                                )
                                            )
                                            == str(
                                                plan_item[
                                                    "column"
                                                ]
                                            )
                                        )
                                    ),
                                    None,
                                )

                                after_failed = (
                                    int(
                                        after_issue.get(
                                            "failed_rows",
                                            0,
                                        )
                                        or 0
                                    )
                                    if after_issue
                                    else 0
                                )

                                batch_history.append(
                                    {
                                        "rule": plan_item[
                                            "rule"
                                        ],
                                        "column": plan_item[
                                            "column"
                                        ],
                                        "action": (
                                            "Fix All Safe Issues · "
                                            + plan_item[
                                                "action"
                                            ]
                                        ),
                                        "data_changed": True,
                                        "failed_before": (
                                            before_failed
                                        ),
                                        "failed_after": (
                                            after_failed
                                        ),
                                        "status": (
                                            "CLEAN"
                                            if after_failed
                                            == 0
                                            else "UPDATED"
                                        ),
                                        "message": message,
                                    }
                                )

                            if current_df.equals(
                                batch_before_df
                            ):

                                st.info(
                                    "No safe automatic changes were required."
                                )

                            else:

                                st.session_state.setdefault(
                                    "undo_stack",
                                    [],
                                ).append(
                                    batch_before_df
                                )

                                st.session_state[
                                    "cleaned_df"
                                ] = current_df

                                st.session_state[
                                    "quality_report"
                                ] = current_report

                                st.session_state.setdefault(
                                    "remediation_history",
                                    [],
                                ).extend(
                                    batch_history
                                )

                                st.session_state[
                                    "last_change"
                                ] = {
                                    "rule": (
                                        "SAFE_FIX_BATCH"
                                    ),
                                    "column": (
                                        "Multiple"
                                    ),
                                    "action": (
                                        "Fix All Safe Issues"
                                    ),
                                    "message": (
                                        f"{len(batch_history)} safe "
                                        "remediation action(s) were applied "
                                        "and revalidated."
                                    ),
                                    "data_changed": True,
                                    "before_rows": len(
                                        batch_before_df
                                    ),
                                    "after_rows": len(
                                        current_df
                                    ),
                                    "row_delta": (
                                        len(
                                            current_df
                                        )
                                        - len(
                                            batch_before_df
                                        )
                                    ),
                                    "before_failed": (
                                        batch_before_report.get(
                                            "total_failed_checks",
                                            0,
                                        )
                                    ),
                                    "after_failed": (
                                        current_report.get(
                                            "total_failed_checks",
                                            0,
                                        )
                                    ),
                                    "resolved": (
                                        current_report.get(
                                            "total_issues",
                                            0,
                                        )
                                        == 0
                                    ),
                                    "after_failure_rate": (
                                        f"{current_report.get('bad_row_rate', 0)}%"
                                    ),
                                    "before_preview": (
                                        pd.DataFrame()
                                    ),
                                    "after_preview": (
                                        pd.DataFrame()
                                    ),
                                }

                                st.session_state[
                                    "last_fix_message"
                                ] = (
                                    "✅ Safe-fix batch completed "
                                    "and revalidated."
                                )

                                st.rerun()

                    else:
                        st.success(
                            "No deterministic safe-fix candidates are currently available."
                        )

                render_latest_change(
                    st.session_state.get(
                        "last_change"
                    )
                )

                undo_stack = (
                    st.session_state.setdefault(
                        "undo_stack",
                        [],
                    )
                )

                if history:

                    action1, action2 = (
                        st.columns(2)
                    )

                    with action1:

                        if st.button(
                            "↩️ Undo Last Approved Action",
                            use_container_width=True,
                            disabled=(
                                len(undo_stack) == 0
                            ),
                        ):

                            current_df = (
                                st.session_state[
                                    "cleaned_df"
                                ].copy()
                            )

                            previous_df = (
                                st.session_state[
                                    "undo_stack"
                                ].pop()
                            )

                            undone_history = None

                            if st.session_state[
                                "remediation_history"
                            ]:
                                undone_history = (
                                    st.session_state[
                                        "remediation_history"
                                    ].pop()
                                )

                            restored_report = (
                                run_current_quality_checks(
                                    previous_df,
                                    industry,
                                    primary_key,
                                )
                            )

                            st.session_state[
                                "cleaned_df"
                            ] = previous_df

                            st.session_state[
                                "quality_report"
                            ] = restored_report

                            st.session_state.pop(
                                "last_change",
                                None,
                            )

                            st.session_state[
                                "last_fix_message"
                            ] = (
                                "↩️ Last approved action "
                                "was undone. Original "
                                "uploaded data remains unchanged."
                            )

                            st.rerun()

                    with action2:

                        if st.button(
                            "🔄 Reset All Approved Changes",
                            use_container_width=True,
                        ):

                            original_report = (
                                run_current_quality_checks(
                                    df,
                                    industry,
                                    primary_key,
                                )
                            )

                            st.session_state[
                                "cleaned_df"
                            ] = df.copy()

                            st.session_state[
                                "baseline_report"
                            ] = original_report

                            st.session_state[
                                "quality_report"
                            ] = original_report

                            st.session_state[
                                "remediation_history"
                            ] = []

                            st.session_state[
                                "undo_stack"
                            ] = []

                            st.session_state.pop(
                                "last_change",
                                None,
                            )

                            st.session_state[
                                "last_fix_message"
                            ] = (
                                "🔄 Working copy reset "
                                "to the original uploaded dataset."
                            )

                            st.rerun()

                if not issues:

                    st.success(
                        "No remediation is required."
                    )

                else:

                    for number, issue in enumerate(
                        issues,
                        start=1,
                    ):

                        severity_value = (
                            issue.get(
                                "severity",
                                "LOW",
                            )
                        )

                        icon = {
                            "CRITICAL": "🔴",
                            "HIGH": "🟠",
                            "MEDIUM": "🟡",
                            "LOW": "🟢",
                        }.get(
                            severity_value,
                            "⚪",
                        )

                        title = (
                            f"{icon} {number}. "
                            f"{issue.get('rule', 'Issue')} "
                            f"→ "
                            f"{issue.get('column', 'N/A')}"
                        )

                        with st.expander(
                            title
                        ):

                            i1, i2, i3 = (
                                st.columns(3)
                            )

                            i1.metric(
                                "Severity",
                                severity_value,
                            )

                            i2.metric(
                                "Failed Rows",
                                issue.get(
                                    "failed_rows",
                                    0,
                                ),
                            )

                            i3.metric(
                                "Failure Rate",
                                issue.get(
                                    "failure_rate",
                                    "0%",
                                ),
                            )

                            affected = (
                                issue.get(
                                    "affected_records",
                                    [],
                                )
                            )

                            if affected:

                                st.write(
                                    "**Affected Records:**"
                                )

                                st.code(
                                    format_affected_records(
                                        affected,
                                        limit=50,
                                    )
                                )

                            examples = issue.get(
                                "examples",
                                [],
                            )

                            if examples:

                                st.write(
                                    "**Example Problem Values:**"
                                )

                                st.write(
                                    examples
                                )

                            st.markdown(
                                "#### 🧹 Cleaning Recommendation"
                            )

                            detail1, detail2 = st.columns(2)

                            with detail1:
                                st.write(
                                    "**Detected problem**"
                                )
                                st.write(
                                    f"{issue.get('rule', 'Issue')} "
                                    f"in `{issue.get('column', 'N/A')}`"
                                )

                            with detail2:
                                st.write(
                                    "**Recommended approach**"
                                )
                                st.write(
                                    issue.get(
                                        "suggestion",
                                        (
                                            "Review this issue "
                                            "before applying changes."
                                        ),
                                    )
                                )

                            st.caption(
                                "Choose a recommended action below, "
                                "or use Direct Cleaning Tools to enter "
                                "verified corrections yourself."
                            )

                            fix_options = (
                                issue.get(
                                    "fix_options",
                                    [],
                                )
                            )

                            if (
                                "DUPLICATE_PRIMARY_KEY"
                                in str(
                                    issue.get(
                                        "rule",
                                        "",
                                    )
                                ).upper()
                                and str(
                                    issue.get(
                                        "column",
                                        "",
                                    )
                                ) != "ALL"
                            ):
                                st.info(
                                    "🔑 **Merge by "
                                    f"{issue.get('column')}** — "
                                    "one row will remain for each duplicate key. "
                                    "The first row is retained, missing values are "
                                    "filled from later duplicates, and conflicting "
                                    "non-null values keep the first row's value."
                                )

                            if fix_options:

                                selected_fix = (
                                    st.radio(
                                        "Choose an action",
                                        fix_options,
                                        key=(
                                            f"fix_"
                                            f"{number}_"
                                            f"{issue.get('rule')}_"
                                            f"{issue.get('column')}"
                                        ),
                                    )
                                )

                                automatic_action = (
                                    is_automatic_fix(
                                        selected_fix
                                    )
                                )

                                if automatic_action:
                                    st.info(
                                        "⚙️ **Automatic fix:** "
                                        "the protected working copy will be updated, "
                                        "quality checks will run again, and the app "
                                        "will verify the Before → After result."
                                    )
                                    action_button_label = (
                                        "✅ Apply & Verify Change"
                                    )
                                else:
                                    st.warning(
                                        "👤 **Manual / external-source action:** "
                                        "the app will record your decision, but it "
                                        "will not invent or automatically change data."
                                    )
                                    action_button_label = (
                                        "📌 Record Selected Decision"
                                    )

                                if st.button(
                                    action_button_label,
                                    key=(
                                        f"approve_"
                                        f"{number}_"
                                        f"{issue.get('rule')}_"
                                        f"{issue.get('column')}"
                                    ),
                                    use_container_width=True,
                                ):

                                    before_df = (
                                        st.session_state[
                                            "cleaned_df"
                                        ].copy()
                                    )

                                    cleaned_df, message = (
                                        apply_fix(
                                            before_df,
                                            issue,
                                            selected_fix,
                                        )
                                    )

                                    data_changed = (
                                        not cleaned_df.equals(
                                            before_df
                                        )
                                    )

                                    # Verify every automatic remediation.
                                    # If a rule reports failures and the selected
                                    # automatic action produces no DataFrame change,
                                    # do not record it as successful.
                                    if (
                                        automatic_action
                                        and not data_changed
                                        and int(
                                            issue.get(
                                                "failed_rows",
                                                0,
                                            )
                                            or 0
                                        ) > 0
                                    ):
                                        st.session_state[
                                            "last_fix_message"
                                        ] = (
                                            "❌ Automatic remediation was not applied. "
                                            f"Action: {selected_fix}. "
                                            "The working data did not change, so the "
                                            "operation was not recorded as successful."
                                        )

                                        st.rerun()

                                    # Only true data-changing actions belong on the
                                    # undo stack. Manual decisions intentionally do not.
                                    if (
                                        automatic_action
                                        and data_changed
                                    ):
                                        st.session_state[
                                            "undo_stack"
                                        ].append(
                                            before_df.copy()
                                        )

                                    after_report = (
                                        run_current_quality_checks(
                                            cleaned_df,
                                            industry,
                                            primary_key,
                                        )
                                    )

                                    change_summary = (
                                        _build_change_summary(
                                            before_df=before_df,
                                            after_df=cleaned_df,
                                            issue=issue,
                                            action=selected_fix,
                                            message=message,
                                            after_report=after_report,
                                        )
                                    )

                                    st.session_state[
                                        "cleaned_df"
                                    ] = cleaned_df

                                    st.session_state[
                                        "quality_report"
                                    ] = after_report

                                    st.session_state[
                                        "last_change"
                                    ] = change_summary

                                    st.session_state.setdefault(
                                        "remediation_history",
                                        [],
                                    ).append(
                                        {
                                            "rule": issue.get(
                                                "rule"
                                            ),
                                            "column": issue.get(
                                                "column"
                                            ),
                                            "action": selected_fix,
                                            "data_changed": (
                                                data_changed
                                            ),
                                            "failed_before": (
                                                change_summary[
                                                    "before_failed"
                                                ]
                                            ),
                                            "failed_after": (
                                                change_summary[
                                                    "after_failed"
                                                ]
                                            ),
                                            "status": (
                                                "MANUAL DECISION"
                                                if not automatic_action
                                                else (
                                                    "CLEAN"
                                                    if change_summary[
                                                        "resolved"
                                                    ]
                                                    else (
                                                        "UPDATED"
                                                        if data_changed
                                                        else "FAILED"
                                                    )
                                                )
                                            ),
                                            "message": message,
                                        }
                                    )

                                    st.session_state[
                                        "last_fix_message"
                                    ] = (
                                        (
                                            "✅ "
                                            if automatic_action
                                            else "📌 "
                                        )
                                        + message
                                        + " Original uploaded "
                                        "data remains unchanged."
                                    )

                                    st.rerun()

                            # ------------------------------------------------
                            # USER-CONTROLLED DIRECT CLEANING
                            # ------------------------------------------------
                            render_direct_cleaning_tools(
                                issue=issue,
                                issue_number=number,
                                working_df=working_df,
                                industry=industry,
                                primary_key=primary_key,
                            )

                    history = (
                        st.session_state.get(
                            "remediation_history",
                            [],
                        )
                    )

                    if history:

                        st.markdown(
                            "### 📋 Approved Action History"
                        )

                        st.dataframe(
                            pd.DataFrame(
                                history
                            ),
                            use_container_width=True,
                            hide_index=True,
                        )

                # If all detected issues have been resolved,
                # offer the final cleaned dataset immediately
                # without making the user switch tabs.
                if (
                    int(
                        report.get(
                            "total_issues",
                            0,
                        )
                        or 0
                    ) == 0
                    and int(
                        report.get(
                            "unique_bad_rows",
                            0,
                        )
                        or 0
                    ) == 0
                ):
                    st.divider()

                    render_clean_dataset_download(
                        working_df,
                        report,
                        Path(
                            uploaded_file.name
                        ).stem,
                    )


            # ====================================================
            # WORKING DATA
            # ====================================================

            if active_results_view == "✨ Working Data":

                st.caption(
                    "This is the protected working copy. "
                    "The original uploaded file remains unchanged."
                )

                render_latest_change(
                    st.session_state.get(
                        "last_change"
                    ),
                    title="Latest Data Update",
                )

                st.markdown(
                    "### 📋 Current Working Dataset"
                )

                st.dataframe(
                    working_df.head(100),
                    use_container_width=True,
                    hide_index=True,
                )

                base_name = Path(
                    uploaded_file.name
                ).stem

                render_clean_dataset_download(
                    working_df,
                    report,
                    base_name,
                )


            # ====================================================
            # SCHEMA
            # ====================================================

            if active_results_view == "🧬 Schema":

                schema_df = pd.DataFrame(
                    {
                        "Column": (
                            working_df.columns
                        ),
                        "Data Type": [
                            str(dtype)
                            for dtype
                            in working_df.dtypes
                        ],
                        "Null Count": [
                            int(
                                working_df[
                                    column
                                ]
                                .isna()
                                .sum()
                            )
                            for column
                            in working_df.columns
                        ],
                        "Unique Values": [
                            int(
                                working_df[
                                    column
                                ].nunique(
                                    dropna=True
                                )
                            )
                            for column
                            in working_df.columns
                        ],
                    }
                )

                st.dataframe(
                    schema_df,
                    use_container_width=True,
                    hide_index=True,
                )

                st.download_button(
                    "⬇️ Download Schema Summary",
                    data=(
                        schema_df
                        .to_csv(
                            index=False
                        )
                        .encode(
                            "utf-8"
                        )
                    ),
                    file_name=(
                        "schema_summary.csv"
                    ),
                    mime="text/csv",
                    use_container_width=True,
                )


            # ====================================================
            # FINAL SUMMARY + AUDIT
            # ====================================================

            if active_results_view == "✅ Final Summary":

                render_section_header(
                    "Final Cleaning Summary",
                    "✅",
                )

                before_score = float(
                    baseline_report.get(
                        "quality_score",
                        0,
                    )
                    or 0
                )

                final_score = float(
                    report.get(
                        "quality_score",
                        0,
                    )
                    or 0
                )

                before_rows = int(
                    baseline_report.get(
                        "rows",
                        len(df),
                    )
                    or 0
                )

                final_rows = int(
                    report.get(
                        "rows",
                        len(working_df),
                    )
                    or 0
                )

                fully_clean = (
                    int(
                        report.get(
                            "total_issues",
                            0,
                        )
                        or 0
                    )
                    == 0
                    and int(
                        report.get(
                            "unique_bad_rows",
                            0,
                        )
                        or 0
                    )
                    == 0
                )

                f1, f2, f3, f4 = st.columns(
                    4
                )

                f1.metric(
                    "Quality Score",
                    f"{final_score}/100",
                    delta=round(
                        final_score
                        - before_score,
                        2,
                    ),
                )

                f2.metric(
                    "Rows",
                    final_rows,
                    delta=(
                        final_rows
                        - before_rows
                    ),
                )

                f3.metric(
                    "Remaining Issues",
                    report.get(
                        "total_issues",
                        0,
                    ),
                    delta=(
                        int(
                            report.get(
                                "total_issues",
                                0,
                            )
                            or 0
                        )
                        - int(
                            baseline_report.get(
                                "total_issues",
                                0,
                            )
                            or 0
                        )
                    ),
                    delta_color="inverse",
                )

                f4.metric(
                    "Rows With Problems",
                    report.get(
                        "unique_bad_rows",
                        0,
                    ),
                    delta=(
                        int(
                            report.get(
                                "unique_bad_rows",
                                0,
                            )
                            or 0
                        )
                        - int(
                            baseline_report.get(
                                "unique_bad_rows",
                                0,
                            )
                            or 0
                        )
                    ),
                    delta_color="inverse",
                )

                s1, s2, s3, s4 = st.columns(
                    4
                )

                s1.metric(
                    "Rows Removed",
                    max(
                        0,
                        before_rows
                        - final_rows,
                    ),
                )

                s2.metric(
                    "Approved Actions",
                    len(
                        history
                    ),
                )

                s3.metric(
                    "Failed Checks",
                    report.get(
                        "total_failed_checks",
                        0,
                    ),
                    delta=(
                        int(
                            report.get(
                                "total_failed_checks",
                                0,
                            )
                            or 0
                        )
                        - int(
                            baseline_report.get(
                                "total_failed_checks",
                                0,
                            )
                            or 0
                        )
                    ),
                    delta_color="inverse",
                )

                s4.metric(
                    "Custom Rules",
                    len(
                        st.session_state.get(
                            "custom_rules",
                            [],
                        )
                    ),
                )

                if fully_clean:

                    st.success(
                        "✅ Dataset cleaned successfully. "
                        "Final deterministic validation passed."
                    )

                else:

                    st.warning(
                        "⚠️ Review required. "
                        f"{report.get('total_issues', 0)} issue rule(s) "
                        f"remain across {report.get('unique_bad_rows', 0)} row(s)."
                    )

                    remaining_preview = []

                    for remaining_issue in issues[:10]:
                        remaining_preview.append(
                            {
                                "Severity": (
                                    remaining_issue.get(
                                        "severity"
                                    )
                                ),
                                "Rule": (
                                    remaining_issue.get(
                                        "rule"
                                    )
                                ),
                                "Column": (
                                    remaining_issue.get(
                                        "column"
                                    )
                                ),
                                "Failed Rows": (
                                    remaining_issue.get(
                                        "failed_rows",
                                        0,
                                    )
                                ),
                            }
                        )

                    if remaining_preview:
                        st.dataframe(
                            pd.DataFrame(
                                remaining_preview
                            ),
                            use_container_width=True,
                            hide_index=True,
                        )

                    if st.button(
                        "🛠 Continue Fixing Remaining Issues",
                        use_container_width=True,
                        key=(
                            f"continue_remediation_"
                            f"{dataset_key}"
                        ),
                    ):
                        st.session_state[
                            "results_view"
                        ] = "🛠 Remediation"

                        st.rerun()

                st.markdown(
                    "### 📜 Audit Report"
                )

                audit_markdown = (
                    build_audit_markdown(
                        dataset_name=(
                            uploaded_file.name
                        ),
                        industry=industry,
                        primary_key=primary_key,
                        baseline_report=(
                            baseline_report
                        ),
                        final_report=report,
                        remediation_history=(
                            history
                        ),
                        custom_rules=(
                            st.session_state.get(
                                "custom_rules",
                                [],
                            )
                        ),
                        schema_contract=(
                            st.session_state.get(
                                "schema_contract"
                            )
                        ),
                    )
                )

                audit1, audit2 = st.columns(
                    2
                )

                with audit1:
                    st.download_button(
                        "⬇️ Download Audit Report (Markdown)",
                        data=audit_markdown.encode(
                            "utf-8"
                        ),
                        file_name=(
                            f"{Path(uploaded_file.name).stem}"
                            "_quality_audit.md"
                        ),
                        mime="text/markdown",
                        use_container_width=True,
                        key=(
                            f"download_audit_md_"
                            f"{dataset_key}"
                        ),
                    )

                with audit2:
                    st.download_button(
                        "⬇️ Download Final Quality Report (JSON)",
                        data=json.dumps(
                            report,
                            indent=2,
                            default=str,
                        ).encode(
                            "utf-8"
                        ),
                        file_name=(
                            f"{Path(uploaded_file.name).stem}"
                            "_quality_report.json"
                        ),
                        mime="application/json",
                        use_container_width=True,
                        key=(
                            f"download_final_report_"
                            f"{dataset_key}"
                        ),
                    )

                st.divider()

                render_clean_dataset_download(
                    working_df,
                    report,
                    Path(
                        uploaded_file.name
                    ).stem,
                )


    except Exception as error:

        st.error(
            f"Error processing dataset: "
            f"{error}"
        )


# ============================================================
# AI COPILOT
# ============================================================

render_ai_copilot(
    page_name="Data Quality Copilot",
    page_context=(
        PAGE_CONTEXTS[
            "Data Quality Copilot"
        ]
    ),
    industry=industry,
)
