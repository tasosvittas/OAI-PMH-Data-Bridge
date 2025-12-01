#!/bin/bash

echo "Starting OAI-PMH2 with Bridge..."

# Build and start services
docker-compose up -d --build

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Show status
docker-compose ps

echo ""
echo "Services started!"
echo ""
echo "OAI-PMH (via Nginx):  http://localhost/"
echo "OAI-PMH (direct):     http://localhost:8080/"
echo "Bridge (via Nginx):   http://localhost/bridge/"
echo "Bridge (direct):      http://localhost:5000/"
echo ""
echo "View logs: docker-compose logs -f"
echo "Stop: docker-compose down"
