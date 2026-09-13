VENV := venv
VENV_PATH := $(CURDIR)/$(VENV)
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PIP_COMPILE := $(VENV)/bin/pip-compile

.DEFAULT_GOAL := help

.PHONY: help venv compile install run test docker-up docker-down docker-logs clean .check-venv-active

help:
	@printf "Comandos disponibles:\n"
	@printf "  🐍 make venv     Crea el entorno virtual local en $(VENV)/.\n"
	@printf "  📦 make compile  Compila requirements.in y genera requirements.txt.\n"
	@printf "  🔧 make install  Instala las dependencias desde requirements.txt.\n"
	@printf "  🚀 make run      Instala dependencias y lanza la app.\n"
	@printf "  🧪 make test     Ejecuta los tests de la aplicación.\n"
	@printf "  🐳 make docker-up    Construye y arranca la app en http://localhost:5000.\n"
	@printf "  🛑 make docker-down  Detiene y elimina el contenedor.\n"
	@printf "  📋 make docker-logs  Muestra los registros del contenedor.\n"
	@printf "  🧹 make clean    Elimina el entorno virtual $(VENV)/.\n"

venv:
	python3 -m venv $(VENV)

.check-venv-active:
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		printf "Error: el entorno virtual no esta activo.\n" >&2; \
		printf "Activalo con: source $(VENV)/bin/activate\n" >&2; \
		exit 1; \
	fi
	@if [ "$$(cd "$$VIRTUAL_ENV" && pwd)" != "$(VENV_PATH)" ]; then \
		printf "Error: hay otro entorno virtual activo: $$VIRTUAL_ENV\n" >&2; \
		printf "Activa este proyecto con: source $(VENV)/bin/activate\n" >&2; \
		exit 1; \
	fi

compile: .check-venv-active
	$(PIP) install pip-tools
	$(PIP_COMPILE) requirements.in

install: .check-venv-active
	$(PIP) install -r requirements.txt

run: .check-venv-active
	$(PYTHON) app.py

test:
	$(PYTHON) -m pytest -v

docker-up:
	docker compose up --build --wait --wait-timeout 60
	@printf "Aplicación disponible en http://localhost:5000\n"

docker-down:
	docker compose down

docker-logs:
	docker compose logs --follow

clean:
	rm -rf $(VENV)
