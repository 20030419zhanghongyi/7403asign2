# 实验入口

在课程 Linux 虚拟机使用 Bash、Python 3、Docker Compose v2；性能实验另需 wrk。所有脚本均可从任意工作目录调用。

| 脚本 | 用途 |
| --- | --- |
| `check_backend.sh` | 后端独立自测，含实例名、50 ms 工作量、单进程与单线程等检查 |
| `check_balance.sh` | 启动双后端，验证两个实例处理请求 |
| `check_failover.sh` | 分别停止、恢复两个后端并保存全部请求记录 |
| `benchmark.sh` | 三组单/双后端 wrk 实验，保存吞吐量和平均延迟 |
| `set_mode.sh single` / `set_mode.sh dual` | 切换并验证实际运行容器和 Nginx upstream |
| `run_all.sh` | 顺序执行负载均衡、容错与正式性能实验 |
| `experiments.py` | 上述集成脚本共用实现；只依赖 Python 标准库 |

默认 Compose 项目名为 `cisc7403-project2`。脚本会重建该项目容器，完成后默认双后端继续运行。原始日志与源码校验值会保存到 `results/`。详见 [集成说明](../docs/integration_runbook.md)。
