#!/bin/bash

set -e

echo "Building Docker images..."
docker-compose build

echo "Stopping existing containers..."
docker-compose down

echo "Starting services..."
docker-compose up -d

echo "Waiting for services..."
sleep 10

echo "Running health checks..."
docker-compose ps

echo "Deployment complete"
echo "Access the application at http://localhost"
echo "Grafana: http://localhost:3000"
echo "Prometheus: http://localhost:9090"
