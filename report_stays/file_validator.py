import csvvalidator
import json
import csv
import pandas as pd

from file_utility import save_df_to_csv, delete_file
from report_stays.report_stays_columns import get_datetime_columns, get_numeric_columns, get_string_columns, get_all_excel_columns, get_renamed_columns_to_use  

def validate_file_has_all_the_columns(df: pd.DataFrame):
    expected_columns = get_all_excel_columns()
    for col in expected_columns:
        if col not in df.columns:
            raise Exception(f"Missing column: {col}")

def validate_filtered_report_stay(df: pd.DataFrame):

    validator = __create_validator()

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


def __check_numeric_column(value: str) -> float | None:
    if value == '':
        return None
    value = float(value)
    if value < 0:
        raise Exception(f"Value is negative: {value}")
    if value > 1_000_000:
        raise Exception(f"Value is too high: {value}")
    return value

def __create_validator() -> csvvalidator.CSVValidator:
    expected_columns = get_renamed_columns_to_use()

    validator = csvvalidator.CSVValidator(expected_columns)
    validator.add_header_check('EX1', 'bad header')
    validator.add_record_length_check('EX2', 'unexpected record length')

    # add checks on the types of the required columns
    for col in get_numeric_columns():
        validator.add_value_check(col, __check_numeric_column, 'EX3', 'expected numeric column')

    for col in get_datetime_columns():
        validator.add_value_check(col, csvvalidator.datetime_string('%d/%m/%Y'),'EX4', 'invalid date')

    for col in get_string_columns():
        validator.add_value_check(col, str, 'EX5', 'expected string column')

    return validator
