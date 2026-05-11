FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir -r /app/requirements.txt

COPY . /app
RUN addgroup --system non-root \
    && adduser --system --ingroup non-root --home /app non-root \
    && chown -R non-root:non-root /app
EXPOSE 8080
USER non-root
CMD ["python", "apps/aria/server.py"]
