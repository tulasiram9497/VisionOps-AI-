PYTHON ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/pip
PYTHON_VENV := $(VENV)/bin/python

.PHONY: backend-install frontend-install test lint run-backend run-frontend

backend-install:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r backend/requirements.txt

frontend-install:
	cd frontend && npm install

test:
	cd backend && $(PYTHON_VENV) -m pytest -q

lint:
	cd backend && $(PYTHON_VENV) -m ruff check app tests || true

run-backend:
	cd backend && $(PYTHON_VENV) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-frontend:
	cd frontend && npm run dev -- --host 0.0.0.0 --port 3000
