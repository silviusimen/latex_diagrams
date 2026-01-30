.PHONY: test clean help coverage

help:
	@echo "Available targets:"
	@echo "  make test     - Run all unit tests"
	@echo "  make coverage - Run tests with coverage report"
	@echo "  make clean    - Remove generated files and caches"
	@echo "  make help     - Show this help message"

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
	cd diagrams && make clean
	@echo "Clean complete"
