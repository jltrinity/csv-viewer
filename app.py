from flask import Flask, request, render_template, session, redirect, url_for
import pandas as pd
import plotly.express as px
import csv
import io
import re
import secrets
from datetime import date

app = Flask(__name__)
app.secret_key = 'log-viewer-local-dev-key'

CSV_CACHE = {}


@app.context_processor
def inject_current_year():
    return {'current_year': date.today().year}


def get_numeric_columns(df: pd.DataFrame) -> list:
    return df.select_dtypes(include="number").columns.tolist()


def get_columns_with_data(df: pd.DataFrame, columns: list) -> list:
    return [column for column in columns if column in df.columns and not df[column].dropna().empty]


def read_csv_file(content: bytes) -> pd.DataFrame:
    text = content.decode('utf-8-sig', errors='replace')
    lines = text.splitlines()
    header_index = detect_csv_header_line(lines)
    delimiter = detect_csv_delimiter('\n'.join(lines[header_index:header_index + 10]))
    df = pd.read_csv(io.StringIO(text), sep=delimiter, header=header_index, engine='python')
    return normalize_csv_dataframe(df)


def detect_csv_delimiter(sample: str) -> str:
    try:
        return csv.Sniffer().sniff(sample, delimiters=',;\t|').delimiter
    except csv.Error:
        delimiter_counts = {delimiter: sample.count(delimiter) for delimiter in [',', ';', '\t', '|']}
        return max(delimiter_counts, key=delimiter_counts.get)


