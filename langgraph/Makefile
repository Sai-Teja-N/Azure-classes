.PHONY: install run run-local build up down logs tail-log smoke clean

# --- Local (no Docker) ---
install:
	pip install -r requirements.txt

run-local:
	uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# --- Docker ---
build:
	docker compose -f deploy/docker-compose.yml build

up:
	docker compose -f deploy/docker-compose.yml up -d

down:
	docker compose -f deploy/docker-compose.yml down

logs:
	docker compose -f deploy/docker-compose.yml logs -f rca-app

tail-log:
	tail -f logs/rca.log

smoke:
	./scripts/smoke_test.sh

clean:
	docker compose -f deploy/docker-compose.yml down -v
	rm -rf logs/*.log*
