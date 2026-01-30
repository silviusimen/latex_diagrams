.PHONY: test clean help

help:
	@echo "Available targets:"
	@echo "  make test    - Run all unit tests"
	@echo "  make clean   - Remove generated files and caches"
	@echo "  make help    - Show this help message"

test:
	@echo "Running tests..."
	python3 -m unittest discover -s tests -p "test_*.py" -v

clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	cd diagrams && make clean
	@echo "Clean complete"
