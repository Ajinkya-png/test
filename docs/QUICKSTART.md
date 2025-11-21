# Quickstart

1. Clone repo.
2. Copy `.env.example` -> `.env`.
3. Run `scripts/setup_environment.sh` and `scripts/init_db.py`.
4. Start services: `docker-compose up --build`.
5. Test health: `curl http://localhost:8000/api/v1/monitoring/health`.
