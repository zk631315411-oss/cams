# P7D：Flow Edge证据审核（暂时弃用）

> **状态：暂时弃用（2026-07-16）**
>
> P7D 暂时不参与 merged-process-ir 流水线。S3 产出的 `cards.raw.json` 直接作为 P7C 最终产物。
>
> **弃用理由：**
> 1. P7D 的”原文明示”审核标准与 merged 模式 S2 的语义建模能力不匹配。S2 正确识别了逻辑先后/参照/产出关系，但教材语言极少逐字标注这些关系，导致大量正确边被判 `llm_inference→pending` 或被拒。
> 2. 旧流程中 P7D 是必要的——旧 LLM 容易把相关写成因果。merged 模式 S2 已用 role+kind+endpoint matrix 做了结构化的语义把关，P7D 变成了对同一判断的重复且更严格的二次审查。
> 3. pending+rejected 占比约 50%，其中相当比例是 S2 建模正确但 P7D 证据标准不匹配的边。
>
> **恢复条件：** 重新定义 P7D 审核口径，使其接受 S2 已建模的逻辑关系，或调整为仅审核”原文明确矛盾”的边。

---

## 定位

P7整体目标是”离线局部流程知识 + 按题生成证明路径”。P7C生成section-local候选card，允许保留一定候选噪声；P7D对现有`flow_edges`逐边审核，决定哪些边可以进入最终程序性证明。

P7D不重新抽card，不修改P7C正本，不新增或连接card，不读取题目、选项或参考答案，也不自动修复P7C产物。

## 两类校验

### 规则校验

规则校验器只处理可确定的结构合同：

- JSON、必填字段和枚举
- card/node/edge ID及重复ID
- edge端点引用和同card边界
- node_category与node_type前缀
- P7B unit引用及同section证据范围
- `DECIDES`必须有condition等schema约束

规则校验器不能确认节点语义、边方向、condition事实、限定词强度或先后关系是否成立。

### 独立LLM证据审核

独立审核器读取P7C card和对应P7B `task.json`中的原始unit、双语教材文本，对每条edge分别检查：

```text
source节点依据
target节点依据
方向依据
condition依据
限定词保留
并列/相关关系是否被误写为先后或产出
```

审核器只返回对现有edge的判断，不生成替代边。

## derivation与review_status

两者必须分开保存：

```text
derivation:
  explicit_text   原文明示关系与方向
  llm_inference   两端有证据，但关系依赖必要功能推理
  unsupported     关系或端点缺少依据

review_status:
  pending         可用于扩展检索，不可用于最终程序断言
  accepted        可用于检索和最终证明路径
  rejected        不可用于检索扩展或最终证明
```

旧P7C边可能携带`derivation`或`evidence_strength`，P7D将其只读保存为可空的`declared_derivation`审计快照。三阶段P7C不输出该字段。`declared_derivation`不参与最终状态计算；最终`derivation`和`review_status`完全由P7D独立审核产生。

P7D审核认为边属于`llm_inference`时，该边保持`pending`并进入人工队列。人工决定后才能变为`accepted`或`rejected`。旧P7C声明本身不会把P7D独立判为`explicit_text`的边压成pending。

## Card结论

Card最终只给：

```text
pass  结构通过，且所有flow edge均为accepted
fail  结构失败，或至少一条edge为pending/rejected
```

Card结论只是汇总，不覆盖边级状态。即使card为fail，也必须保留每条边的独立审核记录。

## 最终答案使用规则

只有`review_status=accepted`的边可以支撑“首先、随后、必须、禁止、如果则进入”等程序断言。

`pending`边可以用于离线召回和扩展检索，但必须携带`answer_eligible=false`，不得进入最终证明路径。

证明路径运行时对`REFERENCES`采用特殊门禁：知识正本仍为`process -> input/standard`，可以派生`input/standard -> process`的反向邻接；反向遍历只表示“作为依据被参照”，不能单独形成因果或结果断言。从辅助节点进入process后，如需证明分类、结果或分支，路径还必须继续经过`accepted`且`answer_eligible=true`的`PRODUCES`或满足`condition`的`DECIDES`。其余边只允许沿正本方向遍历。

运行时不得仅用`card_id + edge_id`复用审核结论，还必须核对P7D保存的`source_edge_snapshot`。如果边的source、target、edge_type、condition、relation_type、derivation或证据unit发生变化，即使edge_id未变，也应视为未审核边，不得进入最终或检索路径。

路径中的任何边只要带`condition`，都必须由当前题目或场景显式满足后才能遍历；这包括限定input/standard适用范围的`REFERENCES.condition`和表达单一路径逻辑前提的`PRECEDES.condition`。`DECIDES`缺少condition时不可遍历。

## 输入

```text
P7C cards.raw.json（只读）
P7B section_packages/<section_id>/task.json
inputs/procedural_schema_v2.json
phases/P7D/inputs/p7d_edge_review_schema_v1.json
```

merged-process-ir 模式下，cards.raw.json 由 S3 LLM 产出（经由 Process IR → cards），P7D 不感知上游 S2/S3 的内部拆分，输入接口不变。

规则结构校验在本地读取完整card、section package和schema，不产生LLM token。

结构通过后，语义审核LLM按card接收：

```text
section_id / section_title
完整section_text_with_unit_anchors
allowed_unit_ids
精简p7c_card_under_review
```

精简card保留title、card_nature、flow_nodes、flow_edges、condition、relation_type和证据unit IDs；移除`candidate_status`、`review_notes`、展示字段、P7C声明的`derivation/source_quote`及旧审核字段。完整section原文仍是唯一事实证据，不再重复发送`section_units`。Runner在LLM审核后使用原始P7C edge另行恢复`declared_derivation`并计算最终状态。

## 输出

```text
p7d_structure_manifest.jsonl       纯结构检查结果
p7d_edge_reviews.jsonl             每条边的当前审核快照
p7d_review_manifest.jsonl          card级pass/fail汇总
p7d_review_history.jsonl           追加式完整审核历史
p7d_human_review_queue.jsonl       llm_inference及其他pending边
p7d_rejected_edge_queue.jsonl      被拒绝边
p7d_run_manifest.json              模型、Prompt、输入和调用记录
p7d_edge_review_report.md          汇总报告
```

上述输出均不回写P7C card。

## 命令

纯结构检查：

```powershell
python scripts\validate_and_route_cards.py `
  --input-dir phases\P7C\outputs\<run_id> `
  --output-dir phases\P7D\outputs\<review_run_id>\structure
```

独立边级审核：

```powershell
python scripts\run_p7d_edge_review_ds.py `
  --input-dir phases\P7C\outputs\<run_id> `
  --output-dir phases\P7D\outputs `
  --run-id <review_run_id> `
  --model deepseek-v4-pro `
  --thinking-effort none `
  --concurrency 10
```

应用人工决定时，决定JSONL每行必须包含`section_id, card_id, edge_id, decision, decided_by, reason`，其中`decision`只能为`accepted`或`rejected`。

## 执行顺序

```text
P7C候选card
  -> P7D规则结构检查
  -> 对结构通过的card逐边LLM审核
  -> 生成edge review、card manifest、history与人工队列
  -> 人工处理关键llm_inference边
  -> 下游按accepted/pending/rejected使用
```

旧目录`outputs/p7c_v5_focus_sections`属于P7D第一版card级启发式产物，只作历史归档，不符合当前边级审核合同。
