# hanyan 系统集成与容错实验分工

课程：CISC 7403 第二次作业  
负责人：hanyan（队友）  
工作分支：`hanyan`  
更新日期：2026-11-15

我负责把 zhanghongyi 交付的后端接入 Nginx 和 Docker Compose，完成负载均衡与容错实验，并合并排版最终报告。zhanghongyi 先提供已自测的后端和基础环境；我按同一套接口约定接入，使 zhanghongyi 能继续完成性能实验。

项目仓库：[7403asign2](https://github.com/20030419zhanghongyi/7403asign2)

## 分支与交接方式

- 我的工作分支为 `hanyan`；后端负责人使用 `zhanghongyi`。
- 收到 `zhanghongyi` 的首次交接提交 SHA 后，从该提交建立 `hanyan`；如果分支已经存在，则将交接提交合并到 `hanyan` 后再开始接入。
- Nginx、Compose、集成运行说明、负载均衡与容错脚本、本人报告章节和报告排版的改动提交到 `hanyan`。
- 完成系统集成后，推送 `hanyan`，提供明确的提交 SHA、`docs/integration_runbook.md` 和验证结果。`zhanghongyi` 合并这个提交后继续做性能实验。
- 后端缺陷反馈给 `zhanghongyi` 修复，再将修复提交同步到 `hanyan`；代理、Compose 与网络配置问题由我修复。
- `main` 用于汇总双方核对通过的版本；最终通过 PR 合并成果，提交前共同验收。

向 `zhanghongyi` 交回集成成果时附上以下信息：

| 信息 | 内容 |
|---|---|
| 来源分支 | `hanyan` |
| 交接提交 | 填写已推送且已验证的集成提交 SHA |
| 集成说明 | `docs/integration_runbook.md` |
| 性能测试准备 | 单后端与双后端的切换、核对和恢复命令 |
| 交接状态 | 6120 入口是否正常，默认双后端状态，以及已知问题 |

## 工作范围与责任边界

| 阶段 | 我负责的工作 | 交付结果 |
| --- | --- | --- |
| 收到后端后 | 按 zhanghongyi 的交接说明构建和运行镜像，复现接口与实例标识。 | 接收验收记录 |
| 系统集成 | 配置官方 Nginx、两个后端、内部网络和 6120 入口。 | Nginx 配置与 Compose 文件 |
| 交还 zhanghongyi 测试 | 提供单后端与双后端切换、核对和恢复方法。 | 完整系统与集成运行说明 |
| 实验阶段 | 验证请求由两个实例处理；停止并恢复后端，记录可用性。 | 实验脚本与原始证据 |
| 最终提交前 | 写架构、部署及实验内容，合并报告并整理分工声明表。 | 约半份报告及最终排版文件 |

zhanghongyi 维护后端源码、Dockerfile、基础环境、性能实验及 README。我维护 Nginx、Compose 和集成运行说明。后端缺陷反馈给 zhanghongyi，代理与网络配置问题由我处理；首次联调与最终验收共同完成。

## 接续工作的顺序

- 先按 zhanghongyi 提供的提交 SHA 和 docs/backend_handoff.md 验证后端。
- 再完成双后端部署，确认外部入口与日志正常，向 zhanghongyi 交付可运行系统及性能测试切换方法。
- zhanghongyi 做性能实验期间，我整理配置说明和报告；负载均衡及故障实验与性能计时错开。
- 双方各写约一半报告，我负责合并排版；共同核对数据、贡献和最终提交材料。

总体按预计工作量各承担约 50%。zhanghongyi 的首次交接不需要包含性能结果；性能实验在我完成系统集成后开展。若排障明显超时，再共同调整文档和收尾任务。

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

## 接收后端与完成系统集成

### 开始前从 zhanghongyi 获取的内容

获取后端源码、requirements.txt、Dockerfile、.dockerignore、docs/backend_handoff.md、自测输出和对应 Git 提交；确认课程虚拟机上的 Docker、Compose、wrk 已准备好。首次交接后的后端问题仍由 zhanghongyi 修复。

```bash
docker build -t cisc7403-backend:v1 ./backend
```

先复现两个接口及实例名，再接入 Nginx。验收成功后直接使用交付的后端镜像与启动入口；实例差异通过 INSTANCE_NAME 注入。

### 系统集成的完成标准

- docker-compose.yml 定义 nginx、backend1、backend2；两个后端从同一源码构建并使用同一应用镜像，实例名分别设置为 backend1 与 backend2。
- Nginx 使用官方镜像，监听容器内 80 端口；通过服务名访问两个 5000 端口，在同一 Compose 网络中转发 / 与 /work。
- 只给 Nginx 配置宿主机映射 6120:80；两个后端不配置宿主机 ports。
- 配置并验证后端不可用时的转发行为，记录必要的故障判定和超时设置。停止任一后端后，请求仍应由剩余后端响应。
- 从干净的项目启动状态验证 docker compose up --build，无需先手工构建后端镜像。

| 我维护的文件 | 内容与交付标准 |
| --- | --- |
| nginx/nginx.conf | 默认双后端配置，以及负载均衡与故障处理所需设置。 |
| docker-compose.yml | 完整三个容器的构建、环境变量、网络、配置挂载和端口。 |
| docs/integration_runbook.md | 一键启动、日志检查、单后端与双后端切换、停止与恢复命令。 |
| 必要的单后端配置或脚本 | 让单后端实验仅运行一个后端，且 upstream 只指向它；可用补充配置或短脚本实现。 |

交还 zhanghongyi 时提供一组可直接复制的模式切换命令，并说明如何检查当前配置已生效。切换时实际重载或重建 Nginx；恢复后核对两个后端均能接收请求。默认交付状态保持双后端。

## 实验验证与最终交付

### 负载均衡验证

启动完整系统，多次请求 http://localhost:6120/。保存两种 instance 响应及对应后端日志，证明两个实例都处理了请求；不要求严格交替返回。把验证过程整理到 scripts/check_balance.sh，证据保存到 results/load_balancing/。

### 故障与恢复验证

- 确认双后端均可接收请求，再停止 backend1 或 backend2。故障实验保留双 upstream 配置，以验证 Nginx 能处理失效节点。
- 继续请求 6120，记录状态码、实际响应实例和日志。若有过渡性错误，保留并分析；不能仅截取成功结果。
- 重启被停止的后端，确认它重新接收请求。建议对两个后端分别验证，至少完整记录一次停止与恢复。

```bash
docker compose stop backend1
curl -i http://localhost:6120/
docker compose start backend1
docker compose logs --tail=50 nginx backend1 backend2
```

把步骤整理到 scripts/check_failover.sh，原始证据保存到 results/fault_tolerance/。自动容器重启、高级健康检查和 Nginx 高可用不属于作业必需内容。

### 支持 zhanghongyi 完成性能实验

提供经过验证的单后端与双后端切换方式，保证 zhanghongyi 使用同样的 wrk 参数访问 /work。性能实验的单后端配置只包含一个有效 upstream；故障实验保持双 upstream 后停止容器。两种实验分别记录配置与证据。

### 报告与提交检查

- 编写 docs/report_hanyan.md，说明系统架构、Nginx 与 Compose、负载均衡和故障实验，以及本人遇到的问题和实际贡献。
- 收到 zhanghongyi 的后端与性能章节后合并报告，正文不超过 3 页，封面如有另计。保留清晰的实验结果和简短解释。
- 整理成员分工声明表；双方核对角色、贡献及评价表填写。评价表分数按模板要求合计为 100，不把计划工作量当成已完成贡献。
- 共同复现一键启动和三个实验，检查源代码、Dockerfile、Nginx 配置、Compose 文件、报告及分工声明材料是否齐全。

依据：Project2_Scalable_Web_Service_Load_Balancing.pdf 第 1 至 3 页；CISC7403Role Declaration Page.docx。具体路径和阶段安排为本小组协作约定。
