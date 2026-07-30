# Infrastructure 代码目录

本目录不是冻结资产本体。冻结教材、索引、KG 和术语位于 `data/infrastructure`。

当前只有 `catalog.py`，用于读取教材 manifest 版本和 `units.json`，但全仓没有调用者。实际检索资产由 `backend/retrieval/assets.py` 读取，教材 PDF 由 `backend/textbook.py` 读取。

接手开发者需要判断该文件是未来统一基础设施入口还是废弃骨架。在结论确定前：

- 不把它写成当前运行依赖。
- 不向其中新增绕过检索资产校验的写入能力。
- 不删除，避免在交接时擅自改变规划边界。
