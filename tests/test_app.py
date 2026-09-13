import pytest
from app import app
VALID_CSV = b'temperatura,presion\n20,1012\n25,1010\n'


def test_initial_page(client, context):
    response = client.get('/')
    assert response.status_code == 200
    assert 'Ningún archivo seleccionado' in response.get_data(as_text=True)
    assert context['message'] is None
    assert context['columns'] == []


def test_valid_upload_and_alert_position(upload, context):
    response = upload()
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'Cabecera detectada en datos.csv' in html
    assert html.index('Seleccionar archivo CSV') < html.index('alert alert-success')
    assert html.index('alert alert-success') < html.index('id="file-name"')
    assert context['columns'] == ['temperatura', 'presion']
    assert context['chart'] is None


@pytest.mark.parametrize('filename,content', [
    ('vacio.csv', b''),
    ('texto.csv', b'esto no es un csv'),
    ('sin_numeros.csv', b'nombre,ciudad\nAna,Madrid\n'),
    ('malformado.csv', b'a,b\n1,2\n3,4,5\n'),
    ('datos.txt', VALID_CSV),
])
def test_invalid_uploads_show_red_alert(upload, context, filename, content):
    response = upload(content, filename)
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'alert alert-danger' in html
    assert 'Cabecera detectada en' not in html
    assert 'Quitar fichero' in html
    assert context['chart'] is None


def test_plot_reuses_uploaded_file_and_selected_columns(client, upload, context):
    upload()
    response = client.post('/', data={'action': 'plot', 'columns': ['temperatura']})
    assert response.status_code == 200
    assert 'plotly-graph-div' in context['chart']
    assert context['selected'] == ['temperatura']
    assert context['stats'] == [{'name': 'temperatura', 'min': '20', 'max': '25', 'mean': '22.5'}]


def test_clear_removes_file_messages_and_results(client, upload, context, cache):
    upload()
    client.post('/', data={'action': 'plot'})
    response = client.post('/', data={'action': 'clear'}, follow_redirects=True)
    assert response.status_code == 200
    assert len(response.history) == 1
    assert cache == {}
    with client.session_transaction() as session:
        assert 'csv_id' not in session
    for field in ('filename', 'message', 'chart'):
        assert context[field] is None
    for field in ('columns', 'selected', 'stats'):
        assert context[field] == []
    html = response.get_data(as_text=True)
    assert 'Ningún archivo seleccionado' in html
    assert 'Quitar fichero' not in html
    client.post('/', data={'action': 'plot'})
    assert context['message_type'] == 'danger'
    assert context['chart'] is None


def test_clear_invalid_upload(client, upload, context, cache):
    upload(b'')
    client.post('/', data={'action': 'clear'}, follow_redirects=True)
    assert context['message'] is None
    assert context['filename'] is None
    assert cache == {}


def test_clear_without_file_is_repeatable(client, context):
    for _ in range(2):
        response = client.post('/', data={'action': 'clear'}, follow_redirects=True)
        assert response.status_code == 200
        assert context['message'] is None


def test_sessions_are_isolated(client, upload, context):
    upload()
    other_client = app.test_client()
    other_client.post('/', data={'action': 'plot'})
    assert context['filename'] is None
    upload(filename='otro.csv', client=other_client)
    client.post('/', data={'action': 'clear'})
    other_client.post('/', data={'action': 'plot'})
    assert context['filename'] == 'otro.csv'
    assert context['chart'] is not None
