.PHONY: test clean help coverage venv install server

VENV_DIR = venv
PYTHON = python3
PIP = $(VENV_DIR)/bin/pip
PYTHON_VENV = $(VENV_DIR)/bin/python

help:
	@echo "Available targets:"
	@echo "  make venv     - Create virtual environment"
	@echo "  make install  - Install dependencies in venv"
	@echo "  make server   - Start the web server (in venv)"
	@echo "  make test     - Run all unit tests"
	@echo "  make coverage - Run tests with coverage report"
	@echo "  make clean    - Remove generated files and caches"
	@echo "  make help     - Show this help message"

venv:
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "✅ Virtual environment created in $(VENV_DIR)/"
	@echo ""
	@echo "To activate the virtual environment, run:"
	@echo "  source $(VENV_DIR)/bin/activate"
	@echo ""
	@echo "Next step: make install"

install-packages-ubuntu:
	sudo apt install -y python3 python3-venv texlive-latex-base texlive-latex-extra imagemagick

install: install-packages-ubuntu venv
	@echo "Installing dependencies in virtual environment..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "✅ Dependencies installed"
	@echo ""
	@echo "To start the web server: make server"

server:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "❌ Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	@echo "Starting web server..."
	@echo "Open your browser to: http://localhost:5000"
	@echo ""
	$(PYTHON_VENV) web_server.py

test:
	@echo "Running tests..."
	python3 -m unittest discover -s tests -p "test_*.py" -v

coverage:
	@echo "Running tests with coverage analysis..."
	python3 -m coverage run -m unittest discover -s tests
	@echo ""
	python3 -m coverage report latex_diagram_generator/*.py
	@echo ""
	@echo "For detailed HTML report, run: python3 -m coverage html"

clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov
	rm -rf temp_diagrams/*
	cd diagrams && make clean
	@echo "Clean complete"

clean-all: clean
	@echo "Removing virtual environment..."
	rm -rf $(VENV_DIR)
	@echo "Complete cleanup done"
