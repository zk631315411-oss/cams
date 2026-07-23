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

section_id: `CH35-S02`

section_title: `Second LOD's AFC role and its interaction with the front office > Second LOD's interaction with other functions`

section_text_with_unit_anchors:

```text
[v7u_N002584|2584] The second line of defense AFC team interacts with various risk management and non-risk management functions to ensure effective risk oversight and regulatory compliance. These interactions maintain the organization's integrity and align functions with risk management strategies. Key functions include:
ZH: 第二道防线金融犯罪防控团队与多个风险管理及非风险管理职能互动，以确保有效的风险监督和合规。

[v7u_N002585|2585] Legal: Assists with interpreting regulations, handling compliance issues, and managing potential legal liabilities, such as reporting requirements and client offboarding in suspected money laundering cases.
ZH: 法律部门协助解释法规、处理合规问题及管理潜在法律责任，如可疑洗钱案件中的报告要求和客户退出。

[v7u_N002586|2586] Training and human resources (HR): Develops and implements materials on staff compliance, AML regulations, and internal policies to embed a culture of compliance, especially in the front office.
ZH: 培训与人力资源部门制定并实施员工合规、反洗钱法规及内部政策的材料，以嵌入合规文化。

[v7u_N002587|2587] In larger organizations, the learning and development team within HR might be responsible for training employees on compliance and risk management policies.
ZH: 在大型组织中，人力资源部门内的学习与发展团队可能负责员工合规与风险管理政策培训。

[v7u_N002588|2588] They ensure staff understand their roles in mitigating risks, including those related to AML/CFT.
ZH: 确保员工理解其在缓解风险（包括反洗钱/反恐怖融资相关风险）中的角色。

[v7u_N002589|2589] HR ensures employees are trained in compliance and risk management policies, and understand their roles in mitigating risks, including those related to AML/CFT.
ZH: 人力资源确保员工接受合规与风险管理政策培训，并理解其在缓解风险（包括反洗钱/反恐怖融资相关风险）中的角色。

[v7u_N002590|2590] HR may address employee accountability and disciplinary measures after a compliance breach.
ZH: 人力资源部门可在合规违规后处理员工问责和纪律措施。

[v7u_N002591|2591] Vendor management: Conduct due diligence and risk assessments, ensuring third-party vendors comply with AFC policies and do not pose additional risks.
ZH: 供应商管理部门对第三方供应商进行尽职调查和风险评估，确保其遵守金融犯罪防控政策且不带来额外风险。

[v7u_N002592|2592] Data integrity and privacy: The privacy team may help the second-line AFC team in drafting data protection impact assessments and advise on personal data handling and retention periods during suspicious activity investigations.
ZH: 隐私团队可协助第二道防线金融犯罪防控团队起草数据保护影响评估，并就可疑活动调查中的个人数据处理和保留期限提供建议。

[v7u_N002593|2593] For new procedures involving personal data for AML/CFT checks, the AFC team may need legal endorsement to navigate compliance.
ZH: 涉及个人数据的反洗钱/反恐怖融资新程序可能需要法律认可以确保合规。

[v7u_N002594|2594] If an organization processes customer identification data for AML/CFT compliance while also following the EU’s General Data Protection Regulation (GDPR), it must balance both requirements.
ZH: 组织在处理客户身份数据以符合反洗钱/反恐怖融资要求的同时，还需遵守欧盟《通用数据保护条例》，必须平衡两者。

[v7u_N002595|2595] The organization should work closely with its legal team to ensure lawful processing, data minimization, and proper handling of customer consent during CDD.
ZH: 组织应与法律团队密切合作，确保客户尽职调查过程中的合法处理、数据最小化及客户同意管理。

[v7u_N002596|2596] General compliance: Aligns broader compliance activities with financial crime risk assessments and mitigations, ensuring consistency in risk thresholds, compliance requirements, and monitoring efforts.
ZH: 一般合规职能将更广泛的合规活动与金融犯罪风险评估和缓解措施对齐，确保风险阈值、合规要求和监控工作的一致性。

[v7u_N002597|2597] Credit risk: Assesses credit requests and gathers data about a client's creditworthiness. Offboarding clients might require considering loan recovery.
ZH: 信用风险部门评估信贷请求并收集客户信用状况数据，客户退出时可能需要考虑贷款回收。

[v7u_N002598|2598] Reputational risks: Evaluates a client’s reputational concerns and the potential impacts to mitigate risks. If reputational risk does not directly involve AFC, decisions may be jointly made with, or escalated to, the second-line risk teams to determine the best course of action.
ZH: 声誉风险部门评估客户声誉问题及潜在影响以缓解风险；若不直接涉及金融犯罪防控，决策可能由第二道防线风险团队共同做出或上报。

[v7u_N002599|2599] Operational risk: Evaluates risks that organizations might encounter in dayto-day operations. Some organizations also manage fraud risk assessments as part of their operational risk management.
ZH: 操作风险部门评估组织在日常运营中可能遇到的风险，部分组织还将欺诈风险评估纳入操作风险管理。
```

