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

section_id: `CH32-S04`

section_title: `Cooperation involving the private sector > Private sector collaboration`

section_text_with_unit_anchors:

```text
[v7u_N002329|2329] Money launderers and terrorists actively seek to avoid detection by spreading their activities across multiple financial institutions to avoid triggering an alert in any one institution.
ZH: 洗钱者和恐怖分子通过跨机构分散活动来规避检测

[v7u_N002330|2330] For this reason, it is important that private sector entities collaborate with each other to spot patterns that are only evident when looking across institutions.
ZH: 私营部门实体应合作发现跨机构的模式

[v7u_N002331|2331] Organizations can collaborate via established industry bodies like trade associations, or through bespoke AML entities.
ZH: 组织可通过行业协会或专门的反洗钱实体进行合作

[v7u_N002332|2332] Some groups collaborate to produce guidance.
ZH: 一些合作团体旨在制定指导文件

[v7u_N002333|2333] For example, the Wolfsberg Group develops frameworks and guidance for financial crime risk management. Another example is the Joint Money Laundering Steering Group, an umbrella body through which the UK financial sector produces government-approved guidance.
ZH: 沃尔夫斯堡集团和联合洗钱指导小组是合作制定指南的实例

[v7u_N002334|2334] Other groups collaborate to share industry best practices, such as best practices for suspicious activity reporting. Many of these groups include representatives from public sector bodies or collaborate closely with them. Such groups might also share typologies and information on risks.
ZH: 私营部门合作团体分享最佳实践、类型学和风险信息，并吸纳公共部门代表

[v7u_N002335|2335] Information sharing is an important form of private-to-private sector collaboration.
ZH: 信息共享是私营部门间合作的重要形式

[v7u_N002336|2336] Some jurisdictions have introduced legislation that enables this type of sharing.
ZH: 一些司法管辖区已立法允许此类信息共享

[v7u_N002337|2337] In these jurisdictions, organizations may share data on customers, activity, and transactions.
ZH: 在这些司法管辖区，组织可共享客户、活动和交易数据

[v7u_N002338|2338] This can be highly impactful, resulting in better quality SARs and preventing customers who have been exited by one organization for AML/CFT concerns from opening an account at another.
ZH: 信息共享可提高可疑交易报告质量，防止被退出的客户在其他机构重新开户

[v7u_N002339|2339] Organizations may also come together to develop or share capabilities, such as KYC utilities. These joint platforms allow organizations to pool their resources and expertise and improve the accuracy of their KYC procedures.
ZH: 组织可联合开发了解你的客户公用平台，共享资源并提高了解你的客户准确性

[v7u_N002340|2340] Compliance officers can and should engage in informal collaboration.
ZH: 合规官可以且应当进行非正式合作

[v7u_N002341|2341] Sharing perspectives and experiences with peer organizations can help benchmark controls against those of comparable organizations and identify and adopt best practices.
ZH: 与同业分享观点和经验有助于对标控制措施并采纳最佳实践

[v7u_N002342|2342] Any such discussion should be compliant with local data privacy laws and with the organization’s own requirements regarding the protection of confidential or commercially sensitive information.
ZH: 讨论须遵守当地数据隐私法和机构对保密信息的保护要求
```

allowed_unit_ids:

```json
[
  "v7u_N002329",
  "v7u_N002330",
  "v7u_N002331",
  "v7u_N002332",
  "v7u_N002333",
  "v7u_N002334",
  "v7u_N002335",
  "v7u_N002336",
  "v7u_N002337",
  "v7u_N002338",
  "v7u_N002339",
  "v7u_N002340",
  "v7u_N002341",
  "v7u_N002342"
]
```

## S2 Process IR

