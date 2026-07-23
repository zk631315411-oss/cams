# P7C Process IR to Cards v1

## 角色与唯一职责

你是 P7C-S3 构图器。输入为 S2 输出的 Process IR（带 role 的元素 + 带 kind 的关系）和 section 原文；你的唯一职责是复核 S2 的结构、为每个 element 确定精确的 `node_type`，输出完整的 `flow_nodes + flow_edges`（cards.raw.json）。

不得重新裁决候选边界（S2 已做），不得新增/删除/合并 episode，不得新增/删除 element 或 relation，不得输出 derivation/evidence_strength/review_status。

## 输入

1. section 原文（唯一事实来源）
2. allowed_unit_ids（证据引用白名单）
3. S2 输出的完整 Process IR（episodes、elements、relations、candidate_audit）

## 任务

### 步骤 1：复核 S2 结构

对照原文和 Process IR，检查：
- 每个 episode 内所有 element 是否通过 relation 连通
- 端点角色是否与 relation kind 兼容（见第 2 节矩阵）
- decision 节点如有 branch 出边，是否至少有两条
- 每条 branch/condition trigger 是否有 condition
- evidence_unit_ids 是否在白名单内

发现 S2 错误时在校验说明中记录，但仍尽力完成构图。

### 步骤 2：确定 node_type

为每个 element 从以下类型中精确选择。**依据原文语义和上下文，**。参考 S2 的 role 和 kind，但最终以原文的语义定义为准。

**节点分类（node_category）**：entry（E-）、process（P-）、exit（X-）、auxiliary（input/standard）

**入口类型组（entry，对应 S2 role=context）：**

| node_type | 定义 |
|---|---|
| E1_event_signal | 可定位的业务事件启动处理 |
| E2_object_entry | 某类客户、交易、账户或载体进入处理范围 |
| E3_state_threshold | 已观察状态或阈值结果要求处理 |
| E4_handoff | 上一局部流程的输出成为本流程输入 |
| E5_time_cycle | 固定周期或期限启动/约束处理 |
| E6_change_exception | 环境变化、异常或信息缺口启动调整 |
| E7_external_command | 法律、监管或执法要求启动处理 |
| E8_decision_finding | 前一判断本身触发后续义务 |

**处理类型组（process，对应 S2 role=action 或 decision）：**

| node_type | 定义 |
|---|---|
| P1_assessment | 识别风险信号或异常模式，使用标准形成分类、适宜性或有效性结论 |
| P2_execution | 对业务对象实施动作或应对措施，使其状态发生变化 |
| P3_branch_routing | 根据条件选择关闭、升级、继续、拒绝或其他路径 |
| P4_collection | 汇集信息或部件，形成调查基础或正式产物 |
| P5_coordination | 多角色、多部门或前后台协同完成任务 |
| P6_feedback | 根据缺陷、复核问题或结果返回修改、补充研究或重新设计 |
| P7_monitoring | 按周期重复，或持续观察直到新事件再次触发 |
| P8_constrained_action | 动作必须同时满足保密、禁止泄密、法律、相称性等约束 |
| P9_planning | 将风险处置组织为责任人、期限、措施、复核和升级机制 |
| P10_sufficiency | 判断证据是否足以支持结论并决定继续或停止研究 |

**出口类型组（exit，对应 S2 role=outcome）：**

| node_type | 定义 |
|---|---|
| X1_classification | 形成可疑性、风险、有效性或适宜性结论 |
| X2_product | 形成可识别、可保存或可提交的对象 |
| X3_state_change | 业务对象进入新的稳定状态 |
| X4_handoff | 转交下一角色、层级或局部流程 |
| X5_config_change | 规则、阈值、场景、控制或培训被修改 |
| X6_termination | 当前局部目标结束且无进一步动作 |
| X7_continuing_obligation | 进入持续监控、周期复核或受限制关系 |

