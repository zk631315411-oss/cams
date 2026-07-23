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

section_id: `CH39-S01`

section_title: `Customer risk assessment versus enterprise-wide risk assessment`

section_text_with_unit_anchors:

```text
[v7u_N002842|2842] The CRA evaluates potential ML/TF risks associated with individual customers and business relationships. In contrast, the EWRA analyzes ML/TF risks that the organization as a whole faces.
ZH: 客户风险评估（CRA）与全机构风险评估（EWRA）的范围区别

[v7u_N002843|2843] According to FinCEN’s Assessing Customer Relationships and Conducting Customer Due Diligence, customer relationships present varying levels of financial crime risks.
ZH: FinCEN指出客户关系存在不同程度的金融犯罪风险

[v7u_N002844|2844] Organizations conduct CRAs to identify risk factors, assign risk ratings to customers, create risk profiles, and decide which level of CDD to apply.
ZH: 客户风险评估（CRA）用于识别风险因素、分配评级并决定客户尽职调查等级

[v7u_N002845|2845] The CRA considers information collected through KYC processes, such as documents, customer business activity, and requested products.
ZH: CRA考虑通过了解你的客户流程收集的客户信息

[v7u_N002846|2846] Higher-risk customers might require EDD, while lower-risk customers might qualify for simplified due diligence (SDD) in some jurisdictions.
ZH: 高风险客户需强化尽职调查（EDD），低风险客户可适用简化尽职调查（SDD）

[v7u_N002847|2847] Due diligence requirements vary depending on the jurisdiction.
ZH: 尽职调查要求因司法管辖区而异

[v7u_N002848|2848] The EWRA identifies inherent risks, assesses controls, and determines the residual risk that the organization faces. The process helps organizations design their AML/CFT framework, guides policy and procedure development, allocates resources toward higher-risk areas, and improves decision-making.
ZH: 全机构风险评估（EWRA）识别固有风险、评估控制并确定剩余风险，指导反洗钱/反恐怖融资框架设计

[v7u_N002849|2849] A product risk assessment helps organizations identify and understand the risks and threats associated with their financial products. It assesses how criminals might use these products to launder illicit funds. After identifying and assessing these risks and threats, organizations can implement measures to mitigate them.
ZH: 产品风险评估帮助识别金融产品相关的洗钱风险并制定缓释措施

[v7u_N002850|2850] To identify and understand risks, organizations should consider factors, including:
ZH: 组织应考虑多种因素以识别和理解风险

[v7u_N002851|2851] Inherent product characteristics: Features or attributes such as crossborder wire payments, third-party payments, anonymity, remote access, third-party access, unusual complexity and structure, minimal transaction oversight, and cash-intensive nature.
ZH: 固有产品特征包括跨境支付、匿名性、远程访问等风险属性

[v7u_N002852|2852] Transactional patterns of the product: Recurring behaviors and trends such as rapid movements, high volumes, frequent transactions, involvement of high-risk or sanctioned jurisdictions, and use by high-risk customers in high-risk sectors.
ZH: 产品交易模式包括快速流动、高交易量、涉及高风险司法管辖区等风险指标

[v7u_N002853|2853] Each product should receive a risk score based on the AML/CFT risks it presents.
ZH: 每个产品应根据其反洗钱/反恐怖融资风险获得风险评分

[v7u_N002854|2854] A clear, documented definition of each product and its risks helps organizations assess them appropriately.
ZH: 清晰记录每个产品的定义和风险有助于适当评估

[v7u_N002855|2855] Identified risks affect the EWRA and the RAS.
ZH: 已识别的风险影响全机构风险评估（EWRA）和风险偏好声明（RAS）

[v7u_N002856|2856] For example, if many products are deemed high-risk, this raises the overall EWRA risk score, prompting additional controls or measures.
ZH: 若多个产品被认定为高风险，将提高EWRA评分并触发额外控制措施

[v7u_N002857|2857] If a product’s risk assessment score exceeds the RAS, the organization might cease offering it.
ZH: 若产品风险评估得分超过风险偏好，组织可能停止提供该产品

[v7u_N002858|2858] A product risk assessment is also very useful in designing controls such as transaction monitoring to ensure adequate coverage of all products.
ZH: 产品风险评估有助于设计交易监控等控制措施以确保充分覆盖

[v7u_N002859|2859] Although the product risk assessment process might vary, depending on the organization’s size, it typically includes:
ZH: 产品风险评估流程因组织规模而异，通常包括以下步骤

[v7u_N002860|2860] Product development: Designs the product and provides specifications.
ZH: 产品开发部门设计产品并提供规格说明

[v7u_N002861|2861] IT: Provides necessary technological infrastructure.
ZH: IT部门为风险评估提供必要的技术基础设施。

[v7u_N002862|2862] Operations: Provides insights about product usage patterns
ZH: 运营部门提供产品使用模式的洞察。

[v7u_N002863|2863] Compliance: Identifies control measures and ensures compliance.
ZH: 合规部门识别控制措施并确保合规。

[v7u_N002864|2864] Legal: Provides legal assistance on applicable laws.
ZH: 法律部门就适用法律提供法律协助。

[v7u_N002865|2865] Compliance officers play an active role in overseeing the product risk assessment. They identify risks, assess relevant controls, and assign appropriate risk scores.
ZH: 合规官在产品风险评估中发挥积极作用，识别风险、评估控制并分配风险评分。

[v7u_N002866|2866] Because risk assessment is an ongoing process, organizations should review both new and existing products regularly. For new products, the assessment should be conducted before they are offered to customers. Once the product becomes available, it should be reviewed periodically and whenever significant product changes occur.
ZH: 组织应定期审查新产品和现有产品，新产品在推出前应进行评估，之后定期审查并在重大变更时审查。

[v7u_N002867|2867] A clear and well-structured risk assessment helps identify vulnerabilities and exposures.
ZH: 清晰且结构良好的风险评估有助于识别漏洞和风险敞口。

[v7u_N002868|2868] Sometimes, organizations might notice previously unidentified risks for a new or existing product.
ZH: 组织可能注意到新产品或现有产品中先前未识别的风险。

[v7u_N002869|2869] For example, a new prepaid card might show high volumes of rapid transactions from high-risk customers.
ZH: 例如，新的预付卡可能显示来自高风险客户的高频交易。

[v7u_N002870|2870] This might require revisiting the product risk assessment and setting thresholds for the number of transactions, volumes, or restricting the product to certain customer sectors.
ZH: 可能需要重新审视产品风险评估并设定交易数量、金额阈值或限制产品面向特定客户群体。
```

