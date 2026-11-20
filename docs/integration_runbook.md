# Integration & Experiment Runbook

## 1. Start Full Stack (Nginx + 2 Backends)
Run:
- `docker compose up --build -d`
- `docker compose ps`

## 2. Switch Between 1 Backend and 2 Backends
- Run with 1 backend (`backend2` only): `docker compose stop backend1`
- Restore 2 backends (`backend1` + `backend2`): `docker compose start backend1`

## 3. Fault Recovery & Cleanup
- Check container logs: `docker compose logs -f`
- Restart a stopped backend: `docker compose start backend1` (or `docker compose start backend2`)
- Stop and remove containers and network: `docker compose down`
