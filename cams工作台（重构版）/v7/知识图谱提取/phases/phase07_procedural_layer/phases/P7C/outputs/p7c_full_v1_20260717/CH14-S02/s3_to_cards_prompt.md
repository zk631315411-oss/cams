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

section_id: `CH14-S02`

section_title: `Money Laundering Risks in DNFBPs and Other High-Risk Sectors > Case example: DNFBP risks in the Hendricks case`

section_text_with_unit_anchors:

```text
[v7u_N001045|1045] Josh is a US-based lawyer and AFC professional with experience in regulated entities. He has been invited to participate in his jurisdiction’s Financial Risk Review Task Force to examine whether additional regulations are needed for DNFBPs and other high-risk sectors. The task force aims to classify the various types of DNFBPs, the customers they serve, and the associated risks to establish the regulatory needs.
ZH: 案例：Josh参与司法管辖区金融风险审查工作组，审查DNFBP及高风险行业监管需求。

[v7u_N001046|1046] A notable case discussed involved Kurt Hendricks, a Russian customer charged with bank fraud and money laundering related to two condominiums in California.
ZH: Hendricks案：俄罗斯客户被控银行欺诈和洗钱，涉及加州两套公寓。

[v7u_N001047|1047] Hendricks used a corporate nominee and a multi-tiered structure of shell companies to conceal his identity from US financial institutions.
ZH: Hendricks使用公司名义代理人和多层壳公司结构向美国金融机构隐瞒身份。

[v7u_N001048|1048] He wired nearly US$4 million from overseas accounts in Latvia and Switzerland, where there are lower regulatory expectations with response to AML/CFT, to fund a US$3 million real estate transaction through a corporate entity set up by the nominee in the British Virgin Islands.
ZH: Hendricks从拉脱维亚和瑞士的低监管账户电汇近400万美元，通过英属维尔京群岛公司实体完成房地产交易。

[v7u_N001049|1049] The remaining funds were invested in a brokerage account maintained by the nominee and used to pay expenses for the condominiums.
ZH: 剩余资金投资于名义代理人维护的经纪账户，并用于支付公寓费用。

[v7u_N001050|1050] The Hendricks case demonstrated how money laundering cases can involve multiple DNFBPs, each presenting unique risks, including:
ZH: Hendricks案展示了洗钱案如何涉及多个DNFBP，各自呈现独特风险。

[v7u_N001051|1051] Real estate agents who facilitate high-value transactions involving ultimate beneficial owners that are not clearly identified.
ZH: 房地产经纪人促成高价值交易，最终受益所有人身份不明。

[v7u_N001052|1052] Lawyers and trust or company service providers (TCSP) who create complex corporate structures to obscure the sources of funds.
ZH: 律师和信托或公司服务提供商（TCSP）创建复杂公司结构以掩盖资金来源。

[v7u_N001053|1053] Accountants who enable illicit transactions to appear legitimate.
ZH: 会计师使非法交易看似合法。

[v7u_N001054|1054] The task force noted that attorneys in the US are self-regulated by state bar associations, which provide recommended rules but lack mandatory reporting requirements.
ZH: 美国律师由州律师协会自律，提供推荐规则但缺乏强制报告要求。

[v7u_N001055|1055] Similarly, real estate agencies and TCSPs do not have to adhere to AML/CFT regulations or conduct audits for compliance.
ZH: 房地产中介和TCSP无需遵守反洗钱/反恐怖融资法规或进行合规审计。

[v7u_N001056|1056] Given the complexities and risks associated with DNFBPs, the task force recommended comprehensive AML/CFT regulations to bridge existing gaps.
ZH: 工作组建议制定全面的反洗钱/反恐怖融资法规以弥补现有差距。

[v7u_N001057|1057] Requiring DNFBPs to set up an AML/CFT framework and find the right balance between customer privacy and AML reporting requirements could deter the financial benefits of enabling such activities and reduce the occurrence of money laundering.
ZH: 要求DNFBP建立反洗钱/反恐怖融资框架并在客户隐私与报告要求间取得平衡。

[v7u_N001058|1058] This tailored regulatory approach enhances the financial system's integrity and protects it from exploitation by criminal actors.
ZH: 量身定制的监管方法增强金融体系完整性，防止被犯罪分子利用。
```

