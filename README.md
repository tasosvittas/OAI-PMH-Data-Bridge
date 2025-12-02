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


## Usage

### Access Points

- **Bridge Web Interface**: http://localhost:5000/
- **OAI-PMH Repository**: http://localhost/
- **List Records**: http://localhost/?verb=ListRecords&metadataPrefix=oai_dc

### Bridge Interface Features

1. **Search GitHub**: Find and import GitHub repositories
2. **Search Zenodo**: Find and import Zenodo datasets
3. **View Records**: Browse imported records
4. **Health Check**: Monitor system status at `/health`

### OAI-PMH Endpoints

Standard OAI-PMH 2.0 verbs are supported:

- `?verb=Identify` - Repository information
- `?verb=ListMetadataFormats` - Available metadata formats
- `?verb=ListRecords&metadataPrefix=oai_dc` - List all records
- `?verb=GetRecord&identifier=ID&metadataPrefix=oai_dc` - Get single record
- `?verb=ListSets` - List available sets

## Project Structure
OAI-PMH-Data-Bridge/
├── bin/ # CLI tools
├── bridge/ # Python Flask bridge application
├── config/ # Configuration files
├── data/ # SQLite database
├── docker/ # Docker configuration
├── public/ # PHP public directory
├── src/ # OAI-PMH PHP source code
├── var/ # Cache and generated files
├── docker-compose.yml # Docker Compose configuration
├── Dockerfile.php # PHP container image
└── README.md # This file


## Technology Stack

### Backend
- PHP 8.1 with Apache
- Doctrine ORM
- Symfony Console
- Python 3.11
- Flask

### Database
- SQLite 3

### Infrastructure
- Docker & Docker Compose
- Nginx

## Configuration

Edit `config/config.yml` to customize:

- Repository name and admin email
- Database connection (default: SQLite)
- Metadata formats
- Deleted records policy
- Maximum records per request
- Resumption token validity

## Stopping the Application

docker-compose down


## Restarting (After Initial Setup)

cd OAI-PMH-Data-Bridge
docker-compose up -d