**辅助类型组（auxiliary，对应 S2 role=input 或 standard）：**
- `input`：输入数据、材料、信息
- `standard`：标准、阈值、规范

role→node_category 是固定的（context→entry, action/decision→process, outcome→exit, input/standard→auxiliary），但 node_type 必须根据上述定义和原文语义选择最精确的一个。

### 步骤 3：构建 flow_nodes + flow_edges

**flow_node（每个 element 对应一个 node）：**
- `node_id`：在 episode 内唯一
- `node_category`：entry/process/exit/auxiliary
- `node_type`：步骤 2 确定的值（27 种之一）
- `label`：保留 element.label 原文
- `evidence_unit_ids`：element 的 evidence_unit_ids
- `evidence_strength`：固定 `explicit`
- `modality`：element 的 modality（可选）

**flow_edge（每个 relation 对应一条 edge，节点引用 node_id）：**

根据 S2 relation 的 kind 和原文语义选择 edge_type。**以原文为准——kind 是建议，不是命令**：

| edge_type | 定义 | S2 kind 的对应关系 |
|---|---|---|
| PRECEDES | 主流程先后关系；表示一个节点在流程上先于另一个节点，或存在明确/强暗示的处理顺序 | trigger、sequence 通常映射为此 |
| REFERENCES | 非时序辅助关联；表示处理节点关联一个输入、线索、标准、判断维度或组成要素，不表示先后、产出或条件分支 | reference 通常映射为此 |
| PRODUCES | 产出关系；表示处理节点产生一个出口节点，如判断、记录、状态变化、交接或持续义务 | produce 通常映射为此，但须确认原文确有产出语义 |
| DECIDES | 条件分流关系；表示根据条件进入不同路径，必须填写 condition | branch 通常映射为此 |
| FEEDBACK | 反馈回流关系；表示结果、复核问题或缺口要求补充、修正、更新或重新处理 | feedback 通常映射为此 |

每条 flow_edge 必填：`edge_id, edge_type, source, target, evidence_unit_ids`。
- `condition`：有则必填（trigger_mode=condition 或 DECIDES 必须有）
- `relation_type`：可选，从 12 种中选择（见下方定义）
- `qualifier`：当 PRODUCES 的原文强度不是"确定产生"时必填：`may_lead_to`（can/may/might 等非确定）、`helps_achieve`（helps/有助于）、`aimed_to`（purpose is to/旨在/以）。原文明确是 produces/results in/导致/产生时省略
- `source_quote`：可选

**12 种 relation_type 定义（可选附加在 edge 上）：**

| relation_type | 定义 |
|---|---|
| clue_supports_identification | 异常、红旗、事实线索支持考生识别风险、可疑性或高风险模式 |
| mechanism_explains_risk | 作案机制、结构安排或产品特征解释为什么存在洗钱/恐融风险 |
| identification_leads_to_conclusion | 识别或评估结果导向风险分类、可疑性、充分性或适宜性结论 |
| conclusion_triggers_response | 风险、可疑、缺陷或合规结论触发加强监控、升级、报告、补救或拒绝等要求 |
| branch_condition_routes_path | 分支条件把流程路由到某条路径；只能用于 DECIDES 边且必须有 condition |
| component_assembles_product | 信息字段、证据、叙述组件或记录要素共同构成正式产物 |
| standard_constrains_action | 法律、保密、相称性、准确性、监管期限等标准限定动作如何执行 |
| result_handoffs_stage | 当前处理结果成为下一角色、层级、系统或外部机构继续处理的输入 |
| feedback_requests_completion | 复核问题、缺失信息或叙述不足要求补充研究、修订或重新处理 |
| cycle_requires_monitoring | 周期、持续义务、后评估或 ongoing monitoring 关系要求复核或继续观察 |
| standard_transmits_requirement | 国际标准、监管原则、指南或评估结果传导为辖区或机构控制要求 |
| parallel_alternative_no_sequence | 多个 typology、标准、组件或案例点互为并列，不应强制串成时间先后边 |

