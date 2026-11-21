# C:\AETHER\agents\system_agent.py
# AETHER — System Agent v1.0
# Real telemetry collector for Windows

import psutil
import time
import json
import os
from datetime import datetime
from loguru import logger

# Log setup
os.makedirs("C:/AETHER/logs", exist_ok=True)
logger.add("C:/AETHER/logs/system_agent.log", rotation="10 MB", retention="7 days")


class SystemAgent:
    """Real-time system telemetry collector."""

    def __init__(self, interval: int = 5):
        self.interval = interval  # seconds between readings
        self.running = False

    def get_cpu_metrics(self) -> dict:
        return {
            "total_percent": psutil.cpu_percent(interval=1),
            "per_core": psutil.cpu_percent(interval=1, percpu=True),
            "core_count": psutil.cpu_count(logical=False),
            "logical_count": psutil.cpu_count(logical=True),
            "freq_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else None,
        }

    def get_ram_metrics(self) -> dict:
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return {
            "total_gb": round(mem.total / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "percent_used": mem.percent,
            "swap_used_gb": round(swap.used / (1024**3), 2),
            "swap_percent": swap.percent,
        }

    def get_disk_metrics(self) -> list:
        disks = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disks.append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "used_gb": round(usage.used / (1024**3), 2),
                    "free_gb": round(usage.free / (1024**3), 2),
                    "percent_used": usage.percent,
                })
            except PermissionError:
                continue
        return disks

    def get_network_metrics(self) -> dict:
        net = psutil.net_io_counters()
        return {
            "bytes_sent_mb": round(net.bytes_sent / (1024**2), 2),
            "bytes_recv_mb": round(net.bytes_recv / (1024**2), 2),
            "packets_sent": net.packets_sent,
            "packets_recv": net.packets_recv,
            "errors_in": net.errin,
            "errors_out": net.errout,
        }

    def get_top_processes(self, limit: int = 10) -> list:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                info = proc.info
                if info['cpu_percent'] is not None:
                    processes.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # CPU usage ke hisaab se sort karo
        processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
        return processes[:limit]

    def collect_snapshot(self) -> dict:
        """Ek complete system snapshot lega."""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "cpu": self.get_cpu_metrics(),
            "ram": self.get_ram_metrics(),
            "disk": self.get_disk_metrics(),
            "network": self.get_network_metrics(),
            "top_processes": self.get_top_processes(),
        }
        return snapshot

    def save_snapshot(self, snapshot: dict):
        """Snapshot ko JSON file mein save karo."""
        filepath = "C:/AETHER/logs/latest_snapshot.json"
        with open(filepath, "w") as f:
            json.dump(snapshot, f, indent=2)

    def run(self):
        """Continuous monitoring loop."""
        self.running = True
        logger.info("AETHER System Agent started — monitoring your machine...")

        while self.running:
            try:
                snapshot = self.collect_snapshot()
                self.save_snapshot(snapshot)

                # Terminal mein clean output
                print("\n" + "="*55)
                print(f"  AETHER SYSTEM AGENT — {snapshot['timestamp']}")
                print("="*55)
                print(f"  CPU     : {snapshot['cpu']['total_percent']}%  |  Cores: {snapshot['cpu']['logical_count']}")
                print(f"  RAM     : {snapshot['ram']['percent_used']}%  |  Used: {snapshot['ram']['used_gb']} GB / {snapshot['ram']['total_gb']} GB")
                print(f"  SWAP    : {snapshot['ram']['swap_percent']}%")

                print(f"\n  DISK:")
                for d in snapshot['disk']:
                    print(f"    {d['device']} → {d['percent_used']}% used ({d['free_gb']} GB free)")

                print(f"\n  NETWORK:")
                print(f"    Sent: {snapshot['network']['bytes_sent_mb']} MB  |  Recv: {snapshot['network']['bytes_recv_mb']} MB")

                print(f"\n  TOP PROCESSES (by CPU):")
                for p in snapshot['top_processes'][:5]:
                    print(f"    [{p['pid']}] {p['name'][:25]:<25} CPU: {p['cpu_percent']}%  RAM: {round(p['memory_percent'], 1)}%")

                logger.info(f"Snapshot saved — CPU: {snapshot['cpu']['total_percent']}% | RAM: {snapshot['ram']['percent_used']}%")

                time.sleep(self.interval)

            except KeyboardInterrupt:
                logger.info("System Agent stopped by user.")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(2)


if __name__ == "__main__":
    agent = SystemAgent(interval=5)
    agent.run()
