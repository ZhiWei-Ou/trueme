.DEFAULT_GOAL := help
DEVICE ?= cpu
ifeq ($(OS),Windows_NT)
PYTHON ?= python
VENV_PYTHON := .venv/Scripts/python.exe
else
PYTHON ?= python3
VENV_PYTHON := .venv/bin/python
endif

.PHONY: help setup download-models run test lint build
help:
	@$(PYTHON) scripts/dev.py help
setup:
	$(PYTHON) scripts/dev.py setup --device $(DEVICE)
download-models:
	$(PYTHON) scripts/dev.py download-models
run:
	$(VENV_PYTHON) -m trueme web --model-dir models
test:
	$(VENV_PYTHON) -m pytest
lint:
	$(VENV_PYTHON) -m ruff check src tests scripts
build:
	$(VENV_PYTHON) -m build --no-isolation
