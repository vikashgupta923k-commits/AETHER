# C:\AETHER\agents\anomaly_detector.py
from collections import deque
from datetime import datetime
from typing import List
from loguru import logger

from core.models import AnomalyEvent, Severity
from core.config import settings


class AnomalyDetector:
    def __init__(self):
        self.history: deque = deque(maxlen=settings.ANOMALY_HISTORY_SIZE)
        self.suspicious_processes = {
            "cryptominer", "miner", "xmrig", "minerd",
            "wannacry", "ransomware", "malware"
        }
        logger.info("AnomalyDetector initialized")

    def analyze(self, snapshot: dict) -> List[AnomalyEvent]:
        anomalies: List[AnomalyEvent] = []
        self.history.append(snapshot)

        cpu = snapshot.get("cpu", {})
        ram = snapshot.get("ram", {})
        disks = snapshot.get("disks", [])
        processes = snapshot.get("top_processes", [])

        # --- CPU Checks ---
        cpu_pct = cpu.get("percent_total", 0)

        if cpu_pct >= settings.CPU_CRITICAL:
            anomalies.append(AnomalyEvent(
                anomaly_type="CPU_CRITICAL",
                severity=Severity.CRITICAL,
                metric_name="cpu.percent_total",
                current_value=cpu_pct,
                threshold_value=settings.CPU_CRITICAL,
                description=f"CPU usage CRITICAL: {cpu_pct:.1f}% (threshold: {settings.CPU_CRITICAL}%)"
            ))
        elif cpu_pct >= settings.CPU_ALERT:
            anomalies.append(AnomalyEvent(
                anomaly_type="CPU_HIGH",
                severity=Severity.HIGH,
                metric_name="cpu.percent_total",
                current_value=cpu_pct,
                threshold_value=settings.CPU_ALERT,
                description=f"CPU usage HIGH: {cpu_pct:.1f}% (threshold: {settings.CPU_ALERT}%)"
            ))

        # CPU Sustained Spike — high for last N readings
        if len(self.history) >= 6:
            recent_cpu = [
                s.get("cpu", {}).get("percent_total", 0)
                for s in list(self.history)[-6:]
            ]
            if all(c >= settings.CPU_ALERT for c in recent_cpu):
                anomalies.append(AnomalyEvent(
                    anomaly_type="CPU_SUSTAINED_SPIKE",
                    severity=Severity.HIGH,
                    metric_name="cpu.percent_total",
                    current_value=cpu_pct,
                    threshold_value=settings.CPU_ALERT,
                    description=f"CPU sustained above {settings.CPU_ALERT}% for last 30 seconds"
                ))

        # --- RAM Checks ---
        ram_pct = ram.get("percent", 0)

        if ram_pct >= settings.RAM_CRITICAL:
            anomalies.append(AnomalyEvent(
                anomaly_type="RAM_CRITICAL",
                severity=Severity.CRITICAL,
                metric_name="ram.percent",
                current_value=ram_pct,
                threshold_value=settings.RAM_CRITICAL,
                description=f"RAM usage CRITICAL: {ram_pct:.1f}% (threshold: {settings.RAM_CRITICAL}%)"
            ))
        elif ram_pct >= settings.RAM_ALERT:
            anomalies.append(AnomalyEvent(
                anomaly_type="RAM_HIGH",
                severity=Severity.HIGH,
                metric_name="ram.percent",
                current_value=ram_pct,
                threshold_value=settings.RAM_ALERT,
                description=f"RAM usage HIGH: {ram_pct:.1f}% (threshold: {settings.RAM_ALERT}%)"
            ))

        # RAM Leak Pattern — consistently increasing over time
        if len(self.history) >= 8:
            recent_ram = [
                s.get("ram", {}).get("percent", 0)
                for s in list(self.history)[-8:]
            ]
            if all(recent_ram[i] < recent_ram[i+1] for i in range(len(recent_ram)-1)):
                if recent_ram[-1] - recent_ram[0] >= 3.0:
                    anomalies.append(AnomalyEvent(
                        anomaly_type="RAM_LEAK_PATTERN",
                        severity=Severity.MEDIUM,
                        metric_name="ram.percent",
                        current_value=ram_pct,
                        threshold_value=recent_ram[0],
                        description=f"RAM leak pattern detected: {recent_ram[0]:.1f}% → {ram_pct:.1f}% over last ~40s"
                    ))

        # --- Disk Checks ---
        for disk in disks:
            disk_pct = disk.get("percent", 0)
            mountpoint = disk.get("mountpoint", "unknown")

            if disk_pct >= settings.DISK_CRITICAL:
                anomalies.append(AnomalyEvent(
                    anomaly_type="DISK_CRITICAL",
                    severity=Severity.CRITICAL,
                    metric_name=f"disk.{mountpoint}.percent",
                    current_value=disk_pct,
                    threshold_value=settings.DISK_CRITICAL,
                    description=f"Disk CRITICAL on {mountpoint}: {disk_pct:.1f}%"
                ))
            elif disk_pct >= settings.DISK_ALERT:
                anomalies.append(AnomalyEvent(
                    anomaly_type="DISK_HIGH",
                    severity=Severity.HIGH,
                    metric_name=f"disk.{mountpoint}.percent",
                    current_value=disk_pct,
                    threshold_value=settings.DISK_ALERT,
                    description=f"Disk HIGH on {mountpoint}: {disk_pct:.1f}%"
                ))

        # --- Process Checks ---
        for proc in processes:
            name = proc.get("name", "").lower()
            cpu_usage = proc.get("cpu_percent", 0)
            pid = proc.get("pid", 0)

            # Suspicious process name
            if any(sus in name for sus in self.suspicious_processes):
                anomalies.append(AnomalyEvent(
                    anomaly_type="SUSPICIOUS_PROCESS",
                    severity=Severity.CRITICAL,
                    metric_name="process.name",
                    current_value=float(pid),
                    threshold_value=0,
                    description=f"Suspicious process detected: {name} (PID: {pid})"
                ))

            # Process hogging CPU
            if cpu_usage > 50.0 and name not in ("system idle process", ""):
                anomalies.append(AnomalyEvent(
                    anomaly_type="PROCESS_CPU_HOG",
                    severity=Severity.HIGH,
                    metric_name=f"process.{name}.cpu_percent",
                    current_value=cpu_usage,
                    threshold_value=50.0,
                    description=f"Process hogging CPU: {name} (PID: {pid}) at {cpu_usage:.1f}%"
                ))

        if anomalies:
            logger.warning(f"Detected {len(anomalies)} anomalies in snapshot")

        return anomalies