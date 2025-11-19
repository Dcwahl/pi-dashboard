import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from contextlib import contextmanager
import os

# Use data directory for database, create if doesn't exist
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "metrics.db"

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    """Initialize the database with required tables"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Metrics table for system metrics (CPU, memory, disk, temp, network)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                metric_type TEXT NOT NULL,
                data TEXT NOT NULL
            )
        """)

        # Docker metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS docker_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                container_id TEXT,
                container_name TEXT,
                data TEXT NOT NULL
            )
        """)

        # Create indexes for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_metrics_timestamp
            ON metrics(timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_metrics_type_timestamp
            ON metrics(metric_type, timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_docker_timestamp
            ON docker_metrics(timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_docker_container_timestamp
            ON docker_metrics(container_name, timestamp)
        """)

        conn.commit()

def insert_metric(metric_type: str, data: dict, timestamp: float = None):
    """Insert a metric into the database"""
    if timestamp is None:
        timestamp = datetime.now().timestamp()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO metrics (timestamp, metric_type, data) VALUES (?, ?, ?)",
            (timestamp, metric_type, json.dumps(data))
        )
        conn.commit()

def insert_docker_metric(container_id: str, container_name: str, data: dict, timestamp: float = None):
    """Insert a Docker metric into the database"""
    if timestamp is None:
        timestamp = datetime.now().timestamp()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO docker_metrics (timestamp, container_id, container_name, data) VALUES (?, ?, ?, ?)",
            (timestamp, container_id, container_name, json.dumps(data))
        )
        conn.commit()

def get_metrics_range(metric_type: str, start_time: float, end_time: float = None):
    """Get metrics for a specific type within a time range"""
    if end_time is None:
        end_time = datetime.now().timestamp()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT timestamp, data
            FROM metrics
            WHERE metric_type = ? AND timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp ASC
            """,
            (metric_type, start_time, end_time)
        )

        results = []
        for row in cursor.fetchall():
            results.append({
                "timestamp": row["timestamp"],
                "data": json.loads(row["data"])
            })

        return results

def get_docker_metrics_range(container_name: str, start_time: float, end_time: float = None):
    """Get Docker metrics for a specific container within a time range"""
    if end_time is None:
        end_time = datetime.now().timestamp()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT timestamp, data
            FROM docker_metrics
            WHERE container_name = ? AND timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp ASC
            """,
            (container_name, start_time, end_time)
        )

        results = []
        for row in cursor.fetchall():
            results.append({
                "timestamp": row["timestamp"],
                "data": json.loads(row["data"])
            })

        return results

def cleanup_old_data(days: int = 7):
    """Delete metrics older than specified days"""
    cutoff_time = (datetime.now() - timedelta(days=days)).timestamp()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM metrics WHERE timestamp < ?", (cutoff_time,))
        cursor.execute("DELETE FROM docker_metrics WHERE timestamp < ?", (cutoff_time,))
        deleted_count = cursor.rowcount
        conn.commit()

        return deleted_count