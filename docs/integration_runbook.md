# 集成运行与实验说明

## 环境与默认部署

在课程 Ubuntu 虚拟机安装 Docker Engine、Compose v2、Python 3、curl 和 wrk。默认项目名为 `cisc7403-project2`；两个 Compose 文件和所有实验脚本都使用该名称。如设置 `COMPOSE_PROJECT_NAME`，应在所有命令中保持一致。端口 6120 必须空闲。

```bash
docker compose up --build
```

后台运行使用 `docker compose up --build -d`。默认启动 nginx、backend1、backend2，只有 Nginx 发布 6120:80；后端共用 `cisc7403-backend:v1`，通过 `app_net` 访问。

```bash
docker compose ps
curl http://localhost:6120/
curl http://localhost:6120/work
docker compose exec nginx nginx -t
docker compose logs --tail=30 nginx backend1 backend2
```

## 正式实验

脚本需在 Linux 虚拟机执行，调用者必须能使用 Docker。可从任意目录通过脚本的完整路径运行。

```bash
bash scripts/check_balance.sh
bash scripts/check_failover.sh
bash scripts/benchmark.sh
# 或依次运行全部三个实验
bash scripts/run_all.sh
```

脚本会重新创建本项目容器并产生新证据目录，完成后恢复默认双后端，保留服务运行。它们不停止其他 Compose 项目。实验期间不要同时手工停容器或启动另一组压测。

- 负载均衡：40 次请求交替访问 `/` 和 `/work`，全部须返回成功 JSON，两个实例都须出现。
- 容错：先确认双后端，再分别停止 backend1/backend2；每种停止状态发出 30 次请求，检查全由存活实例响应；重启并确认两个实例重新处理请求。保留双 upstream。
- 请求诊断的客户端超时为 3 秒，属于本项目验收阈值，不是老师指定时限。Nginx 上游连接超时为 1 秒，并允许连接错误或超时时尝试另一节点。
- 性能：单、双后端交替进行 3 组试验。每轮预热 3 秒、等待 2 秒排空预热请求，再使用完全相同的 `wrk -t2 -c20 -d10s --timeout 5s --latency http://127.0.0.1:6120/work` 测量。报告列出每轮和三轮算术平均值，检查连接错误、超时及非成功响应。

记录分别在 `results/load_balancing/`、`results/fault_tolerance/`、`results/performance/`，每次执行创建独立的时间戳目录。`results/acceptance/` 同时记录环境、源码 SHA-256 和测试汇总。测试失败时保留原始输出，并尝试恢复双后端。

## 正确的单后端性能模式

```bash
bash scripts/set_mode.sh single
```

该命令使用独立的 `docker-compose.single.yml`（不是覆盖文件），只运行 backend1 与 nginx，挂载 `nginx/nginx.single.conf`，upstream 只有 backend1。切换会重建 Nginx，避免沿用旧配置。

```bash
docker compose -f docker-compose.single.yml ps
docker compose -f docker-compose.single.yml exec nginx nginx -T
curl http://localhost:6120/
```

恢复双后端：

```bash
bash scripts/set_mode.sh dual
docker compose ps
docker compose exec nginx nginx -T
```

不使用脚本时，可按同样项目名执行完整切换：

```bash
docker compose down --remove-orphans
docker compose -f docker-compose.single.yml up --build -d
# 恢复
docker compose -f docker-compose.single.yml down --remove-orphans
docker compose up --build -d
```

只执行 `docker compose stop backend1` 是故障实验，不能代替单后端性能模式，因为双 upstream 中仍包含已停止的节点。

## 手工故障与恢复

```bash
bash scripts/set_mode.sh dual
docker compose stop backend1
curl --max-time 3 http://localhost:6120/
docker compose start backend1
```

Nginx 使用被动故障检测；重新启动的后端可能需等待默认故障暂停窗口结束后重新接收请求。自动脚本最多等待 25 秒并保留恢复过程。按相同步骤验证 backend2。课程不要求自动重启、额外健康检查或 Nginx 高可用。

## 清理

```bash
docker compose down --remove-orphans
```

这会清理本项目的两种模式，不删除原始证据。后端及 Nginx 镜像可能仍保留，方便下次复现。
