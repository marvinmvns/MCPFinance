SHELL := /bin/bash

venv:
	python3 -m venv .venv && source .venv/bin/activate && pip install --upgrade pip && pip install poetry && poetry install

lint:
	ruff check src tests && black --check src tests && mypy src && bandit -q -r src

fmt:
	ruff check --fix src tests && black src tests

test:
	pytest -q

cov:
	coverage run -m pytest && coverage report -m --fail-under=85

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8999 --reload

docker-build:
	docker build -t clean-api:latest .

docker-up:
	docker compose up --build

migrate:
	alembic -c alembic.ini upgrade head

revision:
	alembic -c alembic.ini revision -m "change"

fetch-openfinance:
	@if [ ! -d openfinance_specs ]; then \
		git clone --depth 1 https://github.com/OpenBanking-Brasil/openapi openfinance_specs; \
	else \
		cd openfinance_specs && git pull --ff-only; \
	fi

run-mcp:
	python3 run_mcp_server.py

run-grpc:
	python3 -c "from src.app.grpc_server import serve_grpc; serve_grpc(port=50051)"

compile-proto:
	python3 -m grpc_tools.protoc -I protos --python_out=src/app/grpc_server --grpc_python_out=src/app/grpc_server protos/openfinance.proto

test-openfinance:
	pytest tests/test_openfinance_system.py -v
