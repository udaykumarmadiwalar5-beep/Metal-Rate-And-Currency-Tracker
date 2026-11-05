import mysql.connector
import os
from mysql.connector import Error as MySQLError

# ─────────────────────────────────────────────────────────────
#  DB CONFIG
# ─────────────────────────────────────────────────────────────
DB_CONFIG = {
    "host":             os.getenv("DB_HOST",     "localhost"),
    "port":             int(os.getenv("DB_PORT", 3306)),
    "user":             os.getenv("DB_USER",     "root"),
    "password":         os.getenv("DB_PASSWORD", "Uday@2004"),  # ← update if changed
    "database":         os.getenv("DB_NAME",     "metalcur"),
    "connection_timeout": 5,      # fail fast
    "connect_timeout":    5,
}

def get_db():
    """Open a new DB connection. Raises MySQLError on failure."""
    return mysql.connector.connect(**DB_CONFIG)
