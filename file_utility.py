import os

import pandas as pd


def get_xlsx_files(input_folder: str) -> list[str]:
    """
    List all .xlsx files in the given input folder.
    """
    return [f for f in os.listdir(input_folder) if f.endswith('.xlsx')]


def save_df_to_csv(df: pd.DataFrame, csv_path: str):
    """
    Save the DataFrame to a CSV file without the index.
    """
    df.to_csv(csv_path, index=False)

def __get_project_root_path() -> str:
    """
    Get the project root path.
    """
    return os.path.dirname(os.path.abspath(__file__))

def create_folder_structure_for_company(company_name: str):
    """
    Create a folder structure for the given company name.
    """
    base_path = __get_project_root_path()
    raw_files_base_path = os.path.join(base_path, 'raw_files', company_name)
    os.makedirs(raw_files_base_path, exist_ok=True)
    os.makedirs(os.path.join(raw_files_base_path, 'report_stays'), exist_ok=True)
    files_to_upload_path = os.path.join(base_path, 'files_to_upload ', company_name)
    os.makedirs(files_to_upload_path, exist_ok=True)
    os.makedirs(os.path.join(files_to_upload_path, 'intermediate_files'), exist_ok=True)

def get_files_to_upload_path(company_name: str) -> str:
    """
    Get the path to the files to upload folder for the given company name.
    """
    base_path = __get_project_root_path()
    return os.path.join(base_path, 'files_to_upload', company_name)

def get_raw_report_stays_path(company_name: str) -> str:
    """
    Get the path to the raw report stays folder for the given company name.
    """
    base_path = __get_project_root_path()
    return os.path.join(base_path, 'raw_files', company_name, 'report_stays')



