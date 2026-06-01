FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8088

CMD ["python", "main.py", "--server"]
