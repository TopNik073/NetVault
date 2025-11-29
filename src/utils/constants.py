from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
STORAGE_DIR = PROJECT_ROOT / 'storage'
USERS_FILE = PROJECT_ROOT / 'users.json'

# Ensure storage directory exists
STORAGE_DIR.mkdir(exist_ok=True)
