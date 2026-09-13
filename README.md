# Visor de CSV con gráficas locales

Esta aplicación en Python permite cargar un archivo CSV y visualizar gráficas de los valores contenidos en sus columnas.

## Requisitos

- Python 3.10 o superior
- pip

## Instalación

1. Clona o descarga este proyecto en tu equipo.
2. Abre una terminal en la carpeta del proyecto.
3. Crea el entorno virtual:

```bash
make venv
```

4. Activa el entorno virtual:

```bash
source venv/bin/activate
```

5. Instala las dependencias:

```bash
make install
```

## Uso

1. Ejecuta la aplicación:

```bash
make run
```

2. Abre tu navegador y ve a:

```text
http://127.0.0.1:5000
```

3. Selecciona un archivo CSV.
4. La aplicación detectará automáticamente la cabecera y mostrará los parámetros numéricos disponibles.
5. Marca o desmarca los parámetros que quieras visualizar y pulsa **Ver gráfica**.

## Docker

Necesitas Docker con el complemento Docker Compose y el puerto 5000 libre.
No es necesario instalar Python ni crear un entorno virtual en el equipo.

```bash
make docker-up
```

El comando construye la imagen, arranca el contenedor en segundo plano y espera
a que la aplicación responda. Abre **http://localhost:5000**.
La primera construcción necesita conexión a Internet para descargar la imagen
de Python y las dependencias.

```bash
make docker-logs  # Consultar los registros (Ctrl+C para salir)
make docker-down  # Detener y eliminar el contenedor
```

Después de modificar el código, ejecuta de nuevo `make docker-up` para reconstruir
la imagen. El contenedor utiliza Python 3.12 y Gunicorn sin el depurador de Flask,
con un único proceso de trabajo porque los CSV se guardan en memoria.
Los archivos cargados se pierden al reiniciar el proceso o recrear el contenedor.
El puerto 5000 se publica únicamente en la interfaz local del equipo.

## Comandos Make

- `make help`: muestra los comandos disponibles.
- `make venv`: crea el entorno virtual local en `venv/`.
- `make compile`: compila `requirements.in` con `pip-compile` y genera `requirements.txt`.
- `make install`: instala las dependencias desde `requirements.txt`.
- `make run`: instala las dependencias si hace falta y lanza la app con `python app.py`.
- `make test`: ejecuta los tests de la aplicación.
- `make docker-up`: construye y arranca el contenedor en el puerto 5000.
- `make docker-down`: detiene y elimina el contenedor.
- `make docker-logs`: muestra los registros del contenedor.
- `make clean`: elimina el entorno virtual `venv/`.

## Tests

Con el entorno virtual creado y las dependencias instaladas, ejecuta:

```bash
make test
```

Los tests están en `tests/` y utilizan `pytest`, incluido en las dependencias. El comando
usa directamente el Python de `venv/`, sin necesidad de activar el entorno.
Comprueban la lectura de CSV, las alertas, la generación de gráficas y estadísticas,
la limpieza del fichero y el aislamiento entre sesiones. No necesitan arrancar
el servidor ni acceder a la red. Las comprobaciones de interfaz revisan el HTML
generado; no ejecutan JavaScript ni verifican la apariencia en un navegador.

## Formato del CSV

El archivo CSV debe tener:

- Una fila de encabezados con nombres de columnas.
- Cada fila siguiente con valores numéricos para cada parámetro.

Ejemplo:

```csv
temperatura,presion,humedad
23.5,1012,45
24.1,1010,43
22.8,1013,47
```

Si el CSV incluye las columnas `Date` y `Time`, la aplicación combina sus valores
para utilizar la fecha y hora como eje temporal de la gráfica. Si estas columnas
no existen o no contienen ninguna fecha y hora válida, utiliza el número de fila
como eje horizontal.

## Notas

- Solo se grafican las columnas numéricas.
- Si hay varias columnas numéricas, la aplicación dibuja todas por defecto.
- Puedes seleccionar las columnas disponibles en el formulario después de subir el CSV.
