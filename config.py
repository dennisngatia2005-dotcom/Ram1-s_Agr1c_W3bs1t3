"""config.py — Application and database configuration."""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY   = os.getenv("SECRET_KEY",  "agrisoc-change-in-production-2024")
    DB_USER      = os.getenv("DB_USER",     "agrisoc")
    DB_PASS      = os.getenv("DB_PASS",     "agrisoc123")
    DB_DSN       = os.getenv("DB_DSN",      "localhost:1521/XEPDB1")
    DB_POOL_MIN  = int(os.getenv("DB_POOL_MIN", "2"))
    DB_POOL_MAX  = int(os.getenv("DB_POOL_MAX", "10"))
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin2024")
    DEBUG        = os.getenv("FLASK_DEBUG", "true").lower() == "true"