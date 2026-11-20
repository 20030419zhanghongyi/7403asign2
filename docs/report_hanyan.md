# HAN YAN 集成与容错章节

以下整理最终系统的集成与容错部分。HAN YAN 的原始提交完成初始 Nginx、Compose 与运行说明；后续补全与实验由 ZHANG HONGYI 分支统一整理，实际贡献以最终报告为准。

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

The final acceptance run sent 40 sequential requests, alternating between / and /work, through port 6120. All returned HTTP 200 and valid JSON. backend1 handled 20 requests and backend2 handled 20. The requirement is that both instances receive requests; strict alternation is not assumed by the check.

```text
{"instance":"backend1","status":"ok"}
{"instance":"backend2","status":"ok"}
```

These response bodies are reproduced from the recorded successful requests. The request file includes timestamps, paths, HTTP status, instance, content type and elapsed time; backend container logs provide corresponding request evidence.

## 4 Backend failure and recovery

With both upstream entries retained, the experiment stopped backend1, sent 30 requests, restarted it and verified that both instances served requests again. It repeated the same procedure for backend2. The diagnostic client used a 3-second timeout; this is our acceptance threshold, not a time limit specified by the assignment.

| State | Responses | Instance distribution | Failures |
| --- | --- | --- | --- |
| Initial dual backend | 20 / 20 | backend1 10; backend2 10 | 0 |
| backend1 stopped | 30 / 30 | backend2 30 | 0 |
| backend1 restored | 20 / 20 | backend1 10; backend2 10 | 0 |
| backend2 stopped | 30 / 30 | backend1 30 | 0 |
| backend2 restored | 20 / 20 | backend1 10; backend2 10 | 0 |

The maximum response times while backend1 and backend2 were stopped were 1055.97 ms and 1006.32 ms respectively. Thus availability was preserved in these samples, but failover was not instantaneous. Recovery polling also succeeded without failed requests; after the passive failure window, the restarted instances rejoined request handling.

## Challenge and correction

Before the correction, the merged configuration had no explicit connection timeout. In the same VM, stopping backend1 produced 15 client timeouts in 30 attempts, and stopping backend2 produced 13 in 30, using the same 3-second diagnostic limit. These were client timeouts, not observed HTTP 504 responses. Nginx logs showed aborted requests and an unreachable stopped upstream.

Adding proxy_connect_timeout 1s lets connection failure be detected within the client threshold, after which Nginx can try the surviving backend. The final configuration explicitly allows error/timeout retries and at most two upstream attempts [1]. No automatic container restart or high-availability Nginx was added, as neither is required.

## Evidence and reproduction

```text
bash scripts/check_balance.sh
bash scripts/check_failover.sh
```

Final run ID: 20261120T153935Z-31487. See results/load_balancing/<run ID>/ and results/fault_tolerance/<run ID>/ for summaries, requests.jsonl, effective Nginx configuration, stop/start records and container logs. Earlier failure evidence is retained in results/fault_tolerance/pre-fix-20261120/.
