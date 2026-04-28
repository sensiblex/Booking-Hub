# =============================================================
# Makefile — локальный запуск проекта
# =============================================================

.PHONY: dev dev-build dev-down build down logs logs-all ps shell migrate createsuperuser backup restore

# Локальная разработка
dev:
	docker compose up

dev-build:
	docker compose up --build

dev-down:
	docker compose down

build:
	docker compose build backend

down:
	docker compose down

# Логи
logs:
	docker compose logs -f backend

logs-all:
	docker compose logs -f

ps:
	docker compose ps

# Django
shell:
	docker compose exec backend python manage.py shell

migrate:
	docker compose exec backend python manage.py migrate

createsuperuser:
	docker compose exec backend python manage.py createsuperuser

# Бекап / восстановление
backup:
	bash scripts/backup.sh

restore:
	bash scripts/restore.sh
