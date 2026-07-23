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

section_id: `CH19-S07`

section_title: `Financial Action Task Force > Impact of FATF mutual evaluation reports on jurisdictions`

section_text_with_unit_anchors:

```text
[v7u_N001430|1430] After the plenary discussion and final quality review are complete, FATF publishes the mutual evaluation report.
ZH: FATF在全体会议讨论和最终质量审查后发布互评估报告

[v7u_N001431|1431] Jurisdictions that perform poorly on evaluations risk placement on FATF’s grey list or black list.
ZH: 评估表现不佳的司法管辖区可能被列入FATF灰名单或黑名单

[v7u_N001432|1432] A poor evaluation can lead to increased scrutiny from international banks, reputational damage, and economic consequences such as higher transaction costs and reduced foreign investment.
ZH: 评估不佳会导致国际银行审查加强、声誉受损及经济后果

[v7u_N001433|1433] After jurisdictions receive the ratings on Recommendations, they should address the shortcomings FATF identified in the mutual evaluation report.
ZH: 司法管辖区应根据互评估报告中的评级解决FATF指出的缺陷

[v7u_N001434|1434] FATF encourages these jurisdictions to enact new—or amend existing— regulations or laws to strengthen their AML/CFT regime.
ZH: FATF鼓励司法管辖区制定或修订法规以加强反洗钱/反恐怖融资体系

[v7u_N001435|1435] FATF also encourages financial institutions, law enforcement agencies, and regulatory bodies to enhance their compliance frameworks to meet FATF standards.
ZH: FATF鼓励金融机构、执法和监管机构加强合规框架以符合标准

[v7u_N001436|1436] These enhancements lead to greater investment in technology, training, and personnel for detecting and preventing financial crimes.
ZH: 合规增强促使在技术、培训和人员方面加大投资以防范金融犯罪

[v7u_N001437|1437] Additionally, jurisdictions often strengthen national FIUs and cross-border cooperation mechanisms.
ZH: 司法管辖区通常加强国家金融情报机构和跨境合作机制

[v7u_N001438|1438] According to FATF’s website, all jurisdictions are subject to post-assessment monitoring.
ZH: 所有司法管辖区均须接受FATF评估后监测

[v7u_N001439|1439] This monitoring can include regular reports of improvements for jurisdictions that are already largely compliant and actively addressing the remaining few shortcomings.
ZH: 监测包括对基本合规且积极整改的司法管辖区定期提交改进报告

[v7u_N001440|1440] Additionally, FATF can issue public warnings against a jurisdiction that makes insufficient progress to address key deficiencies.
ZH: FATF可对关键缺陷整改不力的司法管辖区发布公开警告

[v7u_N001441|1441] The United Arab Emirates (UAE) offers an example of the strength of the mutual evaluation report process. FATF placed the UAE on the grey list in 2022 and removed it from the list in 2024. The removal was due to the UAE successfully amending its legislation to close loopholes, criminalize money laundering, and improve financial transparency. Specifically, the UAE achieved its removal from the grey list by:
ZH: FATF 互评估报告对司法管辖区的影响示例：阿联酋从灰名单移除

[v7u_N001442|1442] Updating its guidelines for financial institutions and DNFBPs.
ZH: 更新金融机构和 DNFBP 的指引

[v7u_N001443|1443] Engaging in an ongoing legal and regulatory communications campaign, highlighting new and updated requirements.
ZH: 开展持续的法律和监管沟通活动，强调新要求

[v7u_N001444|1444] Increasing the frequency of its assessments.
ZH: 增加评估频率

[v7u_N001445|1445] Increasing the frequency and size of sanctions to penalize AML/CFT failures.
ZH: 增加制裁频率和规模以惩罚 反洗钱/反恐怖融资 失败

[v7u_N001446|1446] Strengthening beneficial ownership regulations.
ZH: 加强受益所有人法规

[v7u_N001447|1447] Creating a dedicated court to hear cases involving financial crime.
ZH: 设立专门法院审理金融犯罪案件

[v7u_N001448|1448] Adopting a new penal code.
ZH: 通过新刑法典

[v7u_N001449|1449] Creating a new platform to streamline the reporting of suspicious activities.
ZH: 创建新平台以简化可疑活动报告

[v7u_N001450|1450] Note that the impacts from a mutual evaluation are not limited to the national level. Changes in laws and regulations would also have an impact on regulated organizations that operate in relevant jurisdictions.
ZH: 互评估的影响不仅限于国家层面，也影响受监管机构

[v7u_N001451|1451] Therefore, regulated organizations should implement control frameworks and resources.
ZH: 受监管机构必须实施控制框架和资源

[v7u_N001452|1452] Recommendation 1 of FATF standards requires jurisdictions to identify, assess, and understand their money laundering and terrorist financing risks and implement measures to ensure effective risk mitigation.
ZH: FATF 建议 1 要求司法管辖区识别、评估并减轻洗钱和恐怖融资风险

[v7u_N001453|1453] To achieve this, FATF promotes a risk-based approach, enabling jurisdictions to enhance efficiency by prioritizing high-risk threats, optimizing resource allocation, improving compliance flexibility, strengthening AML/CFT measures, and adapting to evolving financial crimes.
ZH: FATF 推广风险为本方法以提升效率

[v7u_N001454|1454] There is no universal approach to assessing risks.
ZH: 不存在通用的风险评估方法

[v7u_N001455|1455] FATF states that risk assessments may be undertaken at various levels beyond the national level, and with differing purposes and scope, though the basic obligation of assessing and understanding money laundering and terrorist financing risks rests on the jurisdiction itself.
ZH: FATF 允许在国家层面之外进行风险评估，但基本义务在司法管辖区自身

[v7u_N001456|1456] Therefore, jurisdictions should tailor the national risk assessment process based on their capacity, risk exposure, and context.
ZH: 司法管辖区应根据自身能力、风险敞口和背景定制国家风险评估

[v7u_N001457|1457] To better assist jurisdictions, FATF provides a six-step best-practice framework in which jurisdictions should conduct:
ZH: FATF 提供六步最佳实践框架以协助司法管辖区

[v7u_N001458|1458] 1. An environmental scan to evaluate economic, political, and legal factors.
ZH: 第一步：环境扫描，评估经济、政治和法律因素

[v7u_N001459|1459] 2. An analytical scan to collect and analyze money laundering and terrorist financing data.
ZH: 第二步：分析扫描，收集和分析洗钱和恐怖融资数据

[v7u_N001460|1460] 3. An analysis of threats to identify key money laundering and terrorist financing actors and methods.
ZH: 第三步：威胁分析，识别关键洗钱和恐怖融资行为者及方法

[v7u_N001461|1461] 4. An analysis of vulnerabilities to assess weaknesses in financial systems.
ZH: 分析金融体系漏洞以评估弱点

[v7u_N001462|1462] 5. A risk assessment to assign risk levels and develop mitigation plans.
ZH: 进行风险评估以分配风险等级并制定缓解计划

[v7u_N001463|1463] 6. Horizon scanning to monitor emerging trends and future threats.
ZH: 进行地平线扫描以监测新兴趋势和未来威胁

[v7u_N001464|1464] According to FATF’s 2024 guidance on national risk assessments, sectoral and thematic risk assessments help authorities develop typologies to understand how bad actors could exploit specific sectors for money laundering and terrorist financing.
ZH: 行业和专题风险评估帮助当局制定类型学以了解洗钱和恐怖融资风险

[v7u_N001465|1465] The results of sectoral and thematic risk assessments complement those of the national risk assessment.
ZH: 行业和专题风险评估结果补充国家风险评估

[v7u_N001466|1466] Enterprise-wide risk assessments ensure that organizations systematically identify and assess money laundering and terrorist financing risks across all operations. These assessments strengthen compliance, internal controls, and regulatory alignment while optimizing risk management.
ZH: 全企业风险评估确保组织系统识别和评估洗钱和恐怖融资风险
```

