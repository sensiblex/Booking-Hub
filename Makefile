# =============================================================
# Makefile — удобные команды для команды
# =============================================================

.PHONY: dev prod build down logs shell migrate backup restore

# ─── Разработка ───────────────────────────────────────────────
dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up

dev-build:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

dev-down:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml down

# ─── Продакшн ───────────────────────────────────────────────
prod:
	docker compose up -d

build:
	docker compose build backend

down:
	docker compose down

# ─── Диагностика ───────────────────────────────────────────
logs:
	docker compose logs -f backend

logs-all:
	docker compose logs -f

ps:
	docker compose ps

# ─── Django ───────────────────────────────────────────────
shell:
	docker compose exec backend python manage.py shell

migrate:
	docker compose exec backend python manage.py migrate

createsuperuser:
	docker compose exec backend python manage.py createsuperuser

# ─── Бэкап / восстановление ────────────────────────────────
backup:
	bash scripts/backup.sh

restore:
	bash scripts/restore.sh
