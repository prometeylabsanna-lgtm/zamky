#!/bin/sh
set -e
DB_HOST="${DB_HOST:-db}"
echo "Waiting for postgres..."
while ! nc -z "$DB_HOST" 5432; do sleep 0.1; done
echo "PostgreSQL started"

# Реліз лише для gunicorn: check, міграції, кеш, static. WebP — за прапорцем.
# Нові аплоади конвертує сигнал у процесі.
if [ "$1" = "gunicorn" ]; then
  python manage.py check --deploy
  python manage.py migrate --noinput
  python manage.py createcachetable
  python manage.py collectstatic --noinput
  if [ "$CONVERT_IMAGES_ON_START" = "1" ]; then
    python manage.py convert_images_webp
  fi
fi

exec "$@"
