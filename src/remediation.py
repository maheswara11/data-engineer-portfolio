from __future__ import annotations

import pandas as pd


NO_CHANGE_OPTIONS = frozenset({
    "Keep as NULL",
    "Keep original value",
    "Keep blank if valid",
    "Keep for manual review",
    "Keep all if duplicates are valid",
    "Review manually",
    "Retrieve value from trusted source",
    "Retrieve correct value from source",
    "Retrieve correct ID from source",
    "Replace with approved default",
    "Correct from trusted source",
    "Correct from source system",
    "Correct from billing source",
    "Correct from transaction source",
    "Correct admission/discharge dates from source",
    "Investigate source-system duplication",
})

AUTOMATIC_FIX_OPTIONS = frozenset({
    "Convert blank to NULL",
    "Set affected values to NULL after approval",
    "Remove affected rows after approval",
    "Keep first occurrence",
    "Keep last occurrence",
    "Merge duplicate records",
})


def is_automatic_fix(selected_fix: str) -> bool:
    """Return True only for actions that are expected to modify the working copy."""
    return str(selected_fix) in AUTOMATIC_FIX_OPTIONS


def is_manual_fix(selected_fix: str) -> bool:
    """Return True for actions that intentionally require manual/external work."""
    return str(selected_fix) in NO_CHANGE_OPTIONS



def _positions_from_records(
    df: pd.DataFrame,
    affected_records: list,
) -> list[int]:
    positions: list[int] = []

    for record in affected_records:
        if (
            isinstance(record, int)
            and 1 <= record <= len(df)
        ):
            positions.append(record - 1)

    return positions


def _is_missing_or_blank(value) -> bool:
    if pd.isna(value):
        return True

    if isinstance(value, str):
        return value.strip() == ""

    return False


def _distinct_non_missing_values(
    series: pd.Series,
) -> list:
    """
    Return distinct non-null / non-blank values while preserving order.
    """
    values: list = []

    for value in series.tolist():

        if _is_missing_or_blank(value):
            continue

        duplicate = False

        for existing in values:
            try:
                if value == existing:
                    duplicate = True
                    break
            except Exception:
                if repr(value) == repr(existing):
                    duplicate = True
                    break

        if not duplicate:
            values.append(value)

    return values


def _smart_merge_duplicate_key_groups(
    df: pd.DataFrame,
    key_column: str,
) -> tuple[pd.DataFrame, int, int, list[str]]:
    """
    Merge all duplicate groups based on the selected key column.

    Deterministic approved policy:
    - Keep the first row in each duplicate-key group as the base row.
    - If the base value is missing/blank and a later duplicate has a value,
      fill it from the later row.
    - If multiple non-null values conflict, keep the first row's value.
    - Record conflict columns in the returned message so the user can review
      what was discarded.
    - Result contains exactly one row per non-null/non-blank key.

    This behavior is only executed after the user explicitly approves
    "Merge duplicate records".
    """
    working = df.copy().reset_index(drop=True)

    if key_column not in working.columns:
        return working, 0, 0, []

    key_series = working[key_column]

    valid_key_mask = (
        key_series.notna()
        & ~key_series.astype(str).str.strip().eq("")
    )

    duplicate_mask = (
        valid_key_mask
        & key_series.duplicated(keep=False)
    )

    if not bool(duplicate_mask.any()):
        return working, 0, 0, []

    duplicate_keys = (
        working.loc[
            duplicate_mask,
            key_column,
        ]
        .drop_duplicates()
        .tolist()
    )

    output_rows: list[pd.Series] = []
    consumed_positions: set[int] = set()
    conflict_descriptions: list[str] = []
    merged_groups = 0

    # Preserve original row order by walking row positions.
    for position in working.index:

        if position in consumed_positions:
            continue

        key_value = working.at[
            position,
            key_column,
        ]

        # Missing / blank keys are not merged here.
        if _is_missing_or_blank(key_value):
            output_rows.append(
                working.loc[position].copy()
            )
            consumed_positions.add(position)
            continue

        group_positions = working.index[
            working[key_column].eq(key_value)
        ].tolist()

        if len(group_positions) <= 1:
            output_rows.append(
                working.loc[position].copy()
            )
            consumed_positions.add(position)
            continue

        # This is a duplicate-key group.
        group = working.loc[
            group_positions
        ]

        merged_row = group.iloc[0].copy()
        conflict_columns: list[str] = []

        for column in working.columns:

            if column == key_column:
                continue

            first_value = merged_row[column]

            # Fill missing/blank base value from the first later usable value.
            if _is_missing_or_blank(first_value):

                replacement_value = None

                for candidate in group[column].iloc[1:].tolist():
                    if not _is_missing_or_blank(candidate):
                        replacement_value = candidate
                        break

                if replacement_value is not None:
                    merged_row[column] = replacement_value

            # Detect conflicts among non-missing values.
            distinct_values = _distinct_non_missing_values(
                group[column]
            )

            if len(distinct_values) > 1:
                conflict_columns.append(
                    str(column)
                )

        output_rows.append(
            merged_row
        )

        consumed_positions.update(
            group_positions
        )

        merged_groups += 1

        if conflict_columns:
            conflict_descriptions.append(
                f"{key_column}={key_value}: "
                + ", ".join(conflict_columns)
            )

    merged_df = pd.DataFrame(
        output_rows,
        columns=working.columns,
    ).reset_index(drop=True)

    rows_removed = (
        len(working)
        - len(merged_df)
    )

    return (
        merged_df,
        merged_groups,
        rows_removed,
        conflict_descriptions,
    )


