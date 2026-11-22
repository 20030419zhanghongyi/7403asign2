# 集成与容错章节

摘自[项目报告](../report/Project_II_Group_2.pdf)。成员贡献见报告第 6 节。

## 2 Deployment and networking

| Component | Deployment responsibility |
| --- | --- |
| nginx | Official nginx:alpine image; only published port is host 6120 to container 80. |
| backend1 / backend2 | Same application image; unique INSTANCE_NAME; no host port bindings. |
| app_net | Compose bridge network; Nginx reaches services by backend1:5000 and backend2:5000. |

The default Compose file starts all three containers with one command. Nginx uses a round-robin upstream, a 1-second connection timeout, and retry on connection error or timeout. A separate single-backend Compose file mounts a configuration containing only backend1; mode changes recreate Nginx so the active configuration matches the intended experiment.

```text
docker compose up --build
curl http://localhost:6120/work
docker compose logs --tail=30
```

Source: backend/, nginx/, docker-compose.yml and docker-compose.single.yml. Full commands: README.md and docs/integration_runbook.md.

## 3 Load balancing verification

The load-balancing test sent 40 sequential requests through port 6120, alternating between / and /work. All returned HTTP 200 and valid JSON. Each backend handled 20 requests. The test checks that both instances respond; it does not require the response sequence to alternate strictly.

```text
{"instance":"backend1","status":"ok"}
{"instance":"backend2","status":"ok"}
```

The examples above come from the request log. Each entry records the timestamp, path, HTTP status, responding instance, content type and elapsed time. Container logs record the requests handled by each backend.

## 4 Backend failure and recovery

The failure test kept both servers in the Nginx upstream, stopped backend1 and sent 30 requests. After restarting backend1, it checked that both instances served requests again. The same procedure was then repeated for backend2. The test client used a 3-second timeout.

| State | Responses | Instance distribution | Failures |
| --- | --- | --- | --- |
| Initial dual backend | 20 / 20 | backend1 10; backend2 10 | 0 |
| backend1 stopped | 30 / 30 | backend2 30 | 0 |
| backend1 restored | 20 / 20 | backend1 10; backend2 10 | 0 |
| backend2 stopped | 30 / 30 | backend1 30 | 0 |
| backend2 restored | 20 / 20 | backend1 10; backend2 10 | 0 |

With backend1 stopped, the slowest response took 1055.97 ms; with backend2 stopped, it took 1006.32 ms. All sampled requests succeeded, although switching to the remaining backend could add about one second. Recovery polling also completed without failed requests. Both instances handled requests again after each restart.

## Challenge and correction

The first integrated configuration had no explicit upstream connection timeout. On the same VM and with the same 3-second client limit, stopping backend1 caused 15 of 30 requests to time out; stopping backend2 caused 13 of 30 to time out. The client received no HTTP response for these requests. Nginx logs recorded aborted requests and an unreachable upstream.

Setting proxy_connect_timeout 1s limits the wait for an upstream connection. Nginx can then retry the request on the remaining backend before the client times out. The configuration permits retries on connection errors and timeouts, with at most two upstream attempts [1]. The repeated tests shown above had no failed requests.

## Test commands and records

```text
bash scripts/check_balance.sh
bash scripts/check_failover.sh
```

Run ID: 20261120T153935Z-31487. Summaries, requests.jsonl, active Nginx configurations and container logs are in results/load_balancing/<run ID>/ and results/fault_tolerance/<run ID>/. The latter also includes stop/start records. Tests before the timeout correction are in results/fault_tolerance/pre-fix-20261120/.
