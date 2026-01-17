# Kubernetes Deployment Guide

Deploy Quantum AI API to Kubernetes cluster.

## Prerequisites

- Kubernetes cluster (v1.19+)
- kubectl configured
- Docker image built and pushed to registry

## Quick Deploy

```bash
# Build and push image (adjust registry)
make docker-build
docker tag quantum-ai-api:latest your-registry/quantum-ai-api:v1
docker push your-registry/quantum-ai-api:v1

# Update image in k8s/deployment.yaml
# Then deploy
make k8s-apply

# Check status
make k8s-status

# View logs
make k8s-logs
```

## Manual Deployment

```bash
# Create namespace
kubectl create namespace quantum-ai

# Apply manifests
kubectl apply -f k8s/ -n quantum-ai

# Verify
kubectl get all -n quantum-ai -l app=quantum-ai-api
```

## Configuration

### ConfigMap (`k8s/configmap.yaml`)
- `workers`: Number of Gunicorn workers (default: 2)
- `log_level`: Logging level

### Deployment (`k8s/deployment.yaml`)
- Replicas: 2 (adjust for load)
- Resources: 512Mi-1Gi memory, 250m-1000m CPU
- Health checks: liveness + readiness probes
- Volume: PVC for models (read-only)

### Service (`k8s/service.yaml`)
Two services:
- `quantum-ai-api` (ClusterIP): Internal access on port 80
- `quantum-ai-api-lb` (LoadBalancer): External access on port 5050

### Ingress (`k8s/ingress.yaml`)
- Nginx ingress controller
- Host: `quantum-ai.example.com`
- TLS ready (uncomment and add secret)

## Scaling

Manual:
```bash
kubectl scale deployment quantum-ai-api --replicas=5 -n quantum-ai
```

Autoscaling (HPA):
```bash
kubectl autoscale deployment quantum-ai-api \
  --cpu-percent=70 \
  --min=2 \
  --max=10 \
  -n quantum-ai
```

## Persistent Storage

Models stored in PVC (`quantum-ai-models-pvc`):
- Access mode: ReadOnlyMany
- Size: 1Gi (adjust as needed)
- StorageClass: standard (change to your cluster's SC)

Pre-populate PVC:
```bash
# Create a job to copy models
kubectl run copy-models --image=busybox -n quantum-ai -- sleep 3600
kubectl cp results/ quantum-ai/copy-models:/app/results/
kubectl delete pod copy-models -n quantum-ai
```

## Health Checks

Liveness probe:
- Path: `/health`
- Initial delay: 10s
- Period: 30s
- Failure threshold: 3

Readiness probe:
- Path: `/health`
- Initial delay: 5s
- Period: 10s
- Failure threshold: 2

## Troubleshooting

Describe deployment:
```bash
kubectl describe deployment quantum-ai-api -n quantum-ai
```

Pod logs:
```bash
kubectl logs -f deployment/quantum-ai-api -n quantum-ai
```

Exec into pod:
```bash
kubectl exec -it deployment/quantum-ai-api -n quantum-ai -- /bin/bash
```

Port forward for testing:
```bash
kubectl port-forward service/quantum-ai-api 5050:80 -n quantum-ai
curl http://localhost:5050/health
```

## Cleanup

```bash
make k8s-delete
# or
kubectl delete -f k8s/ -n quantum-ai
```

## Production Checklist

- [ ] Update image tag in deployment.yaml
- [ ] Configure resource limits based on load
- [ ] Set up PVC with actual model files
- [ ] Configure ingress with real domain
- [ ] Add TLS certificate secret
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure HPA for autoscaling
- [ ] Set up network policies
- [ ] Configure RBAC permissions
- [ ] Add pod disruption budget
