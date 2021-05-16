.PHONY: help lint format check-formaty

# Help system from https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
.DEFAULT_GOAL := help

help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

pyenv: ## Install and setup local py env
	python3.8 -m pip install pipenv
	pipenv install --keep-outdated --dev

lint: ## Run Python linters
	pipenv run flake8 app.py
	pipenv run pylint app.py

check-format: lint-py ## Check Python code formatting
	pipenv run black . --check
	pipenv run reorder-python-imports --py38-plus app.py

format: ## Format Python code
	pipenv run black .
	pipenv run reorder-python-imports --py38-plus app.py || pipenv run black .

clean: pyenv ## Cleans and rebuilds sleuth
	echo "Nothing to clean"