allowed_unit_ids:

```json
[
  "v7u_N001045",
  "v7u_N001046",
  "v7u_N001047",
  "v7u_N001048",
  "v7u_N001049",
  "v7u_N001050",
  "v7u_N001051",
  "v7u_N001052",
  "v7u_N001053",
  "v7u_N001054",
  "v7u_N001055",
  "v7u_N001056",
  "v7u_N001057",
  "v7u_N001058"
]
```

## S2 Process IR

```json
{
  "section_id": "CH14-S02",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001",
        "s1c_002",
        "s1c_gap_ch14_s02_case_demo",
        "s1c_gap_ch14_s02_reg_shortfalls"
      ],
      "focal_question": "工作组如何基于DNFBP的风险和监管缺口推荐全面AML/CFT法规？",
      "title": "工作组审查DNFBP风险和监管缺口并推荐全面法规",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "input",
          "label": "The Hendricks case demonstrated how money laundering cases can involve multiple DNFBPs, each presenting unique risks.",
          "evidence_unit_ids": [
            "v7u_N001050"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "The task force noted that attorneys in the US are self-regulated by state bar associations, which provide recommended rules but lack mandatory reporting requirements, and similarly real estate agencies and TCSPs do not have to adhere to AML/CFT regulations or conduct audits for compliance.",
          "evidence_unit_ids": [
            "v7u_N001054",
            "v7u_N001055"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "decision",
          "label": "Given the complexities and risks, the task force recommended comprehensive AML/CFT regulations to bridge existing gaps.",
          "evidence_unit_ids": [
            "v7u_N001056"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "Requiring DNFBPs to set up an AML/CFT framework and find the right balance between customer privacy and AML reporting requirements could deter the financial benefits of enabling such activities and reduce the occurrence of money laundering.",
          "evidence_unit_ids": [
            "v7u_N001057"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "sequence",
          "before_element_id": "e002",
          "after_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001054",
            "v7u_N001055",
            "v7u_N001056"
          ],
          "source_quote": "The task force noted that attorneys in the US ... Similarly, real estate agencies and TCSPs do not have to adhere ... Given the complexities and risks associated with DNFBPs, the task force recommended comprehensive AML/CFT regulations to bridge existing gaps."
        },
        {
          "relation_id": "r002",
          "kind": "reference",
          "process_element_id": "e003",
          "auxiliary_element_id": "e001",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001050",
            "v7u_N001056"
          ],
          "source_quote": "The Hendricks case demonstrated how money laundering cases can involve multiple DNFBPs, each presenting unique risks ... Given the complexities and risks associated with DNFBPs, the task force recommended comprehensive AML/CFT regulations to bridge existing gaps."
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e003",
          "outcome_element_id": "e004",
          "relation_type": null,
          "qualifier": "may_lead_to",
          "evidence_unit_ids": [
            "v7u_N001056",
            "v7u_N001057"
          ],
          "source_quote": "recommended comprehensive AML/CFT regulations to bridge existing gaps. Requiring DNFBPs to set up an AML/CFT framework ... could deter the financial benefits of enabling such activities and reduce the occurrence of money laundering."
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
      "reason": "提供工作组基于风险和复杂性推荐法规的程序性关系，进入episode。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "提供推荐法规的预期效果，作为outcome连接至推荐，进入episode。"
    },
    {
      "candidate_id": "s1c_gap_ch14_s02_case_demo",
      "disposition": "support_only",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "案例展示洗钱涉及多个DNFBP及风险，自身不构成独立程序性关系，但为工作组推荐提供了风险输入，作为episode的input元素。"
    },
    {
      "candidate_id": "s1c_gap_ch14_s02_reg_shortfalls",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "工作组注意到DNFBP缺乏监管义务，构成发现动作，独立支持程序性关系（先注意到后推荐），进入episode。"
    }
  ],
  "skip_reason": null
}
```
