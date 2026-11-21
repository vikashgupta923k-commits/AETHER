from flask import Flask, jsonify
import datetime
app = Flask(__name__)

@app.route("/")
def index():
    return jsonify({"node": "EDGE-02", "status": "healthy", "time": str(datetime.datetime.utcnow())})

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