allowed_unit_ids:

```json
[
  "v7u_N002842",
  "v7u_N002843",
  "v7u_N002844",
  "v7u_N002845",
  "v7u_N002846",
  "v7u_N002847",
  "v7u_N002848",
  "v7u_N002849",
  "v7u_N002850",
  "v7u_N002851",
  "v7u_N002852",
  "v7u_N002853",
  "v7u_N002854",
  "v7u_N002855",
  "v7u_N002856",
  "v7u_N002857",
  "v7u_N002858",
  "v7u_N002859",
  "v7u_N002860",
  "v7u_N002861",
  "v7u_N002862",
  "v7u_N002863",
  "v7u_N002864",
  "v7u_N002865",
  "v7u_N002866",
  "v7u_N002867",
  "v7u_N002868",
  "v7u_N002869",
  "v7u_N002870"
]
```

## S2 Process IR

```json
{
  "section_id": "CH39-S01",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "如何通过客户风险评估决定适用的客户尽职调查等级？",
      "title": "依据 KYC 信息进行客户风险评估并决定 CDD 等级",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "input",
          "label": "通过 KYC 流程收集的信息（文件、客户业务活动、申请产品）",
          "evidence_unit_ids": [
            "v7u_N002845"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "进行客户风险评估，识别风险因素并分配风险评级",
          "evidence_unit_ids": [
            "v7u_N002844"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "decision",
          "label": "决定适用的客户尽职调查等级",
          "evidence_unit_ids": [
            "v7u_N002844"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "高风险客户可能需要强化尽职调查（EDD）",
          "evidence_unit_ids": [
            "v7u_N002846"
          ],
          "modality": null
        },
        {
          "element_id": "e005",
          "role": "outcome",
          "label": "低风险客户在一些司法管辖区可能适用简化尽职调查（SDD）",
          "evidence_unit_ids": [
            "v7u_N002846"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "reference",
          "process_element_id": "e002",
          "auxiliary_element_id": "e001",
          "condition": null,
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002845"
          ],
          "source_quote": "The CRA considers information collected through KYC processes, such as documents, customer business activity, and requested products."
        },
        {
          "relation_id": "r002",
          "kind": "sequence",
          "before_element_id": "e002",
          "after_element_id": "e003",
          "condition": null,
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002844"
          ],
          "source_quote": "Organizations conduct CRAs to identify risk factors, assign risk ratings to customers, create risk profiles, and decide which level of CDD to apply."
        },
        {
          "relation_id": "r003",
          "kind": "branch",
          "decision_element_id": "e003",
          "target_element_id": "e004",
          "condition": "客户被评估为高风险",
          "relation_type": "branch_condition_routes_path",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002846"
          ],
          "source_quote": "Higher-risk customers might require EDD, while lower-risk customers might qualify for simplified due diligence (SDD) in some jurisdictions."
        },
        {
          "relation_id": "r004",
          "kind": "branch",
          "decision_element_id": "e003",
          "target_element_id": "e005",
          "condition": "客户被评估为低风险且司法管辖区允许 SDD",
          "relation_type": "branch_condition_routes_path",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002846"
          ],
          "source_quote": "lower-risk customers might qualify for simplified due diligence (SDD) in some jurisdictions."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "全机构风险评估如何识别固有风险、评估控制并确定剩余风险以指导框架设计？",
      "title": "执行全机构风险评估以确定剩余风险并指导 AML/CFT 框架",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "进行全机构风险评估，识别固有风险并评估控制措施",
          "evidence_unit_ids": [
            "v7u_N002848"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "decision",
          "label": "确定组织面临的剩余风险",
          "evidence_unit_ids": [
            "v7u_N002848"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "帮助设计 AML/CFT 框架",
          "evidence_unit_ids": [
            "v7u_N002848"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "指导政策和程序开发",
          "evidence_unit_ids": [
            "v7u_N002848"
          ],
          "modality": null
        },
        {
          "element_id": "e005",
          "role": "outcome",
          "label": "向高风险领域分配资源",
          "evidence_unit_ids": [
            "v7u_N002848"
          ],
          "modality": null
        },
        {
          "element_id": "e006",
          "role": "outcome",
          "label": "改进决策",
          "evidence_unit_ids": [
            "v7u_N002848"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "sequence",
          "before_element_id": "e001",
          "after_element_id": "e002",
          "condition": null,
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002848"
          ],
          "source_quote": "The EWRA identifies inherent risks, assesses controls, and determines the residual risk that the organization faces."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "condition": null,
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002848"
          ],
          "source_quote": "The process helps organizations design their AML/CFT framework"
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e004",
          "condition": null,
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002848"
          ],
          "source_quote": "guides policy and procedure development"
        },
        {
          "relation_id": "r004",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e005",
          "condition": null,
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002848"
          ],
          "source_quote": "allocates resources toward higher-risk areas"
        },
        {
          "relation_id": "r005",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e006",
          "condition": null,
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002848"
          ],
          "source_quote": "improves decision-making"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "如何进行产品风险评估并应用其结果？",
      "title": "执行产品风险评估以分配风险评分并设计控制措施",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "input",
          "label": "每个产品的清晰记录的定义及其风险",
          "evidence_unit_ids": [
            "v7u_N002854"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "合规官监督产品风险评估，识别风险、评估相关控制并分配适当的风险评分",
          "evidence_unit_ids": [
            "v7u_N002865",
            "v7u_N002849",
            "v7u_N002853"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "实施措施以缓释已识别的风险与威胁",
          "evidence_unit_ids": [
            "v7u_N002849"
          ],
          "modality": "permitted"
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "设计交易监控等控制措施以确保充分覆盖所有产品",
          "evidence_unit_ids": [
            "v7u_N002858"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "reference",
          "process_element_id": "e002",
          "auxiliary_element_id": "e001",
          "condition": null,
          "relation_type": "standard_constrains_action",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002854"
          ],
          "source_quote": "A clear, documented definition of each product and its risks helps organizations assess them appropriately."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "condition": null,
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002849"
          ],
          "source_quote": "After identifying and assessing these risks and threats, organizations can implement measures to mitigate them."
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e004",
          "condition": null,
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N002858"
          ],
          "source_quote": "A product risk assessment is also very useful in designing controls such as transaction monitoring to ensure adequate coverage of all products."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_004"
      ],
      "focal_question": "当许多产品被认定为高风险时，如何影响 EWRA 并触发额外控制？",
      "title": "产品高风险聚集提升 EWRA 评分并触发额外控制",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "许多产品被认定为高风险",
          "evidence_unit_ids": [
            "v7u_N002856"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "提高整体 EWRA 风险评分",
          "evidence_unit_ids": [
            "v7u_N002856"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "触发额外控制或措施",
          "evidence_unit_ids": [
            "v7u_N002856"
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
          "condition": "如果许多产品被认定为高风险",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002856"
          ],
          "source_quote": "if many products are deemed high-risk, this raises the overall EWRA risk score, prompting additional controls or measures."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "condition": null,
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002856"
          ],
          "source_quote": "prompting additional controls or measures."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_005"
      ],
      "focal_question": "当产品风险评估得分超过风险偏好声明（RAS）时如何处置？",
      "title": "产品风险超出 RAS 时可能停止提供产品",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "产品风险评估得分超过风险偏好声明（RAS）",
          "evidence_unit_ids": [
            "v7u_N002857"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "组织可能停止提供该产品",
          "evidence_unit_ids": [
            "v7u_N002857"
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
          "condition": "如果产品风险评估得分超过 RAS",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002857"
          ],
          "source_quote": "If a product’s risk assessment score exceeds the RAS, the organization might cease offering it."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_006",
      "source_candidate_ids": [
        "s1c_006"
      ],
      "focal_question": "组织应何时对产品进行风险评估审查？",
      "title": "基于产品生命周期的持续风险评估审查",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "新产品推出前",
          "evidence_unit_ids": [
            "v7u_N002866"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "context",
          "label": "产品推出后需定期审查",
          "evidence_unit_ids": [
            "v7u_N002866"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "context",
          "label": "产品发生重大变更时",
          "evidence_unit_ids": [
            "v7u_N002866"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "action",
          "label": "应进行产品风险评估",
          "evidence_unit_ids": [
            "v7u_N002866"
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
          "process_element_id": "e004",
          "condition": "对于新产品，在向客户提供前",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002866"
          ],
          "source_quote": "For new products, the assessment should be conducted before they are offered to customers."
        },
        {
          "relation_id": "r002",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e002",
          "process_element_id": "e004",
          "condition": "一旦产品可用，应定期审查",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002866"
          ],
          "source_quote": "Once the product becomes available, it should be reviewed periodically"
        },
        {
          "relation_id": "r003",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e003",
          "process_element_id": "e004",
          "condition": "当发生重大产品变更时",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002866"
          ],
          "source_quote": "whenever significant product changes occur."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_007",
      "source_candidate_ids": [
        "s1c_007"
      ],
      "focal_question": "发现先前未识别的产品风险时如何应对？",
      "title": "发现未识别风险后重新审视产品风险评估并调整控制",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "注意到新产品或现有产品先前未识别的风险",
          "evidence_unit_ids": [
            "v7u_N002868",
            "v7u_N002869"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "重新审视产品风险评估，并设定交易数量、金额阈值或限制产品面向特定客户群体",
          "evidence_unit_ids": [
            "v7u_N002870"
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
          "condition": "如果注意到先前未识别的风险",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N002870"
          ],
          "source_quote": "This might require revisiting the product risk assessment and setting thresholds for the number of transactions, volumes, or restricting the product to certain customer sectors."
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
      "reason": "候选明确描述了组织执行 CRA 以识别风险、分配评级并决定 CDD 等级的程序，包含动作、决策和差异化结果，构成完整的判断性迁移流程。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "候选描述了 EWRA 识别风险、评估控制、确定剩余风险并指导框架设计的完整程序，具有明确动作序列和产出，属于流程。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "候选涵盖产品风险评估的输入、执行（合规官识别风险、评估控制、分配评分）以及产出（缓释措施、控制设计），支持独立流程。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "候选提供了明确的条件触发关系：多个产品高风险导致 EWRA 评分提高并触发额外控制，具备程序性迁移。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005"
      ],
      "reason": "候选呈现了‘如果产品风险评分超过 RAS 则可能停止提供’的条件判断与行动，构成独立决策流程。"
    },
    {
      "candidate_id": "s1c_006",
      "disposition": "mapped",
      "episode_ids": [
        "ep_006"
      ],
      "reason": "候选规定了产品风险评估在生命周期不同阶段（推出前、定期、重大变更）的审查义务，具有多个触发条件和评估动作，属于流程。"
    },
    {
      "candidate_id": "s1c_007",
      "disposition": "mapped",
      "episode_ids": [
        "ep_007"
      ],
      "reason": "候选描述了发现未识别风险后触发重新审视评估并调整控制的流程，包含触发事件和具体响应动作，符合流程定义。"
    }
  ],
  "skip_reason": null
}
```
