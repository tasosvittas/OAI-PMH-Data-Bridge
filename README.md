# OAI-PMH Data Bridge

A Docker-based bridge application that synchronizes research datasets
from external sources (GitHub, Zenodo) into a fully compliant **OAI-PMH
2.0 repository**.\
Designed for reproducible research, metadata interoperability, and
automated dataset ingestion.

## Features

-   Sync datasets from:
    -   GitHub repositories
    -   Zenodo records
    -   arxiv records
-   Full **OAI-PMH 2.0** data provider
-   Web UI for dataset management
-   Dockerized architecture (PHP/Apache, Flask, Nginx)
-   Dublin Core (oai_dc) metadata support
-   Search and filtering tools
-   Lightweight SQLite backend

## Architecture Overview

The project consists of three main services:

- **OAI-PMH Provider** (PHP/Apache) - OAI-PMH 2.0 compliant repository
- **Bridge Application** (Python/Flask) - Data synchronization interface
- **Nginx** - Reverse proxy and load balancer

## Prerequisites

Install before starting:

-   **Docker Desktop**\
    https://www.docker.com/products/docker-desktop/
-   **Git**

## Quick Start

### 1. Clone the repository

``` bash
git clone https://github.com/YOUR_USERNAME/OAI-PMH-Data-Bridge.git
cd OAI-PMH-Data-Bridge
```


### 2. Build and start the containers

``` bash
docker-compose up -d --build
```

### 3. Wait \~60 seconds for initialization

### 4. Configure Doctrine proxy directory

``` bash
docker-compose exec oai-pmh bash -c "mkdir -p var/generated && chmod -R 777 var"
```

### 5. Restart the OAI-PMH container

``` bash
docker-compose restart oai-pmh
```

## Verification

Check running containers:

``` bash
docker-compose ps
```

## Usage

### Access Points

  ------------------------------------------------------------------------------------------------------
  Service                                     URL
  ------------------------------------------- ----------------------------------------------------------
  Bridge Web Interface                        http://localhost:5000/

  OAI-PMH Repository                          http://localhost/

  ListRecords (oai_dc)                        http://localhost/?verb=ListRecords&metadataPrefix=oai_dc
  ------------------------------------------------------------------------------------------------------

## Bridge Interface Features

-   GitHub repository search\
-   Zenodo dataset search\
-   Dataset import\
-   Record browsing\
-   Health status at `/health`

## Supported OAI-PMH 2.0 Endpoints

-   `?verb=Identify`
-   `?verb=ListMetadataFormats`
-   `?verb=ListRecords&metadataPrefix=oai_dc`
-   `?verb=GetRecord&identifier={ID}&metadataPrefix=oai_dc`
-   `?verb=ListSets`

Example:

``` bash
http://localhost/?verb=ListRecords&metadataPrefix=oai_dc
```

## Project Structure

    OAI-PMH-Data-Bridge/
    ├── bin/                 # CLI tools
    ├── bridge/              # Python Flask bridge application
    ├── config/              # YAML configuration files
    ├── data/                # SQLite database
    ├── docker/              # Docker-level configuration
    ├── public/              # OAI-PMH public directory (PHP)
    ├── src/                 # PHP OAI-PMH source code
    ├── var/                 # Cache and generated proxies
    ├── Dockerfile.php       # PHP/Apache build image
    ├── docker-compose.yml   # Multi-service environment
    └── README.md

## Technology Stack

### Backend

-   PHP 8.1 (Apache)
-   Doctrine ORM
-   Symfony Console
-   Python 3.11 (Flask)

### Database

-   SQLite 3

### Infrastructure

-   Docker & Docker Compose
-   Nginx Reverse Proxy

## Configuration

Edit `config/config.yml` to customize:

-   Repository name and admin e-mail\
-   Database connection settings\
-   Metadata formats\
-   Deleted record policies\
-   Max records per request\
-   Resumption token validity

## Managing the Application

### Stop all services

``` bash
docker-compose down
```

### Restart after initial setup

``` bash
docker-compose up -d
```

## Troubleshooting

### Containers won't start
``` bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Permission errors
``` bash
docker-compose exec oai-pmh bash -c "chmod -R 777 var temp data"
docker-compose restart oai-pmh
```

### Clear cache
``` bash
docker-compose exec oai-pmh php bin/cli oai:clear-cache
```
