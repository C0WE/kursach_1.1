#!/bin/bash

check_service() {
    local service=$1
    local endpoint=$2

    response=$(curl -s -o /dev/null -w "%{http_code}" "$endpoint")
    if [ "$response" = "200" ] || [ "$response" = "302" ]; then
        echo "✓ $service: OK ($response)"
        return 0
    else
        echo "✗ $service: FAILED ($response)"
        return 1
    fi
}

echo "Checking services..."
check_service "nginx" "http://localhost"
check_service "webapp" "http://localhost/health"
check_service "prometheus" "http://localhost:9090"
check_service "grafana" "http://localhost:3000"

echo "Check complete"
