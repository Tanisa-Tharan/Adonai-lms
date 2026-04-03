#!/bin/sh

echo "Starting LMS..."

until python manage.py migrate
do
  echo "Waiting for DB..."
  sleep 2
done

python manage.py collectstatic --noinput

exec gunicorn core.wsgi:application --bind 0.0.0.0:8000
