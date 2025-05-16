from collections import defaultdict
import csvvalidator
import csv
import pandas as pd
from datetime import datetime

from file_utility import save_df_to_csv, delete_file
from file_columns import FileColumns

def validate_file_has_all_the_columns(df: pd.DataFrame, file_columns: FileColumns):
    expected_columns = file_columns.get_all_excel_columns()
    visited_columns = defaultdict(int)
    assert len(expected_columns) == len(df.columns), f"Expected {len(expected_columns)} columns, got {len(df.columns)}"
    for expected_column, df_column in zip(expected_columns, df.columns):
        visited_columns[expected_column] += 1
        if (count := visited_columns[expected_column]) > 1:
            # we need this because pandas adds a .1, .2, etc. to the column name if it's duplicated
            expected_column = f"{expected_column}.{count-1}"
        if expected_column != df_column:
            raise Exception(f"Missing column: '{expected_column}' vs '{df_column}'")
        

def validate_filtered_report_stay(df: pd.DataFrame, file_columns: FileColumns):

    validator = __create_validator(file_columns)

    file_path = './test.csv'
    save_df_to_csv(df, file_path)

    try:
        with open(file_path, 'r') as f:
            data = csv.reader(f, delimiter=",")
            problems = validator.validate(data, summarize=False)
        if problems:
            for i, problem in enumerate(problems):
                print(f"{i+1}. {problem}")
            raise Exception(f"Invalid report stays file")
    finally:
        delete_file(file_path)


def __check_numeric_column(value: str, can_be_negative: bool) -> float | None:
    if value == '':
        return None
    value = float(value)
    if not can_be_negative and value < 0:
        raise Exception(f"Value is negative: {value}")
    if value > 1_000_000:
        raise Exception(f"Value is too high: {value}")
    return value

def check_date_column(value: str, format: str) -> datetime | None:
    if value == '':
        return None
    return datetime.strptime(value, format)

def __create_validator(file_columns: FileColumns) -> csvvalidator.CSVValidator:
    expected_columns = file_columns.get_renamed_columns_to_use()

    validator = csvvalidator.CSVValidator(expected_columns)
    validator.add_header_check('EX1', 'bad header')
    validator.add_record_length_check('EX2', 'unexpected record length')

    # add checks on the types of the required columns
    for col, can_be_negative in file_columns.get_numeric_columns_and_can_be_negative():
        validator.add_value_check(col, lambda x: __check_numeric_column(x, can_be_negative), 'EX3', 'expected numeric column')

    for col, format in file_columns.get_datetime_columns_and_format():
        validator.add_value_check(col, lambda x: check_date_column(x, format), 'EX4', 'invalid date')

    for col in file_columns.get_string_columns():
        validator.add_value_check(col, str, 'EX5', 'expected string column')

    return validator
