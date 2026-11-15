# 实验脚本

## 已完成：后端自测

```bash
bash scripts/check_backend.sh
```

依赖 Linux、Bash、Docker CLI 和可访问的 Docker daemon；首次构建需要访问 Docker Hub 与 PyPI。HTTP 验证使用镜像中 Python 的标准库，无需在虚拟机额外安装 Python 库。

- 默认构建 `cisc7403-backend:v1`，可用 `IMAGE=其他标签 bash scripts/check_backend.sh` 覆盖。
- 默认输出到 `results/backend/cisc7403-check-时间-PID/`；`OUTPUT=/绝对路径 bash scripts/check_backend.sh` 可指定独立输出目录。
- 验证两个实例和 hostname 回退实例的 HTTP 状态、JSON、50 ms 等待及并发排队行为，并检查同一镜像、单进程、单线程、非 root 用户、无发布端口和请求日志。
- 使用三个临时后端及一个临时测试客户端，仅用于自测；hanyan 的最终系统仍是 Nginx 加两个后端。
- 成功或失败均保存日志并尝试清理本次创建的容器与网络；失败返回非零退出码。镜像和结果文件会保留。
- 测试用例在 `backend_http_test.py`；通过包装脚本在同一 Docker 网络中运行，不能直接在宿主机解析测试服务名。

## 系统集成后实现

以下脚本待完整系统接通后完成；运行前记录单后端或双后端配置。

| 计划脚本 | 负责人 | 主要职责 | 结果目录 |
| --- | --- | --- | --- |
| `benchmark.sh` | zhanghongyi | 用相同 wrk 负载比较单后端与双后端，保存原始输出 | `results/performance/` |
| `check_balance.sh` | hanyan | 多次请求 6120，记录两个实例的响应和日志 | `results/load_balancing/` |
| `check_failover.sh` | hanyan | 停止一个后端、验证服务响应、重启并确认恢复 | `results/fault_tolerance/` |

共用课程虚拟机时，性能测试与停止后端等操作应错开。保留错误和超时等原始记录，实验后恢复双后端运行状态。
