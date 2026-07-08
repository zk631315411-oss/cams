# KG shared library

本目录是 v7 知识图谱提取的跨阶段公共代码层，不是 phase 产物目录，也不是临时脚本堆放区。

## 当前职责

- `kg_common.py`：集中维护 KG 根目录、v7 根目录、正式知识单元输入路径、各 phase 目录常量、旧 `work/kg` 到新 `phases/*` 布局的兼容映射。
- 提供跨 phase 复用的基础 I/O：`load_units`、`read_jsonl`、`write_jsonl`、`write_text`、`ensure_dir`。
- 提供跨 phase 共享的规则常量：`BLOCKING_RISK_FLAGS`。
- 提供通用排序、章节聚合、计数摘要等无业务副作用的辅助函数。

## 放置规则

- 可以放：被两个及以上 phase 复用的纯函数、路径常量、schema/枚举、兼容层。
- 不放：某个 phase 独有的脚本、实验脚本、一次性修复脚本、LLM prompt、阶段产物、审计报告。
- 不放：会在 import 时读取大文件、写文件、调用模型、跑 pipeline 的代码。

## 使用约定

各 phase 脚本可以通过以下方式导入公共库：

```python
SCRIPT_DIR = Path(__file__).resolve().parent
KG_ROOT = SCRIPT_DIR.parents[2]
sys.path.insert(0, str(KG_ROOT / "lib"))

from kg_common import DEFAULT_KG_WORK_DIR
```

`DEFAULT_KG_WORK_DIR` 是迁移兼容层：旧脚本仍可使用 `kg_dir / "phase..."` 风格路径，但实际读写会落到新的 `phases/phaseXX/...` 自包含目录。新增脚本应优先使用显式 phase 目录常量，减少继续扩大兼容层。

## 后续整理方向

当前保持单文件 `kg_common.py`，便于迁移期稳定。等全书 KG 流程稳定后，可以拆成：

- `paths.py`：目录常量与兼容映射。
- `io_utils.py`：JSON/JSONL/Markdown 读写。
- `unit_rules.py`：unit 质量门、排序、章节聚合。
- `schemas.py`：跨 phase 共享枚举和 schema 常量。

拆分前提是调用方稳定，不为追求形式拆分而增加维护成本。
