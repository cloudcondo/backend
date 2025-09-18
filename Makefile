VENV=.venv
PY=$(VENV)/bin/python
PIP=$(VENV)/bin/pip

.PHONY: init check makemigrations migrate seed roundtrip test resetdb lint shell run docs schema superuser

init:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

check:
	$(PY) manage.py check

makemigrations:
	$(PY) manage.py makemigrations

migrate:
	$(PY) manage.py migrate

seed:
	$(PY) manage.py load_sample_data

roundtrip:
	$(PY) manage.py check_csv_roundtrip

test:
	$(PY) manage.py test -q

resetdb:
	$(PY) manage.py flush --no-input && $(PY) manage.py migrate

lint:
	$(VENV)/bin/flake8 accounts core

shell:
	$(PY) manage.py shell

run:
	$(PY) manage.py runserver 0.0.0.0:8000

# OpenAPI helpers
schema:
	$(PY) manage.py spectacular --file openapi.yaml

docs:
	@echo "Docs live at http://localhost:8000/api/docs/ (Swagger) and /api/redoc/"

superuser:
	$(PY) manage.py createsuperuser