**不得输出**：`derivation`、边级 `evidence_strength`、`review_status`。

## 2. Relation 端点兼容矩阵

| kind | 起点 role | 终点 role | 额外约束 |
|---|---|---|---|
| `trigger` | context | action 或 decision | trigger_mode 必须为 event 或 condition |
| `sequence` | action/decision/outcome | action/decision/outcome | 原文明示先后；context 起点应改用 trigger |
| `reference` | action 或 decision | input 或 standard | 固定 process→auxiliary |
| `produce` | action 或非 P3 的 decision | outcome | target 必须是独立语义结果 |
| `branch` | decision | action 或 outcome | 至少两个互斥分支；每条 condition 必填 |
| `feedback` | outcome 或 decision | action 或 decision | 原文支持复核、补充、更新或调优 |

## 输出 Contract

```json
{
  "section_id": "CH06-S10",
  "cards": [
    {
      "card_id": "p7card_CH06-S10_001",
      "section_id": "CH06-S10",
      "card_nature": "assessment",
      "title": "依据直接和间接持股及适用阈值认定UBO",
      "flow_nodes": [
        {
          "node_id": "n001",
          "node_category": "auxiliary",
          "node_type": "input",
          "label": "直接持股比例",
          "evidence_unit_ids": ["v7u_N000477"],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "edge_001",
          "edge_type": "REFERENCES",
          "source": "n004",
          "target": "n001",
          "evidence_unit_ids": ["v7u_N000477"]
        }
      ],
      "source_unit_ids": ["v7u_N000477", "v7u_N000478"],
      "candidate_status": "candidate",
      "review_notes": "局部命题：...；证据范围：...；待P7D逐边审核。"
    }
  ],
  "coverage_audit": [
    {
      "candidate_id": "s1c_001",
      "disposition": "mapped",
      "card_ids": ["p7card_CH06-S10_001"],
      "reason": "..."
    }
  ],
  "node_type_reasons": {
    "ep_001": {
      "e001": "input role → node_type=input",
      "e005": "decision role + 2 branch relations → P3_branch_routing"
    }
  },
  "skip_reason": null
}
```

- 一个 episode 对应一张 card
- card_id 格式 `p7card_{section_id}_{NNN}`
- 每个 flow_node 有 `node_id, node_category, node_type, label, evidence_unit_ids, evidence_strength`
- 每条 flow_edge 有 `edge_id, edge_type, source, target, evidence_unit_ids`
- 条件必填 `condition`，不输出 `derivation`
- candidate_status 固定 `candidate`
- review_notes 中文说明增量命题、证据范围、待 P7D 审核
- `node_type_reasons` 记录每个 element 的 node_type 选择理由（至少记录非平凡选择）

`coverage_audit` 沿用 S2 的 `candidate_audit.disposition`，映射规则：
- `mapped/support_only` → `decision: "p7c_card"`，card_ids 至少一张
- `excluded_nonprocedural` → `decision: "kg_only"`，card_ids 为空
- `ungraphable` → `decision: "p7c_ungraphable"`，card_ids 为空

## 当前section

section_id: `CH36-S05`

section_title: `Types of risk assessment > Preparing a risk appetite statement`

section_text_with_unit_anchors:

