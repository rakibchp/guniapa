FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 10001 guniapa \
    && useradd --system --uid 10001 --gid guniapa --home-dir /app guniapa

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=10001:10001 . .
RUN mkdir -p /app/staticfiles && chown -R 10001:10001 /app/staticfiles

USER 10001:10001
EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-"]
