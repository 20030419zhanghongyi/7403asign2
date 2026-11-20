# 实验结果与证据索引

正式验收编号：`20261120T153935Z-31487`，2026-11-20 在课程 Ubuntu 24.04 虚拟机执行。4 vCPU、7.7 GiB 内存、aarch64；Docker 29.8.2、Compose 5.6.0、wrk 4.1.0。

| 实验 | 结果 | 证据 |
| --- | --- | --- |
| 后端首次自测 | 已通过，源码未变 | [后端索引](backend/README.md) |
| 负载均衡 | 40/40 成功，两个实例各 20 次 | [汇总](load_balancing/20261120T153935Z-31487/summary.json)、同目录请求和容器日志 |
| backend1 停止 | 30/30 成功，全部由 backend2 响应 | [容错汇总](fault_tolerance/20261120T153935Z-31487/summary.json) |
| backend2 停止 | 30/30 成功，全部由 backend1 响应 | 同上 |
| 每次恢复 | 20/20 成功，两个实例各 10 次 | 同上；recovery 目录保留恢复过程 |
| 正式性能实验 | 三组配对、无连接错误或超时 | [性能汇总](performance/20261120T153935Z-31487/summary.json) |
| 完整验收 | 所有实验通过 | [总汇总](acceptance/20261120T153935Z-31487/summary.json) |

## 性能数据

同一负载：`wrk -t2 -c20 -d10s --timeout 5s --latency http://127.0.0.1:6120/work`。每轮预热 3 秒，排空等待 2 秒；测量次序为单/双、单/双、单/双。单后端模式只运行 backend1，upstream 也只有 backend1。

| 轮次 | 配置 | 吞吐量 req/s | wrk 平均延迟 ms | socket errors |
| --- | --- | ---: | ---: | ---: |
| 1 | 单后端 | 18.81 | 1010.00 | 0 |
| 1 | 双后端 | 37.52 | 515.99 | 0 |
| 2 | 单后端 | 18.84 | 1010.00 | 0 |
| 2 | 双后端 | 37.41 | 519.63 | 0 |
| 3 | 单后端 | 18.82 | 1010.00 | 0 |
| 3 | 双后端 | 37.67 | 516.02 | 0 |
| 三轮均值 | 单后端 | 18.82 | 1010.00 | 0 |
| 三轮均值 | 双后端 | 37.53 | 517.21 | 0 |

均值为各轮 wrk 报告值的算术平均，吞吐量比值 1.994。单后端原始延迟输出为 `1.01s`，转换为 1010 ms；不要把显示精度理解为更高精度。所有六轮都没有 wrk 报告的 socket errors 或非 2xx/3xx 响应。原始输出见 performance 下各轮 `wrk.txt`；预热和容器日志另存，不混入正式结果。

## 源码对应与复现

[源码 SHA-256](acceptance/20261120T153935Z-31487/source-sha256.json)覆盖后端、Dockerfile、两个 Compose、两个 Nginx 配置及实验脚本。最终交付源码逐项核对与实测文件一致。虚拟机是在基础提交 `cbdce3e` 上导入待验收源码，因此 `git-head.txt` 是基础提交；不能仅用该文件将本次结果归给未修改的旧 main。以 SHA-256 对照最终文件为准。

源码核对：在仓库根目录执行以下标准库命令。

```bash
python3 - <<'PYCODE'
import hashlib, json
from pathlib import Path
manifest = json.loads(Path('results/acceptance/20261120T153935Z-31487/source-sha256.json').read_text())
for name, expected in manifest.items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == expected, name
print('All tested source hashes match.')
PYCODE
```

[修复前记录](fault_tolerance/pre-fix-20261120/README.md)保留了原版在 3 秒诊断阈值下超时的证据。最终版连接超时调整为 1 秒，两种故障方向均通过。本次短时测试用于课程演示，不能推断所有网络故障或长期负载下的表现。

完整复现：`bash scripts/run_all.sh`；结束后双后端继续运行。每次生成新证据，不覆盖本次数据。测试使用的 `nginx:alpine` 为官方浮动标签，运行时镜像 ID 已保存；将来重新拉取可能是不同镜像版本。
