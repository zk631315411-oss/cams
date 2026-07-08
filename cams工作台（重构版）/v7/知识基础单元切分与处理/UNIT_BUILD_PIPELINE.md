# v7 知识单元构建链路

> 一页纸导航：从教材原文到 4973 个冻结 unit 经过了哪些步骤。
> 详细设计见同目录 README.md，逐日实验记录见 实验日志_归档.md。

## 主线：1次 LLM 主切分 + 规则物化

```
MinerU md（中英分离：v7_en_mineru_merged.md / v7_zh_mineru_merged.md）
  ↓ prepare_base_blocks.py        规则：拆block、英文拆句、过滤噪声
v7_en_blocks.json（35470个英文句）
  ↓ 切117个切片 → 1724个DeepSeek请求
  ↓ prompt: v7_unit_split_v2.md   LLM做：决定哪些句属于同一个知识单元
  ↓ materialize_fullbook_llm_pilot_units.py   规则：回填en_quote、编号、去重
基底: v7_units_draft.v2_fullbook_all.combined.json
      direct=4399, review=234, parent=210
```

## 5层 overlay：每层解决基底里的一个具体毛病

| 层 | 脚本 | 解决什么 | 决策方式 | 增减 | 输出文件后缀 |
|---|---|---|---|---|---|
| 1 prefreeze_qa | apply_prefreeze_qa_decisions.py | 修拼写错误、救回被误删段落 | 人工决策表 | direct +6 | `.prefreeze_qa` |
| 2 crossblock | apply_cross_block_join_overlay.py | MinerU把同一句切到两个block，拼回来 | 纯规则（65对自动配对） | direct +82 | `.prefreeze_qa_crossblock` |
| 3 toobroad_v2 | apply_too_broad_resplit_overlay.py | "3句以上"被降级但可拆的，重拆 | LLM（50请求） | direct +192 | `.prefreeze_qa_crossblock_toobroad_v2` |
| 4 policy | apply_remaining_review_policy_overlay.py | 剩余91个review逐个定生死 | 人工决策表 | direct +20, parent +61 | `.prefreeze_qa_crossblock_toobroad_policy` |
| 5 zh_enrichment | apply_zh_enrichment_overlay.py | 给所有unit生成中文摘要+术语 | LLM（249请求） | 4973全enrich | `.prefreeze_qa_crossblock_toobroad_policy_zh_enriched` |

## 冻结：freeze_formal_units.py

```
输入: ...prefreeze_qa_crossblock_toobroad_policy_zh_enriched.json
  → 排序（按教材原文顺序：block → sentence → direct优先）
  → 校验（必填字段en_quote/knowledge_en/knowledge_zh、去重）
  → 重编号（v7u_tmp_* → v7u_N######，按原文顺序）
输出:
  v7_bilingual_units.json          4973个冻结unit（4702 direct + 271 parent）
  v7_units_as_cards.json           adapter（v6风格精简字段）
  unit_freeze_manifest.json        tmp→formal全量映射
  excluded_or_review_manifest.json 10个未冻结的review
```

## 数字对账

```
基底:              direct=4399, review=234, parent=210
+prefreeze_qa:     direct=4404, review=271, parent=210
+crossblock:       direct=4486, review=141, parent=210
+toobroad_v2:      direct=4678, review=91,  parent=210
+policy:           direct=4702, review=10,  parent=271
+zh_enrichment:    4973个全部enrich（不改变数量）
冻结:              4973 = 4702 direct + 271 parent, 10 excluded
```

## 关键设计原则

1. **LLM 不写证据原文**：LLM 只决定"哪几句属于一个知识点"，`en_quote` 是脚本按 `sentence_ids` 从原文拼接回填的。证据锚点是教材原文，不是模型生成。
2. **每层 overlay 痕迹可追溯**：最终 unit 的 `risk_flags` 字段记录了它经过哪些 overlay（如 `cross_block_sentence_joined_prefreeze_qa`、`derived_from_too_broad_resplit_overlay`）。
3. **人工决策表承担关键拍板**：prefreeze QA 的 8 条修复 + policy 的 30 条升降级 + terms_map 的 30 个术语，是人工硬编码的，LLM 不做最终拍板。
4. **数字逐层对账**：每一层 overlay 的增减数量在对应 audit 报告里有据可查，最终 4973 = 4702 + 271，数字闭合。

## LLM 调用总计

| 用途 | 模型 | 请求数 | prompt |
|---|---|---|---|
| 英文句子分组（主切分） | DeepSeek Chat | 1724 | v7_unit_split_v2.md |
| 过宽单元重拆 | DeepSeek Chat | 50 | v7_unit_split_v2.md |
| 中文摘要+术语 | DeepSeek Chat | 249+8 | v7_unit_zh_enrichment_v1.md |
| **合计** | | **2031** | |

## 产物位置

```
work/base_units/
├── units/
│   ├── v7_bilingual_units.json          ← 正式资产（4973个冻结unit）
│   ├── v7_units_as_cards.json           ← adapter
│   ├── unit_freeze_manifest.json        ← tmp→formal映射
│   ├── excluded_or_review_manifest.json ← 10个未冻结
│   └── unit_build_report.md
├── draft/v2_fullbook/                   ← 13个版本叠层（基底+5层overlay产物）
├── llm_batches/                         ← LLM请求/响应
├── llm_runs/                            ← 3次跑批的raw_responses
└── audit/                               ← 28个审计目录（12个必要+16个组合冗余）
```
