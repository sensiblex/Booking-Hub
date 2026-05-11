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
echo "[2/4] Создаём суперпользователя (если не существует)..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
username = '${DJANGO_SUPERUSER_USERNAME}'
email = '${DJANGO_SUPERUSER_EMAIL}'
password = '${DJANGO_SUPERUSER_PASSWORD}'
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f'Superuser {username} created successfully')
else:
    user = User.objects.get(username=username)
    if not user.is_staff:
        user.is_staff = True
        user.role = 'administrator'
        user.save()
        print(f'User {username} updated to administrator')
    else:
        print(f'Superuser {username} already exists')
"

echo ""
echo "[3/4] Собираем статику..."
python manage.py collectstatic --noinput --clear

echo ""
echo "[4/5] Заполняем тестовые данные..."
python manage.py seed_spaces

echo ""
echo "[5/5] Запускаем Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
