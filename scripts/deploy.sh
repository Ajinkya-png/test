#!/usr/bin/env bash
set -e

# Simple deploy script for local docker-compose deployment
echo "Building Docker images..."
docker-compose build

echo "Starting services..."
docker-compose up -d

echo "Deployment complete. Use 'docker-compose logs -f web' to view app logs."
