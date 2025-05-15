import datetime
import os
from typing import List, Tuple

import pandas as pd

from file_utility import get_xlsx_files, save_df_to_csv
from report_stays.report_stays_columns import get_datetime_columns, get_excel_columns_to_use, get_numeric_columns, \
    get_renamed_columns_to_use


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

    # Remove the first 4 rows and set the 5th as header
    df.columns = list(df.iloc[4])
    df = df.iloc[6:].reset_index(drop=True)

    # Remove the last row if the first column starts with 'totali' (case-insensitive)
    first_col = df.columns[0]
    if not df.empty and str(df.iloc[-1][first_col]).strip().lower().startswith('totali'):
        df = df.iloc[:-1]

    df = process_raw_columns(df)
    df = df.dropna(subset=['id_appartamento'])
    
    df = calculate_derived_columns(df)
    df.fillna(0, inplace=True)

    # Round all numeric columns to 2 decimal places
    for col in df.columns:
        if df[col].dtype == 'float64':
            df[col] = df[col].round(2)

    return df

def process_raw_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = get_renamed_columns_to_use()

    # Correct types
    # datetime columns (original format: dd/mm/yyyy)
    for col in get_datetime_columns():
        df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', dayfirst=True)

    # numeric columns (original format: 1234,56)
    for col in get_numeric_columns():
        df[col] = pd.to_numeric(df[col], errors='coerce')

    return df

def calculate_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Calculate derived columns
    df['durata_soggiorno'] = (df['data_check_out'] - df['data_check_in']).dt.days
    df['ricavi_totali'] = (df['ricavi_locazione'] - df['iva_provvigioni_pm'] + df['ricavi_pulizie'] / 1.22)
    df['commissioni_totali'] = (df['commissioni_ota'] / 1.22 + df['commissioni_itw_nette'] + df['commissioni_proprietari_lorde'])  
    df['marginalità_totale'] = (df['ricavi_totali'] - df['commissioni_totali'])    
    df['commissioni_ota_locazioni'] = (df['commissioni_ota']/1.22 - (df['ricavi_locazione'] / (df['ricavi_locazione'] + df['ricavi_pulizie'])))    
    df['marginalità_locazioni'] = (df['ricavi_locazione']-df['commissioni_proprietari_lorde'] - df['iva_provvigioni_pm'] - df['commissioni_ota_locazioni'])
    df['marginalità_pulizie'] = (df['ricavi_pulizie']/1.22 - (df['commissioni_ota'] - df['marginalità_locazioni']))
    df['mese'] = df['data_check_in'].dt.to_period('M').astype(str)

    return df


def process_stays_reports(input_folder: str, output_folder: str):
    """
    Process all xlsx files: clean them and save as CSVs. Return list of (csv_path, original_file_name).
    """
    xlsx_files = get_xlsx_files(input_folder)
    print(f"Found {len(xlsx_files)} xlsx files in {input_folder}")
    csv_paths = []
    for xlsx_file in xlsx_files:
        xlsx_path = os.path.join(input_folder, xlsx_file)
        try:
            df = clean_short_stay_sheet(xlsx_path)
            csv_name = os.path.splitext(xlsx_file)[0] + '.csv'
            csv_path = os.path.join(output_folder, 'intermediate_files', csv_name)
            save_df_to_csv(df, csv_path)
            csv_paths.append((csv_path, xlsx_file))
            print(f"CSV saved to {csv_path}")
        except Exception as e:
            print(f"Error processing {xlsx_file}: {e}")
            raise e
        
    concat_csvs_with_filename(csv_paths, output_folder + '/all_short_stay_concat.csv')

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

        save_df_to_csv(concat_df, output_path)
        print(f"Concatenated CSV saved to {output_path}")
    else:
        print("No CSVs were created.")