```json
{
  "section_id": "CH32-S04",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "如何通过私营部门合作发现跨机构模式以应对洗钱威胁？",
      "title": "私营部门实体合作以发现跨机构模式",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "洗钱者和恐怖分子通过跨机构分散活动来规避检测",
          "evidence_unit_ids": [
            "v7u_N002329"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "私营部门实体相互合作",
          "evidence_unit_ids": [
            "v7u_N002330"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "input",
          "label": "可通过行业协会或专门反洗钱实体进行合作",
          "evidence_unit_ids": [
            "v7u_N002331"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "发现跨机构模式",
          "evidence_unit_ids": [
            "v7u_N002330"
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
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002329",
            "v7u_N002330"
          ],
          "source_quote": "Money launderers and terrorists actively seek to avoid detection by spreading their activities across multiple financial institutions... For this reason, it is important that private sector entities collaborate with each other to spot patterns that are only evident when looking across institutions."
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "trigger_mode": null,
          "process_element_id": "e002",
          "auxiliary_element_id": "e003",
          "condition": null,
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002330",
            "v7u_N002331"
          ],
          "source_quote": "collaborate via established industry bodies like trade associations, or through bespoke AML entities."
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "trigger_mode": null,
          "process_element_id": "e002",
          "outcome_element_id": "e004",
          "condition": null,
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002330"
          ],
          "source_quote": "collaborate with each other to spot patterns that are only evident when looking across institutions."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "在立法允许的信息共享下，组织如何通过共享数据提高SAR质量并防止客户重新开户？",
      "title": "基于立法允许的信息共享以提升SAR质量并防止客户重新开户",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "一些司法管辖区引入了允许信息共享的立法",
          "evidence_unit_ids": [
            "v7u_N002336"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "组织共享客户、活动和交易数据",
          "evidence_unit_ids": [
            "v7u_N002337"
          ],
          "modality": "permitted"
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "更好的可疑交易报告质量",
          "evidence_unit_ids": [
            "v7u_N002338"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "防止因反洗钱/反恐融资问题被退出的客户在其他机构开设账户",
          "evidence_unit_ids": [
            "v7u_N002338"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e001",
          "process_element_id": "e002",
          "condition": "司法管辖区已引入立法允许信息共享",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002336",
            "v7u_N002337"
          ],
          "source_quote": "Some jurisdictions have introduced legislation that enables this type of sharing. In these jurisdictions, organizations may share data on customers, activity, and transactions."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "trigger_mode": null,
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "condition": null,
          "relation_type": null,
          "qualifier": "may_lead_to",
          "evidence_unit_ids": [
            "v7u_N002337",
            "v7u_N002338"
          ],
          "source_quote": "This can be highly impactful, resulting in better quality SARs"
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "trigger_mode": null,
          "process_element_id": "e002",
          "outcome_element_id": "e004",
          "condition": null,
          "relation_type": null,
          "qualifier": "may_lead_to",
          "evidence_unit_ids": [
            "v7u_N002337",
            "v7u_N002338"
          ],
          "source_quote": "preventing customers who have been exited by one organization for AML/CFT concerns from opening an account at another."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_004"
      ],
      "focal_question": "组织如何通过联合开发KYC公用设施提高KYC程序准确性？",
      "title": "联合开发KYC公用设施以集中资源并提高KYC准确性",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "组织联合开发或共享KYC能力",
          "evidence_unit_ids": [
            "v7u_N002339"
          ],
          "modality": "permitted"
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "集中资源与专业知识",
          "evidence_unit_ids": [
            "v7u_N002339"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "提高KYC程序准确性",
          "evidence_unit_ids": [
            "v7u_N002339"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "produce",
          "trigger_mode": null,
          "process_element_id": "e001",
          "outcome_element_id": "e002",
          "condition": null,
          "relation_type": null,
          "qualifier": "helps_achieve",
          "evidence_unit_ids": [
            "v7u_N002339"
          ],
          "source_quote": "These joint platforms allow organizations to pool their resources and expertise"
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "trigger_mode": null,
          "process_element_id": "e001",
          "outcome_element_id": "e003",
          "condition": null,
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002339"
          ],
          "source_quote": "improve the accuracy of their KYC procedures."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_005"
      ],
      "focal_question": "合规官如何进行非正式合作以对标控制并采纳最佳实践？",
      "title": "合规官的非正式合作：对标控制与采纳最佳实践",
      "card_nature": "control",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "合规官可以且应当进行非正式合作，分享观点和经验",
          "evidence_unit_ids": [
            "v7u_N002340",
            "v7u_N002341"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "standard",
          "label": "讨论必须遵守当地数据隐私法和机构对保密信息的保护要求",
          "evidence_unit_ids": [
            "v7u_N002342"
          ],
          "modality": "required"
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "对标控制措施",
          "evidence_unit_ids": [
            "v7u_N002341"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "识别和采纳最佳实践",
          "evidence_unit_ids": [
            "v7u_N002341"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "reference",
          "trigger_mode": null,
          "process_element_id": "e001",
          "auxiliary_element_id": "e002",
          "condition": null,
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002340",
            "v7u_N002342"
          ],
          "source_quote": "Any such discussion should be compliant with local data privacy laws and with the organization’s own requirements regarding the protection of confidential or commercially sensitive information."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "trigger_mode": null,
          "process_element_id": "e001",
          "outcome_element_id": "e003",
          "condition": null,
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002341"
          ],
          "source_quote": "Sharing perspectives and experiences with peer organizations can help benchmark controls against those of comparable organizations"
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "trigger_mode": null,
          "process_element_id": "e001",
          "outcome_element_id": "e004",
          "condition": null,
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002341"
          ],
          "source_quote": "identify and adopt best practices."
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
      "reason": "候选描述了跨机构威胁触发私营实体合作的流程，构成程序性 episode。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "候选仅为静态事实陈述，描述一些团体合作制定指导或分享实践，未包含触发、条件或决策等程序性迁移。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "候选包含立法允许触发信息共享、共享数据动作及产生更好SAR和防止客户重新开户的结果，形成清晰的判断性流程。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "候选描述组织联合开发能力并因此提高KYC准确性的目的导向流程，构成 episode。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "候选包含合规官非正式合作、受标准约束并通过分享达成对标和采纳最佳实践，为完整的流程。"
    }
  ],
  "skip_reason": null
}
```
