# 课程要求对应表

依据课程 Project II 说明第 3.1–3.6 节。下表列出实现位置和测试记录，实验数据见 [results/README.md](../results/README.md)。

| 教师要求 | 实现或证据 |
| --- | --- |
| 课程虚拟机安装 Docker | acceptance 环境记录中的系统、Docker、Compose 版本 |
| 默认恰好 Nginx 加两个后端 | `docker-compose.yml`；实验运行时容器检查 |
| 同一应用镜像 | 两后端均使用 `cisc7403-backend:v1`；runtime.json 比较实际镜像 ID |
| `/` 标识实例 | `backend/app.py` 的 JSON 响应；逐请求记录 |
| `/work` 约 50 ms | `time.sleep(0.05)`；后端自测原始记录 |
| 单服务进程、关闭请求多线程 | Flask `processes=1, threaded=False`；每轮检查进程数与 `/proc/1/status` 的线程数 |
| 后端仅内部网络可达 | 后端无宿主机 ports；runtime.json 核对空绑定 |
| 后端请求日志可见 | `docker compose logs`；实验目录中的 container-logs.txt |
| Nginx 为独立官方镜像容器 | `nginx:alpine`；运行时镜像 ID 保留 |
| 通过 Compose 服务名访问上游 | `backend1:5000`、`backend2:5000` |
| 仅外部端口 6120 | Nginx 映射 6120:80；脚本断言 |
| `docker compose up --build` 启动 | 默认 Compose 构建部署；startup.log |
| 多请求证明两个实例工作 | check_balance.sh；40 请求、实例分布及日志 |
| 停止后端仍能响应，再重启 | check_failover.sh；对两个后端分别执行并保留停止、请求、恢复记录 |
| wrk 访问 Nginx 的 `/work` | benchmark.sh；每轮 wrk.txt 保存完整参数 |
| 单、双后端相同工作负载 | 固定 t2/c20/d10s/timeout5s；每种三轮，单模式 upstream 只含一个运行后端 |
| 吞吐量与平均延迟 | performance summary.json 与最终报告表格 |
| 简要解释结果、问题和贡献 | 最终报告第 2–3 页 |
| 正文最多 3 页 | `report/Project_II_Group_2.pdf`，3 页，无封面 |
| 完整源代码及配置 | backend、nginx、Compose、scripts 随仓库与提交包提供 |
| 成员分工声明 | 提交包中每人一份，分别评价对方，每表总分 100 |

容错测试的客户端超时设为 3 秒。课程说明没有指定响应时间或吞吐量下限。测得的故障切换等待和短时性能结果见报告第 4–5 节。
