# LM Studio MCP Server Configuration Examples

## Local Development

### Environment Variables (Bash/Linux/macOS)

```bash
export LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1
export LMSTUDIO_MODEL=mistral-7b
export LMSTUDIO_TEMPERATURE=0.7
export LMSTUDIO_MAX_TOKENS=2048
```

### Environment Variables (PowerShell/Windows)

```powershell
$env:LMSTUDIO_BASE_URL="http://127.0.0.1:1234/v1"
$env:LMSTUDIO_MODEL="mistral-7b"
$env:LMSTUDIO_TEMPERATURE="0.7"
$env:LMSTUDIO_MAX_TOKENS="2048"
```

### Running the Server

```bash
# Simple run
python lmstudio_mcp_server.py

# With environment variables
LMSTUDIO_MODEL=mistral-7b python lmstudio_mcp_server.py

# With custom port/endpoint
LMSTUDIO_BASE_URL=http://localhost:1234/v1 python lmstudio_mcp_server.py
```

## Remote Development

### Configuration for Remote LM Studio

```bash
# SSH tunnel approach (secure)
ssh -L 8888:localhost:1234 user@remote-host

# Then use local tunnel
export LMSTUDIO_BASE_URL=http://127.0.0.1:8888/v1
python lmstudio_mcp_server.py
```

### Direct Remote Connection (if firewall allows)

```bash
export LMSTUDIO_BASE_URL=http://192.168.1.100:1234/v1
export LMSTUDIO_MODEL=neural-chat-7b
python lmstudio_mcp_server.py
```

## Docker Usage

### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY mcp-requirements.txt .
RUN pip install -r mcp-requirements.txt

# Copy server
COPY lmstudio_mcp_server.py .

# Environment defaults
ENV LMSTUDIO_BASE_URL=http://lmstudio:1234/v1
ENV LMSTUDIO_MODEL=local-model
ENV LMSTUDIO_TEMPERATURE=0.7
ENV LMSTUDIO_MAX_TOKENS=2048

# Run server
CMD ["python", "lmstudio_mcp_server.py"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  lmstudio-mcp:
    build: .
    container_name: lmstudio-mcp
    environment:
      LMSTUDIO_BASE_URL: http://lmstudio:1234/v1
      LMSTUDIO_MODEL: mistral-7b
      LMSTUDIO_TEMPERATURE: "0.7"
      LMSTUDIO_MAX_TOKENS: "2048"
    depends_on:
      - lmstudio
    networks:
      - shared

  lmstudio:
    image: lmstudio:latest  # Placeholder - adjust as needed
    ports:
      - "1234:1234"
    volumes:
      - lmstudio_data:/root/.cache/lms
    networks:
      - shared

volumes:
  lmstudio_data:

networks:
  shared:
```

## GitHub Copilot Configuration

### `.github/copilot-config.yaml`

```yaml
tools:
  - name: lmstudio-mcp
    type: mcp
    command: python
    args:
      - /path/to/lmstudio_mcp_server.py
    environment:
      LMSTUDIO_BASE_URL: http://127.0.0.1:1234/v1
      LMSTUDIO_MODEL: mistral-7b
```

## VS Code Settings

### `.vscode/settings.json`

```json
{
  "pythonPath": ".venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.python",
    "editor.formatOnSave": true
  },
  "python.envFile": "${workspaceFolder}/.env"
}
```

### `.env` file

```
LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1
LMSTUDIO_MODEL=mistral-7b
LMSTUDIO_TEMPERATURE=0.7
LMSTUDIO_MAX_TOKENS=2048
```

## Production Deployment

### Systemd Service (Linux)

Create `/etc/systemd/system/lmstudio-mcp.service`:

```ini
[Unit]
Description=LM Studio MCP Server
After=network.target

[Service]
Type=simple
User=mcp
WorkingDirectory=/opt/lmstudio-mcp
Environment="LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1"
Environment="LMSTUDIO_MODEL=mistral-7b"
ExecStart=/usr/bin/python3 /opt/lmstudio-mcp/lmstudio_mcp_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Start the service:

```bash
sudo systemctl start lmstudio-mcp
sudo systemctl enable lmstudio-mcp
sudo systemctl status lmstudio-mcp
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lmstudio-mcp
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: lmstudio-mcp
  template:
    metadata:
      labels:
        app: lmstudio-mcp
    spec:
      containers:
      - name: lmstudio-mcp
        image: myregistry/lmstudio-mcp:latest
        env:
        - name: LMSTUDIO_BASE_URL
          value: "http://lmstudio-service:1234/v1"
        - name: LMSTUDIO_MODEL
          value: "mistral-7b"
        - name: LMSTUDIO_TEMPERATURE
          value: "0.7"
        - name: LMSTUDIO_MAX_TOKENS
          value: "2048"
        ports:
        - containerPort: 3000
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
```

## Environment Variable Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `LMSTUDIO_BASE_URL` | `http://127.0.0.1:1234/v1` | LM Studio server endpoint |
| `LMSTUDIO_MODEL` | `local-model` | Default model to use |
| `LMSTUDIO_TEMPERATURE` | `0.7` | Sampling temperature (0.0-2.0) |
| `LMSTUDIO_MAX_TOKENS` | `2048` | Maximum tokens in response |

## Troubleshooting Configuration

### Connection Issues

```bash
# Test connectivity
curl http://127.0.0.1:1234/v1/models

# Check firewall (if remote)
telnet 127.0.0.1 1234

# View server logs
tail -f /path/to/lmstudio/logs
```

### Model Not Found

```bash
# List available models
curl http://127.0.0.1:1234/v1/models | jq .data[].id

# Update LMSTUDIO_MODEL to match output
export LMSTUDIO_MODEL=<model-name-from-above>
```

### Performance Tuning

```bash
# For faster responses, reduce max_tokens
export LMSTUDIO_MAX_TOKENS=256

# For more creative responses, increase temperature
export LMSTUDIO_TEMPERATURE=1.0

# For deterministic responses, lower temperature
export LMSTUDIO_TEMPERATURE=0.2
```
