import pytest

from report_stays.file_validator import (
    validate_file_has_all_the_columns,
    validate_filtered_report_stay,
)
from report_stays.report_stays_columns import (
    get_all_excel_columns,
    get_renamed_columns_to_use,
)


class TestValidateFileHasAllTheColumns:
    """Unit-tests for `validate_file_has_all_the_columns`."""

    def test_success_when_all_columns_are_present(self, excel_df):
        # Should **not** raise
        validate_file_has_all_the_columns(excel_df)

    def test_raise_when_a_column_is_missing(self, excel_df):
        missing_col = get_all_excel_columns()[-1]
        df_without_column = excel_df.drop(columns=[missing_col])

        with pytest.raises(Exception) as exc_info:
            validate_file_has_all_the_columns(df_without_column)

        # Error message should mention the missing column name for debugging
        assert missing_col in str(exc_info.value)


class TestValidateFilteredReportStay:
    """Unit-tests for `validate_filtered_report_stay`."""

    def test_success_with_valid_dataframe(self, valid_report_stay_df):
        # Should **not** raise
        validate_filtered_report_stay(valid_report_stay_df)

    @pytest.mark.parametrize("invalid_value", [-1, 1_000_001])
    def test_raise_with_out_of_range_numeric(self, valid_report_stay_df, numeric_col, invalid_value):
        df = valid_report_stay_df.copy()
        df.loc[0, numeric_col] = invalid_value

        with pytest.raises(Exception):
            validate_filtered_report_stay(df)

    def test_raise_with_invalid_date_format(self, valid_report_stay_df, datetime_col):
        df = valid_report_stay_df.copy()
        # Wrong format – validator expects DD/MM/YYYY
        df.loc[0, datetime_col] = "2023-01-01"

        with pytest.raises(Exception):
            validate_filtered_report_stay(df)

    def test_raise_when_header_is_missing_column(self, valid_report_stay_df):
        missing_col = get_renamed_columns_to_use()[0]
        df_without_column = valid_report_stay_df.drop(columns=[missing_col])

        with pytest.raises(Exception):
            validate_filtered_report_stay(df_without_column) 