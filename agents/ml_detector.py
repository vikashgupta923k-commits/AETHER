import sys, json, os
sys.path.insert(0, "C:/AETHER")

import numpy as np
from loguru import logger

logger.add("C:/AETHER/logs/ml_detector.log", rotation="5 MB")

class MLAnomalyDetector:
    def __init__(self):
        self.model = None
        self.trained = False
        self.history = []
        self.min_samples = 20
        try:
            from sklearn.ensemble import IsolationForest
            self.IsolationForest = IsolationForest
            logger.info("MLAnomalyDetector initialized — IsolationForest ready")
        except ImportError:
            logger.error("scikit-learn not installed")
            self.IsolationForest = None

    def add_snapshot(self, snapshot: dict):
        cpu = snapshot.get("cpu", {})
        ram = snapshot.get("ram", {})
        disk = snapshot.get("disk", [])
        disk0 = disk[0] if isinstance(disk, list) and disk else {}
        features = [
            float(cpu.get("total_percent", 0)),
            float(ram.get("percent_used", 0)),
            float(disk0.get("percent_used", 0)),
            float(ram.get("used_gb", 0)),
            float(cpu.get("freq_mhz", 0)),
        ]
        self.history.append(features)
        if len(self.history) > 500:
            self.history = self.history[-500:]
        if len(self.history) >= self.min_samples and not self.trained:
            self._train()
        elif len(self.history) % 50 == 0 and self.trained:
            self._train()

    def _train(self):
        if not self.IsolationForest:
            return
        try:
            X = np.array(self.history)
            self.model = self.IsolationForest(
                n_estimators=100,
                contamination=0.05,
                random_state=42
            )
            self.model.fit(X)
            self.trained = True
            logger.success(f"ML model trained on {len(self.history)} samples")
        except Exception as e:
            logger.error(f"Training failed: {e}")

    def predict(self, snapshot: dict) -> dict:
        if not self.trained or not self.model:
            return {"anomaly": False, "score": 0.0, "reason": "model_not_trained", "samples": len(self.history)}
        cpu = snapshot.get("cpu", {})
        ram = snapshot.get("ram", {})
        disk = snapshot.get("disk", [])
        disk0 = disk[0] if isinstance(disk, list) and disk else {}
        features = np.array([[
            float(cpu.get("total_percent", 0)),
            float(ram.get("percent_used", 0)),
            float(disk0.get("percent_used", 0)),
            float(ram.get("used_gb", 0)),
            float(cpu.get("freq_mhz", 0)),
        ]])
        score = float(self.model.score_samples(features)[0])
        prediction = int(self.model.predict(features)[0])
        is_anomaly = prediction == -1
        reason = []
        if cpu.get("total_percent", 0) > 85:
            reason.append("cpu_spike")
        if ram.get("percent_used", 0) > 90:
            reason.append("ram_critical")
        if disk0.get("percent_used", 0) > 90:
            reason.append("disk_critical")
        if is_anomaly and not reason:
            reason.append("pattern_anomaly")
        return {
            "anomaly": is_anomaly,
            "score": round(score, 4),
            "reason": reason,
            "samples_trained": len(self.history),
            "cpu_percent": cpu.get("total_percent", 0),
            "ram_percent": ram.get("percent_used", 0),
        }

if __name__ == "__main__":
    import time
    detector = MLAnomalyDetector()
    snap_path = "C:/AETHER/logs/latest_snapshot.json"
    logger.info("Running ML detector test — feeding 25 snapshots...")
    for i in range(25):
        if os.path.exists(snap_path):
            with open(snap_path) as f:
                snap = json.load(f)
            detector.add_snapshot(snap)
            if i % 5 == 0:
                logger.info(f"Sample {i+1}/25 added")
        time.sleep(0.1)
    result = detector.predict(snap)
    logger.info(f"ML Prediction: {json.dumps(result, indent=2)}")
    print(json.dumps(result, indent=2))