```text
[v7u_N002704|2704] According to the Financial Stability Board in the US, the RAS is a formal document, developed by an organization’s senior management and approved by the board of directors. It establishes risk limits while supporting the organization’s business objectives. This prospective document defines what types of risks the organization is willing to accept, mitigate, or avoid based on its strategic targets, regulatory environment, and expectations.
ZH: 风险偏好声明（RAS）是由高级管理层制定、董事会批准的形式文件

[v7u_N002705|2705] To prepare an effective RAS, an organization should have a structured approach to:
ZH: 准备有效RAS的结构化方法列表引导

[v7u_N002706|2706] Drive the decision-making process with top-down board leadership and bottom-up feedback from all levels of management.
ZH: 通过自上而下的董事会领导和自下而上的管理层反馈推动决策

[v7u_N002707|2707] Identify unique risks to the organization and assess the effects, actively consulting with risk management teams.
ZH: 识别机构特有风险并评估影响，积极咨询风险管理团队

[v7u_N002708|2708] Decide the extent to which these risks can be accepted.
ZH: 决定这些风险可接受的程度

[v7u_N002709|2709] Define clear thresholds or limits.
ZH: 定义明确的阈值或限额

[v7u_N002710|2710] Draft the RAS with senior management and seek approval from the board.
ZH: 与高级管理层共同起草RAS并寻求董事会批准

[v7u_N002711|2711] Regularly monitor and update the RAS.
ZH: 定期监控和更新RAS

[v7u_N002712|2712] Ensure that all business units are aware of the RAS, including updates.
ZH: 确保所有业务单元了解RAS及其更新

[v7u_N002713|2713] An effective RAS allows informed decision-making and helps the organization reach its strategic objectives while mitigating and managing risks effectively.
ZH: 有效的RAS有助于明智决策并实现战略目标

[v7u_N002714|2714] Regulatory expectations and legal obligations help determine the acceptable level of risks in the RAS.
ZH: 监管期望和法律义务帮助确定RAS中的可接受风险水平

[v7u_N002715|2715] Financial institutions should not accept risks that violate applicable AML/CFT laws or sanctions regimes.
ZH: 金融机构不得接受违反反洗钱/反恐怖融资法律或制裁制度的风险

[v7u_N002716|2716] For example, if a potential customer resides in a Category I jurisdiction, that jurisdiction might have strategic AML/CFT deficiencies, and countermeasures might apply.
ZH: 示例：一类辖区可能具有战略性反洗钱/反恐怖融资缺陷并适用反制措施

[v7u_N002717|2717] If the applicable laws require financial institutions to seek permission from the regulator before entering any business relationships, the RAS must carefully address customer acceptance or business relationships with those jurisdictions.
ZH: 若法律要求获得监管许可才能建立业务关系，RAS必须审慎处理客户接纳

[v7u_N002718|2718] A financial institution’s RAS might include zero appetite statements. Zero appetite means the financial institution refuses to take on certain risks related to specific customer types, products, services, or sectors.
ZH: 零容忍偏好指金融机构拒绝承担特定客户、产品或行业相关风险

[v7u_N002719|2719] For example, a financial institution might declare it will not accept customers from countries under strict EU, UN, or OFAC sanctions.
ZH: 示例：金融机构声明不接受受欧盟、联合国或OFAC严格制裁国家的客户

[v7u_N002720|2720] By avoiding certain risks, the organization minimizes exposure to high-risk areas.
ZH: 规避特定风险可最小化机构对高风险领域的敞口
```

allowed_unit_ids:

```json
[
  "v7u_N002704",
  "v7u_N002705",
  "v7u_N002706",
  "v7u_N002707",
  "v7u_N002708",
  "v7u_N002709",
  "v7u_N002710",
  "v7u_N002711",
  "v7u_N002712",
  "v7u_N002713",
  "v7u_N002714",
  "v7u_N002715",
  "v7u_N002716",
  "v7u_N002717",
  "v7u_N002718",
  "v7u_N002719",
  "v7u_N002720"
]
```

## S2 Process IR

