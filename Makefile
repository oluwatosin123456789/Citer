.PHONY: up down dev-backend dev-frontend test eval

up:
	docker compose up -d --build

down:
	docker compose down

dev-backend:
	cd backend && uvicorn app.main:app --reload

dev-frontend:
	cd frontend && npm run dev

test:
	cd backend && pytest

eval:
	cd backend && python -m scripts.eval