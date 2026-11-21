# C:\AETHER\core\config.py
from pydantic_settings import BaseSettings
from pathlib import Path


class AETHERConfig(BaseSettings):
    # --- Thresholds ---
    CPU_ALERT: float = 85.0
    CPU_CRITICAL: float = 95.0
    RAM_ALERT: float = 80.0
    RAM_CRITICAL: float = 92.0
    DISK_ALERT: float = 85.0
    DISK_CRITICAL: float = 95.0

    # --- Recovery Policy ---
    AUTO_RESTART_ENABLED: bool = True
    MAX_AUTO_RESTARTS: int = 3
    RESTART_COOLDOWN_SEC: int = 30

    # --- Paths ---
    BASE_DIR: Path = Path("C:/AETHER")
    DB_PATH: str = "C:/AETHER/database/aether.db"
    LOG_DIR: Path = Path("C:/AETHER/logs")

    # --- API ---
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # --- Monitoring ---
    COLLECTION_INTERVAL_SEC: int = 5
    ANOMALY_HISTORY_SIZE: int = 12  # 12 readings = ~1 min

    class Config:
        env_file = "C:/AETHER/.env"
        case_sensitive = True


# Singleton instance
settings = AETHERConfig()