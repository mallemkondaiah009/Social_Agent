1. Running Server
uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --reload

2. Celery Worker
celery -A config worker -P gevent -c 50 -l info

3. Celery Beat
celery -A config beat -l info

4. Docker for Redis, postgres
docker compose up -d