def detect_csv_header_line(lines: list) -> int:
    for index, line in enumerate(lines[:30]):
        if not line.strip():
            continue

        delimiter = detect_csv_delimiter('\n'.join(lines[index:index + 5]))
        row = next(csv.reader([line], delimiter=delimiter), [])
        cells = [cell.strip() for cell in row if cell.strip()]
        if len(cells) < 2:
            continue

        text_cells = [cell for cell in cells if re.search(r'[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]', cell)]
        if len(text_cells) >= max(2, len(cells) // 2):
            return index

    return 0


def normalize_csv_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(axis=0, how='all')
    unnamed_columns = [column for column in df.columns if re.match(r'^Unnamed: \d+', str(column))]
    empty_unnamed_columns = [column for column in unnamed_columns if df[column].dropna().empty]
    df = df.drop(columns=empty_unnamed_columns)
    df.columns = get_clean_column_names(df.columns)

    for column in df.columns:
        if not (pd.api.types.is_object_dtype(df[column]) or pd.api.types.is_string_dtype(df[column])):
            continue

        values = df[column].astype(str).str.strip()
        normalized_values = values.str.replace(',', '.', regex=False)
        converted = pd.to_numeric(normalized_values, errors='coerce')
        original_has_value = values.ne('') & values.ne('nan')
        if original_has_value.any() and converted.notna().sum() == original_has_value.sum():
            df[column] = converted

    return df


def get_clean_column_names(columns) -> list:
    clean_columns = []
    counts = {}

    for index, column in enumerate(columns, start=1):
        name = str(column).strip()
        name = re.sub(r'^Unnamed: \d+(_level_\d+)?$', '', name)
        name = re.sub(r'\.\d+$', '', name)
        if not name:
            name = f'Columna {index}'

        count = counts.get(name, 0) + 1
        counts[name] = count
        clean_columns.append(name if count == 1 else f'{name} {count}')

    return clean_columns


def read_uploaded_file(content: bytes, filename: str) -> pd.DataFrame:
    extension = filename.rsplit('.', 1)[-1].lower()
    if extension == 'csv':
        return read_csv_file(content)

    raise ValueError('Formato no soportado. Usa un archivo CSV.')


def get_default_plot_columns(df: pd.DataFrame, numeric_columns: list) -> list:
    return get_columns_with_data(df, numeric_columns)


def get_plot_x_column(df: pd.DataFrame):
    if {'Date', 'Time'}.issubset(df.columns):
        date_time = pd.to_datetime(
            df['Date'].astype(str).str.strip() + ' ' + df['Time'].astype(str).str.strip(),
            errors='coerce',
        )
        if not date_time.dropna().empty:
            df['Fecha/Hora'] = date_time
            return 'Fecha/Hora', 'Fecha/Hora'

    return 'index', 'Fila'


def get_plot_column_options(numeric_columns: list) -> list:
    return numeric_columns


def format_number(value):
    if pd.isna(value):
        return ''

    if float(value).is_integer():
        return f'{value:,.0f}'

    return f'{value:,.2f}'.rstrip('0').rstrip('.')


def get_column_stats(df: pd.DataFrame, columns: list) -> list:
    stats = []
    for column in columns:
        values = df[column].dropna()
        if values.empty:
            continue

        stats.append({
            'name': column,
            'min': format_number(values.min()),
            'max': format_number(values.max()),
            'mean': format_number(values.mean()),
        })

    return stats


def get_csv_content():
    uploaded_file = request.files.get('csv_file')
    if uploaded_file and uploaded_file.filename:
        content = uploaded_file.stream.read()
        csv_id = secrets.token_urlsafe(16)
        CSV_CACHE[csv_id] = {
            'content': content,
            'filename': uploaded_file.filename,
        }
        session['csv_id'] = csv_id
        return content, uploaded_file.filename

    csv_id = session.get('csv_id')
    cached_csv = CSV_CACHE.get(csv_id)
    if cached_csv:
        return cached_csv['content'], cached_csv['filename']

    return None, None


@app.route('/', methods=['GET', 'POST'])
def index():
    chart = None
    columns = []
    selected = []
    message = None
    message_type = 'danger'
    filename = None
    stats = []

    if request.method == 'POST':
        action = request.form.get('action', 'plot')
        if action == 'clear':
            csv_id = session.pop('csv_id', None)
            CSV_CACHE.pop(csv_id, None)
            return redirect(url_for('index'))

        content, filename = get_csv_content()
        if content:
            try:
                df = read_uploaded_file(content, filename)
                numeric_columns = get_numeric_columns(df)
                columns = get_plot_column_options(numeric_columns)
                selected = request.form.getlist('columns')

                if not columns:
                    message = 'No se encontraron columnas numéricas en el archivo para graficar.'
                else:
                    default_columns = get_default_plot_columns(df, numeric_columns)
                    selected = [col for col in selected if col in columns] or default_columns
                    selected_with_data = get_columns_with_data(df, selected)

                    if action == 'load':
                        message = f'Cabecera detectada en {filename}. Selecciona los parámetros que quieras graficar.'
                        message_type = 'success'
                    elif not selected_with_data:
                        message = 'Selecciona al menos un parámetro con datos para graficar.'
                        message_type = 'warning'
                    else:
                        x_axis, x_label = get_plot_x_column(df)
                        df_plot = df[selected_with_data].copy()
                        if x_axis == 'index':
                            df_plot = df_plot.reset_index()
                        else:
                            df_plot.insert(0, x_axis, df[x_axis])

                        fig = px.line(
                            df_plot,
                            x=x_axis,
                            y=selected_with_data,
                            title=f'Gráfica de valores de {filename}',
                            labels={x_axis: x_label, 'value': 'Valor', 'variable': 'Parámetro'},
                        )
                        fig.update_layout(xaxis_title=x_label, yaxis_title='Valor', legend_title='Parámetro')
                        chart = fig.to_html(full_html=False, include_plotlyjs=True)
                        stats = get_column_stats(df, selected_with_data)

            except Exception as exc:
                message = f'El archivo no tiene un formato CSV válido o no se ha podido procesar: {exc}'
        else:
            message = 'Por favor, selecciona un archivo CSV válido.'

    return render_template(
        'index.html',
        columns=columns,
        selected=selected,
        chart=chart,
        message=message,
        message_type=message_type,
        filename=filename,
        stats=stats,
    )


if __name__ == '__main__':
    app.run(debug=True)
