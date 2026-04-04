# Откат деплоя (Rollback Guide)

> Инструкция для всей команды. Читай это ДО деплоя.

---

## Быстрый откат — через меню

```bash
bash /root/Booking-Hub/scripts/restore.sh
```

Появится интерактивное меню с выбором действия.

---

## Сценарий 1: код сломался после деплоя

```bash
cd /root/Booking-Hub

# 1. Узнать SHA предыдущего деплоя
cat /root/last_deploy_sha.txt

# 2. Откатить код
git checkout <SHA>

# 3. Пересобрать и запустить
docker compose build backend
docker compose up -d

# 4. Проверить
docker compose ps
docker compose logs backend --tail=30
```

---

## Сценарий 2: миграция сломала БД

```bash
# Посмотреть доступные бэкапы
ls -lh /root/backups/db_*.sql.gz

# Восстановить конкретный бэкап (введи дату)
bash /root/Booking-Hub/scripts/restore.sh db 20260404_210000

# После восстановления — откатить миграции до нужной точки
docker compose exec backend python manage.py showmigrations
docker compose exec backend python manage.py migrate spaces 0001_initial
```

---

## Сценарий 3: попали медиафайлы

```bash
# Посмотреть доступные бэкапы
ls -lh /root/backups/media_*.tar.gz

# Восстановить
bash /root/Booking-Hub/scripts/restore.sh media 20260404_210000
```

---

## Сценарий 4: полный откат всего

```bash
bash /root/Booking-Hub/scripts/restore.sh
# Выбери: 4) Полный откат (код + БД + медиа)
```

---

## Полезные команды диагностики

```bash
# Логи бэкенда в реальном времени
docker compose logs backend -f

# Статус всех контейнеров
docker compose ps

# Зайти внутрь контейнера
docker compose exec backend bash

# Перезапустить только бэкенд
docker compose restart backend

# Полностью пересобрать
docker compose up -d --build backend
```

---

## Где хранятся бэкапы

```
/root/backups/
  db_20260404_210000.sql.gz     ← дамп БД
  media_20260404_210000.tar.gz  ← архив медиафайлов

/root/last_deploy_sha.txt       ← git SHA предыдущего деплоя
```

Хранится **5 последних** бэкапов, старые удаляются автоматически.
