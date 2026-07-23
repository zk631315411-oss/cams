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

section_id: `CH24-S07`

section_title: `US AML/CFT regulatory landscape > History of AML regime in Europe`

section_text_with_unit_anchors:

```text
[v7u_N001781|1781] The EU is a political and economic union of jurisdictions.
ZH: 欧盟是一个由多个司法管辖区组成的政治经济联盟。

[v7u_N001782|1782] Note that Norway, Iceland, and Liechtenstein are not part of the EU but are members of the European Economic Area (EEA).
ZH: 挪威、冰岛和列支敦士登不是欧盟成员，但属于欧洲经济区。

[v7u_N001783|1783] Although members of the EEA do not take part in the EU’s legislative process, they are required to comply with the EU’s AML/CFT legislation, which can be issued as a regulation or a directive.
ZH: 欧洲经济区成员必须遵守欧盟反洗钱/反恐怖融资法规。

[v7u_N001784|1784] A regulation is a legal act that is immediately applicable in each member state.
ZH: 法规是一种在成员国直接适用的法律行为。

[v7u_N001785|1785] A directive is a legal act that sets principles and goals.
ZH: 指令是一种设定原则和目标的立法行为。

[v7u_N001786|1786] National legislators must transpose, or incorporate into their legislation, EU directives by a certain deadline to make them binding.
ZH: 国家立法者必须在截止日期前将欧盟指令转化为国内法。

[v7u_N001787|1787] Since 1991, the EU has used directives to establish its AML/CFT regime.
ZH: 自1991年起，欧盟通过指令建立反洗钱/反恐怖融资制度。

[v7u_N001788|1788] The first AML directive (1AMLD) primarily applied to banks and required member states to criminalize money laundering.
ZH: 第一项反洗钱指令主要适用于银行，并要求成员国将洗钱定为刑事犯罪。

[v7u_N001789|1789] Since then, the EU has amended the AMLDs, with the 2AMLD in 2001, 3AMLD in 2005, 4AMLD in 2015, and 5AMLD in 2018.
ZH: 欧盟后续修订了反洗钱指令，包括2001年、2005年、2015年和2018年的版本。

[v7u_N001790|1790] Many of the EU’s provisions to the AMLDs were to address previous challenges.
ZH: 欧盟反洗钱指令的许多条款旨在解决先前挑战。

[v7u_N001791|1791] For example, some member states did not transpose the AMLDs in their national legislation in a timely manner or in full compliance.
ZH: 一些成员国未能及时或完全将反洗钱指令转化为国内法。

[v7u_N001792|1792] These factors resulted in lapses, such as banks failing to comply with core requirements and deficiencies in consolidated supervision for cross-border entities.
ZH: 转化不力导致银行未能遵守核心要求以及跨境实体合并监管缺陷。

[v7u_N001793|1793] This fragmentation between entities reduced the effectiveness of supervision and cooperation among authorities and resulted in AML breaches.
ZH: 实体间的碎片化降低了监管和合作的有效性，导致反洗钱违规。

[v7u_N001794|1794] Therefore, the EU passed the 5AMLD to strengthen the obligation for cooperation between AML and banking supervisors. The AMLD amendments also aimed to strengthen existing regulations and expand regulatory scope to include entities such as NBFIs, DNFBPs, and cryptoasset service providers.
ZH: 欧盟通过第五项反洗钱指令加强反洗钱与银行监管合作，并扩大监管范围至非银行金融机构、指定非金融行业和加密资产服务商。

[v7u_N001795|1795] Until 2018, member states differed on the predicate offenses for money laundering.
ZH: 2018年前，成员国对洗钱上游犯罪的定义存在差异。

[v7u_N001796|1796] This led the EU to pass Directive 2018/1673, or the “AML Criminal Law Directive,” which establishes minimum rules concerning the definition of criminal offenses and penalties for money laundering.
ZH: 欧盟通过2018/1673号指令（反洗钱刑法指令）统一洗钱犯罪定义和处罚最低标准。

[v7u_N001797|1797] In 2024, the EU amended Directive 2018/1673 to ensure that violations of EU restrictive measures constitute a criminal offense.
ZH: 2024年，欧盟修订2018/1673号指令，将违反限制性措施定为刑事犯罪。

[v7u_N001798|1798] The EU also introduced the EU AML Single Rulebook, also known as the EU AML package, which includes the 6AMLD.
ZH: 欧盟推出反洗钱单一规则手册（含第六项反洗钱指令）。

[v7u_N001799|1799] For the first time, this framework combined a regulation with a directive to increase its level of harmonization and effectiveness within member states.
ZH: 该框架首次结合法规与指令，提高成员国间的协调性和有效性。
```

