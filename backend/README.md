# 后端服务

后端使用 Flask，代码和镜像构建文件均位于本目录。Compose 的连接方式见[集成运行说明](../docs/integration_runbook.md)。

## 实现约定

- 使用 Python 与 Flask，监听 `0.0.0.0:5000`。
- 读取 `INSTANCE_NAME`，未提供或为空时使用容器 hostname。
- `GET /` 返回 HTTP 200，例如 `{"instance":"backend1","status":"ok"}`。
- `GET /work` 等待约 0.05 秒后返回相同结构。
- 单服务进程，关闭请求多线程、debug 和重载器。
- 请求日志写入标准输出或标准错误，能够通过 `docker logs` 查看。
- 两个后端使用同一个镜像，差异通过环境变量注入。

## 构建与测试

从仓库根目录构建并运行自测：

```bash
docker build -t cisc7403-backend:v1 ./backend
bash scripts/check_backend.sh
```

脚本会构建镜像、创建临时网络和测试容器，验证 HTTP 行为与进程状态，输出到 `results/backend/`，最后清理本次创建的容器和网络。需在可运行 Docker 的 Linux 虚拟机上执行。

镜像以 UID 10001 运行，基础镜像固定摘要，Python 直接和间接依赖固定版本。启动命令为 `python app.py`，无需在 Compose 覆盖。

`EXPOSE 5000` 仅声明容器端口。两个后端在 Compose 中没有宿主机端口映射，Nginx 通过同一网络内的 `backend1:5000`、`backend2:5000` 访问它们。

按课程实验使用 Flask 开发服务器，保留单进程串行处理。不要改成默认多线程的 `flask run` 或增加 worker，否则会改变实验条件。[Flask 运行参数说明](https://flask.palletsprojects.com/en/stable/api/#flask.Flask.run)
