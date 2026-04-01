FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ingestor.py .
COPY app/config.py .
COPY app/api.py .

CMD ["sleep", "infinity"]