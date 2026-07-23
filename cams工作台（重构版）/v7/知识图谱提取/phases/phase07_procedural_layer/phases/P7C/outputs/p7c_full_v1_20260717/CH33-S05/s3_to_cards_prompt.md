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

section_id: `CH33-S05`

section_title: `Introduction > Pillars of an AFC compliance program`

section_text_with_unit_anchors:

```text
[v7u_N002396|2396] According to FinCEN, the five pillars of an AML program include:
ZH: FinCEN提出的反洗钱项目五大支柱。

[v7u_N002397|2397] Internal policies, procedures, and controls: Framework supporting the program.
ZH: 内部政策、程序和控制措施是支持AML项目的框架。

[v7u_N002398|2398] Designated AML compliance officer: Individual responsible for overseeing the program.
ZH: 指定的反洗钱合规官负责监督反洗钱项目。

[v7u_N002399|2399] Ongoing employee training: Regular training on AML policies, procedures, and risk awareness.
ZH: 持续的员工培训包括反洗钱政策、程序和风险意识的定期培训。

[v7u_N002400|2400] Independent audit: Periodic testing and evaluation of the program's effectiveness.
ZH: 独立审计定期测试和评估AML项目的有效性。

[v7u_N002401|2401] CDD: Processes to verify customer identity and assess risk.
ZH: 客户尽职调查（客户尽职调查）是验证客户身份并评估风险的过程。

[v7u_N002402|2402] Other organizations, such as FATF and regulators from multiple jurisdictions, have similar expectations in place.
ZH: FATF及多辖区监管机构也提出了类似期望。

[v7u_N002403|2403] The first pillar of an effective AML program is a system of internal policies and controls that ensure ongoing compliance with AML regulations.
ZH: 有效反洗钱计划的第一大支柱是确保持续合规的内部政策与控制系统。

[v7u_N002404|2404] These controls should align with the organization's risk profile and be documented in writing.
ZH: 控制措施应与组织的风险状况保持一致并书面记录。

[v7u_N002405|2405] They must clearly define AML responsibilities—from senior executives to employees responsible for customer onboarding.
ZH: 必须明确界定从高管到客户入职人员的反洗钱职责。

[v7u_N002406|2406] AML policies should also include escalation procedures for escalating concerns to senior management and the board of directors.
ZH: 反洗钱政策应包含向高级管理层和董事会上报问题的程序。

[v7u_N002407|2407] The second pillar requires a designated compliance officer who oversees the AML process. The designated compliance officer is responsible for managing the program. Compliance officers must have the appropriate experience and knowledge.
ZH: 第二大支柱要求指定一名合规官负责监督反洗钱流程，该官员须具备适当经验与知识。

[v7u_N002408|2408] The third pillar mandates regular, ongoing AML training for employees.
ZH: 第三大支柱要求对员工进行定期、持续的反洗钱培训。

[v7u_N002409|2409] Regulations and laws change frequently, and so do financial criminal tactics and sophistication.
ZH: 法规与犯罪手法及复杂程度频繁变化，因此培训必须持续更新。

[v7u_N002410|2410] Training should cover internal controls and clearly explain employees’ roles and responsibilities within the AML program.
ZH: 培训应涵盖内部控制并清晰说明员工在反洗钱计划中的角色与职责。

[v7u_N002411|2411] The fourth pillar is an independent audit function that tests whether internal AML policies are adequate and effective.
ZH: 第四大支柱是独立审计职能，用于测试内部反洗钱政策是否充分有效。

[v7u_N002412|2412] Independent audit functions must have sufficient knowledge and experience to understand and analyze the AML program.
ZH: 独立审计职能必须具备足够的知识和经验来理解与分析反洗钱计划。

[v7u_N002413|2413] The purpose of independent testing is to confirm whether the program is operating as expected, with effective internal controls.
ZH: 独立测试的目的是确认计划是否按预期运行且内部控制有效。

[v7u_N002414|2414] The fifth pillar, CDD, requires organizations to identify and verify the identity of customers.
ZH: 第五大支柱客户尽职调查要求机构识别并验证客户身份。

[v7u_N002415|2415] Organizations must also conduct ongoing transaction monitoring to identify and report suspicious transactions.
ZH: 机构还必须进行持续交易监控以识别并报告可疑交易。

[v7u_N002416|2416] The organization must understand the potential AML risks presented by its clients.
ZH: 机构必须了解客户带来的潜在反洗钱风险。
```

