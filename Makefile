.PHONY: help lint format check-format dist

# Help system from https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
.DEFAULT_GOAL := help

help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

pyenv: ## Install and setup local py env
	python3.8 -m venv venv
	venv/bin/pip install -r requirements.txt

lint: ## Run Python linters
	venv/bin/flake8 app.py
	venv/bin/pylint app.py

check-format: lint-py ## Check Python code formatting
	venv/bin/black sleuth --check
	venv/bin/reorder-python-imports --py38-plus `find sleuth -name "*.py"`h

format: ## Format Python code
	venv/bin/black sleuth
	venv/bin/reorder-python-imports --py38-plus `find sleuth -name "*.py"` || venv/bin/black sleuth

dist: ## Builds the app with pyinstaller
	venv/bin/pyinstaller app.spec

run: ## Runs the app
	venv/bin/python app.py

clean: pyenv ## Cleans and rebuilds sleuth
	rm -rf dist


