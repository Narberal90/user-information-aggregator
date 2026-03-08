FROM python:3.11-slim

WORKDIR /app

RUN addgroup --system appgroup && \
    adduser \
    --disabled-password \
    --no-create-home \
    --ingroup appgroup \
    appuser

RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R appuser:appgroup /app

USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
