# Deployment

For local dev:
1. Copy `.env.example` to `.env` and fill keys.
2. Start `docker-compose up --build`.

For Kubernetes:
- Build and push images.
- Apply manifests in `kubernetes/` (customize secrets).
