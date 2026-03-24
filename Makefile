lint:
	source .venv/bin/activate && \
	isort app/ tests/ && \
	black app/ tests/ && \
	bandit -r app/

# make test TEST_ARGS=-s for verbose test outputs
test: lint
	source .venv/bin/activate && \
	export CAAS_API_SALT=testsalt && \
	export CAAS_API=testing && \
	export CAAS_API_NAMESPACE="testing" && \
	export CAAS_API_KUBERNETES_URL="https://testing:1234" && \
	export CAAS_DEFAULT_CPU= && \
	export CAAS_DEFAULT_MEM= && \
	pytest $(TEST_ARGS)

coverage: lint
	source .venv/bin/activate && \
	export CAAS_API_SALT=testsalt && \
	export CAAS_API=testing && \
	export CAAS_API_NAMESPACE=testing && \
	export CAAS_API_KUBERNETES_URL="https://testing:1234" && \
	export CAAS_DEFAULT_CPU= && \
	export CAAS_DEFAULT_MEM= && \
	coverage run --source=. -m pytest && \
	coverage html

CONTAINER_CMD ?= podman
BUILD_TAG=develop
build:
	$(CONTAINER_CMD) build -t caas-api:$(BUILD_TAG) .

startdb:
	$(CONTAINER_CMD) start timescaledb

stopdb:
	$(CONTAINER_CMD) stop timescaledb

run:
	. ./scripts/set_kubernetes.sh; \
	. ./scripts/set_salt.sh; \
	$(CONTAINER_CMD) run --rm \
	-e CAAS_API_NAMESPACE="caas-api" \
	-e CAAS_API_KUBERNETES_URL="" \
	-e CAAS_API_SALT \
	-e CAAS_KUBE_JOBS_TOKEN \
	-e CAAS_API=development \
	-v /etc/localtime:/etc/localtime:ro \
	-v /etc/timezone:/etc/timezone:ro \
	--mount type=bind,source=$$(pwd)/app,target=/app \
	-p=8000:8000 \
	--name caas-api \
	caas-api:$(BUILD_TAG) --reload

pre-commit:
	set -e; \
	$(MAKE) lint; \
	$(MAKE) test; \
	$(CONTAINER_CMD) build --pull --no-cache -t caas-api:$(BUILD_TAG) .

