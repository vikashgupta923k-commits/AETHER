import docker
import time
from datetime import datetime
from typing import Optional
from loguru import logger


class DockerRecoveryEngine:
    def __init__(self):
        try:
            self.client = docker.from_env()
            self.client.ping()
            logger.info("Docker Recovery Engine connected")
        except Exception as e:
            logger.error(f"Docker connection failed: {e}")
            self.client = None

    def get_edge_nodes(self) -> list:
        if not self.client:
            return []
        try:
            containers = self.client.containers.list(all=True, filters={"label": "aether.monitor=true"})
            result = []
            for c in containers:
                result.append({
                    "id": c.short_id,
                    "name": c.name,
                    "status": c.status,
                    "node": c.labels.get("aether.node", "unknown"),
                    "role": c.labels.get("aether.role", "unknown"),
                })
            return result
        except Exception as e:
            logger.error(f"get_edge_nodes failed: {e}")
            return []

    def restart_container(self, container_name: str, timeout: int = 10) -> dict:
        if not self.client:
            return {"success": False, "error": "Docker not connected"}
        start_time = time.time()
        try:
            container = self.client.containers.get(container_name)
            prior_status = container.status
            logger.warning(f"[RECOVERY] Restarting {container_name}")
            container.stop(timeout=5); container.start()
            for attempt in range(6):
                time.sleep(5)
                container.reload()
                if container.status == "running":
                    elapsed = time.time() - start_time
                    logger.success(f"[RECOVERY] {container_name} recovered in {elapsed:.1f}s")
                    return {"success": True, "container": container_name, "prior_status": prior_status, "new_status": "running", "recovery_time_sec": elapsed, "timestamp": datetime.utcnow().isoformat()}
            return {"success": False, "container": container_name, "error": "Did not recover in 60s"}
        except docker.errors.NotFound:
            return {"success": False, "error": f"{container_name} not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def stop_container(self, container_name: str) -> dict:
        if not self.client:
            return {"success": False, "error": "Docker not connected"}
        try:
            container = self.client.containers.get(container_name)
            container.stop(timeout=5)
            logger.warning(f"[FAILURE-LAB] Stopped: {container_name}")
            return {"success": True, "action": "stopped", "container": container_name}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_container_stats(self, container_name: str) -> Optional[dict]:
        if not self.client:
            return None
        try:
            container = self.client.containers.get(container_name)
            if container.status != "running":
                return None
            stats = container.stats(stream=False)
            cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            sys_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
            num_cpus = stats["cpu_stats"].get("online_cpus", 1)
            cpu_pct = (cpu_delta / sys_delta) * num_cpus * 100 if sys_delta > 0 else 0
            mem_usage = stats["memory_stats"].get("usage", 0)
            mem_limit = stats["memory_stats"].get("limit", 1)
            return {"container": container_name, "cpu_percent": round(cpu_pct, 2), "mem_usage_mb": round(mem_usage / 1024 / 1024, 2), "mem_percent": round((mem_usage / mem_limit) * 100, 2), "status": container.status}
        except Exception as e:
            logger.error(f"get_container_stats failed: {e}")
            return None

