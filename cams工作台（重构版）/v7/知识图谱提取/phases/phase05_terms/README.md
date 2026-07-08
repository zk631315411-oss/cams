# Phase 05：术语大字典与检索索引

## 定位

P5 是术语大字典阶段，用来整理 CAMS v7 教材中的术语、缩写、全称、中英文表达、别名和同义词。

P5 的产物不写入知识图谱主结构，不生成 `core_point`，不生成 `core_point -> core_point` 关系，也不生成 `core_point -> unit` 边。

P5 的核心用途是：为后续“选项证据生成”和“证据召回”提供检索索引。

也就是说，P5 只回答：

```text
用户或题目中出现某个术语时，可以用哪些等价说法、缩写、全称、中英文表达去召回教材证据？
```

它不回答：

```text
两个知识点之间是否存在教材逻辑关系？
两个 core_point 是否应当相连？
某个术语是否应成为图谱节点？
```

## 阶段职责

P5 只做四件事：

```text
1. 缩写 ↔ 全称
2. 中文 ↔ 英文
3. 别名 / 同义词 / 检索等价词
4. 出现位置索引（选做）
```

示例：

```text
AML ↔ anti-money laundering ↔ 反洗钱
CDD ↔ customer due diligence ↔ 客户尽职调查
SAR ↔ suspicious activity report ↔ 可疑活动报告
STR ↔ suspicious transaction report ↔ 可疑交易报告
```

其中，某些词并不是严格本体意义上的同义词，但为了选项证据生成，可以作为“检索等价词”使用。

例如：

```text
bribe / bribery / 贿赂
money transfer / remittance / 汇款
SAR / STR / 可疑活动报告 / 可疑交易报告
```

这些只用于检索召回，不代表知识图谱中的概念等价关系。

## 边界

P5 可以记录：

```text
canonical_en
canonical_zh
aliases_en
aliases_zh
abbreviations
full_forms
compound_terms
evidence_unit_ids
alias_scope
review_note
```

P5 不做：

```text
不生成 core_point
不生成 KG 主图谱边
不生成 grounds / illustrates / summarizes 等 CP 关系
不判断两个 CP 是否有教材逻辑关系
不修改 frozen unit
不替代全文搜索
```

正式 P5C 产物必须显式标记：

```json
{
  "index_purpose": "option_evidence_retrieval",
  "not_kg_edge": true
}
```

## 子阶段

### P5A：缩写与全称

P5A 生成缩写与全称的 pair-level 映射。

正式脚本：

```text
scripts/p5a_abbreviation_mapping.py
```

正式产物：

```text
outputs/p5a_abbreviation_mapping.json
previews/p5a_abbreviation_mapping_preview.md
reports/p5a_abbreviation_mapping_report.md
```

P5A 只输出 pair-level 缩写边，不负责最终术语组装。

### P5B：中英文映射

P5B 生成中文与英文术语之间的映射，并标记一英多中、一中多英等冲突项。

正式脚本：

```text
scripts/p5b_zh_en_mapping.py
```

正式产物：

```text
outputs/p5b_zh_en_mapping.json
previews/p5b_zh_en_mapping_preview.md
reports/p5b_zh_en_mapping_report.md
```

P5B 不决定最终 canonical term，也不合并别名；这些交给 P5C。

### P5C：别名组与检索索引

P5C 把 P5A/P5B 的候选结果合并成术语检索索引。

P5C 的定位非常明确：

```text
P5C = 后续选项证据生成使用的 alias / synonym / retrieval-equivalent 索引
```

P5C 不写入知识图谱主结构，不生成 KG 边。

正式脚本：

```text
scripts/p5c_alias_index.py
```

正式产物：

```text
outputs/p5c_alias_index.json
previews/p5c_alias_index_preview.md
reports/p5c_alias_index_report.md
```

当前 P5C 物化结果：

```text
source_review_count: 194
alias_group_count: 184
compound_term_count: 5
rejected_or_split_count: 7
auto_accept_count: 176
manual_alias_count: 8
```

其中复合缩写保留为检索项，但不把组成部分互相合并：

```text
AML/CFT
AML/CTF
BSA/AML
KYC/CDD
MLRO/BSA
```

## 输入

P5 的主要输入来自冻结知识单元：

```text
phases/phase00_quality_gate/outputs/eligible_units.jsonl
```

主要使用字段：

```text
unit_id
en_quote
knowledge_zh
terms
heading_context
```

P5C 还使用 P5A/P5B 的正式产物，以及人工审核后的 P5C 测试结果。

## 输出使用方式

后续选项证据生成可以使用 P5C 索引做召回扩展。

例如题目或选项中出现：

```text
SAR
```

可以扩展召回：

```text
suspicious activity report
suspicious transaction report
可疑活动报告
可疑交易报告
```

但这些扩展只用于找证据，不代表图谱中这些概念被合并为同一个节点或边。

## 当前状态

P5A、P5B、P5C 均已形成正式产物。

P5C 已完成全量候选审核与人工复核，并已物化为正式检索索引：

```text
outputs/p5c_alias_index.json
```

后续如果进入选项证据生成阶段，应优先使用 `p5c_alias_index.json`，而不是旧版 `p5_term_alias_map.json`。
