# """Configuration settings"""
# import os

# # Config
# OAI_PMH_CLI = 'C:/xampp82/htdocs/oai-pmh2/bin/cli'
# OAI_PMH_BASE_URL = 'http://localhost/oai-pmh2/public/'
# TEMP_DIR = 'C:/xampp82/htdocs/oai-pmh2/temp'

# # API Tokens (optional)
# ZENODO_TOKEN = os.getenv('ZENODO_TOKEN', '')
# GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')

# # Flask
# FLASK_HOST = '0.0.0.0'
# FLASK_PORT = 5000
# FLASK_DEBUG = True

# # Ensure temp directory exists
# os.makedirs(TEMP_DIR, exist_ok=True)


"""Configuration settings - Docker compatible"""
import os
from pathlib import Path

# Auto-detect if running in Docker
IS_DOCKER = os.path.exists('/.dockerenv')

# Paths
if IS_DOCKER:
    BRIDGE_ROOT = Path('/app')
    OAI_PMH_CLI = '/oai-pmh2/bin/cli'
    TEMP_DIR = '/app/temp'

    OAI_PMH_BASE_URL = os.getenv('OAI_PMH_BASE_URL', 'http://oai-pmh')
else:
    BRIDGE_ROOT = Path(__file__).parent.absolute()
    PROJECT_ROOT = BRIDGE_ROOT.parent
    OAI_PMH_CLI = str(PROJECT_ROOT / 'bin' / 'cli')
    TEMP_DIR = str(PROJECT_ROOT / 'temp')
    OAI_PMH_BASE_URL = os.getenv('OAI_PMH_BASE_URL', 'http://localhost')

# API Tokens
ZENODO_TOKEN = os.getenv('ZENODO_TOKEN', '')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')

# Flask settings
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

# Ensure temp directory exists
os.makedirs(TEMP_DIR, exist_ok=True)

print(f"[Config] Docker: {IS_DOCKER}")
print(f"[Config] CLI: {OAI_PMH_CLI}")
print(f"[Config] Temp: {TEMP_DIR}")
print(f"[Config] OAI-PMH URL: {OAI_PMH_BASE_URL}")
