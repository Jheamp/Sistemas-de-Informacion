"""
database.py — Pool de conexiones PostgreSQL para ERP-CRM
Utiliza psycopg3 (psycopg[binary]) con python-dotenv.
"""

import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

# ─── DSN construido desde variables de entorno ───────────────
DSN = (
    f"host={os.getenv('DB_HOST', 'localhost')} "
    f"port={os.getenv('DB_PORT', '5432')} "
    f"dbname={os.getenv('DB_NAME', 'erp_crm_db')} "
    f"user={os.getenv('DB_USER', 'erp_user')} "
    f"password={os.getenv('DB_PASSWORD', '')} "
)

# ─── Pool de conexiones (ConnectionPool de psycopg3) ─────────
from psycopg_pool import ConnectionPool

pool: ConnectionPool = None


def init_pool():
    """Inicializa el pool al arrancar FastAPI."""
    global pool
    pool = ConnectionPool(
        conninfo=DSN,
        min_size=2,
        max_size=10,
        kwargs={"row_factory": dict_row},
    )


def get_conn():
    """Context manager: devuelve una conexión del pool."""
    return pool.connection()
