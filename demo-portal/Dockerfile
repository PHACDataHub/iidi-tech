FROM python:3.8-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    FLASK_APP=app.py \
    FLASK_DEBUG=0 

RUN addgroup --system appgroup && adduser --system --group appuser

WORKDIR /app

COPY requirements.txt /app/
RUN apt-get update && apt-get install -y \
    build-essential \
    && pip install --no-cache-dir -r /app/requirements.txt \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 80

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:80", "app:app"]
