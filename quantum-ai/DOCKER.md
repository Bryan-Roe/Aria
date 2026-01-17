# Quantum AI API - Docker Setup

Docker deployment for the Quantum ML Fraud Detection API.

## Quick Start

Build and run:
```bash
cd quantum-ai
make docker-build
make docker-run
```

Test:
```bash
curl http://localhost:5050/health
```

Stop:
```bash
make docker-stop
```

## Manual Docker Commands

Build image:
```bash
docker build -t quantum-ai-api:latest .
```

Run container:
```bash
docker run -d \
  --name quantum-ai-api \
  -p 5050:5050 \
  -v $(pwd)/results:/app/results:ro \
  quantum-ai-api:latest
```

## Docker Compose

Using docker-compose (recommended):
```bash
# Start (detached)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Custom port
PORT=8080 docker-compose up -d
```

## Configuration

Environment variables in `docker-compose.yml`:
- `PORT` - API port (default: 5050)
- `WORKERS` - Gunicorn workers (default: 2)

Volume mounts:
- `./results` → `/app/results` (read-only models)
- `./logs` → `/app/logs` (persistent logs)

## Health Checks

Built-in Docker health check:
```bash
docker inspect --format='{{.State.Health.Status}}' quantum-ai-api
```

Manual health check:
```bash
docker exec quantum-ai-api curl -f http://localhost:5050/health
```

## Troubleshooting

View logs:
```bash
docker logs -f quantum-ai-api
```

Shell into container:
```bash
docker exec -it quantum-ai-api /bin/bash
```

Rebuild from scratch:
```bash
docker-compose down
docker rmi quantum-ai-api:latest
make docker-build
make docker-run
```

## Production Notes

- Image runs as non-root user (`apiuser`)
- Health checks every 30s with 3 retries
- Automatic restart on failure
- Models mounted read-only for safety
- Logs persisted to host
