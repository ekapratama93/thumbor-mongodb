.PHONY: prepare-dev
prepare-dev:
	@echo "Preparing your development environment..."; \
	PIPENV_VENV_IN_PROJECT=1 pipenv install --dev --deploy

.PHONY: prepare-test
prepare-test:
		pip install pyvows coverage tornado_pyvows

stop_mongo:
	@echo "Stopping MongoDB"
	@docker-compose down

mongodb: stop_mongo
	@echo "Starting MongoDB"
	@docker-compose up -d

coverage:
	@pipenv run coverage xml --fail-under=10

unit:
	@@ASYNC_TEST_TIMEOUT=10 pipenv run pytest --cov=thumbor_mongodb tests/

.PHONY: test
test: mongodb
	@$(MAKE) unit coverage
	@$(MAKE) stop_mongo

.PHONY: lint
lint:
	@tput bold; echo "Running code style checker..."; tput sgr0; \
	PIPENV_DONT_LOAD_ENV=1 pipenv run flake8 -v
	@tput bold; echo "Running linter..."; tput sgr0; \
	PIPENV_DONT_LOAD_ENV=1 pipenv run pylint -E *.py

