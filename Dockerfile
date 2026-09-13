FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt requirements-docker.txt ./
RUN pip install --no-cache-dir -r requirements-docker.txt

RUN useradd --create-home --uid 10001 appuser
COPY app.py ./
COPY templates/ ./templates/
COPY static/ ./static/

USER appuser
EXPOSE 5000

# A single worker keeps the in-memory CSV cache shared between requests.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
