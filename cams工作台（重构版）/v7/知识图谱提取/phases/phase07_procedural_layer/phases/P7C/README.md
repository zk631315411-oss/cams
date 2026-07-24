# P7C：Section Flow Card 抽取

## 定位

P7C 是 section-local 候选流程知识抽取层。它从 P7B 证据包中发现并构建候选 card，允许保留一定候选噪声。P7C 产出的 `cards.raw.json` 直接作为最终产物供 P7G 按题遍历证明路径，不再经过 P7D（P7D 已于 2026-07-16 弃用）。

P7C card 固定 `candidate_status=candidate`。节点 `evidence_strength` 固定 `explicit`。

## 主流程（merged-process-ir）

```
S1.1 (LLM) 候选发现 → S1.2 (LLM) 补漏 → S2 (LLM) Process IR 简易图 → S3 (LLM) 复核+填node_type → cards.raw.json
```

四个阶段的分工：

| 阶段 | 谁 | 输入 | 做什么 | 接触 schema | 输出 |
|---|---|---|---|---|---|
| S1.1 | LLM | section 原文 | 高召回发现候选框架 | — | s11_propositions.json |
| S1.2 | LLM | 原文 + S1.1 候选 | 独立补漏，只增不改 | — | s12_gap_propositions.json |
| S2 | LLM | 原文 + 合并候选 | 语义建模：识别元素(6种role)和关系(6种kind)，建简易图 | 6 role + 6 kind | process_ir.json |
| S3 | LLM | 原文 + Process IR | 复核 S2 结构 + 选 node_type + 输出 cards | 25 node_type + 5 edge_type | cards.raw.json |
| P7D | LLM | cards + 原文 | 逐边证据审核 | — | p7d_edge_reviews.jsonl |

核心设计原则：

- **S2 不读 KG**。输入只有 section 原文 + S1 候选，不做 KG 对比。问题从"KG 有没有"变为"原文能否构成局部流程"
- **允许 KG-P7 重叠**。阈值、标准、事实即使已在 KG 中，只要是流程的构成要素，就可以进入 Process IR
- **S2/S3 职责分离**：S2 做 LLM 擅长的语义理解（role + kind），S3 做 LLM 擅长的 schema 细化（25 种 node_type），中间不插机械步骤

### S1.1：候选发现

S1.1 高召回地发现可能进入 P7 的局部流程或判断单元，围绕一个中心处理/判断/法律适用/归责组织候选框架：

```text
触发 / 情境 / 输入 / 标准 / 条件
                -> 中心处理 / 判断 / 法律适用 / 归责
                -> 结果 / 分支 / 后续行动
```

S1.1 只接收 `section_id`、`section_title` 和完整 `section_text_with_unit_anchors`。不发送 KG、allowed_unit_ids、题目或答案。

### S1.2：独立补漏

S1.2 接收原文和 S1.1 完整候选列表，重新扫描 section，只增加未承接的候选。不删除、不改写、不做 KG 裁决，不构图。使用与 S1.1 相同的候选定义和证据合同。

### S2：Process IR 简易图

S2 将 S1 候选建模为 episod 级别的局部流程。每个 episode 围绕一个中心问题，element 只用 **6 种 role**（无 node_type）：

| role | 含义 | 示例 |
|---|---|---|
| context | 情境、触发事件、状态、发现 | 审查所有权结构 |
| input | 输入数据、材料 | 直接和间接持股数据 |
| standard | 标准、阈值、规范 | 受益所有权识别阈值（25%+） |
| action | 业务处理、执行、收集 | 合计直接和间接持股比例 |
| decision | 判断、分支路由、充分性判定 | 判断合计持股是否达到阈值 |
| outcome | 分类、产物、状态变化、义务 | 认定为 UBO / 不认定为 UBO |

relation 只用 **6 种 kind**：

| kind | 语义 | 方向 |
|---|---|---|
| trigger | 情境触发动作/判断 | context → action/decision |
| sequence | 先后顺序 | action/decision/outcome → action/decision/outcome |
| reference | 动作参照输入/标准 | action/decision → input/standard |
| produce | 动作产出结果 | action/decision → outcome |
| branch | 判断分支路由 | decision → action/outcome |
| feedback | 结果反馈修正 | outcome/decision → action/decision |