allowed_unit_ids:

```json
[
  "v7u_N002396",
  "v7u_N002397",
  "v7u_N002398",
  "v7u_N002399",
  "v7u_N002400",
  "v7u_N002401",
  "v7u_N002402",
  "v7u_N002403",
  "v7u_N002404",
  "v7u_N002405",
  "v7u_N002406",
  "v7u_N002407",
  "v7u_N002408",
  "v7u_N002409",
  "v7u_N002410",
  "v7u_N002411",
  "v7u_N002412",
  "v7u_N002413",
  "v7u_N002414",
  "v7u_N002415",
  "v7u_N002416"
]
```

## S2 Process IR

```json
{
  "section_id": "CH33-S05",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "如何进行持续交易监控以识别和报告可疑交易",
      "title": "进行持续交易监控以识别和报告可疑交易",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "进行持续交易监控",
          "evidence_unit_ids": [
            "v7u_N002415"
          ],
          "modality": "required"
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "识别并报告可疑交易",
          "evidence_unit_ids": [
            "v7u_N002415"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e002",
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002415"
          ],
          "source_quote": "to identify and report suspicious transactions",
          "relation_type": null
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_gap_ch33_s05_pillar5_customer_id"
      ],
      "focal_question": "如何依据第五支柱要求识别和验证客户身份",
      "title": "依据第五支柱要求识别和验证客户身份",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "第五大支柱：CDD要求",
          "evidence_unit_ids": [
            "v7u_N002414"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "识别和验证客户身份",
          "evidence_unit_ids": [
            "v7u_N002414"
          ],
          "modality": "required"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "trigger",
          "trigger_mode": "event",
          "trigger_element_id": "e001",
          "process_element_id": "e002",
          "condition": null,
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002414"
          ],
          "source_quote": "The fifth pillar, CDD, requires organizations to identify and verify the identity of customers."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_gap_ch33_s05_pillar2"
      ],
      "focal_question": "如何指定合规官并确保其具备资格与职责",
      "title": "指定合规官并赋予监督职责",
      "card_nature": "control",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "第二支柱要求",
          "evidence_unit_ids": [
            "v7u_N002407"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "指定合规官",
          "evidence_unit_ids": [
            "v7u_N002407"
          ],
          "modality": "required"
        },
        {
          "element_id": "e003",
          "role": "standard",
          "label": "合规官必须具备适当经验和知识",
          "evidence_unit_ids": [
            "v7u_N002407"
          ],
          "modality": "required"
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "合规官监督和管理反洗钱过程",
          "evidence_unit_ids": [
            "v7u_N002407"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "trigger",
          "trigger_mode": "event",
          "trigger_element_id": "e001",
          "process_element_id": "e002",
          "condition": null,
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002407"
          ],
          "source_quote": "The second pillar requires a designated compliance officer..."
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "process_element_id": "e002",
          "auxiliary_element_id": "e003",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002407"
          ],
          "source_quote": "Compliance officers must have the appropriate experience and knowledge."
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e004",
          "relation_type": "component_assembles_product",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002407"
          ],
          "source_quote": "who oversees the AML process. The designated compliance officer is responsible for managing the program."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_gap_ch33_s05_pillar3"
      ],
      "focal_question": "如何提供符合要求的持续AML培训",
      "title": "根据第三支柱要求提供定期持续AML培训",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "第三支柱要求",
          "evidence_unit_ids": [
            "v7u_N002408"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "提供定期持续AML培训",
          "evidence_unit_ids": [
            "v7u_N002408"
          ],
          "modality": "required"
        },
        {
          "element_id": "e003",
          "role": "standard",
          "label": "涵盖内部控制",
          "evidence_unit_ids": [
            "v7u_N002410"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "standard",
          "label": "清晰说明员工角色与职责",
          "evidence_unit_ids": [
            "v7u_N002410"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "trigger",
          "trigger_mode": "event",
          "trigger_element_id": "e001",
          "process_element_id": "e002",
          "condition": null,
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002408"
          ],
          "source_quote": "The third pillar mandates regular, ongoing AML training for employees."
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "process_element_id": "e002",
          "auxiliary_element_id": "e003",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002410"
          ],
          "source_quote": "Training should cover internal controls"
        },
        {
          "relation_id": "r003",
          "kind": "reference",
          "process_element_id": "e002",
          "auxiliary_element_id": "e004",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002410"
          ],
          "source_quote": "Training should clearly explain employees’ roles and responsibilities within the AML program."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_gap_ch33_s05_pillar4"
      ],
      "focal_question": "如何实施独立审计以确认AML计划的有效性",
      "title": "实施独立审计测试以确认AML政策与计划的有效性",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "第四支柱要求",
          "evidence_unit_ids": [
            "v7u_N002411"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "执行独立审计测试",
          "evidence_unit_ids": [
            "v7u_N002411"
          ],
          "modality": "required"
        },
        {
          "element_id": "e003",
          "role": "standard",
          "label": "具备足够知识和经验",
          "evidence_unit_ids": [
            "v7u_N002412"
          ],
          "modality": "required"
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "确认内部AML政策是否充分有效，以及计划是否按预期运行且内部控制有效",
          "evidence_unit_ids": [
            "v7u_N002413"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "trigger",
          "trigger_mode": "event",
          "trigger_element_id": "e001",
          "process_element_id": "e002",
          "condition": null,
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002411"
          ],
          "source_quote": "The fourth pillar is an independent audit function that tests whether internal AML policies are adequate and effective."
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "process_element_id": "e002",
          "auxiliary_element_id": "e003",
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002412"
          ],
          "source_quote": "Independent audit functions must have sufficient knowledge and experience to understand and analyze the AML program."
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e004",
          "qualifier": "aimed_to",
          "relation_type": null,
          "evidence_unit_ids": [
            "v7u_N002413"
          ],
          "source_quote": "The purpose of independent testing is to confirm whether the program is operating as expected, with effective internal controls."
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
      "reason": "该候选包含了持续交易监控及其识别报告可疑交易的目的，构成程序性流程。"
    },
    {
      "candidate_id": "s1c_gap_ch33_s05_pillar1",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "原文仅描述政策和控制系统应满足的静态要求（如与风险一致、书面记录、明确职责、包含上报程序），未包含业务处理动作或判断，不构成程序性流程。"
    },
    {
      "candidate_id": "s1c_gap_ch33_s05_pillar2",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "该候选要求指定合规官并规定其资格与职责，构成指定人员并赋予监督职能的流程。"
    },
    {
      "candidate_id": "s1c_gap_ch33_s05_pillar3",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "该候选要求提供定期持续培训，并规定了培训内容，构成培训提供及内容要求的流程。"
    },
    {
      "candidate_id": "s1c_gap_ch33_s05_pillar4",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005"
      ],
      "reason": "该候选要求实施独立审计测试，并规定审计人员的资质和审计目的，构成审计执行的流程。"
    },
    {
      "candidate_id": "s1c_gap_ch33_s05_pillar5_customer_id",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选要求识别和验证客户身份，构成身份确认的执行流程。"
    }
  ],
  "skip_reason": null
}
```
