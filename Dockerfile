FROM python:3.14-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_DB_PATH=/data/db.sqlite3

WORKDIR /app

COPY requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock

COPY . .
WORKDIR /app/backend

RUN DJANGO_DEBUG=true python manage.py collectstatic --noinput \
    && useradd --create-home appuser \
    && mkdir -p /data /app/backend/media \
    && chown -R appuser:appuser /data /app/backend/media

USER appuser

VOLUME ["/data"]

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/session/', timeout=2)"

CMD ["sh", "-c", "gunicorn backend.wsgi:application --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-2} --access-logfile - --error-logfile -"]
