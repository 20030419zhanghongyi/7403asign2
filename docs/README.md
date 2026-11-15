# 分工与交接文档

两人的工作范围和接口约定：

- [zhanghongyi 工作范围与交接说明](zhanghongyi_工作范围与交接说明.md)
- [hanyan 工作范围与交接说明](hanyan_工作范围与交接说明.md)

后续需要编写的文档：

| 文件 | 负责人 | 完成时间与内容 |
| --- | --- | --- |
| `backend_handoff.md` | zhanghongyi | 首次交接前，记录构建、启动、自测、日志、环境版本和已知问题 |
| `integration_runbook.md` | hanyan | 系统接通后，记录一键启动、单后端和双后端切换、故障与恢复方法 |
| `report_zhanghongyi.md` | zhanghongyi | 后端与镜像、性能实验、结果分析及实际贡献 |
| `report_hanyan.md` | hanyan | 架构、Nginx 与 Compose、负载均衡及容错实验、实际贡献 |

交接时提供分支名、明确的提交 SHA、操作说明及实际验证记录。最终报告由双方核对后合并到 `report/`，正文不超过 3 页。
