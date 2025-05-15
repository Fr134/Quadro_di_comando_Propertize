import pandas as pd

def clean_report_expenses_file(file_path: str) -> pd.DataFrame:
    df = pd.read_excel(file_path, sheet_name=0, engine='openpyxl', header=1)

    print(df.head())

    return df

if __name__ == "__main__":
    clean_report_expenses_file("raw_files/company_1/Esempio nota spese.xlsx")
