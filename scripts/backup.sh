#!/bin/bash
# =============================================================
# Бэкап БД и медиафайлов перед деплоем
# Запуск: bash scripts/backup.sh
# =============================================================
set -e

BACKUP_DIR="/root/backups"
DATE=$(date +%Y%m%d_%H%M%S)
KEEP_LAST=5

# Имя контейнера БД (откуда берём имя)
DB_CONTAINER="booking-hub-db"
DB_USER="postgres"
DB_NAME="bookinghub"

mkdir -p "$BACKUP_DIR"

echo "[1/4] 📅 Дата: $DATE"
echo "[1/4] 📂 Папка бэкапов: $BACKUP_DIR"

# --- Сохраняем текущий git SHA для отката ---
echo "[2/4] 🔖 Сохраняем текущий git SHA..."
git -C /root/Booking-Hub rev-parse HEAD > /root/last_deploy_sha.txt
SHA=$(cat /root/last_deploy_sha.txt)
echo "     SHA: $SHA"

# --- Бэкап БД ---
echo "[3/4] 🐘 Бэкап БД..."
DB_FILE="$BACKUP_DIR/db_${DATE}.sql"
docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" > "$DB_FILE"
gzip "$DB_FILE"
echo "     ✓ $DB_FILE.gz ($(du -sh ${DB_FILE}.gz | cut -f1))"

# --- Бэкап медиафайлов ---
echo "[4/4] 🖼  Бэкап медиафайлов..."
MEDIA_FILE="$BACKUP_DIR/media_${DATE}.tar.gz"

# Находим volume медиафайлов
MEDIA_VOLUME=$(docker volume ls --format '{{.Name}}' | grep 'media' | head -1)
if [ -n "$MEDIA_VOLUME" ]; then
    docker run --rm \
        -v "${MEDIA_VOLUME}:/media:ro" \
        -v "$BACKUP_DIR:/backup" \
        alpine tar czf "/backup/media_${DATE}.tar.gz" -C /media .
    echo "     ✓ $MEDIA_FILE ($(du -sh $MEDIA_FILE | cut -f1))"
else
    echo "     ⚠ Media volume не найден, пропускаем"
fi

# --- Удаляем старые бэкапы (оставляем последние 5) ---
echo ""
echo "🧹 Удаляем старые бэкапы (храним $KEEP_LAST)..."
ls -t "$BACKUP_DIR"/db_*.sql.gz 2>/dev/null | tail -n +$((KEEP_LAST + 1)) | xargs -r rm
ls -t "$BACKUP_DIR"/media_*.tar.gz 2>/dev/null | tail -n +$((KEEP_LAST + 1)) | xargs -r rm

echo ""
echo "✅ Бэкап готов!"
echo "📁 Файлы в $BACKUP_DIR:"
ls -lh "$BACKUP_DIR" | grep -E 'db_|media_'
