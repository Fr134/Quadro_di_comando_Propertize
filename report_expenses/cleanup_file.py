import pandas as pd

from file_columns import REPORT_EXPENSES_COLUMNS
from file_utility import save_df_to_csv
from file_validator import validate_file_has_all_the_columns, validate_filtered_report_stay

def clean_report_expenses_file(file_path: str) -> pd.DataFrame:
    df = pd.read_excel(file_path, sheet_name=0, engine='openpyxl', header=1)
    validate_file_has_all_the_columns(df, REPORT_EXPENSES_COLUMNS)
    df = process_raw_columns(df)

    # Drop rows where:
    # - the "Importo Totale" column is null
    # - and the "Codice" column has a value different from "59.01.01"
    df = df[~(df['importo_totale'].isnull() & (df['codice'] != '59.01.01'))]

    # Reset the index to ensure the rows are consecutive
    df.reset_index(drop=True, inplace=True)

    # For rows with IVA (Codice "59.01.01") that don't have a date, assign the date of the previous row
    iva_mask = (df['codice'] == '59.01.01') & (df['data'].isnull())
    df.loc[iva_mask, 'data'] = df['data'].shift(1)

    # For rows with IVA (Codice "59.01.01"), assign the "Settore di spesa" of the previous row
    df.loc[df['codice'] == '59.01.01', 'settore_spesa'] = df['settore_spesa'].shift(1)

    return df

def process_raw_columns(df: pd.DataFrame) -> pd.DataFrame:
    # only keep the columns we need
    df = df.iloc[:, REPORT_EXPENSES_COLUMNS.get_columns_positions_to_use()].copy()
    # rename columns
    df.columns = REPORT_EXPENSES_COLUMNS.get_renamed_columns_to_use()
    # validate the file
    validate_filtered_report_stay(df, REPORT_EXPENSES_COLUMNS)

    # correct types
    for col, format in REPORT_EXPENSES_COLUMNS.get_datetime_columns_and_format():
        df[col] = pd.to_datetime(df[col], format=format, dayfirst=True)

    for col in REPORT_EXPENSES_COLUMNS.get_numeric_columns():
        df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


def process_expenses_file(input_file: str, output_file: str) -> pd.DataFrame:
    df = clean_report_expenses_file(input_file)
    save_df_to_csv(df, output_file)
    return df
