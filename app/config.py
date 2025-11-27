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

# Credentials
# TODO: In production, load these from environment variables
USERNAME = "facarvajalz@cge.cl"
PASSWORD = "J&99Z9BM10gf"
