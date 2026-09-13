import pytest
import pandas as pd
from app import get_column_stats, get_plot_x_column, read_csv_file, read_uploaded_file


@pytest.mark.parametrize('delimiter', [',', ';', '\t', '|'])
def test_supported_delimiters(delimiter):
    content = f'temperatura{delimiter}presion\n23{delimiter}1012\n'
    df = read_csv_file(content.encode())
    assert df.to_dict('list') == {'temperatura': [23], 'presion': [1012]}


def test_metadata_before_header_and_utf8_bom():
    content = '\ufeffRegistro de vuelo\ntemperatura,presion\n23,1012\n'
    df = read_csv_file(content.encode())
    assert df.to_dict('list') == {'temperatura': [23], 'presion': [1012]}


def test_decimal_comma_and_empty_trailing_column():
    df = read_csv_file(b'temperatura;presion;\n23,5;1012;\n24,5;1010;\n')
    assert df.to_dict('list') == {'temperatura': [23.5, 24.5], 'presion': [1012, 1010]}


def test_unsupported_extension():
    with pytest.raises(ValueError, match='Formato no soportado'):
        read_uploaded_file(b'temperatura,presion\n23,1012\n', 'datos.txt')


def test_uppercase_csv_extension():
    df = read_uploaded_file(b'temperatura,presion\n23,1012\n', 'datos.CSV')
    assert df.shape == (1, 2)


def test_malformed_csv():
    with pytest.raises(pd.errors.ParserError):
        read_csv_file(b'temperatura,presion\n23,1012\n24,1010,99\n')


def test_date_time_axis():
    df = pd.DataFrame({'Date': ['2026-09-13'], 'Time': ['12:30:00']})
    assert get_plot_x_column(df) == ('Fecha/Hora', 'Fecha/Hora')
    assert df['Fecha/Hora'].iloc[0] == pd.Timestamp('2026-09-13 12:30:00')


def test_row_axis_without_dates():
    assert get_plot_x_column(pd.DataFrame({'temperatura': [23]})) == ('index', 'Fila')


def test_stats_ignore_missing_values():
    df = pd.DataFrame({'temperatura': [20, None, 25], 'vacia': [None, None, None]})
    assert get_column_stats(df, ['temperatura', 'vacia']) == [{'name': 'temperatura', 'min': '20', 'max': '25', 'mean': '22.5'}]
