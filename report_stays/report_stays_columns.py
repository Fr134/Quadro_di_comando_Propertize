import json

def __get_file_columns() -> list[dict[str, str | bool]]:
    with open('report_stays/report_stays_columns.json', 'r') as f:
        return json.load(f)
    
def __get_required_columns() -> list[dict[str, str | bool]]:
    return [col for col in __get_file_columns() if col['is_required']]

def get_all_excel_columns() -> list[str]:
    return [col['excel_column'] for col in __get_file_columns()]

def get_columns_positions_to_use() -> list[str]:
    return [i for i, col in enumerate(__get_file_columns()) if col['is_required']]

def get_renamed_columns_to_use() -> list[str]:
    return [col['renamed_column'] for col in __get_required_columns()]

def get_numeric_columns() -> list[str]:
    return [col['renamed_column'] for col in __get_required_columns() if col['column_type'] == 'float']

def get_datetime_columns() -> list[str]:
    return [col['renamed_column'] for col in __get_required_columns() if col['column_type'] == 'datetime']

def get_string_columns() -> list[str]:
    return [col['renamed_column'] for col in __get_required_columns() if col['column_type'] == 'string']
