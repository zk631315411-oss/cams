# Plan B：句卡挂载改进方案

## 背景

当前教材知识图谱的节点和关系边已经可用，但句卡挂载在短句、列表项和泛语义句卡上存在误挂风险。

典型样例：

- 节点：`GIABA的目标`
- 节点证据：`保护签署国的国家经济和金融及银行系统不受犯罪所得及恐怖融资活动侵害 / 改善打击犯罪所得的措施 / 巩固各成员国之间的合作`
- 句卡：`v6s_N02536`，citation 为 `巩固各成员国之间的合作`

这张句卡实际在 GIABA 小节内，且原文出现在 `GIABA的目标` 的 `evidence_span` 中。但旧版挂载线因为短句缺少实体锚点，BGE 将其挂到了更泛的 `金融行动特别工作组` 节点。

## 旧版问题

旧版脚本：

- `05_mount_cards.py`
- `05a_audit_mount.py`

主要问题：

1. `citation[:30]` 的确定性匹配对短句不友好。
2. BGE top1 只看语义相似，不看教材位置。
3. 每张句卡只保留一个 BGE 节点候选，选错后没有比较空间。
4. `BGE >= 0.7` 自动通过，部分泛语义误挂不会进入人工/LLM 审核。
5. LLM 审核时只看到句卡 `knowledge`，没有 `citation/context/chapter_path/evidence_span`。

## Plan B 原则

Plan B 不改原始 KG 节点和关系，只改句卡挂载策略。

核心原则：

1. **原文证据优先**  
   如果句卡 `citation` 或 `knowledge` 出现在节点 `evidence_span` 中，直接作为强证据候选。

2. **教材位置优先**  
   使用句卡的 `source_line_start`、`chapter_path` 和节点的 `section/subsection/section_node_id` 判断同叶子节、同小节、同章关系。

3. **BGE 只做候选召回**  
   BGE 不直接决定最终挂载，只产出 top-k 候选，再根据教材位置重排。

4. **产物与主线分开**  
   Plan B 默认写入 `work/planb_mounts/`，不会覆盖 `work/ch*/card_mounts*.jsonl`。

## 新脚本

`05_mount_cards_v2.py`

用法：

```bash
python 05_mount_cards_v2.py
python 05_mount_cards_v2.py --no-bge
python 05_mount_cards_v2.py --chapters 3 --top-k 8
```

默认输出：

```text
work/planb_mounts/
├── card_candidates.jsonl
├── summary.json
├── ch2/
│   ├── card_mounts_candidates.jsonl
│   └── card_mounts_strong.jsonl
├── ch3/
│   ├── card_mounts_candidates.jsonl
│   └── card_mounts_strong.jsonl
├── ch4/
│   ├── card_mounts_candidates.jsonl
│   └── card_mounts_strong.jsonl
└── ch5/
    ├── card_mounts_candidates.jsonl
    └── card_mounts_strong.jsonl
```

产物说明：

- `card_candidates.jsonl`：按句卡输出候选节点列表，适合诊断每张卡为什么挂到某个节点。
- `card_mounts_candidates.jsonl`：按节点聚合的候选挂载，适合后续 LLM 审核。
- `card_mounts_strong.jsonl`：只包含 evidence_span 命中的强证据挂载，适合做高精度展示版。
- `summary.json`：统计信息。

## 候选字段

每个候选包含：

```json
{
  "node_id": "cams_v6:C03:S04:U06:N001",
  "method": "evidence_span_citation",
  "score": 1.0,
  "source_alignment": "same_leaf",
  "reason": "card.citation appears in node.evidence_span/definition/title"
}
```

字段含义：

- `method`：候选来源，如 `evidence_span_citation`、`evidence_span_knowledge`、`bge_topk_rerank`。
- `score`：重排后的候选分数。
- `bge_score`：若来自 BGE，则保留原始向量分。
- `source_alignment`：教材位置对齐关系，取值包括 `same_leaf`、`same_subsection`、`same_section`、`same_chapter`、`none`。
- `reason`：挂载原因说明。

## 验证重点

第一批建议抽查：

1. `GIABA的目标`
   - `v6s_N02534`
   - `v6s_N02535`
   - `v6s_N02536`

2. FATF 目标类节点
   - 检查是否仍吸入过多泛化的“打击犯罪/合作/金融系统”句卡。

3. 机构类节点
   - 检查同名机构不同段落是否被误合并后产生泛挂载。

4. 短句/列表项
   - 检查短句是否优先依赖 `evidence_span + source_alignment`，而不是裸 BGE。

## 后续建议

Plan B 当前只生成候选，不直接替换主线。建议后续再新增：

- `05a_audit_mount_v2.py`：对 Plan B 候选做更严格审核。
- `05_assemble_planb.py`：用 Plan B 审核结果生成单独的 `kg_data_planb.json`。
- 抽查通过后，再决定是否同步到 `data/derived/kg_data.json`。

## 2026-07-01 扩大测试记录

已跑两类测试，产物均与主线分离。

### 纯规则测试

命令：

```bash
python 05_mount_cards_v2.py --chapters 3 --no-bge
```

输出：

```text
work/planb_mounts/
```

结果：

- 第 3 章节点数：116
- 强证据挂载句卡：127
- `v6s_N02534 / v6s_N02535 / v6s_N02536` 均正确挂到 `GIABA的目标`
- `v6s_N02536` 命中方式：`evidence_span_citation + same_leaf`

### 全量 BGE 候选测试

命令：

```bash
python 05_mount_cards_v2.py --chapters 2,3,4,5 --top-k 5 --min-score 0.5 --out-dir work/planb_mounts_bge_full_20260701_0925
```

输出：

```text
work/planb_mounts_bge_full_20260701_0925/
```

结果：

- 全书节点数：651
- 句卡数：5199
- 有候选句卡：5197
- 无候选句卡：2
- 强证据挂载句卡：989
- BGE 已启用：`true`
- 平均每张句卡约 5 个候选

重要结论：

1. Plan B 可修复 `GIABA的目标` 这类短句/列表项漏挂问题，强证据候选排在第 1。
2. BGE top-k 仍会召回大量泛相关候选，例如 ACAMS 句卡仍会把 `GIABA的目标` 作为候选之一。
3. 因此 `card_mounts_candidates.jsonl` 只能视为候选包，不能直接作为最终挂载结果。
4. 可直接进入最终展示或组装的，暂时只应是 `card_mounts_strong.jsonl` 或经过 `05a_audit_mount_v2.py` 严格审核后的结果。
