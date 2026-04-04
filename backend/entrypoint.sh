#!/bin/sh
# =============================================================
# Entrypoint — запускается при старте контейнера
# =============================================================
set -e

echo ""  
echo "====================================="
echo " BookingHub Backend Starting..."
echo "====================================="

echo ""
echo "[1/4] Применяем миграции..."
python manage.py migrate --noinput

echo ""
echo "[2/4] Собираем статику..."
python manage.py collectstatic --noinput --clear

echo ""
echo "[3/4] Заполняем тестовые данные..."
python manage.py seed_spaces

echo ""
echo "[4/4] Запускаем Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
