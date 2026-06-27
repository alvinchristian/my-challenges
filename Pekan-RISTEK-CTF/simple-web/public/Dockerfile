
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

RUN groupadd -r app && useradd --no-log-init -r -g app app
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt

COPY ./src /app

RUN mkdir -p /app/data /app/reports && \
    chown -R app:app /app && \
    chmod -R 755 /app


USER app

CMD ["python", "app.py"]
