# Nginx 负载均衡配置

负责人：hanyan。工作分支：`hanyan`。

收到后端交接提交后，在本目录实现 `nginx.conf`，并在仓库根目录创建 `docker-compose.yml`。

## 接入约定

- 使用官方 Nginx 镜像，在容器内监听 80 端口，向宿主机映射 `6120:80`。
- 默认 upstream 包含 `backend1:5000` 与 `backend2:5000`。
- 通过 Compose 服务名连接后端，转发 `/` 和 `/work`。
- 两个后端只在 Compose 内部网络提供服务，不映射宿主机端口。
- 停止任一后端后，验证服务仍能由剩余后端响应，并验证恢复过程。

## 交回性能测试环境

提供单后端与双后端的切换、核对和恢复命令，写入 `docs/integration_runbook.md`。单后端性能模式仅运行一个后端，且 upstream 只指向该后端；故障实验保留双 upstream 配置后停止容器。

默认提交状态为双后端，完整系统应能用 `docker compose up --build` 启动。

完整范围见 [hanyan 分工文档](../docs/hanyan_工作范围与交接说明.md)。
