# 后端虚拟机自测证据

本目录保存真实运行输出。首次交接结论以 **最终固定摘要版本** 的运行记录为准。

| 运行目录 | 对应代码提交 | 说明 |
| --- | --- | --- |
| `cisc7403-check-20261115T085310Z-12111/` | `7a7dc322b45253958f9a27256052c8e0b917a33a` | 首次完整下载、构建和自测通过；尚未安装 wrk；记录基础镜像摘要 |
| `cisc7403-check-20261115T085624Z-15899/` | `7fb6a188d1f55c33c4bde987cb13a6d6d3023a50` | 固定基础镜像摘要并整理证据采集后复测通过；wrk 已安装 |

两次均执行 `bash scripts/check_backend.sh`，`result.txt` 均为 `exit_code=0`。通过源码归档传入虚拟机，最终运行的 `environment.txt` 从 `TESTED_COMMIT.txt` 读取提交号；每个运行目录的 `source.sha256` 提供独立内容核对依据。

在 Linux 仓库根目录核对最终交付代码：

```bash
sha256sum -c results/backend/cisc7403-check-20261115T085624Z-15899/source.sha256
```

文件说明：

- `build.log`：完整 Docker 构建输出。
- `environment.txt` / `dependencies.txt`：虚拟机、容器工具、Python 和库版本。
- `image.txt` / `runtime.txt`：镜像、单进程、单线程、非 root 用户和无发布端口检查。
- `http-tests.log`：HTTP、实例名、hostname 回退、等待时间和并发排队测试。
- `*-backend1.log`、`*-backend2.log`、`*-fallback.log`：对应容器原始请求日志；`*-client.log` 是测试客户端输出。
- `result.txt`：脚本退出状态，0 表示所有断言通过。
- 顶层 `TESTED_COMMIT.txt`：最终实测代码提交。
- 顶层 `wrk-package.txt`：`dpkg-query -W wrk` 的实际安装版本。
- 顶层 `remaining-containers.txt` / `remaining-networks.txt`：测试完成后分别执行 `docker ps -a --format '{{.Names}}' | grep cisc7403-check` 和 `docker network ls --format '{{.Name}}' | grep cisc7403-check` 的输出；空文件表示没有匹配的遗留测试资源。

第一次运行时 `pip freeze` 在终端提示非 root 用户没有 pip 缓存目录，未影响测试；最终脚本使用 `pip --no-cache-dir freeze` 避免此提示。原始应用日志中的 Flask 开发服务器提示属于预期行为。

后端源码和自测脚本在最终验收后未修改；后续提交仅补充 Markdown 文档和证据。本目录中的延迟仅用于验证约 50 ms 等待与串行处理，不代表完整系统性能实验已完成。
