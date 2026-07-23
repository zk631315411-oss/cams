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

section_id: `CH38-S01`

section_title: `The importance of continuous risk assessment > Continuously assessing financial crime risk`

section_text_with_unit_anchors:

```text
[v7u_N002823|2823] Financial crime risks are dynamic and constantly evolving.
ZH: 金融犯罪风险是动态且不断演变的

[v7u_N002824|2824] Criminals will always attempt to move illicit funds through the financial sector undetected. They will use new technologies and trends, regardless of the controls that organizations establish. Criminals continuously search for loopholes to exploit and test the resilience of AFC frameworks.
ZH: 犯罪分子持续利用新技术寻找漏洞以不被察觉地转移非法资金

[v7u_N002825|2825] Organizations must reevaluate risks whenever there is a material change to their business. This could include higher-risk product offerings, entering a new market, or changes in jurisdictions where the organization operates.
ZH: 组织在业务发生重大变化时必须重新评估风险

[v7u_N002826|2826] Continuously assessing financial crime risk helps organizations adapt to evolving ML/TF techniques and threats, monitor transactions to detect patterns and significant changes, respond to emerging geographical risks, and meet regulations and international standards.
ZH: 持续评估金融犯罪风险有助于组织适应不断变化的洗钱/恐怖融资手法和威胁

[v7u_N002827|2827] FATF and regulatory bodies promote a proactive approach to risk management and reassessing risks as required. This approach, and regular risk assessments, enable organizations to divert their resources to high-risk areas to mitigate them effectively.
ZH: FATF和监管机构提倡主动风险管理，将资源转向高风险领域以有效缓解风险

[v7u_N002828|2828] In addition to conducting overarching enterprise-wide risk assessments regularly, organizations manage risk continually through CRAs.
ZH: 组织通过客户风险评估（CRA）持续管理风险

[v7u_N002829|2829] Organizations should conduct a CRA for every customer they onboard before establishing a business relationship with that customer. They should also review the CRA regularly and whenever there are changes in a customer’s behavior and risk profile. These changes might include:
ZH: 组织应在建立业务关系前对每位客户进行CRA，并定期或在客户行为变化时审查

[v7u_N002830|2830] Transaction pattern deviations.
ZH: 交易模式偏离是触发CRA审查的变化之一

[v7u_N002831|2831] Requests for new products or services.
ZH: 客户请求新产品或服务是触发CRA审查的变化之一

[v7u_N002832|2832] Reluctance to provide information or documentation.
ZH: 客户不愿提供信息或文件是触发CRA审查的变化之一

[v7u_N002833|2833] Increased exposure to high-risk jurisdictions.
ZH: 客户对高风险司法管辖区的敞口增加是触发CRA审查的变化之一

[v7u_N002834|2834] Changes in the customer’s sector.
ZH: 客户所在行业发生变化是触发CRA审查的变化之一

[v7u_N002835|2835] Changes in how the organization operates, such as changing product lines or shifting to online business operations.
ZH: 组织运营方式变化（如产品线变更或转向线上业务）是触发CRA审查的变化之一

[v7u_N002836|2836] CRAs enable organizations to detect changes in customer behavior and reassess risks.
ZH: CRA使组织能够检测客户行为变化并重新评估风险

[v7u_N002837|2837] For example, if an organization detects that a customer plans to extend its sales to high-risk jurisdictions, it might need to introduce enhanced measures such as increased third-party screening, request additional documentation, or increase transaction scrutiny.
ZH: 例如：客户扩展销售至高风险司法管辖区时，需采取增强措施如加强第三方筛查、要求额外文件或增加交易审查

[v7u_N002838|2838] Product and channel risk assessments enable organizations to detect deviations from the intended use of their products, helping to identify new threats or risks.
ZH: 产品和渠道风险评估有助于检测产品预期用途的偏离，识别新威胁或风险

[v7u_N002839|2839] Some risks might not be clear at product launch, but might be identified through ongoing monitoring.
ZH: 某些风险在产品推出时可能不明显，但可通过持续监控识别

[v7u_N002840|2840] For example, during COVID-19, organizations shifted to digital channels. This required aligning existing faceto-face channel controls to address emerging fraud risks, such as digital identity fraud, cross-border wire transfers, and new ways of verifying the authenticity of documentation.
ZH: 例如：疫情期间组织转向数字渠道，需调整现有面对面渠道控制以应对数字身份欺诈等新兴欺诈风险

[v7u_N002841|2841] These risk assessments help organizations continuously assess financial crime risks and enable them to take a holistic, proactive approach to manage and reassess risks as needed.
ZH: 风险持续评估帮助组织主动管理金融犯罪风险
```

allowed_unit_ids:

```json
[
  "v7u_N002823",
  "v7u_N002824",
  "v7u_N002825",
  "v7u_N002826",
  "v7u_N002827",
  "v7u_N002828",
  "v7u_N002829",
  "v7u_N002830",
  "v7u_N002831",
  "v7u_N002832",
  "v7u_N002833",
  "v7u_N002834",
  "v7u_N002835",
  "v7u_N002836",
  "v7u_N002837",
  "v7u_N002838",
  "v7u_N002839",
  "v7u_N002840",
  "v7u_N002841"
]
```

