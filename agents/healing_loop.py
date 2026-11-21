import sys, time, json, uuid, datetime
sys.path.insert(0, "C:/AETHER")

from loguru import logger
from core.database import AETHERDatabase
from core.models import IncidentRecord, IncidentStatus, Severity
from recovery.docker_recovery import DockerRecoveryEngine

logger.add("C:/AETHER/logs/healing_loop.log", rotation="10 MB")

db = AETHERDatabase()
recovery = DockerRecoveryEngine()

logger.info("AETHER Self-Healing Loop started")

while True:
    try:
        nodes = recovery.get_edge_nodes()
        for node in nodes:
            name = node.get("name", "")
            status = node.get("status", "")
            if status != "running":
                logger.warning(f"Node {name} is {status} — triggering auto-recovery")
                start = datetime.datetime.now(datetime.timezone.utc)
                result = recovery.restart_container(name)
                if result.get("success"):
                    mttr = result.get("recovery_time_sec", 0)
                    logger.success(f"Node {name} recovered in {mttr:.2f}s")
                    incident = IncidentRecord(
                        incident_id=str(uuid.uuid4()),
                        node_id=name,
                        anomaly_type="container_down",
                        severity=Severity.HIGH,
                        description=f"Node {name} was {status}, auto-recovered in {mttr:.2f}s",
                        status=IncidentStatus.RESOLVED,
                        recovery_action="auto_restart",
                        mttr_seconds=mttr,
                        detected_at=start,
                        resolved_at=datetime.datetime.now(datetime.timezone.utc)
                    )
                    db.save_incident(incident.dict())
                    logger.info(f"Incident saved for {name}")
                else:
                    logger.error(f"Node {name} recovery FAILED: {result}")
            else:
                logger.debug(f"Node {name} OK")
    except Exception as e:
        logger.error(f"Healing loop error: {e}")
    time.sleep(10)

