# zhanghongyi 后端开发与性能实验分工

课程：CISC 7403 第二次作业  
负责人：zhanghongyi（本人）  
工作分支：`zhanghongyi`  
更新日期：2026-11-15

我负责后端程序、应用镜像、课程虚拟机基础环境和性能实验。先交付可独立构建、已自测通过的后端，供 hanyan 直接接入 Nginx 和 Docker Compose；完整系统接通后，我再完成性能测试与相应报告内容。

项目仓库：[7403asign2](https://github.com/20030419zhanghongyi/7403asign2)

## 分支与交接方式

- 我的工作分支为 `zhanghongyi`；队友的工作分支为 `hanyan`。
- 后端、基础环境说明、性能脚本、本人报告章节和 README 的改动提交到 `zhanghongyi`。
- 首次交接时，推送已完成自测的提交，记录提交 SHA，并提供 `docs/backend_handoff.md` 与自测证据。`hanyan` 从该提交建立自己的工作分支；如果分支已经存在，则将该提交合并到 `hanyan` 后继续开发。
- `hanyan` 完成集成后，在其分支推送可运行版本及 `docs/integration_runbook.md`，并提供提交 SHA。我将该集成提交合并到 `zhanghongyi`，再运行性能实验。
- 双方以明确的提交 SHA 交接。交接后的接口、端口或启动方式如有变更，先同步说明，再更新代码与配置。
- `main` 用于汇总双方核对通过的版本；最终通过 PR 合并成果，提交前共同验收。

首次交接时附上以下信息：

| 信息 | 内容 |
|---|---|
| 来源分支 | `zhanghongyi` |
| 交接提交 | 填写已推送且已自测的提交 SHA |
| 后端说明 | `docs/backend_handoff.md` |
| 自测证据 | `results/backend/` |
| 交接状态 | 验收项目是否通过，以及影响接入的已知问题 |

## 工作范围与责任边界

| 阶段 | 我负责的工作 | 交付结果 |
| --- | --- | --- |
| 首次交接前 | 实现两个接口、实例标识、请求日志和规定的并发模式。 | backend/app.py |
| 首次交接前 | 固定依赖，编写 Dockerfile，在课程虚拟机验证镜像能构建并启动。 | backend/ 及自测记录 |
| 首次交接前 | 准备 Docker、Compose 和 wrk，记录环境版本与运行说明。 | 环境记录与后端交接说明 |
| 系统接通后 | 用相同负载比较一个与两个后端，整理吞吐量和平均延迟。 | 性能脚本、原始结果与分析 |
| 最终提交前 | 编写后端、镜像与性能报告内容，整理 README，核对源代码。 | 约半份报告及运行文档 |

hanyan 负责 Nginx、docker-compose.yml、负载均衡与容错实验、报告合并排版。后端问题由我修复；代理、Compose 或网络配置问题由 hanyan 修复。首次联调与最终验收共同完成。

## 交接顺序与工作量安排

- 阶段一：我完成后端并提交首次交接材料，hanyan 按交接清单验收。首次交接不等待性能实验。
- 阶段二：hanyan 接入 Nginx 与 Compose，向我提供可运行系统及单后端和双后端切换方法。
- 阶段三：我运行性能实验；hanyan 完成负载均衡与容错实验。共用虚拟机时错开测试时段。
- 阶段四：双方各写约一半报告，互相复核，hanyan 合并排版，我检查源码与运行说明。

总体按预计工作量各承担约 50%。若环境或联调问题明显超时，双方共同排查，并调整 README 整理或排版等收尾任务。

## 双方共用的接口与运行约定

以下内容同时适用于两份分工文档。6120 端口、约 50 ms 处理、同一后端镜像及单进程关闭多线程来自作业要求；5000 内部端口、服务名、环境变量和 JSON 字段是小组为便于交接统一的约定。

| 约定项目 | 双方遵循的内容 |
| --- | --- |
| 实现技术 | 小组约定使用 Python 与 Flask，依赖版本写入 requirements.txt。 |
| 应用镜像 | 统一名称 cisc7403-backend:v1；两个后端使用同一镜像，不分别写两套程序。 |
| 监听地址 | 后端固定监听 0.0.0.0:5000；5000 是小组内部约定。 |
| 实例标识 | 读取环境变量 INSTANCE_NAME；未设置时使用容器 hostname。不得在代码中写死 backend1。 |
| GET / | 返回 HTTP 200 和 JSON；至少包含 instance 与 status，status 的值为 ok。 |
| GET /work | 等待约 0.05 秒后返回 HTTP 200；JSON 同样包含 instance 与 status。总响应时间可能包含排队时间。 |
| 请求并发 | 每个容器只运行一个服务进程；Flask 设置 threaded=False、debug=False、use_reloader=False。 |
| 日志 | 请求日志输出到容器标准输出或标准错误，可通过 docker logs 或 docker compose logs 查看。 |
| 服务名称 | Compose 中固定使用 nginx、backend1、backend2；后端 INSTANCE_NAME 分别设为 backend1 与 backend2。 |
| 网络入口 | Nginx 通过 backend1:5000、backend2:5000 访问后端；最终部署仅映射 6120:80，后端不发布宿主机端口。 |

当 INSTANCE_NAME=backend1 时，两个接口的响应格式示例如下。两个实例的主要区别是 instance 字段。

```json
{"instance": "backend1", "status": "ok"}
```

zhanghongyi 交接后如需更改上述端口、字段或启动方式，应先与 hanyan 同步，再更新交接说明与两侧配置。其余内部实现由各文件负责人维护。

## 首次交接的材料与验收标准

首次交接目标：hanyan 在课程虚拟机拉取指定提交后，无需改动后端源码，即可构建镜像并按约定调用两个接口。镜像可在虚拟机从源代码重建，不依赖我电脑上已有的本地镜像。

| 计划文件或材料 | 交接时必须包含的内容 |
| --- | --- |
| backend/app.py | 两个接口、实例标识、50 ms 等待、单进程与多线程关闭设置。 |
| backend/requirements.txt | 已验证的依赖版本。 |
| backend/Dockerfile | 可从 backend/ 构建；自动启动应用；日志可被容器日志命令读取。 |
| backend/.dockerignore | 排除本地虚拟环境、缓存和与构建无关的文件。 |
| docs/backend_handoff.md | 构建与启动命令、接口与变量说明、环境版本、验收结果、可复现的问题。 |
| results/backend/ | 实际自测响应及日志；注明对应 Git 提交。 |
| Git 交接信息 | 分支或提交 SHA、构建镜像名、已完成事项、未解决且会影响接入的问题。 |

### 交付前逐项检查

- 从仓库根目录构建成功，运行时不需要手动进入容器安装依赖。
- 分别设置两种 INSTANCE_NAME，确认响应标识随环境变量变化。
- 两个接口返回 200 与约定 JSON；/work 含 0.05 秒等待。
- 核对只有一个服务进程，关闭请求多线程、debug 和重载器。
- docker logs 能看到请求；测试后清理临时容器，不保留后端宿主机端口映射。

### 约定的构建入口

```bash
docker build -t cisc7403-backend:v1 ./backend
```

后端交接说明还应给出临时容器启动和容器内请求验证命令。启动时传入 INSTANCE_NAME；验证可使用容器中的 Python 标准库，无需为后端开放宿主机端口。

我提交并完成自测后交接；hanyan 复现通过即进入系统集成。影响上述验收的后端缺陷仍由我修复，其他部分可同步推进。

## 系统接通后的性能实验与收尾

### 开始实验前由 hanyan 提供的材料

hanyan 提供能以 docker compose up --build 启动的系统，以及 docs/integration_runbook.md。运行说明必须写明单后端和双后端的切换、核对与恢复命令。我先确认 6120 入口正常，再开始计时实验。

### 性能实验的执行范围

- 单后端状态只保留一个运行的后端，并让 Nginx upstream 仅指向该后端；双后端状态恢复两个后端和双 upstream。切换配置由 hanyan 提供，我按说明执行。
- 两种状态均通过 Nginx 的 /work 测试，使用相同虚拟机、镜像、wrk 参数及相同预热方法；记录服务状态和配置。

```bash
wrk -t2 -c20 -d10s http://localhost:6120/work
```

- 保存完整 wrk 输出，提取 Requests/sec 与平均 Latency，延迟统一换算为 ms；保留超时、连接错误和非成功响应等信息。
- 建议每种状态重复 3 次，汇总每次结果及均值；这是小组为便于比较的安排，作业没有规定重复次数或加速比。
- 解释吞吐量与延迟变化；出现异常时结合日志、资源占用或错误数量分析。实验结束恢复双后端状态。

| 我后续维护的文件 | 应达到的结果 |
| --- | --- |
| scripts/benchmark.sh | 能重复运行相同负载并保存结果；具体调用方法写入 README。 |
| results/performance/ | 两种状态的原始输出、环境与配置记录，以及吞吐量和延迟汇总。 |
| docs/report_zhanghongyi.md | 后端与镜像实现、性能方法、结果分析、遇到的问题及本人实际贡献。 |
| README.md | 准备环境、构建启动、两个接口、实验入口与恢复方法。 |

报告正文与 hanyan 的内容合并后不超过 3 页，封面如有另计。我负责约一半内容，并核对所有性能数据与原始输出一致。共同完成分工声明，最终贡献按实际完成情况填写。

依据：Project2_Scalable_Web_Service_Load_Balancing.pdf 第 1 至 3 页；CISC7403Role Declaration Page.docx。具体路径和阶段安排为本小组协作约定。