```json
{
  "section_id": "CH36-S05",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001",
        "s1c_002"
      ],
      "focal_question": "如何准备有效的RAS并确定可接受风险水平？",
      "title": "通过结构化方法制定RAS并依据监管和法律义务确定风险接受水平",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "应驱动决策过程（自上而下董事会领导和自下而上管理层反馈）",
          "evidence_unit_ids": [
            "v7u_N002706"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "应识别机构特有风险并评估影响，积极咨询风险管理团队",
          "evidence_unit_ids": [
            "v7u_N002707"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "decision",
          "label": "应决定这些风险可接受的程度",
          "evidence_unit_ids": [
            "v7u_N002708"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "action",
          "label": "应定义明确的阈值或限额",
          "evidence_unit_ids": [
            "v7u_N002709"
          ],
          "modality": null
        },
        {
          "element_id": "e005",
          "role": "action",
          "label": "应与高级管理层共同起草RAS并寻求董事会批准",
          "evidence_unit_ids": [
            "v7u_N002710"
          ],
          "modality": null
        },
        {
          "element_id": "e006",
          "role": "action",
          "label": "应定期监控和更新RAS",
          "evidence_unit_ids": [
            "v7u_N002711"
          ],
          "modality": null
        },
        {
          "element_id": "e007",
          "role": "action",
          "label": "应确保所有业务单元了解RAS及其更新",
          "evidence_unit_ids": [
            "v7u_N002712"
          ],
          "modality": null
        },
        {
          "element_id": "e008",
          "role": "outcome",
          "label": "有效的RAS被制定并传达",
          "evidence_unit_ids": [
            "v7u_N002705",
            "v7u_N002712"
          ],
          "modality": null
        },
        {
          "element_id": "e009",
          "role": "standard",
          "label": "监管期望和法律义务",
          "evidence_unit_ids": [
            "v7u_N002714"
          ],
          "modality": null
        },
        {
          "element_id": "e010",
          "role": "outcome",
          "label": "确定的可接受风险水平及限制，如零容忍声明（不得接受违反AML/CFT法律或制裁的风险、拒绝受制裁国家客户等）",
          "evidence_unit_ids": [
            "v7u_N002708",
            "v7u_N002715",
            "v7u_N002718",
            "v7u_N002719"
          ],
          "modality": null
        },
        {
          "element_id": "e011",
          "role": "outcome",
          "label": "识别的风险及其评估影响",
          "evidence_unit_ids": [
            "v7u_N002707"
          ],
          "modality": null
        },
        {
          "element_id": "e012",
          "role": "outcome",
          "label": "经批准的风险偏好声明(RAS)",
          "evidence_unit_ids": [
            "v7u_N002710"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "sequence",
          "trigger_mode": null,
          "trigger_element_id": null,
          "process_element_id": null,
          "before_element_id": "e001",
          "after_element_id": "e002",
          "condition": null,
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002705",
            "v7u_N002706",
            "v7u_N002707"
          ],
          "source_quote": "To prepare an effective RAS, an organization should have a structured approach to: (1) Drive the decision-making process..., (2) Identify unique risks..."
        },
        {
          "relation_id": "r002",
          "kind": "sequence",
          "trigger_mode": null,
          "trigger_element_id": null,
          "process_element_id": null,
          "before_element_id": "e002",
          "after_element_id": "e003",
          "condition": null,
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002707",
            "v7u_N002708"
          ],
          "source_quote": "... (2) Identify unique risks... (3) Decide the extent..."
        },
        {
          "relation_id": "r003",
          "kind": "sequence",
          "trigger_mode": null,
          "trigger_element_id": null,
          "process_element_id": null,
          "before_element_id": "e003",
          "after_element_id": "e004",
          "condition": null,
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002708",
            "v7u_N002709"
          ],
          "source_quote": "... (3) Decide the extent... (4) Define clear thresholds..."
        },
        {
          "relation_id": "r004",
          "kind": "sequence",
          "trigger_mode": null,
          "trigger_element_id": null,
          "process_element_id": null,
          "before_element_id": "e004",
          "after_element_id": "e005",
          "condition": null,
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002709",
            "v7u_N002710"
          ],
          "source_quote": "... (4) Define clear thresholds... (5) Draft the RAS..."
        },
        {
          "relation_id": "r005",
          "kind": "sequence",
          "trigger_mode": null,
          "trigger_element_id": null,
          "process_element_id": null,
          "before_element_id": "e005",
          "after_element_id": "e006",
          "condition": null,
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002710",
            "v7u_N002711"
          ],
          "source_quote": "... (5) Draft the RAS... (6) Regularly monitor and update..."
        },
        {
          "relation_id": "r006",
          "kind": "sequence",
          "trigger_mode": null,
          "trigger_element_id": null,
          "process_element_id": null,
          "before_element_id": "e006",
          "after_element_id": "e007",
          "condition": null,
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002711",
            "v7u_N002712"
          ],
          "source_quote": "... (6) Regularly monitor... (7) Ensure that all business units are aware..."
        },
        {
          "relation_id": "r007",
          "kind": "reference",
          "trigger_mode": null,
          "trigger_element_id": null,
          "process_element_id": "e003",
          "auxiliary_element_id": "e009",
          "condition": null,
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002714"
          ],
          "source_quote": "Regulatory expectations and legal obligations help determine the acceptable level of risks in the RAS."
        },
        {
          "relation_id": "r008",
          "kind": "reference",
          "trigger_mode": null,
          "trigger_element_id": null,
          "process_element_id": "e003",
          "auxiliary_element_id": "e011",
          "condition": null,
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002707",
            "v7u_N002708"
          ],
          "source_quote": "Identify unique risks ... and assess the effects ... Decide the extent to which these risks can be accepted."
        },
        {
          "relation_id": "r009",
          "kind": "produce",
          "trigger_mode": null,
          "trigger_element_id": null,
          "process_element_id": "e002",
          "outcome_element_id": "e011",
          "condition": null,
          "relation_type": "identification_leads_to_conclusion",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002707"
          ],
          "source_quote": "Identify unique risks to the organization and assess the effects"
        },
        {
          "relation_id": "r010",
          "kind": "produce",
          "trigger_mode": null,
          "trigger_element_id": null,
          "process_element_id": "e003",
          "outcome_element_id": "e010",
          "condition": null,
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002708",
            "v7u_N002715",
            "v7u_N002718"
          ],
          "source_quote": "Decide the extent to which these risks can be accepted. ... Financial institutions should not accept risks ... zero appetite ..."
        },
        {
          "relation_id": "r011",
          "kind": "produce",
          "trigger_mode": null,
          "trigger_element_id": null,
          "process_element_id": "e005",
          "outcome_element_id": "e012",
          "condition": null,
          "relation_type": "component_assembles_product",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002710"
          ],
          "source_quote": "Draft the RAS with senior management and seek approval from the board."
        },
        {
          "relation_id": "r012",
          "kind": "reference",
          "trigger_mode": null,
          "trigger_element_id": null,
          "process_element_id": "e006",
          "auxiliary_element_id": "e012",
          "condition": null,
          "relation_type": "cycle_requires_monitoring",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002711"
          ],
          "source_quote": "Regularly monitor and update the RAS."
        },
        {
          "relation_id": "r013",
          "kind": "reference",
          "trigger_mode": null,
          "trigger_element_id": null,
          "process_element_id": "e007",
          "auxiliary_element_id": "e012",
          "condition": null,
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002712"
          ],
          "source_quote": "... all business units are aware of the RAS, including updates."
        },
        {
          "relation_id": "r014",
          "kind": "produce",
          "trigger_mode": null,
          "trigger_element_id": null,
          "process_element_id": "e007",
          "outcome_element_id": "e008",
          "condition": null,
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002712",
            "v7u_N002705"
          ],
          "source_quote": "Ensure that all business units are aware of the RAS ... To prepare an effective RAS"
        }
      ],
      "split_reason": null
    }
  ],
  "candidate_audit": [
    {
      "candidate_id": "s1c_001",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "该候选描述了准备有效RAS的结构化步骤序列，构成流程的主体动作和顺序，独立支持程序性关系。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "该候选提供了确定可接受风险水平时需考虑的监管和法律义务及具体限制，为决策步骤提供标准、约束和结果说明，是同一流程的必要组成部分。"
    }
  ],
  "skip_reason": null
}
```