## S2 Process IR

```json
{
  "section_id": "CH38-S01",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "何时必须重新评估风险？",
      "title": "业务重大变化触发风险重新评估",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "业务发生重大变化（如高风险产品、新市场、司法管辖区变化）",
          "evidence_unit_ids": [
            "v7u_N002825"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "重新评估风险",
          "evidence_unit_ids": [
            "v7u_N002825"
          ],
          "modality": "required"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e001",
          "process_element_id": "e002",
          "condition": "业务发生重大变化时",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002825"
          ],
          "source_quote": "Organizations must reevaluate risks whenever there is a material change to their business."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "何时应对客户进行初步客户风险评估？",
      "title": "建立业务关系前进行客户风险评估",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "建立业务关系前",
          "evidence_unit_ids": [
            "v7u_N002829"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "对每位新客户进行客户风险评估（CRA）",
          "evidence_unit_ids": [
            "v7u_N002829"
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
          "condition": "在建立业务关系前",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002829"
          ],
          "source_quote": "Organizations should conduct a CRA for every customer they onboard before establishing a business relationship with that customer."
        }
      ],
      "split_reason": "原候选包含两个独立中心：建立关系前进行CRA和之后定期/变化时审查CRA，CRA文档作为可复用的中间产物，应拆分为不同episode。"
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "何时应审查客户的客户风险评估？",
      "title": "定期或发生特定变化时审查客户风险评估",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "定期 或 客户行为/风险状况发生变化（交易模式偏离、请求新产品/服务、不愿提供信息/文件、高风险司法管辖区暴露增加、客户行业变化、组织运营方式变化）",
          "evidence_unit_ids": [
            "v7u_N002829",
            "v7u_N002830",
            "v7u_N002831",
            "v7u_N002832",
            "v7u_N002833",
            "v7u_N002834",
            "v7u_N002835"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "审查客户风险评估（CRA）",
          "evidence_unit_ids": [
            "v7u_N002829"
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
          "condition": "定期或发生特定变化时",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002829"
          ],
          "source_quote": "They should also review the CRA regularly and whenever there are changes in a customer’s behavior and risk profile."
        }
      ],
      "split_reason": "同ep_002，需与初步CRA执行拆分。"
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "发现客户计划拓展至高风险区域时应采取什么措施？",
      "title": "检测到客户高危计划后采取增强措施",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "检测到客户计划扩展销售至高风险司法管辖区",
          "evidence_unit_ids": [
            "v7u_N002837"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "采取增强措施（如加强第三方筛查、要求额外文件、增加交易审查）",
          "evidence_unit_ids": [
            "v7u_N002837"
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
          "condition": "检测到客户计划扩展销售至高风险司法管辖区",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002837"
          ],
          "source_quote": "if an organization detects that a customer plans to extend its sales to high-risk jurisdictions, it might need to introduce enhanced measures such as increased third-party screening, request additional documentation, or increase transaction scrutiny."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_gap_ch38_s01_digital_channel_controls"
      ],
      "focal_question": "组织转向数字渠道时应如何应对新兴欺诈风险？",
      "title": "转向数字渠道时调整控制以应对欺诈风险",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "组织转向数字渠道（如疫情期间）",
          "evidence_unit_ids": [
            "v7u_N002840"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "调整现有面对面渠道控制",
          "evidence_unit_ids": [
            "v7u_N002840"
          ],
          "modality": "required"
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "应对新兴欺诈风险（如数字身份欺诈、跨境电汇、新的文件真伪验证方式）",
          "evidence_unit_ids": [
            "v7u_N002840"
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
            "v7u_N002840"
          ],
          "source_quote": "organizations shifted to digital channels. This required aligning existing faceto-face channel controls"
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002840"
          ],
          "source_quote": "to address emerging fraud risks, such as digital identity fraud, cross-border wire transfers, and new ways of verifying the authenticity of documentation."
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
      "reason": "候选明确表达了业务重大变化触发风险重新评估的程序性关系。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002",
        "ep_003"
      ],
      "reason": "候选包含两个独立中心：建立关系前进行CRA和定期/变化时审查CRA，拆分后分别映射为两个episode。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "候选表述了检测到特定计划后采取增强措施的条件性程序。"
    },
    {
      "candidate_id": "s1c_gap_ch38_s01_active_approach",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "原文描述主动风险管理方法的好处，无具体的业务判断或流程步骤，属于知识性陈述。"
    },
    {
      "candidate_id": "s1c_gap_ch38_s01_product_channel_assessment",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "原文描述产品和渠道风险评估的能力，无具体触发条件或业务判断，属于知识性陈述。"
    },
    {
      "candidate_id": "s1c_gap_ch38_s01_digital_channel_controls",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005"
      ],
      "reason": "候选给出了转向数字渠道时需调整控制以应对风险的明确程序步骤。"
    }
  ],
  "skip_reason": null
}
```
