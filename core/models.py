# C:\AETHER\core\models.py
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional, List


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStatus(str, Enum):
    DETECTED = "DETECTED"
    ANALYSING = "ANALYSING"
    RECOVERING = "RECOVERING"
    RESOLVED = "RESOLVED"
    FAILED = "FAILED"
    MANUAL_REQUIRED = "MANUAL_REQUIRED"


class AnomalyEvent(BaseModel):
    anomaly_type: str
    severity: Severity
    metric_name: str
    current_value: float
    threshold_value: float
    description: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    node_id: str = "LOCAL"


class SystemSnapshot(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    node_id: str = "LOCAL"
    cpu: dict
    ram: dict
    disks: list
    network: dict
    top_processes: list
    anomalies: List[AnomalyEvent] = []


class IncidentRecord(BaseModel):
    incident_id: str
    node_id: str = "LOCAL"
    anomaly_type: str
    severity: Severity
    status: IncidentStatus = IncidentStatus.DETECTED
    description: str
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    recovery_action: Optional[str] = None
    recovery_result: Optional[str] = None
    auto_resolved: bool = False
    mttd_seconds: Optional[float] = None  # Mean Time to Detect
    mttr_seconds: Optional[float] = None  # Mean Time to Recover