FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        wget \
        gnupg \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

RUN python -m playwright install-deps chromium

COPY . /app/

RUN python manage.py collectstatic --noinput

RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

RUN python -m playwright install chromium

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "BuyBuddy.wsgi:application"]

