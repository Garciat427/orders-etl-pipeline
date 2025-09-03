"""
Configuration file for the Related Items Pipeline.
Contains all configurable settings and constants.
"""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
DB_DIR = PROJECT_ROOT / "db"
SRC_DIR = PROJECT_ROOT / "src"
DAGS_DIR = PROJECT_ROOT / "dags"

# Data files
ORDERS_CSV_PATH = DATA_DIR / "orders.csv"
RELATED_ITEMS_JSON_PATH = DATA_DIR / "related_items.json"

# Database configuration
DATABASE_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "airflow"),
    "user": os.getenv("DB_USER", "airflow"),
    "password": os.getenv("DB_PASSWORD", "airflow"),
}

# Connection string
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"
)

# Pipeline configuration
MAX_RECOMMENDATIONS_PER_ITEM = int(os.getenv("MAX_RECOMMENDATIONS_PER_ITEM", "10"))
MIN_CONFIDENCE_THRESHOLD = float(os.getenv("MIN_CONFIDENCE_THRESHOLD", "0.1"))

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Airflow configuration
AIRFLOW_UID = int(os.getenv("AIRFLOW_UID", "50000"))
AIRFLOW_GID = int(os.getenv("AIRFLOW_GID", "0"))

# Sample data configuration
SAMPLE_DATA_ENABLED = os.getenv("SAMPLE_DATA_ENABLED", "true").lower() == "true"
