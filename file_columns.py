import json
import os


class FileColumns:

    def __init__(self, file_path: str):
        self.file_path = file_path

    def get_file_columns(self) -> list[dict[str, str | bool]]:
        with open(self.file_path, 'r') as f:
            return json.load(f)

    def __get_required_columns(self) -> list[dict[str, str | bool]]:
        return [col for col in self.get_file_columns() if col['is_required']]

    def get_all_excel_columns(self) -> list[str]:
        return [col['excel_column'] for col in self.get_file_columns()]

    def get_columns_positions_to_use(self) -> list[int]:
        return [i for i, col in enumerate(self.get_file_columns()) if col['is_required']]

    def get_renamed_columns_to_use(self) -> list[str]:
        return [col['renamed_column'] for col in self.__get_required_columns()]

    def get_numeric_columns(self) -> list[str]:
        return [col['renamed_column'] for col in self.__get_required_columns() if col['column_type'] == 'float']

    def get_numeric_columns_and_can_be_negative(self) -> list[tuple[str, bool]]:
        return [(col['renamed_column'], col.get('can_be_negative', False)) for col in self.__get_required_columns() if col['column_type'] == 'float']

    def get_datetime_columns_and_format(self) -> list[tuple[str, str]]:
        return [(col['renamed_column'], col['format']) for col in self.__get_required_columns() if col['column_type'] == 'datetime']

    def get_string_columns(self) -> list[str]:
        return [col['renamed_column'] for col in self.__get_required_columns() if col['column_type'] == 'string']
    
__curr_dir = os.path.dirname(__file__)
REPORT_STAYS_COLUMNS = FileColumns(f'{__curr_dir}/report_stays/report_stays_columns.json')
REPORT_EXPENSES_COLUMNS = FileColumns(f'{__curr_dir}/report_expenses/report_expenses_columns.json')
