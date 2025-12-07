#!/bin/bash

echo "Initializing Docker Swarm..."
docker swarm init

echo "Creating secrets..."
echo "testpass" | docker secret create db_password -
echo "secret-key-12345" | docker secret create secret_key -
echo "admin123!" | docker secret create grafana_password -

echo "Building images..."
docker-compose build

echo "Deploying stack..."
docker stack deploy -c docker-compose.swarm.yml test-env

echo "Stack deployment complete"
docker service ls
