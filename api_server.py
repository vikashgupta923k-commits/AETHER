import sys
sys.path.insert(0, "C:/AETHER")
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
import json, uvicorn, psutil
from datetime import datetime
from core.database import AETHERDatabase
from agents.anomaly_detector import AnomalyDetector
from agents.ml_detector import MLAnomalyDetector
from recovery.docker_recovery import DockerRecoveryEngine
from loguru import logger

app = FastAPI(title="AETHER Control Plane", version="1.0.0", docs_url="/api/docs", redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

db = AETHERDatabase()
detector = AnomalyDetector()
ml_detector = MLAnomalyDetector()
recovery = DockerRecoveryEngine()

@app.get("/", include_in_schema=False)
def root(): return RedirectResponse("/dashboard")

@app.get("/health")
def health():
    nodes = recovery.get_edge_nodes()
    running = [n for n in nodes if n["status"] == "running"]
    return {"status": "healthy" if len(running) == len(nodes) else "degraded", "nodes_total": len(nodes), "nodes_running": len(running), "timestamp": datetime.utcnow().isoformat()}

@app.get("/nodes")
def get_nodes(): return {"nodes": recovery.get_edge_nodes(), "timestamp": datetime.utcnow().isoformat()}

@app.get("/nodes/{node_name}/stats")
def get_node_stats(node_name: str):
    stats = recovery.get_container_stats(node_name)
    if not stats: raise HTTPException(status_code=404, detail=f"Node {node_name} not found")
    return stats

@app.post("/nodes/{node_name}/restart")
def restart_node(node_name: str):
    result = recovery.restart_container(node_name)
    if not result.get("success"): raise HTTPException(status_code=500, detail=result.get("error"))
    return result

@app.post("/nodes/{node_name}/stop")
def stop_node(node_name: str): return recovery.stop_container(node_name)

@app.get("/snapshot")
def get_snapshot():
    try:
        with open("C:/AETHER/logs/latest_snapshot.json") as f:
            snap = json.load(f)
        anomalies = detector.analyze(snap)
        snap["anomalies"] = [a.dict() for a in anomalies]
        # normalize field names for dashboard
        cpu = snap.get("cpu", {})
        ram = snap.get("ram", {})
        disk = snap.get("disk", [])
        disk0 = disk[0] if isinstance(disk, list) and len(disk) > 0 else {}
        snap["_dash"] = {
            "cpu_percent": cpu.get("total_percent", 0),
            "cpu_cores": cpu.get("logical_count", 0),
            "ram_percent": ram.get("percent_used", 0),
            "ram_used_gb": ram.get("used_gb", 0),
            "ram_total_gb": ram.get("total_gb", 0),
            "disk_percent": disk0.get("percent_used", 0),
            "disk_free_gb": disk0.get("free_gb", 0),
        }
        ml_detector.add_snapshot(snap)
        snap['ml_anomaly'] = ml_detector.predict(snap)
        return snap
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/incidents")
def get_incidents(limit: int = 20):
    return {"incidents": db.get_recent_incidents(limit), "total": len(db.get_recent_incidents(limit))}

@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
def dashboard():
    return open("C:/AETHER/dashboard/index.html", encoding="utf-8").read()

if __name__ == "__main__":
    logger.info("Starting AETHER Control Plane on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")

@app.post("/failure-lab/stop/{container_name}")
def failure_lab_stop(container_name: str):
    result = recovery.stop_container(container_name)
    db.log_audit("failure_lab_stop", container_name, result)
    return result

@app.post("/failure-lab/restart/{container_name}")
def failure_lab_restart(container_name: str):
    result = recovery.restart_container(container_name)
    db.log_audit("failure_lab_restart", container_name, result)
    return result


