.DEFAULT_GOAL := help
DEVICE ?= cpu
ifeq ($(OS),Windows_NT)
PYTHON ?= python
VENV_PYTHON := .venv/Scripts/python.exe
else
PYTHON ?= python3
VENV_PYTHON := .venv/bin/python
endif

.PHONY: help setup test lint build
help:
	@$(PYTHON) scripts/dev.py help
setup:
	$(PYTHON) scripts/dev.py setup --device $(DEVICE)
test:
	$(VENV_PYTHON) -m pytest
lint:
	$(VENV_PYTHON) -m ruff check src tests scripts
build:
	$(VENV_PYTHON) -m build --no-isolation
