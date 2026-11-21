# C:\AETHER\core\database.py
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from loguru import logger


class AETHERDatabase:
    def __init__(self, db_path: str = "C:/AETHER/database/aether.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()
        logger.info(f"Database initialized at {db_path}")

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_tables(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_id TEXT UNIQUE NOT NULL,
                    node_id TEXT DEFAULT 'LOCAL',
                    anomaly_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    status TEXT NOT NULL,
                    description TEXT,
                    detected_at TEXT,
                    resolved_at TEXT,
                    recovery_action TEXT,
                    recovery_result TEXT,
                    auto_resolved INTEGER DEFAULT 0,
                    mttd_seconds REAL,
                    mttr_seconds REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_id TEXT DEFAULT 'LOCAL',
                    timestamp TEXT NOT NULL,
                    cpu_percent REAL,
                    ram_percent REAL,
                    disk_summary TEXT,
                    anomaly_count INTEGER DEFAULT 0,
                    raw_json TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    action TEXT NOT NULL,
                    actor TEXT DEFAULT 'SYSTEM',
                    details TEXT
                )
            """)
            conn.commit()

    def save_incident(self, incident: dict) -> bool:
        try:
            with self._get_conn() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO incidents
                    (incident_id, node_id, anomaly_type, severity, status,
                     description, detected_at, resolved_at, recovery_action,
                     recovery_result, auto_resolved, mttd_seconds, mttr_seconds)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    incident.get("incident_id"),
                    incident.get("node_id", "LOCAL"),
                    incident.get("anomaly_type"),
                    incident.get("severity"),
                    incident.get("status"),
                    incident.get("description"),
                    incident.get("detected_at"),
                    incident.get("resolved_at"),
                    incident.get("recovery_action"),
                    incident.get("recovery_result"),
                    int(incident.get("auto_resolved", False)),
                    incident.get("mttd_seconds"),
                    incident.get("mttr_seconds"),
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"DB save_incident failed: {e}")
            return False

    def save_snapshot(self, snapshot: dict) -> bool:
        try:
            cpu = snapshot.get("cpu", {})
            ram = snapshot.get("ram", {})
            anomalies = snapshot.get("anomalies", [])
            with self._get_conn() as conn:
                conn.execute("""
                    INSERT INTO snapshots
                    (node_id, timestamp, cpu_percent, ram_percent, anomaly_count, raw_json)
                    VALUES (?,?,?,?,?,?)
                """, (
                    snapshot.get("node_id", "LOCAL"),
                    snapshot.get("timestamp", datetime.utcnow().isoformat()),
                    cpu.get("percent_total", 0),
                    ram.get("percent", 0),
                    len(anomalies),
                    json.dumps(snapshot),
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"DB save_snapshot failed: {e}")
            return False

    def get_recent_incidents(self, limit: int = 50) -> List[dict]:
        try:
            with self._get_conn() as conn:
                rows = conn.execute(
                    "SELECT * FROM incidents ORDER BY detected_at DESC LIMIT ?",
                    (limit,)
                ).fetchall()
                cols = [d[0] for d in conn.execute(
                    "SELECT * FROM incidents LIMIT 0"
                ).description or []]
                # get column names properly
                cursor = conn.execute(
                    "SELECT * FROM incidents ORDER BY detected_at DESC LIMIT ?",
                    (limit,)
                )
                col_names = [desc[0] for desc in cursor.description]
                return [dict(zip(col_names, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"DB get_recent_incidents failed: {e}")
            return []

    def get_snapshot_history(self, limit: int = 100) -> List[dict]:
        try:
            with self._get_conn() as conn:
                cursor = conn.execute(
                    "SELECT * FROM snapshots ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                )
                col_names = [desc[0] for desc in cursor.description]
                return [dict(zip(col_names, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"DB get_snapshot_history failed: {e}")
            return []

    def log_audit(self, action: str, actor: str = "SYSTEM", details: str = "") -> bool:
        try:
            with self._get_conn() as conn:
                conn.execute(
                    "INSERT INTO audit_log (timestamp, action, actor, details) VALUES (?,?,?,?)",
                    (datetime.utcnow().isoformat(), action, actor, details)
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"DB log_audit failed: {e}")
            return False