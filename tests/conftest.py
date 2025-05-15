import pytest
import pandas as pd

from file_columns import REPORT_STAYS_COLUMNS


@pytest.fixture(scope="session")
def excel_df() -> pd.DataFrame:
    """DataFrame that contains every column returned by `get_all_excel_columns`."""
    cols = REPORT_STAYS_COLUMNS.get_all_excel_columns()
    data = {c: ["dummy"] for c in cols}
    return pd.DataFrame(data)


@pytest.fixture(scope="session")
def valid_report_stay_df() -> pd.DataFrame:
    """DataFrame that passes `validate_filtered_report_stay`."""
    renamed_cols = REPORT_STAYS_COLUMNS.get_renamed_columns_to_use()

    numeric_default = {c: 100.0 for c in REPORT_STAYS_COLUMNS.get_numeric_columns()}
    datetime_default = {c: "01/01/2023" for c in REPORT_STAYS_COLUMNS.get_datetime_columns()}
    string_default = {c: "test" for c in REPORT_STAYS_COLUMNS.get_string_columns()}

    row = {c: None for c in renamed_cols}
    row.update({**numeric_default, **datetime_default, **string_default})

    for k, v in row.items():
        if v is None:
            row[k] = "N/A"

    return pd.DataFrame([row])


@pytest.fixture(scope="session")
def numeric_col() -> str:
    """Return one numeric column name for negative/out-of-range tests."""
    return REPORT_STAYS_COLUMNS.get_numeric_columns()[0]


@pytest.fixture(scope="session")
def datetime_col() -> str:
    """Return one datetime column name for invalid-format tests."""
    return REPORT_STAYS_COLUMNS.get_datetime_columns()[0]
