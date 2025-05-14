# (Excel Colnum, Renamed Column Name, Column Type)

REPORT_COLUMNS: list[tuple[str, str, str]] = [
    ('B', 'id_appartamento', 'string'),
    ('C', 'nome_appartamento', 'string'),
    ('D', 'nome_proprietario', 'string'),
    ('G', 'data_check_in', 'datetime64[ns]'),
    ('H', 'data_check_out', 'datetime64[ns]'),
    ('I', 'ricavi_locazione', 'float64'),
    ('J', 'ricavi_pulizie', 'float64'),
    ('O', 'tassa_soggiorno', 'float64'),
    ('P', 'ota', 'string'),
    ('Q', 'ota_lordo_netta', 'string'),
    ('R', 'commissioni_ota', 'float64'),
    ('U', 'commissioni_itw_nette', 'float64'),
    ('V', 'iva_commissioni_itw', 'float64'),
    ('W', 'commissioni_itw_lorde', 'float64'),
    ('X', 'costi_incasso', 'float64'),
    ('AA', 'provvigioni_pm_nette', 'float64'),
    ('AB', 'iva_provvigioni_pm', 'float64'),
    ('AC', 'provvigioni_pm_lorde', 'float64'),
    ('AJ', 'commissioni_proprietari_lorde', 'float64'),
    ('AK', 'cedolare_secca', 'float64'),
    ('AL', 'commissioni_proprietari_nette', 'float64')
]

def get_excel_columns_to_use() -> list[str]:
    return [col[0] for col in REPORT_COLUMNS]

def get_renamed_columns_to_use() -> list[str]:
    return [col[1] for col in REPORT_COLUMNS]

def get_numeric_columns() -> list[str]:
    return [col[1] for col in REPORT_COLUMNS if col[2] == 'float64']

def get_datetime_columns() -> list[str]:
    return [col[1] for col in REPORT_COLUMNS if col[2] == 'datetime64[ns]']

def get_string_columns() -> list[str]:
    return [col[1] for col in REPORT_COLUMNS if col[2] == 'string']
