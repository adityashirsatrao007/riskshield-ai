.PHONY: all train backend frontend docker clean

all: train

train:
	cd ml && pip install -r requirements.txt && python scripts/generate_data.py && python scripts/train.py

backend:
	cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm install && npm run dev

docker:
	docker compose up --build

clean:
	rm -rf ml/data/*.csv ml/models/*.joblib
	rm -rf backend/*.db backend/data/
	rm -rf frontend/node_modules frontend/dist
