# AETHER — Self-Healing AI-Native Edge-Cloud Continuum Platform

> Autonomous infrastructure monitoring, ML anomaly detection, and self-healing orchestration for edge-cloud environments.

![Python](https://img.shields.io/badge/Python-3.11+-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green) ![Docker](https://img.shields.io/badge/Docker-SDK-blue) ![ML](https://img.shields.io/badge/ML-IsolationForest-purple)

## What is AETHER?

AETHER is a production-grade autonomous infrastructure platform that:

- **Monitors** real-time system telemetry (CPU, RAM, Disk, Network) via psutil
- **Detects** anomalies using ML (IsolationForest) trained on live system patterns
- **Heals** failed containers automatically with MTTR tracking
- **Logs** every incident to a persistent SQLite audit trail
- **Visualizes** everything on a live purple-black dashboard

## Quick Start

\\\ash
git clone https://github.com/vikashgupta923k-commits/AETHER.git
cd AETHER
python -m venv venv
venv\Scripts\activate
pip install fastapi uvicorn psutil docker sqlalchemy pydantic loguru scikit-learn numpy
\\\

\\\powershell
# Terminal 1
python api_server.py

# Terminal 2
python agents/healing_loop.py

# Terminal 3 - spawn edge nodes
docker run -d --name EDGE-01 nginx
docker run -d --name EDGE-02 nginx
docker run -d --name EDGE-03 nginx
\\\

Open dashboard/index.html in browser.

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| /snapshot | GET | Full system telemetry + ML anomaly status |
| /health | GET | Platform health check |
| /nodes | GET | All Docker edge node statuses |
| /incidents | GET | Incident history with MTTR |
| /nodes/{name}/restart | POST | Restart a node |
| /failure-lab/stop/{name} | POST | Simulate node failure |
| /failure-lab/restart/{name} | POST | Manual recovery trigger |

## Tech Stack

| Component | Technology |
|-----------|------------|
| API | FastAPI + uvicorn |
| Telemetry | psutil |
| ML | scikit-learn IsolationForest |
| Containers | Docker SDK for Python |
| Database | SQLite + SQLAlchemy |
| Models | Pydantic v2 |
| Logging | loguru |
| Dashboard | Vanilla JS + CSS |

## Author

**Vikash Gupta** — vikashgupta923k@gmail.com

## License

MIT
