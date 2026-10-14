FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    WEB_CONCURRENCY=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

EXPOSE 8000

CMD ["sh", "-c", "exec uvicorn app:app --app-dir src --host 0.0.0.0 --port ${PORT} --workers ${WEB_CONCURRENCY} --no-access-log"]
