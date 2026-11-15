# 后端服务

负责人：zhanghongyi。工作分支：`zhanghongyi`。

本目录将包含 `app.py`、`requirements.txt`、`Dockerfile` 和 `.dockerignore`。当前提供目录约定及构建忽略规则，后端实现由 zhanghongyi 完成。

## 实现约定

- 使用 Python 与 Flask，监听 `0.0.0.0:5000`。
- 读取 `INSTANCE_NAME`，未提供时使用容器 hostname。
- `GET /` 返回 HTTP 200，例如 `{"instance":"backend1","status":"ok"}`。
- `GET /work` 等待约 0.05 秒后返回相同结构。
- 单服务进程，关闭请求多线程、debug 和重载器。
- 请求日志写入标准输出或标准错误，能够通过 `docker logs` 查看。
- 两个后端使用同一个镜像，差异通过环境变量注入。

## 首次交接

实现完成后，从仓库根目录验证以下构建入口：

```bash
docker build -t cisc7403-backend:v1 ./backend
```

在 `docs/backend_handoff.md` 写明启动、自测、日志查看和清理临时容器的方法，将实际自测材料保存到 `results/backend/`，并记录交接提交 SHA。

交接前核对两个接口、实例名变化、约 50 ms 等待、单进程设置及日志。hanyan 应能按说明直接复现，随后接入 Nginx 与 Compose。

完整范围见 [zhanghongyi 分工文档](../docs/zhanghongyi_工作范围与交接说明.md)。
