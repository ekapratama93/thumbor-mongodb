.PHONY: prepare-dev
prepare-dev:
	@echo "Preparing your development environment..."; \
	PIPENV_VENV_IN_PROJECT=1 pipenv install --dev --deploy

.PHONY: prepare-test
prepare-test:
		pip install pyvows coverage tornado_pyvows

.PHONY: test
test:
	@echo "Restart MongoDB"
	@docker-compose down && docker-compose up -d
	@echo "Run Vows"
	@pipenv run pyvows -c -r coverage.xml -l thumbor_mongodb

.PHONY: lint
lint:
	@tput bold; echo "Running code style checker..."; tput sgr0; \
	PIPENV_DONT_LOAD_ENV=1 pipenv run flake8 -v
	@tput bold; echo "Running linter..."; tput sgr0; \
	PIPENV_DONT_LOAD_ENV=1 pipenv run pylint -E *.py

