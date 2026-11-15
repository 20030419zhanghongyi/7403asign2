#!/usr/bin/env bash
# Run from any directory. Requires Bash, Docker and a Linux VM (sha256sum).
set -Eeuo pipefail

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"
IMAGE=${IMAGE:-cisc7403-backend:v1}
RUN_ID="cisc7403-check-$(date -u +%Y%m%dT%H%M%SZ)-$$"
OUTPUT=${OUTPUT:-"$ROOT/results/backend/$RUN_ID"}
mkdir -p "$OUTPUT"
OUTPUT=$(cd "$OUTPUT" && pwd)
NETWORK="$RUN_ID"
B1="$RUN_ID-backend1"
B2="$RUN_ID-backend2"
FALLBACK="$RUN_ID-fallback"
CLIENT="$RUN_ID-client"
CREATED=()
NETWORK_CREATED=0

cleanup() {
    local status=$?
    trap - EXIT
    for container in "${CREATED[@]}"; do
        docker logs "$container" > "$OUTPUT/$container.log" 2>&1 || true
        docker rm -f "$container" > /dev/null || true
    done
    if (( NETWORK_CREATED )); then
        docker network rm "$NETWORK" > /dev/null || true
    fi
    printf 'exit_code=%s\n' "$status" > "$OUTPUT/result.txt"
    printf 'Evidence: %s (exit %s)\n' "$OUTPUT" "$status"
    exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

{
    date -u +%FT%TZ
    uname -srmo
    cat /etc/os-release
    docker version
    docker compose version
    if command -v wrk > /dev/null; then wrk --version; fi
    git rev-parse HEAD 2>/dev/null || true
    git status --short 2>/dev/null || true
} > "$OUTPUT/environment.txt" 2>&1
sha256sum backend/app.py backend/Dockerfile backend/requirements.txt \
    backend/.dockerignore scripts/check_backend.sh scripts/backend_http_test.py \
    > "$OUTPUT/source.sha256"

docker build --progress=plain -t "$IMAGE" ./backend 2>&1 | tee "$OUTPUT/build.log"
docker image inspect "$IMAGE" --format \
    'id={{.Id}} os={{.Os}} arch={{.Architecture}} user={{.Config.User}} cmd={{json .Config.Cmd}}' \
    > "$OUTPUT/image.txt"
docker network create "$NETWORK" > /dev/null
NETWORK_CREATED=1

docker run -d --name "$B1" --network "$NETWORK" --network-alias backend1 \
    -e INSTANCE_NAME=backend1 "$IMAGE" > /dev/null
CREATED+=("$B1")
docker run -d --name "$B2" --network "$NETWORK" --network-alias backend2 \
    -e INSTANCE_NAME=backend2 "$IMAGE" > /dev/null
CREATED+=("$B2")
docker run -d --name "$FALLBACK" --network "$NETWORK" --network-alias fallback \
    --hostname fallback-host "$IMAGE" > /dev/null
CREATED+=("$FALLBACK")

image1=$(docker inspect --format '{{.Image}}' "$B1")
image2=$(docker inspect --format '{{.Image}}' "$B2")
[[ "$image1" == "$image2" ]]
printf 'Both instances use %s\n' "$image1" > "$OUTPUT/runtime.txt"
for container in "$B1" "$B2" "$FALLBACK"; do
    [[ -z "$(docker port "$container")" ]]
    printf '\n%s: no published ports\n' "$container" >> "$OUTPUT/runtime.txt"
    processes=$(docker top "$container" -eo pid,args)
    printf '%s\n' "$processes" >> "$OUTPUT/runtime.txt"
    [[ $(printf '%s\n' "$processes" | wc -l) -eq 2 ]]
    docker exec "$container" python -c '
import json
from pathlib import Path
status = dict(line.split(":", 1) for line in Path("/proc/1/status").read_text().splitlines())
cmd = Path("/proc/1/cmdline").read_bytes().split(b"\0")
assert int(status["Threads"]) == 1, status["Threads"]
assert cmd[:2] == [b"python", b"app.py"], cmd
assert int(status["Uid"].split()[0]) == 10001, status["Uid"]
print(json.dumps({"pid1": "python app.py", "threads": 1, "uid": 10001}))
' >> "$OUTPUT/runtime.txt"
done

docker run --name "$CLIENT" --network "$NETWORK" \
    --mount "type=bind,src=$ROOT/scripts/backend_http_test.py,dst=/test.py,readonly" \
    "$IMAGE" python /test.py 2>&1 | tee "$OUTPUT/http-tests.log" || {
        CREATED+=("$CLIENT")
        exit 1
    }
CREATED+=("$CLIENT")
for container in "$B1" "$B2" "$FALLBACK"; do
    docker logs "$container" > "$OUTPUT/$container.log" 2>&1
    grep -q '"event": "request".*"path": "/work".*"status": 200' "$OUTPUT/$container.log"
done
docker run --rm "$IMAGE" pip freeze > "$OUTPUT/dependencies.txt"
docker run --rm "$IMAGE" python --version >> "$OUTPUT/dependencies.txt"
printf 'PASS: image, single process/thread, non-root user, internal networking and logs\n' \
    | tee -a "$OUTPUT/http-tests.log"
