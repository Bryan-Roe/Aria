FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir -r /app/requirements.txt \
    && python -m pip install --no-cache-dir pydantic pydantic-settings tenacity

COPY . /app
RUN python -m pip install --no-cache-dir . \
    && groupadd --system non-root \
    && useradd --system --gid non-root --create-home --shell /usr/sbin/nologin non-root \
    && chown -R non-root:non-root /app
EXPOSE 7071
USER non-root
CMD ["python", "local_dev_adapter.py"]