allowed_unit_ids:

```json
[
  "v7u_N001430",
  "v7u_N001431",
  "v7u_N001432",
  "v7u_N001433",
  "v7u_N001434",
  "v7u_N001435",
  "v7u_N001436",
  "v7u_N001437",
  "v7u_N001438",
  "v7u_N001439",
  "v7u_N001440",
  "v7u_N001441",
  "v7u_N001442",
  "v7u_N001443",
  "v7u_N001444",
  "v7u_N001445",
  "v7u_N001446",
  "v7u_N001447",
  "v7u_N001448",
  "v7u_N001449",
  "v7u_N001450",
  "v7u_N001451",
  "v7u_N001452",
  "v7u_N001453",
  "v7u_N001454",
  "v7u_N001455",
  "v7u_N001456",
  "v7u_N001457",
  "v7u_N001458",
  "v7u_N001459",
  "v7u_N001460",
  "v7u_N001461",
  "v7u_N001462",
  "v7u_N001463",
  "v7u_N001464",
  "v7u_N001465",
  "v7u_N001466"
]
```

## S2 Process IR

```json
{
  "section_id": "CH19-S07",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "FATF如何发布互评估报告？",
      "title": "FATF在全体会议讨论和质量审查后发布互评估报告",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "全体会议讨论和最终质量审查完成",
          "evidence_unit_ids": [
            "v7u_N001430"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "FATF发布互评估报告",
          "evidence_unit_ids": [
            "v7u_N001430"
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
            "v7u_N001430"
          ],
          "source_quote": "After the plenary discussion and final quality review are complete, FATF publishes the mutual evaluation report."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "评估不佳的司法管辖区面临什么后果？",
      "title": "评估表现不佳可能导致被列入FATF灰名单或黑名单",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "评估表现不佳",
          "evidence_unit_ids": [
            "v7u_N001431"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "decision",
          "label": "存在被列入FATF灰名单或黑名单的风险",
          "evidence_unit_ids": [
            "v7u_N001431"
          ],
          "modality": "risky"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e001",
          "process_element_id": "e002",
          "condition": "司法管辖区在评估中表现不佳",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001431"
          ],
          "source_quote": "Jurisdictions that perform poorly on evaluations risk placement on FATF’s grey list or black list."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "司法管辖区在收到互评估报告评级后应如何响应？",
      "title": "收到评级后应解决FATF指出的缺陷",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "收到互评估报告评级",
          "evidence_unit_ids": [
            "v7u_N001433"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "解决FATF在互评估报告中指出的缺陷",
          "evidence_unit_ids": [
            "v7u_N001433"
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
            "v7u_N001433"
          ],
          "source_quote": "After jurisdictions receive the ratings on Recommendations, they should address the shortcomings FATF identified in the mutual evaluation report."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_006"
      ],
      "focal_question": "合规增强如何导致更好的金融犯罪防范？",
      "title": "合规增强促使加大技术和人员投资以防范金融犯罪",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "合规增强",
          "evidence_unit_ids": [
            "v7u_N001436"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "加大对技术、培训和人员的投资",
          "evidence_unit_ids": [
            "v7u_N001436"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "检测和防范金融犯罪",
          "evidence_unit_ids": [
            "v7u_N001436"
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
            "v7u_N001436"
          ],
          "source_quote": "These enhancements lead to greater investment in technology, training, and personnel for detecting and preventing financial crimes."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N001436"
          ],
          "source_quote": "for detecting and preventing financial crimes"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_007",
        "s1c_008"
      ],
      "focal_question": "FATF如何对司法管辖区进行评估后监测？",
      "title": "所有司法管辖区接受评估后监测，并根据表现采取不同措施",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "standard",
          "label": "所有司法管辖区须接受评估后监测",
          "evidence_unit_ids": [
            "v7u_N001438"
          ],
          "modality": "required"
        },
        {
          "element_id": "e002",
          "role": "context",
          "label": "司法管辖区基本合规且积极整改",
          "evidence_unit_ids": [
            "v7u_N001439"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "定期提交改进报告",
          "evidence_unit_ids": [
            "v7u_N001439"
          ],
          "modality": "optional"
        },
        {
          "element_id": "e004",
          "role": "context",
          "label": "司法管辖区关键缺陷整改不力",
          "evidence_unit_ids": [
            "v7u_N001440"
          ],
          "modality": null
        },
        {
          "element_id": "e005",
          "role": "action",
          "label": "FATF发布公开警告",
          "evidence_unit_ids": [
            "v7u_N001440"
          ],
          "modality": "permitted"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e002",
          "process_element_id": "e003",
          "condition": "基本合规且积极整改",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001439"
          ],
          "source_quote": "This monitoring can include regular reports of improvements for jurisdictions that are already largely compliant and actively addressing the remaining few shortcomings."
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "process_element_id": "e003",
          "auxiliary_element_id": "e001",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001439"
          ],
          "source_quote": "This monitoring can include regular reports of improvements..."
        },
        {
          "relation_id": "r003",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e004",
          "process_element_id": "e005",
          "condition": "关键缺陷整改不力",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001440"
          ],
          "source_quote": "FATF can issue public warnings against a jurisdiction that makes insufficient progress to address key deficiencies."
        },
        {
          "relation_id": "r004",
          "kind": "reference",
          "process_element_id": "e005",
          "auxiliary_element_id": "e001",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001440"
          ],
          "source_quote": "FATF can issue public warnings against a jurisdiction..."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_006",
      "source_candidate_ids": [
        "s1c_009"
      ],
      "focal_question": "阿联酋如何从FATF灰名单被移除？",
      "title": "阿联酋通过成功整改在2024年被FATF从灰名单移除",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "outcome",
          "label": "FATF在2022年将阿联酋列入灰名单",
          "evidence_unit_ids": [
            "v7u_N001441"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "阿联酋成功修订立法、更新指引、加强受益所有人法规等整改措施",
          "evidence_unit_ids": [
            "v7u_N001441",
            "v7u_N001442",
            "v7u_N001443",
            "v7u_N001444",
            "v7u_N001445",
            "v7u_N001446",
            "v7u_N001447",
            "v7u_N001448",
            "v7u_N001449"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "FATF在2024年将阿联酋从灰名单移除",
          "evidence_unit_ids": [
            "v7u_N001441"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "sequence",
          "before_element_id": "e001",
          "after_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001441"
          ],
          "source_quote": "FATF placed the UAE on the grey list in 2022 and removed it from the list in 2024."
        },
        {
          "relation_id": "r002",
          "kind": "trigger",
          "trigger_mode": "event",
          "trigger_element_id": "e002",
          "process_element_id": "e003",
          "condition": null,
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001441"
          ],
          "source_quote": "The removal was due to the UAE successfully amending its legislation to close loopholes, criminalize money laundering, and improve financial transparency."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_007",
      "source_candidate_ids": [
        "s1c_010"
      ],
      "focal_question": "受监管机构因互评估影响应采取什么措施？",
      "title": "受监管机构因互评估影响应实施控制框架和资源",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "互评估影响不仅限于国家层面，也影响受监管机构",
          "evidence_unit_ids": [
            "v7u_N001450"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "受监管机构实施控制框架和资源",
          "evidence_unit_ids": [
            "v7u_N001451"
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
          "condition": "互评估影响也适用于受监管机构",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001450",
            "v7u_N001451"
          ],
          "source_quote": "the impacts from a mutual evaluation are not limited to the national level... Therefore, regulated organizations should implement control frameworks and resources."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_008",
      "source_candidate_ids": [
        "s1c_014"
      ],
      "focal_question": "司法管辖区如何根据自身情况定制国家风险评估？",
      "title": "根据自身能力、风险敞口和背景定制国家风险评估过程",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "input",
          "label": "自身能力、风险敞口和背景",
          "evidence_unit_ids": [
            "v7u_N001456"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "定制国家风险评估过程",
          "evidence_unit_ids": [
            "v7u_N001456"
          ],
          "modality": "required"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "reference",
          "process_element_id": "e002",
          "auxiliary_element_id": "e001",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001456"
          ],
          "source_quote": "jurisdictions should tailor the national risk assessment process based on their capacity, risk exposure, and context."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_009",
      "source_candidate_ids": [
        "s1c_015",
        "s1c_011"
      ],
      "focal_question": "FATF建议司法管辖区如何执行国家风险评估？",
      "title": "按照FATF六步最佳实践框架进行国家风险评估",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "环境扫描，评估经济、政治和法律因素",
          "evidence_unit_ids": [
            "v7u_N001458"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "分析扫描，收集和分析洗钱和恐怖融资数据",
          "evidence_unit_ids": [
            "v7u_N001459"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "威胁分析，识别关键洗钱和恐怖融资行为者及方法",
          "evidence_unit_ids": [
            "v7u_N001460"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "action",
          "label": "漏洞分析，评估金融体系弱点",
          "evidence_unit_ids": [
            "v7u_N001461"
          ],
          "modality": null
        },
        {
          "element_id": "e005",
          "role": "action",
          "label": "风险评估，分配风险等级并制定缓解计划",
          "evidence_unit_ids": [
            "v7u_N001462"
          ],
          "modality": null
        },
        {
          "element_id": "e006",
          "role": "action",
          "label": "地平线扫描，监测新兴趋势和未来威胁",
          "evidence_unit_ids": [
            "v7u_N001463"
          ],
          "modality": null
        },
        {
          "element_id": "e007",
          "role": "standard",
          "label": "FATF建议1要求司法管辖区识别、评估和理解洗钱和恐怖融资风险",
          "evidence_unit_ids": [
            "v7u_N001452"
          ],
          "modality": "required"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "sequence",
          "before_element_id": "e001",
          "after_element_id": "e002",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001458",
            "v7u_N001459"
          ],
          "source_quote": "1. An environmental scan... 2. An analytical scan..."
        },
        {
          "relation_id": "r002",
          "kind": "sequence",
          "before_element_id": "e002",
          "after_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001459",
            "v7u_N001460"
          ],
          "source_quote": "2. An analytical scan... 3. An analysis of threats..."
        },
        {
          "relation_id": "r003",
          "kind": "sequence",
          "before_element_id": "e003",
          "after_element_id": "e004",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001460",
            "v7u_N001461"
          ],
          "source_quote": "3. An analysis of threats... 4. An analysis of vulnerabilities..."
        },
        {
          "relation_id": "r004",
          "kind": "sequence",
          "before_element_id": "e004",
          "after_element_id": "e005",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001461",
            "v7u_N001462"
          ],
          "source_quote": "4. An analysis of vulnerabilities... 5. A risk assessment..."
        },
        {
          "relation_id": "r005",
          "kind": "sequence",
          "before_element_id": "e005",
          "after_element_id": "e006",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001462",
            "v7u_N001463"
          ],
          "source_quote": "5. A risk assessment... 6. Horizon scanning..."
        },
        {
          "relation_id": "r006",
          "kind": "reference",
          "process_element_id": "e001",
          "auxiliary_element_id": "e007",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001458",
            "v7u_N001452"
          ],
          "source_quote": "Recommendation 1 of FATF standards requires jurisdictions to identify, assess, and understand their money laundering and terrorist financing risks; environmental scan to evaluate..."
        }
      ],
      "split_reason": "合并s1c_015和s1c_011，因六步框架旨在协助辖区满足建议1的风险评估要求。"
    },
    {
      "episode_id": "ep_010",
      "source_candidate_ids": [
        "s1c_016"
      ],
      "focal_question": "行业和专题风险评估如何帮助理解风险？",
      "title": "行业和专题风险评估帮助当局制定类型学以了解洗钱和恐怖融资风险",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "行业和专题风险评估",
          "evidence_unit_ids": [
            "v7u_N001464"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "制定类型学以了解行为人如何利用特定部门进行洗钱和恐怖融资",
          "evidence_unit_ids": [
            "v7u_N001464"
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
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N001464"
          ],
          "source_quote": "sectoral and thematic risk assessments help authorities develop typologies to understand how bad actors could exploit specific sectors for money laundering and terrorist financing."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_011",
      "source_candidate_ids": [
        "s1c_017"
      ],
      "focal_question": "全企业风险评估如何加强合规？",
      "title": "全企业风险评估系统识别和评估风险以强化合规和内控",
      "card_nature": "control",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "全企业风险评估",
          "evidence_unit_ids": [
            "v7u_N001466"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "系统性识别和评估所有运营中的洗钱和恐怖融资风险",
          "evidence_unit_ids": [
            "v7u_N001466"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "强化合规、内控和监管对齐，优化风险管理",
          "evidence_unit_ids": [
            "v7u_N001466"
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
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001466"
          ],
          "source_quote": "Enterprise-wide risk assessments ensure that organizations systematically identify and assess money laundering and terrorist financing risks across all operations."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001466"
          ],
          "source_quote": "These assessments strengthen compliance, internal controls, and regulatory alignment while optimizing risk management."
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
      "reason": "明确描述发布报告的流程触发与行动。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "表达评估不佳与列入名单风险之间的判断关系。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "接收评级触发解决缺陷的义务，构成程序性流程。"
    },
    {
      "candidate_id": "s1c_004",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "仅陈述FATF的鼓励行为，无后续实际触发或业务流程改变。"
    },
    {
      "candidate_id": "s1c_005",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "与s1c_004类似，仅表达FATF的鼓励，不构成程序性迁移。"
    },
    {
      "candidate_id": "s1c_006",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "合规增强引发投资行为，并目的于防范金融犯罪，形成有向流程。"
    },
    {
      "candidate_id": "s1c_007",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005"
      ],
      "reason": "提供监测要求与部分分支措施，与s1c_008共同构成完整监测分支。"
    },
    {
      "candidate_id": "s1c_008",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005"
      ],
      "reason": "补充监测的另一分支（警告），与s1c_007合并为同一评估后监测流程。"
    },
    {
      "candidate_id": "s1c_009",
      "disposition": "mapped",
      "episode_ids": [
        "ep_006"
      ],
      "reason": "案例展示以整改成功触发灰名单移除的完整程序。"
    },
    {
      "candidate_id": "s1c_010",
      "disposition": "mapped",
      "episode_ids": [
        "ep_007"
      ],
      "reason": "互评估影响推导出受监管机构应实施控制框架的程序性要求。"
    },
    {
      "candidate_id": "s1c_011",
      "disposition": "support_only",
      "episode_ids": [
        "ep_009"
      ],
      "reason": "作为FATF建议1的要求，为六步国家风险评估框架提供标准支撑。"
    },
    {
      "candidate_id": "s1c_012",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "仅描述FATF推广风险为本方法，无具体程序或判断迁移。"
    },
    {
      "candidate_id": "s1c_013",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "陈述风险评估可在多层面进行的允许性规则，不属于流程。"
    },
    {
      "candidate_id": "s1c_014",
      "disposition": "mapped",
      "episode_ids": [
        "ep_008"
      ],
      "reason": "明确根据辖区自身条件定制NRA的动作和依据，构成决策流程。"
    },
    {
      "candidate_id": "s1c_015",
      "disposition": "mapped",
      "episode_ids": [
        "ep_009"
      ],
      "reason": "提供六步NRA框架的序列步骤，是核心执行流程。"
    },
    {
      "candidate_id": "s1c_016",
      "disposition": "mapped",
      "episode_ids": [
        "ep_010"
      ],
      "reason": "行业风险评估产出类型学，具有明确的目的性产出关系。"
    },
    {
      "candidate_id": "s1c_017",
      "disposition": "mapped",
      "episode_ids": [
        "ep_011"
      ],
      "reason": "企业风险评估产生系统性风险识别和合规加强的结果。"
    },
    {
      "candidate_id": "s1c_gap_ch19_s07_poor_eval_consequences",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "描述评估不佳导致的外部经济后果，非机构内部程序或判断迁移。"
    }
  ],
  "skip_reason": null
}
```
