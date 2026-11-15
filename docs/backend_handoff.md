# 后端首次交接：zhanghongyi → hanyan

日期：2026-11-15。状态：后端、Dockerfile、虚拟机自测与基础工具准备完成，可以开始 Nginx / Compose 集成。

## 版本与交付内容

- 来源分支：`zhanghongyi`。
- 已实测的后端与自测脚本提交：[7fb6a188d1f55c33c4bde987cb13a6d6d3023a50](https://github.com/20030419zhanghongyi/7403asign2/commit/7fb6a188d1f55c33c4bde987cb13a6d6d3023a50)。后续提交补充本文档和原始证据，后端与脚本内容保持该提交的版本。
- 镜像：`cisc7403-backend:v1`，从仓库的 `backend/` 构建；不依赖预先上传到镜像仓库的成品。
- 文件：`backend/app.py`、`backend/requirements.txt`、`backend/Dockerfile`、`backend/.dockerignore`、`scripts/check_backend.sh`、`scripts/backend_http_test.py`。
- 最终自测证据：[20261115T085624Z-15899](../results/backend/cisc7403-check-20261115T085624Z-15899/)。其中 `source.sha256` 能核对实际测试的六个源码文件。

本次属于首次后端交接。Nginx、Compose、6120 统一入口及负载均衡、故障实验由 hanyan 继续完成；单后端与双后端的 wrk 性能对比在系统集成后由 zhanghongyi 完成。

## hanyan 从这里开始

新克隆仓库时：

```bash
git clone --branch zhanghongyi https://github.com/20030419zhanghongyi/7403asign2.git
cd 7403asign2
git rev-parse HEAD                 # 保存完整交接提交 SHA，包含文档和证据
git switch -c hanyan
bash scripts/check_backend.sh
```

已有 `hanyan` 分支时，先保存自己的未提交修改，然后执行：

```bash
git fetch origin
git switch hanyan
git merge origin/zhanghongyi
git rev-parse HEAD
bash scripts/check_backend.sh
```

不要仅从 `main` 开始集成；首次后端成果在 `zhanghongyi`。自测最后显示两行 `PASS`、结果目录中的 `result.txt` 为 `exit_code=0` 后，就可以直接写 Nginx 和 Compose，无需改后端源码。

## 接口与容器契约

| 项目 | 接入约定 |
| --- | --- |
| 技术与启动 | Python / Flask；镜像默认执行 `python app.py` |
| 监听 | `0.0.0.0:5000` |
| 实例名称 | `INSTANCE_NAME=backend1` 或 `INSTANCE_NAME=backend2`；未设置或空值时回退到容器 hostname |
| `GET /` | HTTP 200，`Content-Type: application/json`，如 `{"instance":"backend1","status":"ok"}` |
| `GET /work` | 先等待 0.05 秒，再返回同样 JSON；并发时总延迟还包括排队和网络时间 |
| 并发模式 | 每个容器一个进程、一个服务线程；显式设置 `processes=1`、`threaded=False`、`debug=False`、`use_reloader=False` |
| 日志 | `docker logs` 可查看；JSON 请求日志含 `instance`、`method`、`path`、`status`、`elapsed_ms` |
| 镜像内容 | 无外部数据库、状态文件或运行时下载；应用以 UID 10001 运行 |
| 网络 | 两个后端与 Nginx 共用 Docker 网络；后端没有宿主机端口映射 |

`elapsed_ms` 是应用开始处理请求之后的时间，不包含客户端在服务端队列里等待的时间；后续报告使用 wrk 的延迟测量，不用这项日志值代替端到端延迟。

hanyan 的配置应满足：

1. Compose 服务名为 `nginx`、`backend1`、`backend2`；两个后端使用相同的 `cisc7403-backend:v1` 镜像。
2. 使用 `./backend` 作为构建上下文，在 Compose 中配置构建，确保全新环境执行 `docker compose up --build` 可构建并启动。
3. 为两个后端分别设置 `INSTANCE_NAME`，保留镜像默认启动命令。不要切换到 `flask run`、多线程或多 worker 启动方式。
4. Nginx upstream 使用 `backend1:5000` 和 `backend2:5000`，两个接口原路径转发。
5. 仅 Nginx 发布 `6120:80`；后端不配置 `ports`，`EXPOSE 5000` 本身不会发布端口。
6. 提供单后端、双后端配置切换和故障恢复命令，写入 `docs/integration_runbook.md`，供后续性能实验使用。

## 一键自测

在 Linux 虚拟机的仓库根目录执行：

```bash
bash scripts/check_backend.sh
```

脚本先构建镜像，然后创建独立的临时 Docker 网络，启动两个有指定实例名的后端、一个用于验证 hostname 回退的后端，以及一个 HTTP 测试客户端。测试客户端按服务名访问后端，整个过程不发布宿主机端口。这里的额外容器只是测试设施，不是最终部署架构。

输出保存在 `results/backend/cisc7403-check-时间-PID/`，包括构建日志、环境、源码哈希、镜像 ID、实际依赖、进程 / 线程检查、HTTP 结果、各容器日志和退出状态。成功或失败都会尝试清理本次创建的容器与网络，保留镜像和日志。不要同时在同一个镜像标签上运行多个构建。

可以指定独立输出目录或镜像标签：

```bash
OUTPUT=/tmp/7403-backend-check bash scripts/check_backend.sh
IMAGE=cisc7403-backend:review bash scripts/check_backend.sh
```

## 手动构建、启动、请求与清理

以下使用独立的演示名称；若已有同名资源，先核对用途或换一组名称。

```bash
docker build -t cisc7403-backend:v1 ./backend
docker network create cisc7403-backend-demo
docker run -d --name cisc7403-demo-1 --network cisc7403-backend-demo \
  --network-alias backend1 -e INSTANCE_NAME=backend1 cisc7403-backend:v1
docker run -d --name cisc7403-demo-2 --network cisc7403-backend-demo \
  --network-alias backend2 -e INSTANCE_NAME=backend2 cisc7403-backend:v1
docker logs cisc7403-demo-1
docker logs cisc7403-demo-2
```

日志出现 `Running on` 后，用镜像自带 Python 验证，不需要安装 curl 到镜像，也不需要 `-p`：

```bash
docker exec cisc7403-demo-1 python -c \
  'import urllib.request; print(urllib.request.urlopen("http://127.0.0.1:5000/").read().decode())'
docker exec cisc7403-demo-2 python -c \
  'import urllib.request; print(urllib.request.urlopen("http://127.0.0.1:5000/work").read().decode())'
docker run --rm --network cisc7403-backend-demo cisc7403-backend:v1 python -c \
  'import urllib.request; print(urllib.request.urlopen("http://backend2:5000/work").read().decode())'
docker logs cisc7403-demo-1
docker logs cisc7403-demo-2
docker top cisc7403-demo-1
docker port cisc7403-demo-1         # 应无输出
```

完成手动验证后，只清理上面创建的演示资源：

```bash
docker rm -f cisc7403-demo-1 cisc7403-demo-2
docker network rm cisc7403-backend-demo
```

## 实际环境与验收结果

实测日期为 2026-11-15，最终自测于 UTC 08:56:24（北京时间 16:56:24）开始。

| 环境项 | 实际版本 |
| --- | --- |
| 课程虚拟机 | Ubuntu 24.04.4 LTS，Linux 7.0.0-31-generic，aarch64 |
| Docker Engine / CLI | 29.8.2 |
| Docker Compose | v5.6.0 |
| wrk | Ubuntu 包 `4.1.0-4build2`，已通过 apt 安装 |
| 镜像 Python | 3.12.16 |
| Flask / Werkzeug | 3.1.3 / 3.1.9；其余版本见 `backend/requirements.txt` |
| 基础镜像 | 官方 `python:3.12-slim-bookworm`，Dockerfile 已固定本次构建的摘要 |

Docker 与 Compose 原已安装并可用；此次补充的系统包是 wrk 及其 LuaJIT 依赖。在新的 Ubuntu 环境中，可按 [Docker 官方 Ubuntu 安装说明](https://docs.docker.com/engine/install/ubuntu/)准备 Docker / Compose，并执行 `sudo apt-get update && sudo apt-get install -y wrk`。先用 `docker version`、`docker compose version`、`wrk --version` 核对；wrk 可能在版本信息后附带用法，这是该版本的正常输出。

| 验收项 | 最终自测观察 | 证据 |
| --- | --- | --- |
| 构建及依赖 | 镜像构建成功；首次完整构建执行 `pip check` 通过；最终固定摘要构建命中同一应用层缓存 | 两次 `build.log`、`dependencies.txt` |
| HTTP 与实例名 | 两个路径均返回 200 和约定 JSON；两个环境变量实例名、hostname 回退均通过 | `http-tests.log` |
| 约 50 ms 工作 | backend1 三次 51.264 / 51.155 / 50.960 ms；backend2 三次 51.287 / 51.522 / 51.755 ms | `http-tests.log` |
| 单进程 / 单线程 | 每个后端仅 `python app.py`，PID 1，Threads=1，UID=10001 | `runtime.txt` |
| 串行处理 | 6 个并发请求总计 312.076 ms；各请求约 52.731 / 103.669 / 156.493 / 208.429 / 260.502 / 311.311 ms 完成 | `http-tests.log` |
| 同一镜像 | 两个实例的镜像 ID 相同 | `image.txt`、`runtime.txt` |
| 端口与日志 | 后端没有发布宿主机端口；`docker logs` 包含实例名和成功 `/work` 请求 | `runtime.txt`、各容器 `.log` |
| 清理 | 没有遗留 `cisc7403-check-*` 容器或网络 | `remaining-containers.txt`、`remaining-networks.txt` 均为空 |

这些是后端正确性验收数据，不是作业要求的 Nginx 单 / 双后端性能对比。最终性能实验仍需使用统一入口及相同 wrk 参数。

## 已知情况与后续交接

- 当前没有阻止后端集成的已知问题。实测平台是 Linux arm64；其他平台应重新构建并运行同一自测。
- Flask 会打印开发服务器提示，这是课程串行处理实验所选启动方式；不要为了去掉提示改变并发模式。运行参数见 [Flask 官方说明](https://flask.palletsprojects.com/en/stable/api/#flask.Flask.run)。
- 首次构建需要访问 Docker Hub 和 PyPI。依赖和基础镜像已固定，不应在联调中各自升级。
- `localhost:6120` 需要 hanyan 完成 Nginx / Compose 后才能使用；当前仓库的后端自测不使用该入口。
- hanyan 完成集成后提供明确提交 SHA、`docs/integration_runbook.md` 以及单 / 双后端切换方式。zhanghongyi 接入后执行 `wrk -t2 -c20 -d10s http://localhost:6120/work` 的正式性能对比，保存原始输出并完成对应报告。
