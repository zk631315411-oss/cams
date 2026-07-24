# 极简测试：v7 中英双语知识点提取

v7 教材知识单元提取的早期原型实验。验证从 MinerU Markdown 中按英文基准切分知识点、再归集中文片段、输出可审计对照表的可行性。

## 定位

这是一个**快速验证实验**，不是正式管线。它探索的核心问题是：

> 能不能从 v7 中英文 MinerU 产物中，以英文为基准切分知识点，再把中文片段按位置归集到同一个知识点单元下，最后输出到 Excel 供人工审计？

后续正式管线（`v7/work/base_units/`）沿用了"英文原文 + 中文摘要 + LLM 标注"的核心思路，但做了更精细的切分规则、更丰富的元数据和检索索引构建。

## 输入

| 文件 | 说明 |
|---|---|
| `教材原文/v7/mineru提取/英文/v7_en_mineru_merged.md` | MinerU 解析后的英文教材全文 |
| `教材原文/v7/mineru提取/中文/v7_zh_mineru_merged.md` | MinerU 解析后的中文教材全文 |

## 产物

| 文件 | 说明 |
|---|---|
| `bilingual_alignment.json` | 中英知识点对齐结果（按章节组织，含知识点ID、英文原文、中文对应片段、位置偏移） |
| `v7中英对照.xlsx` | 可审计的 Excel 对照表（按章节分 sheet，含中英对照、匹配分数、审核标记） |

## 核心逻辑

1. **英文切分**：按章节标题 + 段落/句边界规则切分英文 MinerU Markdown
2. **中文归集**：用位置偏移 + 文本相似度（SequenceMatcher）把中文片段映射到英文知识点单元
3. **审计输出**：生成 xlsx，按章节分 sheet，每行一个知识点对，标注匹配分数和潜在问题

## 运行

```bash
python extract_knowledge_points.py
```

需要提前准备好 MinerU 提取的 `v7_en_mineru_merged.md` 和 `v7_zh_mineru_merged.md`。

## 与正式管线的区别

正式 units 管线（`v7/work/base_units/`）在此基础上做了以下提升：
- 不再依赖 SequenceMatcher 对齐，改用 PDF 页码 + 章节路径精确定位
- 每个 unit 增加 `heading_context`、`terms`、`evidence_status`、`can_be_direct_evidence` 等元数据
- LLM 标注从"提取知识点"改为"给已切分的 unit 打标签"（类型、术语），证据原文由程序保留
- 最终产物是结构化的 `v7_units_as_cards.json`（4973 条），而非对齐表
