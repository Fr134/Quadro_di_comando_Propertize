import datetime
import os
import pandas as pd
from typing import List, Tuple
import re

from report_columns import get_datetime_columns, get_excel_columns_to_use, get_numeric_columns, get_renamed_columns_to_use

def get_xlsx_files(input_folder: str) -> List[str]:
    """
    List all .xlsx files in the given input folder.
    """
    return [f for f in os.listdir(input_folder) if f.endswith('.xlsx')]


def clean_short_stay_sheet(xlsx_path: str) -> pd.DataFrame:
    """
    Read the 'SHORT STAY' sheet from the Excel file, remove the first 6 rows (set 6th as header),
    and remove the last row if it starts with 'totali'.
    """
    # Read sheet with no header
    df = pd.read_excel(
        xlsx_path, 
        sheet_name='SHORT STAY', 
        engine='openpyxl',
        usecols=",".join(get_excel_columns_to_use()),
    )
    print("DataFrame after read_excel (first 6 rows, row 5 should be headers):")
    print(df.head(6))
    df.columns = list(df.iloc[4])
    df = df.iloc[6:].reset_index(drop=True)

    # Remove the last row if the first column starts with 'totali' (case-insensitive)
    first_col = df.columns[0]
    if not df.empty and str(df.iloc[-1][first_col]).strip().lower().startswith('totali'):
        df = df.iloc[:-1]

    df = process_columns(df)
    df = calculate_derived_columns(df)

    return df

def process_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Drop columns that are not needed
    df.columns = get_renamed_columns_to_use()

    # Correct types
    # datetime columns (original format: dd/mm/yyyy)
    for col in get_datetime_columns():
        df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', dayfirst=True)

    # numeric columns (original format: 1234,56)
    for col in get_numeric_columns():
        df[col] = pd.to_numeric(df[col])

    return df

def calculate_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Calculate derived columns
    df['durata_soggiorno'] = (df['data_check_out'] - df['data_check_in']).dt.days
    df['ricavi_totali'] = df['ricavi_locazione'] - df['iva_provvigioni_pm'] + df['ricavi_pulizie'] / 1.22
    df['commissioni_totali'] = df['commissioni_ota'] / 1.22 + df['commissioni_itw_nette'] + df['commissioni_proprietari_lorde']
    df['marginalità_totale'] = df['ricavi_totali'] - df['commissioni_totali']
    df['commissioni_ota_locazioni'] = df['commissioni_ota']/1.22 - (df['ricavi_locazione'] / (df['ricavi_locazione'] + df['ricavi_pulizie']))
    df['marginalità_locazioni'] = df['ricavi_locazione']-df['commissioni_proprietari_lorde'] - df['iva_provvigioni_pm'] - df['commissioni_ota_locazioni']
    df['marginalità_pulizie'] = df['ricavi_pulizie']/1.22 - (df['commissioni_ota'] - df['marginalità_locazioni'])
    df['mese'] = df['data_check_in'].dt.to_period('M').astype(str)

    return df



def save_df_to_csv(df: pd.DataFrame, csv_path: str):
    """
    Save the DataFrame to a CSV file without the index.
    """
    df.to_csv(csv_path, index=False)

def process_all_files(input_folder: str, csv_folder: str) -> List[Tuple[str, str]]:
    """
    Process all xlsx files: clean them and save as CSVs. Return list of (csv_path, original_file_name).
    """
    xlsx_files = get_xlsx_files(input_folder)
    csv_paths = []
    for xlsx_file in xlsx_files:
        xlsx_path = os.path.join(input_folder, xlsx_file)
        try:
            df = clean_short_stay_sheet(xlsx_path)
            csv_name = os.path.splitext(xlsx_file)[0] + '.csv'
            csv_path = os.path.join(csv_folder, csv_name)
            save_df_to_csv(df, csv_path)
            csv_paths.append((csv_path, xlsx_file))
            print(f"CSV saved to {csv_path}")
        except Exception as e:
            print(f"Error processing {xlsx_file}: {e}")
            raise e

    return csv_paths

def concat_csvs_with_filename(csv_paths: List[Tuple[str, str]], output_path: str):
    """
    Concatenate all CSVs, adding a column for the original file name, and save to output_path.
    """
    all_dfs = []
    for csv_path, original_file in csv_paths:
        df = pd.read_csv(csv_path)
        df['original_file'] = original_file
        df['original_file_creation_date'] = datetime.datetime.fromtimestamp(os.path.getctime(csv_path))
        all_dfs.append(df)
    if all_dfs:
        concat_df = pd.concat(all_dfs, ignore_index=True)
        # Remove duplicates ignoring the 'original_file' column
        cols_to_check = [col for col in concat_df.columns if col != 'original_file']
        concat_df = concat_df.drop_duplicates(subset=cols_to_check)
        concat_df.to_csv(output_path, index=False)
        print(f"Concatenated CSV saved to {output_path}")
    else:
        print("No CSVs were created.")

def main():
    """
    Main function to orchestrate the cleaning and concatenation process.
    """
    input_folder = 'raw_files/company_1'
    csv_folder = os.path.join(input_folder, 'raw_csv')
    os.makedirs(csv_folder, exist_ok=True)
    csv_paths = process_all_files(input_folder, csv_folder)
    output_path = os.path.join(csv_folder, 'all_short_stay_concat.csv')
    concat_csvs_with_filename(csv_paths, output_path)

if __name__ == "__main__":
    main()
