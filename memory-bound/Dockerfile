FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

ENV WORKERS=2
EXPOSE 1602

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 1602 --workers ${WORKERS}"]
