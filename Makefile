.PHONY: all train backend frontend docker docker-prod dev clean lint test

all: train

train:
	cd ml && pip install -r requirements.txt && python scripts/generate_data.py && python scripts/train.py

backend:
	cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm install && npm run dev

docker:
	docker compose up --build

docker-prod:
	docker compose -f docker-compose.prod.yml --env-file .env up --build -d

docker-down:
	docker compose -f docker-compose.prod.yml down

docker-logs:
	docker compose -f docker-compose.prod.yml logs -f backend

dev: backend

lint:
	cd backend && python -m ruff check app/

test:
	cd backend && python -m pytest tests/ -v --tb=short

clean:
	rm -rf ml/data/*.csv ml/models/*.joblib
	rm -rf backend/*.db backend/data/
	rm -rf frontend/node_modules frontend/dist