allowed_unit_ids:

```json
[
  "v7u_N002584",
  "v7u_N002585",
  "v7u_N002586",
  "v7u_N002587",
  "v7u_N002588",
  "v7u_N002589",
  "v7u_N002590",
  "v7u_N002591",
  "v7u_N002592",
  "v7u_N002593",
  "v7u_N002594",
  "v7u_N002595",
  "v7u_N002596",
  "v7u_N002597",
  "v7u_N002598",
  "v7u_N002599"
]
```

## S2 Process IR

```json
{
  "section_id": "CH35-S02",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "在可疑洗钱案件中，法律部门如何协助处理报告和客户退出？",
      "title": "法律部门在可疑洗钱案件中协助报告和退出",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "可疑洗钱案件",
          "evidence_unit_ids": [
            "v7u_N002585"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "法律部门协助处理报告要求和客户退出",
          "evidence_unit_ids": [
            "v7u_N002585"
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
          "relation_type": "result_handoffs_stage",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002585"
          ],
          "source_quote": "Legal: Assists with interpreting regulations, handling compliance issues, and managing potential legal liabilities, such as reporting requirements and client offboarding in suspected money laundering cases."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "合规违规后，人力资源部门如何处理员工问责和纪律？",
      "title": "人力资源部门在合规违规后处理员工问责和纪律措施",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "合规违规后",
          "evidence_unit_ids": [
            "v7u_N002590"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "HR may address employee accountability and disciplinary measures",
          "evidence_unit_ids": [
            "v7u_N002590"
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
          "relation_type": "result_handoffs_stage",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002590"
          ],
          "source_quote": "HR may address employee accountability and disciplinary measures after a compliance breach."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "涉及个人数据的新AML/CFT程序是否需要法律认可？",
      "title": "AFC团队在涉及个人数据的新程序中可能需要法律认可",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "涉及个人数据的新AML/CFT检查程序",
          "evidence_unit_ids": [
            "v7u_N002593"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "AFC团队可能需要法律认可以符合合规",
          "evidence_unit_ids": [
            "v7u_N002593"
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
          "relation_type": "result_handoffs_stage",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002593"
          ],
          "source_quote": "For new procedures involving personal data for AML/CFT checks, the AFC team may need legal endorsement to navigate compliance."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_004"
      ],
      "focal_question": "当GDPR与AML/CFT要求冲突时，组织必须如何平衡？",
      "title": "组织在处理客户身份数据时须平衡GDPR与AML/CFT要求",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "组织处理客户身份数据以符合AML/CFT要求并同时遵守GDPR",
          "evidence_unit_ids": [
            "v7u_N002594"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "必须平衡两者要求",
          "evidence_unit_ids": [
            "v7u_N002594"
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
          "condition": "If the organization processes customer identification data for AML/CFT compliance while also following the EU's GDPR",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002594"
          ],
          "source_quote": "If an organization processes customer identification data for AML/CFT compliance while also following the EU’s General Data Protection Regulation (GDPR), it must balance both requirements."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_005"
      ],
      "focal_question": "当声誉风险不直接涉及AFC时，决策如何确定？",
      "title": "声誉风险不涉及AFC时由第二道防线风险团队决策或上报",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "声誉风险不直接涉及AFC",
          "evidence_unit_ids": [
            "v7u_N002598"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "decision",
          "label": "决策可能由第二道防线风险团队共同做出或上报",
          "evidence_unit_ids": [
            "v7u_N002598"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "确定最佳行动方案",
          "evidence_unit_ids": [
            "v7u_N002598"
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
          "condition": "If reputational risk does not directly involve AFC",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002598"
          ],
          "source_quote": "If reputational risk does not directly involve AFC, decisions may be jointly made with, or escalated to, the second-line risk teams to determine the best course of action."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": "result_handoffs_stage",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002598"
          ],
          "source_quote": "to determine the best course of action."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_006",
      "source_candidate_ids": [
        "s1c_gap_ch35_s02_vendor_dd"
      ],
      "focal_question": "供应商管理如何进行尽职调查和风险评估以确保供应商合规？",
      "title": "供应商管理对第三方供应商进行尽职调查和风险评估以确保合规",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "供应商管理进行尽职调查和风险评估",
          "evidence_unit_ids": [
            "v7u_N002591"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "确保第三方供应商遵守AFC政策且不带来额外风险",
          "evidence_unit_ids": [
            "v7u_N002591"
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
          "relation_type": "result_handoffs_stage",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002591"
          ],
          "source_quote": "Vendor management: Conduct due diligence and risk assessments, ensuring third-party vendors comply with AFC policies and do not pose additional risks."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_007",
      "source_candidate_ids": [
        "s1c_gap_ch35_s02_privacy_team_assist"
      ],
      "focal_question": "在可疑活动调查中，隐私团队如何协助AFC团队？",
      "title": "隐私团队在可疑活动调查中协助AFC团队起草评估和提供建议",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "可疑活动调查期间",
          "evidence_unit_ids": [
            "v7u_N002592"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "隐私团队可能协助起草数据保护影响评估并就个人数据处理和保留期限提供建议",
          "evidence_unit_ids": [
            "v7u_N002592"
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
          "relation_type": "result_handoffs_stage",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002592"
          ],
          "source_quote": "The privacy team may help the second-line AFC team in drafting data protection impact assessments and advise on personal data handling and retention periods during suspicious activity investigations."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_008",
      "source_candidate_ids": [
        "s1c_gap_ch35_s02_legal_coop_cdd"
      ],
      "focal_question": "在CDD过程中，组织应如何与法律团队合作？",
      "title": "组织在CDD中应与法律团队密切合作确保数据合法处理",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "客户尽职调查（CDD）期间",
          "evidence_unit_ids": [
            "v7u_N002595"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "组织应与法律团队密切合作",
          "evidence_unit_ids": [
            "v7u_N002595"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "确保合法处理、数据最小化及客户同意管理",
          "evidence_unit_ids": [
            "v7u_N002595"
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
          "relation_type": "result_handoffs_stage",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002595"
          ],
          "source_quote": "The organization should work closely with its legal team to ensure lawful processing, data minimization, and proper handling of customer consent during CDD."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": "result_handoffs_stage",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002595"
          ],
          "source_quote": "to ensure lawful processing, data minimization, and proper handling of customer consent"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_009",
      "source_candidate_ids": [
        "s1c_gap_ch35_s02_loan_recovery"
      ],
      "focal_question": "退出客户时，是否需要考虑贷款回收？",
      "title": "退出客户时可能需要考虑贷款回收",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "退出客户",
          "evidence_unit_ids": [
            "v7u_N002597"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "可能需要考虑贷款回收",
          "evidence_unit_ids": [
            "v7u_N002597"
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
          "relation_type": "result_handoffs_stage",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002597"
          ],
          "source_quote": "Offboarding clients might require considering loan recovery."
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
      "reason": "该候选描述了在可疑洗钱案件中法律部门协助处理报告和客户退出的触发与行动，构成独立的程序性流程。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选描述了合规违规后人力资源部门处理员工问责和纪律措施的触发与行动，构成独立的程序性流程。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "该候选描述了涉及个人数据的新程序可能触发AFC团队寻求法律认可的判断性流程。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "该候选描述了在同时处理GDPR与AML/CFT要求时组织必须平衡两者的强制性判断流程。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005"
      ],
      "reason": "该候选描述了在声誉风险不直接涉及AFC时决策由第二道防线风险团队共同做出或上报的触发、决策与结果流程。"
    },
    {
      "candidate_id": "s1c_gap_ch35_s02_vendor_dd",
      "disposition": "mapped",
      "episode_ids": [
        "ep_006"
      ],
      "reason": "该候选描述了供应商管理进行尽职调查和风险评估以确保第三方合规的动作与结果，构成独立的程序性流程。"
    },
    {
      "candidate_id": "s1c_gap_ch35_s02_privacy_team_assist",
      "disposition": "mapped",
      "episode_ids": [
        "ep_007"
      ],
      "reason": "该候选描述了在可疑活动调查期间隐私团队协助AFC团队起草评估和提供建议的触发与协助动作，构成独立的流程。"
    },
    {
      "candidate_id": "s1c_gap_ch35_s02_legal_coop_cdd",
      "disposition": "mapped",
      "episode_ids": [
        "ep_008"
      ],
      "reason": "该候选描述了在CDD期间组织应与法律团队密切合作以确保数据合法处理的触发、动作与预期结果，构成独立的程序性流程。"
    },
    {
      "candidate_id": "s1c_gap_ch35_s02_loan_recovery",
      "disposition": "mapped",
      "episode_ids": [
        "ep_009"
      ],
      "reason": "该候选描述了退出客户时可能需要考虑贷款回收的触发与考量动作，构成独立的判断性流程。"
    }
  ],
  "skip_reason": null
}
```
