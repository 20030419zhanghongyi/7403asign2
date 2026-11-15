"""Single-process, single-threaded backend for the CISC 7403 experiment."""

import json
import os
import socket
import time

from flask import Flask, g, jsonify, request

app = Flask(__name__, static_folder=None)
INSTANCE_NAME = os.environ.get("INSTANCE_NAME") or socket.gethostname()
WORK_SECONDS = 0.05


@app.before_request
def start_timer():
    g.started_at = time.perf_counter()


@app.after_request
def log_request(response):
    print(json.dumps({
        "event": "request",
        "instance": INSTANCE_NAME,
        "method": request.method,
        "path": request.path,
        "status": response.status_code,
        "elapsed_ms": round((time.perf_counter() - g.started_at) * 1000, 3),
    }), flush=True)
    return response


@app.get("/")
def index():
    return jsonify(instance=INSTANCE_NAME, status="ok")


@app.get("/work")
def work():
    time.sleep(WORK_SECONDS)
    return jsonify(instance=INSTANCE_NAME, status="ok")


if __name__ == "__main__":
    print(json.dumps({
        "event": "startup",
        "instance": INSTANCE_NAME,
        "work_seconds": WORK_SECONDS,
        "processes": 1,
        "threaded": False,
    }), flush=True)
    # These settings are required for the course's horizontal-scaling comparison.
    app.run(host="0.0.0.0", port=5000, processes=1, threaded=False,
            debug=False, use_reloader=False, load_dotenv=False)
