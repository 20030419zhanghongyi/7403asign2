"""Exercise the real HTTP servers from another container on their Docker network."""

import concurrent.futures
import json
import threading
import time
import urllib.error
import urllib.request


def get(service, path="/"):
    start = time.perf_counter()
    with urllib.request.urlopen(f"http://{service}:5000{path}", timeout=10) as response:
        assert response.status == 200, response.status
        assert response.headers.get_content_type() == "application/json"
        body = json.load(response)
    return body, time.perf_counter() - start


def check_identity(body, expected):
    assert body.get("instance") == expected, body
    assert body.get("status") == "ok", body


for service, expected in [("backend1", "backend1"), ("backend2", "backend2"),
                          ("fallback", "fallback-host")]:
    for attempt in range(50):
        try:
            body, _ = get(service)
            break
        except (urllib.error.URLError, TimeoutError):
            if attempt == 49:
                raise
            time.sleep(0.1)
    check_identity(body, expected)
    print(json.dumps({"check": "identity", "service": service, "response": body}), flush=True)
    samples = []
    for _ in range(3):
        body, elapsed = get(service, "/work")
        check_identity(body, expected)
        assert elapsed >= 0.045, f"/work returned too quickly: {elapsed}s"
        samples.append(round(elapsed * 1000, 3))
    print(json.dumps({"check": "work_delay", "service": service,
                      "latency_ms": samples}), flush=True)

# Simultaneous clients must queue behind a single request handler. This is a
# correctness check, not the later single-vs-dual-backend wrk benchmark.
clients = 6
gate = threading.Barrier(clients + 1)


def concurrent_request():
    gate.wait(timeout=10)
    body, elapsed = get("backend1", "/work")
    check_identity(body, "backend1")
    return elapsed


with concurrent.futures.ThreadPoolExecutor(max_workers=clients) as pool:
    futures = [pool.submit(concurrent_request) for _ in range(clients)]
    started = time.perf_counter()
    gate.wait(timeout=10)
    latencies = sorted(f.result() for f in futures)
    total = time.perf_counter() - started
assert total >= clients * 0.045, f"Requests appear concurrent: {total}s"
assert latencies[-1] - latencies[0] >= (clients - 1) * 0.04, latencies
print(json.dumps({"check": "serial_requests", "clients": clients,
                  "total_ms": round(total * 1000, 3),
                  "latency_ms": [round(t * 1000, 3) for t in latencies]}), flush=True)
print("PASS: HTTP contracts, instance names, hostname fallback, delay and serial requests", flush=True)
