# 测试

当前测试使用 Python `unittest`：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

2026-07-30 的 Windows 基线为 27 项通过。

## 文件与覆盖

- `test_storage.py`：两类检索的测试替身、题目锁、版本失效、档案修订号、备份生成、MCP 工具列表、当前题、新题归档、重复判断和旧流程兼容。
- `test_workflow_v2.py`：证据去重、候选冻结、证据重开、解析门禁、任务/阶段分离、可选 DS 和发布版本绑定。
- `test_textbook.py`：教材 manifest、PDF 页渲染、无效页码和文字坐标匹配。

测试中的 MuPDF `unknown keyword` 警告来自伪 PDF 夹具；用例通过不代表正式教材 PDF 已完成视觉验收。

## 未覆盖

- 真实 BGE-M3 加载、`encode` 和 RAG+KG 检索。
- HTTP API 路由和错误码。
- MCP stdio 进程协议及 Codex Desktop 实际连接。
- 检索 CLI、迁移脚本和依赖构建脚本。
- 浏览器半屏布局、五秒高亮和未保存内容保护。
- 备份恢复、macOS M3、Gatekeeper 和断网交付。

新增功能不能用现有 27 项通过证明上述能力可用；应按影响补充相应集成或验收测试。
