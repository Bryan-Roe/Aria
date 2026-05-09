FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir -r /app/requirements.txt

COPY . /app
RUN python -m pip install --no-cache-dir .
EXPOSE 7071
USER non-root
CMD ["python", "local_dev_adapter.py"]
