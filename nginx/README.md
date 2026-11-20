# Nginx 配置

`nginx.conf` 是默认双后端配置，按 Compose 服务名访问 backend1:5000 和 backend2:5000；`nginx.single.conf` 是性能实验用的单后端配置，只包含 backend1。

两者均监听容器内 80，由 Compose 对外发布 6120。连接超时 1 秒，连接错误和超时允许尝试下一上游；默认使用轮询和被动故障判定。只停止容器但保留双 upstream 的配置用于故障测试。模式切换须重新创建 Nginx，见 [集成运行说明](../docs/integration_runbook.md)。