def apply_fix(
    df: pd.DataFrame,
    issue: dict,
    selected_fix: str,
) -> tuple[pd.DataFrame, str]:
    """
    Apply one explicitly approved remediation to a working copy only.

    The original caller DataFrame is never modified in place.
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            "df must be a pandas DataFrame"
        )

    cleaned_df = (
        df.copy()
        .reset_index(drop=True)
    )

    allowed_options = issue.get(
        "fix_options",
        [],
    )

    if (
        allowed_options
        and selected_fix
        not in allowed_options
    ):
        return cleaned_df, (
            f"Action '{selected_fix}' is "
            "not allowed for this issue. "
            "No change was applied."
        )

    column = issue.get(
        "column"
    )

    affected_records = issue.get(
        "affected_records",
        [],
    )

    positions = _positions_from_records(
        cleaned_df,
        affected_records,
    )

    # --------------------------------------------------------
    # Explicitly manual / external-data actions
    # --------------------------------------------------------

    if selected_fix in NO_CHANGE_OPTIONS:
        return cleaned_df, (
            "No automatic data change was applied. "
            "This action requires manual review, "
            "trusted external data, or a "
            "business-approved value."
        )

    # --------------------------------------------------------
    # Blank -> NULL
    # --------------------------------------------------------

    if selected_fix == "Convert blank to NULL":

        if column not in cleaned_df.columns:
            return cleaned_df, (
                f"Column '{column}' no longer exists. "
                "No change was applied."
            )

        mask = (
            cleaned_df[column].notna()
            & cleaned_df[column]
            .astype(str)
            .str.strip()
            .eq("")
        )

        changed_count = int(
            mask.sum()
        )

        cleaned_df.loc[
            mask,
            column,
        ] = pd.NA

        return cleaned_df, (
            f"{changed_count} blank value(s) "
            f"in '{column}' were converted "
            "to NULL."
        )

    # --------------------------------------------------------
    # Set affected values to NULL
    # --------------------------------------------------------

    if (
        selected_fix
        == "Set affected values to NULL after approval"
    ):

        if column not in cleaned_df.columns:
            return cleaned_df, (
                f"Column '{column}' no longer exists. "
                "No change was applied."
            )

        valid_positions = [
            position
            for position in positions
            if position in cleaned_df.index
        ]

        cleaned_df.loc[
            valid_positions,
            column,
        ] = pd.NA

        return cleaned_df, (
            f"{len(valid_positions)} affected "
            f"value(s) in '{column}' were "
            "set to NULL."
        )

    # --------------------------------------------------------
    # Remove affected rows
    # --------------------------------------------------------

    if (
        selected_fix
        == "Remove affected rows after approval"
    ):

        valid_positions = [
            position
            for position in positions
            if position in cleaned_df.index
        ]

        cleaned_df = (
            cleaned_df.drop(
                index=valid_positions
            )
            .reset_index(drop=True)
        )

        return cleaned_df, (
            f"{len(valid_positions)} affected "
            "row(s) were removed from the "
            "working copy."
        )

    # --------------------------------------------------------
    # Keep first / last duplicate
    # --------------------------------------------------------

    if selected_fix in {
        "Keep first occurrence",
        "Keep last occurrence",
    }:

        keep = (
            "first"
            if selected_fix
            == "Keep first occurrence"
            else "last"
        )

        before_rows = len(
            cleaned_df
        )

        if column == "ALL":

            cleaned_df = (
                cleaned_df.drop_duplicates(
                    keep=keep
                )
                .reset_index(drop=True)
            )

        elif column in cleaned_df.columns:

            cleaned_df = (
                cleaned_df.drop_duplicates(
                    subset=[column],
                    keep=keep,
                )
                .reset_index(drop=True)
            )

        else:

            return cleaned_df, (
                f"Column '{column}' no longer exists. "
                "No change was applied."
            )

        removed = (
            before_rows
            - len(cleaned_df)
        )

        return cleaned_df, (
            f"{removed} duplicate row(s) "
            f"were removed by keeping the "
            f"{keep} occurrence."
        )

    # --------------------------------------------------------
    # Smart merge duplicates
    # --------------------------------------------------------

    if (
        selected_fix
        == "Merge duplicate records"
    ):

        # Exact duplicate rows contain no conflicting values.
        # Retaining one identical copy is a safe merge.
        if column == "ALL":

            before_rows = len(cleaned_df)

            duplicate_mask = cleaned_df.duplicated(
                keep=False
            )

            duplicate_rows_before = int(
                duplicate_mask.sum()
            )

            cleaned_df = (
                cleaned_df
                .drop_duplicates(
                    keep="first"
                )
                .reset_index(drop=True)
            )

            removed = (
                before_rows
                - len(cleaned_df)
            )

            if duplicate_rows_before > 0 and removed == 0:
                return df.copy().reset_index(drop=True), (
                    "Merge verification failed: duplicate rows were detected, "
                    "but no rows were removed. No result was committed."
                )

            if removed == 0:
                return cleaned_df, (
                    "No exact duplicate rows remain. No data change was required."
                )

            return cleaned_df, (
                f"Merge completed: {removed} redundant duplicate row(s) "
                f"were removed from {duplicate_rows_before} duplicate record(s). "
                "One identical copy of each duplicate group was retained."
            )

        # Primary-key duplicate groups can contain complementary
        # data. Merge only groups without conflicting non-null values.
        if column in cleaned_df.columns:

            (
                merged_df,
                merged_groups,
                rows_removed,
                conflicts,
            ) = _smart_merge_duplicate_key_groups(
                cleaned_df,
                str(column),
            )

            if merged_groups == 0:

                if conflicts:
                    return cleaned_df, (
                        "No duplicate groups were "
                        "auto-merged because conflicting "
                        "non-null values were found. "
                        "Manual review is required. "
                        "Conflicts: "
                        + " | ".join(
                            conflicts[:5]
                        )
                    )

                return cleaned_df, (
                    "No mergeable duplicate groups "
                    "were found. No data change "
                    "was applied."
                )

            message = (
                f"{merged_groups} duplicate "
                f"group(s) were merged by '{column}', "
                f"removing {rows_removed} redundant row(s). "
                "The first row in each key group was retained; "
                "missing values were filled from later duplicates."
            )

            if conflicts:
                message += (
                    " Conflicting non-null values were resolved by "
                    "keeping the first row's value. Review conflicts: "
                    + " | ".join(
                        conflicts[:5]
                    )
                )

            return (
                merged_df,
                message,
            )

        return cleaned_df, (
            f"Column '{column}' no longer exists. "
            "No merge was applied."
        )

    return cleaned_df, (
        f"Unsupported remediation option: "
        f"'{selected_fix}'. No change was applied."
    )
