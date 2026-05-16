import os
from pathlib import Path

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Output directory for downloads
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Target URL
# We use the Bizagi URL which redirects to SSO if needed
URL = "https://digital-coordinador.bizagi.com/"

# Credentials - load from environment variables
# Set APP_USERNAME and APP_PASSWORD in your environment or a .env file (never commit credentials)
USERNAME = os.environ.get("APP_USERNAME")
PASSWORD = os.environ.get("APP_PASSWORD")
