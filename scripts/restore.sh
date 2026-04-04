#!/bin/bash
# =============================================================
# Восстановление из бэкапа
# Использование:
#   bash scripts/restore.sh                    ← покажет меню выбора
#   bash scripts/restore.sh db 20260404_2100   ← восстановить БД
#   bash scripts/restore.sh media 20260404_2100 ← восстановить медиа
#   bash scripts/restore.sh code               ← откатить код на пред. SHA
# =============================================================
set -e

BACKUP_DIR="/root/backups"
DB_CONTAINER="booking-hub-db"
DB_USER="postgres"
DB_NAME="bookinghub"
PROJECT_DIR="/root/Booking-Hub"

# Цветовые выводы
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ---- Функции ----

show_menu() {
    echo ""
    echo -e "${YELLOW}=== ВОССТАНОВЛЕНИЕ ИЗ БЭКАПА ===${NC}"
    echo ""
    echo "  1) Откатить код на предыдущий деплой"
    echo "  2) Восстановить БД из бэкапа"
    echo "  3) Восстановить медиафайлы из бэкапа"
    echo "  4) Полный откат (код + БД + медиа)"
    echo "  0) Выход"
    echo ""
    read -p "Выбери действие: " CHOICE

    case $CHOICE in
        1) restore_code ;;
        2) pick_and_restore_db ;;
        3) pick_and_restore_media ;;
        4) restore_code && pick_and_restore_db && pick_and_restore_media ;;
        0) echo "Выход"; exit 0 ;;
        *) echo -e "${RED}Неверный выбор${NC}"; exit 1 ;;
    esac
}

restore_code() {
    echo ""
    if [ ! -f /root/last_deploy_sha.txt ]; then
        echo -e "${RED}Ошибка: /root/last_deploy_sha.txt не найден${NC}"
        exit 1
    fi
    SHA=$(cat /root/last_deploy_sha.txt)
    echo -e "${YELLOW}Откатываем код на SHA: $SHA${NC}"
    cd "$PROJECT_DIR"
    git checkout "$SHA"
    docker compose build backend
    docker compose up -d
    echo -e "${GREEN}✓ Код откачен!${NC}"
}

pick_and_restore_db() {
    echo ""
    echo "Доступные бэкапы БД:"
    ls -lt "$BACKUP_DIR"/db_*.sql.gz 2>/dev/null | awk '{print NR") "$NF}' || { echo -e "${RED}Бэкапов нет${NC}"; return; }
    echo ""
    read -p "Введи полный путь к файлу: " DB_FILE
    restore_db "$DB_FILE"
}

restore_db() {
    local FILE=$1
    if [ ! -f "$FILE" ]; then
        echo -e "${RED}Ошибка: файл $FILE не найден${NC}"
        exit 1
    fi
    echo -e "${YELLOW}Восстанавливаем БД из: $FILE${NC}"
    echo -e "${RED}ВНИМАНИЕ: текущие данные БД будут заменены!${NC}"
    read -p "Продолжить? (yes/no): " CONFIRM
    [ "$CONFIRM" != "yes" ] && { echo "Отменено"; return; }

    gunzip -c "$FILE" | docker exec -i "$DB_CONTAINER" \
        psql -U "$DB_USER" -d "$DB_NAME"
    echo -e "${GREEN}✓ БД восстановлена!${NC}"
}

pick_and_restore_media() {
    echo ""
    echo "Доступные бэкапы медиа:"
    ls -lt "$BACKUP_DIR"/media_*.tar.gz 2>/dev/null | awk '{print NR") "$NF}' || { echo -e "${RED}Бэкапов нет${NC}"; return; }
    echo ""
    read -p "Введи полный путь к файлу: " MEDIA_FILE
    restore_media "$MEDIA_FILE"
}

restore_media() {
    local FILE=$1
    if [ ! -f "$FILE" ]; then
        echo -e "${RED}Ошибка: файл $FILE не найден${NC}"
        exit 1
    fi
    echo -e "${YELLOW}Восстанавливаем медиафайлы из: $FILE${NC}"
    MEDIA_VOLUME=$(docker volume ls --format '{{.Name}}' | grep 'media' | head -1)
    if [ -z "$MEDIA_VOLUME" ]; then
        echo -e "${RED}Media volume не найден${NC}"
        exit 1
    fi
    docker run --rm \
        -v "${MEDIA_VOLUME}:/media" \
        -v "$BACKUP_DIR:/backup:ro" \
        alpine sh -c "rm -rf /media/* && tar xzf /backup/$(basename $FILE) -C /media"
    echo -e "${GREEN}✓ Медиафайлы восстановлены!${NC}"
}

# ---- Точка входа ----
case "${1:-menu}" in
    menu)          show_menu ;;
    code)          restore_code ;;
    db)            restore_db "$BACKUP_DIR/db_${2}.sql.gz" ;;
    media)         restore_media "$BACKUP_DIR/media_${2}.tar.gz" ;;
    *)
        echo "Usage: $0 [menu|code|db <DATE>|media <DATE>]"
        exit 1
        ;;
esac
