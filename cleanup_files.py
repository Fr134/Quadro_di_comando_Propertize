import os
import pandas as pd
from typing import List, Tuple
import re

def get_xlsx_files(input_folder: str) -> List[str]:
    """
    List all .xlsx files in the given input folder.
    """
    return [f for f in os.listdir(input_folder) if f.endswith('.xlsx')]

def to_snake_case(s):
    """
    Convert a string to snake_case, replacing '%' with 'perc'.
    """
    s = str(s).strip().replace(" ", "_").replace("-", "_")
    s = s.replace('%', 'perc')
    s = re.sub(r'[^0-9a-zA-Z_]', '', s)
    s = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s)
    return s.lower()

def clean_short_stay_sheet(xlsx_path: str) -> pd.DataFrame:
    """
    Read the 'SHORT STAY' sheet from the Excel file, remove the first 6 rows (set 6th as header),
    and remove the last row if it starts with 'totali'.
    Also, if a column is named 'Imponibile provvigione $word', the next three columns (%, Provvigione netta, IVA 22%)
    are renamed to include $word for uniqueness and clarity.
    """
    # Read sheet with no header
    df = pd.read_excel(xlsx_path, sheet_name='SHORT STAY', engine='openpyxl', header=None)
    # Set the 6th row as header and remove the first 6 rows
    columns = list(df.iloc[5])
    new_columns = []
    i = 0
    while i < len(columns):
        col = columns[i]
        # Check for 'Imponibile provvigione $word'
        match = re.match(r'Imponibile provvigione (.+)', str(col))
        if match and i + 3 < len(columns):
            word = match.group(1).strip()
            new_columns.append(col)
            # Rename next three columns
            new_columns.append(f'{word} %')
            new_columns.append(f'{word} provvigione netta')
            new_columns.append(f'{word} iva 22%')
            i += 4
        else:
            new_columns.append(col)
            i += 1

    # Add suffixes to specific column ranges
    for idx in range(38, 46 + 1):  # 0-based index
        new_columns[idx] = f"pren_{new_columns[idx]}"
    for idx in range(47, 55 + 1):
        new_columns[idx] = f"tassasogg_{new_columns[idx]}"
    df.columns = new_columns
    df = df.iloc[6:].reset_index(drop=True)
    # Remove the last row if the first column starts with 'totali' (case-insensitive)
    first_col = df.columns[0]
    if not df.empty and str(df.iloc[-1][first_col]).strip().lower().startswith('totali'):
        df = df.iloc[:-1]
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
        except Exception as e:
            print(f"Error processing {xlsx_file}: {e}")
    return csv_paths

def concat_csvs_with_filename(csv_paths: List[Tuple[str, str]], output_path: str):
    """
    Concatenate all CSVs, adding a column for the original file name, and save to output_path.
    """
    all_dfs = []
    for csv_path, original_file in csv_paths:
        df = pd.read_csv(csv_path)
        df['original_file'] = original_file
        all_dfs.append(df)
    if all_dfs:
        concat_df = pd.concat(all_dfs, ignore_index=True)
        # Remove duplicates ignoring the 'original_file' column
        cols_to_check = [col for col in concat_df.columns if col != 'original_file']
        concat_df = concat_df.drop_duplicates(subset=cols_to_check)
        # Convert column names to snake_case
        
        concat_df.columns = [to_snake_case(col) for col in concat_df.columns]
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
