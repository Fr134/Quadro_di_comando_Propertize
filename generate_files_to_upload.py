
from kpis import KPIs
from report_expenses.cleanup_file import process_expenses_file
from report_stays.cleanup_files import process_stays_reports
from file_utility import create_folder_structure_for_company, get_raw_report_stays_path, get_files_to_upload_path

def main():
    """
    Main function to orchestrate the cleaning and concatenation process.
    """
    company_name = 'company_1'
    create_folder_structure_for_company(company_name)
    # input("File structure created, if you have uploaded the files, press enter to continue...")
    stays_df = process_stays_reports(get_raw_report_stays_path(company_name), get_files_to_upload_path(company_name))
    expenses_df = process_expenses_file(f"raw_files/{company_name}/Esempio nota spese.xlsx", f"files_to_upload/{company_name}/expenses.csv")
    kpis = KPIs(stays_df=stays_df, expenses_df=expenses_df)
    kpis.save_kpis(f"files_to_upload/{company_name}/kpis.csv")

if __name__ == "__main__":
    main()
