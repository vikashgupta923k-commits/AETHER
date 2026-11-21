import sys, uuid
from datetime import datetime
sys.path.insert(0, "C:/AETHER")
from core.database import AETHERDatabase
from core.models import IncidentStatus, Severity
from agents.anomaly_detector import AnomalyDetector
from recovery.docker_recovery import DockerRecoveryEngine
from loguru import logger
import json

class IncidentManager:
    def __init__(self):
        self.db = AETHERDatabase()
        self.detector = AnomalyDetector()
        self.recovery = DockerRecoveryEngine()
        logger.info("IncidentManager initialized")

    def run_once(self):
        with open("C:/AETHER/logs/latest_snapshot.json") as f:
            snap = json.load(f)
        anomalies = self.detector.analyze(snap)
        nodes = self.recovery.get_edge_nodes()
        for node in nodes:
            if node["status"] != "running":
                logger.critical(f"Container DOWN: {node['name']} - auto-recovering")
                self.recovery.restart_container(node["name"])
        incidents = self.db.get_recent_incidents(10)
        return anomalies, incidents

if __name__ == "__main__":
    mgr = IncidentManager()
    anomalies, incidents = mgr.run_once()
    print("Anomalies:", len(anomalies))
    print("DB incidents:", len(incidents))
    print("All nodes:")
    from recovery.docker_recovery import DockerRecoveryEngine
    e = DockerRecoveryEngine()
    for n in e.get_edge_nodes():
        print(" ", n["node"], n["status"])
    print("AETHER OK.")