### S3：IR → Cards

S3 接收 S2 的 Process IR + section 原文 + allowed_unit_ids，做三件事：

1. **复核 S2 结构**：连通性、端点角色兼容、branch 数量、条件完整性
2. **确定 node_type**：从 25 种中为每个 element 精确选择。确定性规则：input→input、standard→standard、decision+2+branch→P3_branch_routing；其余依据 role、label 语义、邻接关系、card_nature 判断
3. **输出 cards.raw.json**：完整的 flow_nodes（带 node_type/nod_category/evidence_strength） + flow_edges（带 edge_type）

kind → edge_type 映射：trigger/sequence→PRECEDES、reference→REFERENCES、produce→PRODUCES、branch→DECIDES、feedback→FEEDBACK。

S3 不输出 derivation、evidence_strength、review_status。

## merged 模式产物

```
s11_propositions.json              S1.1 候选发现
s12_gap_propositions.json          S1.2 补漏候选
s1_propositions.json               S1.1+S1.2 合并正本
s2_process_ir_prompt.md             S2 发出的 Prompt
s2_process_ir_raw_response.txt      S2 LLM 原始返回
process_ir.json                     S2 产物——简易图（无 node_type）
s3_to_cards_prompt.md              S3 发出的 Prompt
s3_to_cards_raw_response.txt       S3 LLM 原始返回
cards.raw.json                     最终产物——完整 flow_nodes+flow_edges
compile_audit.json                 代码后处理——IR→cards 映射追溯
run_manifest.json                  运行元信息
```

## 使用方式

```bash
python scripts/run_p7c_batch_ds.py \
  --pipeline-mode merged-process-ir \
  --sections CH06-S10,CH07-S03 \
  --thinking-effort none \
  --concurrency 6 \
  --run-id <run_id>
```

## 旧路径（历史兼容）

`--four-stage` / `--three-stage` / `--two-stage` 为历史兼容模式，旧 Prompt 和产物可读取、可归档，不删除。merged-process-ir 是当前 P7C 实验主线。

四阶段产物对比（merged 模式不生成 boundary_decisions.json 和 construction_audit.json）：

```text
# 旧四阶段
boundary_decisions.json   S2 KG 边界裁决
construction_audit.json   S3 构图记录

# merged 模式（替代上述）
process_ir.json           S2 Process IR 简易图
s3_to_cards_prompt.md     S3 Prompt
compile_audit.json        IR→cards 映射
```

## p7_card 合同

每张 card 必填：`card_id, section_id, card_nature, title, flow_nodes, flow_edges, source_unit_ids, candidate_status, review_notes`。

`card_nature`：`execution`（流程）、`assessment`（评估判断）、`risk_indicator`（风险指标）、`control`（控制措施）。

## flow_nodes（27 种）

```
E1_event_signal  E2_object_entry  E3_state_threshold  E4_handoff
E5_time_cycle    E6_change_exception  E7_external_command  E8_decision_finding
P1_assessment    P2_execution  P3_branch_routing  P4_collection  P5_coordination
P6_feedback      P7_monitoring  P8_constrained_action  P9_planning  P10_sufficiency
X1_classification  X2_product  X3_state_change  X4_handoff
X5_config_change   X6_termination  X7_continuing_obligation
input  standard
```

node_category：entry（E-）、process（P-）、exit（X-）、auxiliary（input/standard）。

## flow_edges（5 种）

`PRECEDES / REFERENCES / PRODUCES / DECIDES / FEEDBACK`。每条边必填 `edge_id, edge_type, source, target, evidence_unit_ids`。`DECIDES` 必填 `condition`。不输出 `derivation`。

`relation_type`（12 种，可选）：补充 edge_type 无法表达的语义关系。

## P7C 不做

```text
不生成 p7_bridge_edge     不跨 section 合并流程
不生成 cluster             不生成 scenario_path
不生成 Mermaid / draw.io   不写考生解析
不读取题目或参考答案
```