allowed_unit_ids:

```json
[
  "v7u_N001781",
  "v7u_N001782",
  "v7u_N001783",
  "v7u_N001784",
  "v7u_N001785",
  "v7u_N001786",
  "v7u_N001787",
  "v7u_N001788",
  "v7u_N001789",
  "v7u_N001790",
  "v7u_N001791",
  "v7u_N001792",
  "v7u_N001793",
  "v7u_N001794",
  "v7u_N001795",
  "v7u_N001796",
  "v7u_N001797",
  "v7u_N001798",
  "v7u_N001799"
]
```

## S2 Process IR

```json
{
  "section_id": "CH24-S07",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001"
      ],
      "focal_question": "欧洲经济区成员为何必须遵守欧盟反洗钱/反恐怖融资法规？",
      "title": "欧洲经济区成员的反洗钱/反恐怖融资合规义务",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "欧洲经济区成员不参与欧盟立法过程",
          "evidence_unit_ids": [
            "v7u_N001783"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "必须遵守欧盟反洗钱/反恐怖融资法规",
          "evidence_unit_ids": [
            "v7u_N001783"
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
            "v7u_N001783"
          ],
          "source_quote": "Although members of the EEA do not take part in the EU’s legislative process, they are required to comply with the EU’s AML/CFT legislation, which can be issued as a regulation or a directive."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_002"
      ],
      "focal_question": "国家立法者如何使欧盟指令具有约束力？",
      "title": "国家立法者转化欧盟指令的义务",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "国家立法者将欧盟指令转化为国内法",
          "evidence_unit_ids": [
            "v7u_N001786"
          ],
          "modality": "required"
        },
        {
          "element_id": "e002",
          "role": "standard",
          "label": "在截止日期前",
          "evidence_unit_ids": [
            "v7u_N001786"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "使指令具有约束力",
          "evidence_unit_ids": [
            "v7u_N001786"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "reference",
          "process_element_id": "e001",
          "auxiliary_element_id": "e002",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001786"
          ],
          "source_quote": "National legislators must transpose, or incorporate into their legislation, EU directives by a certain deadline to make them binding."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e003",
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N001786"
          ],
          "source_quote": "to make them binding"
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_003"
      ],
      "focal_question": "第一项反洗钱指令提出了哪些要求？",
      "title": "第一项反洗钱指令的适用范围与刑事化要求",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "第一项反洗钱指令主要适用于银行",
          "evidence_unit_ids": [
            "v7u_N001788"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "要求成员国将洗钱定为刑事犯罪",
          "evidence_unit_ids": [
            "v7u_N001788"
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
            "v7u_N001788"
          ],
          "source_quote": "The first AML directive (1AMLD) primarily applied to banks and required member states to criminalize money laundering."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_004",
      "source_candidate_ids": [
        "s1c_gap_ch24_s07_5amld_response"
      ],
      "focal_question": "欧盟因应转化不力及监管碎片化采取了哪些措施？",
      "title": "欧盟通过第五项反洗钱指令加强合作并扩大监管范围",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "成员国未及时或完全将反洗钱指令转化为国内法",
          "evidence_unit_ids": [
            "v7u_N001791"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "导致银行未能遵守核心要求、跨境实体并表监管缺陷、实体间碎片化、监管有效性降低和反洗钱违规",
          "evidence_unit_ids": [
            "v7u_N001792",
            "v7u_N001793"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "action",
          "label": "欧盟通过第五项反洗钱指令",
          "evidence_unit_ids": [
            "v7u_N001794"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "outcome",
          "label": "加强反洗钱与银行监管合作，加强现有法规，并扩大监管范围至非银行金融机构、指定非金融行业和加密资产服务商",
          "evidence_unit_ids": [
            "v7u_N001794"
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
            "v7u_N001791",
            "v7u_N001792"
          ],
          "source_quote": "some member states did not transpose the AMLDs in their national legislation in a timely manner or in full compliance. These factors resulted in lapses, such as banks failing to comply with core requirements and deficiencies in consolidated supervision for cross-border entities."
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
            "v7u_N001793",
            "v7u_N001794"
          ],
          "source_quote": "This fragmentation between entities reduced the effectiveness of supervision and cooperation among authorities and resulted in AML breaches. Therefore, the EU passed the 5AMLD to strengthen the obligation for cooperation between AML and banking supervisors."
        },
        {
          "relation_id": "r003",
          "kind": "produce",
          "process_element_id": "e003",
          "outcome_element_id": "e004",
          "relation_type": null,
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N001794"
          ],
          "source_quote": "to strengthen the obligation for cooperation between AML and banking supervisors. The AMLD amendments also aimed to strengthen existing regulations and expand regulatory scope to include entities such as NBFIs, DNFBPs, and cryptoasset service providers."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_005",
      "source_candidate_ids": [
        "s1c_gap_ch24_s07_amld_criminal"
      ],
      "focal_question": "欧盟如何应对成员国对洗钱上游犯罪的差异？",
      "title": "欧盟通过反洗钱刑法指令统一犯罪定义和处罚",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "2018年前成员国对洗钱上游犯罪定义存在差异",
          "evidence_unit_ids": [
            "v7u_N001795"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "欧盟通过2018/1673指令（反洗钱刑法指令）",
          "evidence_unit_ids": [
            "v7u_N001796"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "建立犯罪定义和处罚最低规则",
          "evidence_unit_ids": [
            "v7u_N001796"
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
            "v7u_N001795",
            "v7u_N001796"
          ],
          "source_quote": "This led the EU to pass Directive 2018/1673, or the \"AML Criminal Law Directive,\" which establishes minimum rules concerning the definition of criminal offenses and penalties for money laundering."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001796"
          ],
          "source_quote": "establishes minimum rules concerning the definition of criminal offenses and penalties for money laundering."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_006",
      "source_candidate_ids": [
        "s1c_gap_ch24_s07_amended_restrictive_measures"
      ],
      "focal_question": "2024年欧盟为何修订反洗钱刑法指令？",
      "title": "2024年修订反洗钱刑法指令以涵盖限制措施违规",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "2024年修订2018/1673指令",
          "evidence_unit_ids": [
            "v7u_N001797"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "确保违反欧盟限制措施构成刑事犯罪",
          "evidence_unit_ids": [
            "v7u_N001797"
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
            "v7u_N001797"
          ],
          "source_quote": "In 2024, the EU amended Directive 2018/1673 to ensure that violations of EU restrictive measures constitute a criminal offense."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_007",
      "source_candidate_ids": [
        "s1c_gap_ch24_s07_single_rulebook"
      ],
      "focal_question": "欧盟反洗钱单一规则手册有何创新？",
      "title": "欧盟推出单一规则手册结合法规与指令",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "欧盟推出反洗钱单一规则手册（含第六项反洗钱指令），首次结合法规与指令",
          "evidence_unit_ids": [
            "v7u_N001798",
            "v7u_N001799"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "提高成员国间的协调性和有效性",
          "evidence_unit_ids": [
            "v7u_N001799"
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
            "v7u_N001799"
          ],
          "source_quote": "to increase its level of harmonization and effectiveness within member states."
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
      "reason": "该候选自身独立支持欧洲经济区成员必须遵守欧盟反洗钱/反恐怖融资法规的义务，构成触发关系。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选自身独立支持国家立法者转化指令的义务及其约束条件和目的，构成行动、标准与产出关系。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "该候选自身独立支持第一项反洗钱指令的适用范围及刑事化要求，构成触发关系。"
    },
    {
      "candidate_id": "s1c_gap_ch24_s07_5amld_response",
      "disposition": "mapped",
      "episode_ids": [
        "ep_004"
      ],
      "reason": "该候选承接成员国转化不力、监管失效及欧盟通过第五项反洗钱指令的完整应对链，构成多步触发与产出关系。"
    },
    {
      "candidate_id": "s1c_gap_ch24_s07_amld_criminal",
      "disposition": "mapped",
      "episode_ids": [
        "ep_005"
      ],
      "reason": "该候选承接成员国上游犯罪定义差异及欧盟通过反洗钱刑法指令的立法应对链，构成触发与产出关系。"
    },
    {
      "candidate_id": "s1c_gap_ch24_s07_amended_restrictive_measures",
      "disposition": "mapped",
      "episode_ids": [
        "ep_006"
      ],
      "reason": "该候选自身独立支持2024年修订指令将违反限制措施刑事化的立法行动及其目的。"
    },
    {
      "candidate_id": "s1c_gap_ch24_s07_single_rulebook",
      "disposition": "mapped",
      "episode_ids": [
        "ep_007"
      ],
      "reason": "该候选自身独立支持欧盟推出单一规则手册、首次结合法规与指令以提高协调性和有效性的制度创新举措。"
    }
  ],
  "skip_reason": null
}
```
