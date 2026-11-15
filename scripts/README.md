# 实验脚本

脚本在完整系统接通后实现，并从仓库根目录运行。每份脚本应说明依赖、输入参数、输出位置，以及实验后的恢复方式。

| 计划脚本 | 负责人 | 主要职责 | 结果目录 |
| --- | --- | --- | --- |
| `benchmark.sh` | zhanghongyi | 用相同 wrk 负载比较单后端与双后端，保存原始输出 | `results/performance/` |
| `check_balance.sh` | hanyan | 多次请求 6120，记录两个实例的响应和日志 | `results/load_balancing/` |
| `check_failover.sh` | hanyan | 停止一个后端、验证服务响应、重启并确认恢复 | `results/fault_tolerance/` |

共用课程虚拟机时，性能测试与停止后端等操作应错开。保留错误和超时等原始记录，实验后恢复双后端运行状态。
