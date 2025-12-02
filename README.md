# OAI-PMH Data Bridge

A Docker-based bridge application that synchronizes research datasets from external repositories (GitHub, Zenodo) to a local OAI-PMH 2.0 repository.

## Features

- Sync datasets from GitHub repositories and Zenodo
- OAI-PMH compliant data provider
- Fully containerized with Docker
- Web interface for easy data management
- Support for Dublin Core metadata format (oai_dc)
- Search and filter capabilities

## Architecture

The project consists of three main services:

- **OAI-PMH Provider** (PHP/Apache) - OAI-PMH 2.0 compliant repository
- **Bridge Application** (Python/Flask) - Data synchronization interface
- **Nginx** - Reverse proxy and load balancer

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker Desktop** - [Download here](https://www.docker.com/products/docker-desktop/)
- **Git** - For cloning the repository

## Quick Start

### Installation
1. Clone the repository
git clone https://github.com/YOUR_USERNAME/OAI-PMH-Data-Bridge.git

2. Navigate to project directory
cd OAI-PMH-Data-Bridge

3. Copy configuration template
copy config\config.dist.yml config\config.yml

4. Build and start containers
docker-compose up -d --build

5. Wait for services to initialize (60 seconds)

6. Configure Doctrine proxies
docker-compose exec oai-pmh bash -c "mkdir -p var/generated && chmod -R 777 var"

8. Restart PHP container
docker-compose restart oai-pmh


### Verification

Check that all services are running:
docker-compose ps


### Test the service:
http://localhost:5000/


