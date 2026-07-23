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

section_id: `CH19-S01`

section_title: `Financial Action Task Force > Financial Action Task Force`

section_text_with_unit_anchors:

```text
[v7u_N001303|1303] The G-7 established the Financial Action Task Force (FATF) in 1989 as an international organization to coordinate efforts to combat money laundering.
ZH: FATF于1989年由G7成立，旨在协调打击洗钱

[v7u_N001304|1304] Its original membership included 15 countries and the EU, and it now includes nearly 40 countries as well as a global network of regional groups.
ZH: FATF初始成员包括15国和欧盟，现扩展至近40国及区域网络

[v7u_N001305|1305] Within a year of its founding, FATF issued its original 40 Recommendations setting forth guidance and a comprehensive action plan for fighting money laundering worldwide.
ZH: FATF成立一年内发布40项建议，指导全球反洗钱行动

[v7u_N001306|1306] In the wake of the September 11 terrorist attacks in the US, FATF issued eight Special Recommendations on terrorist financing to supplement the original Recommendations. FATF eventually added a ninth Special Recommendation.
ZH: 9/11后FATF发布关于恐怖融资的八项特别建议，后增至九项

[v7u_N001307|1307] In addition to setting standards through FATF Recommendations, FATF accomplishes its work through:
ZH: FATF除制定标准外，还通过其他方式开展工作

[v7u_N001308|1308] Assessing implementation: FATF conducts periodic formal evaluations and other assessments to determine whether jurisdictions have fully and effectively implemented its standards. If FATF identifies deficiencies, it implements and monitors action plans and publicly reports progress.
ZH: FATF通过定期评估监督各辖区标准实施情况

[v7u_N001309|1309] Monitoring methods and trends: FATF continuously monitors how criminals and terrorists raise, use, and move funds, and publishes reports to raise awareness of the latest techniques and trends. Over 200 countries and jurisdictions have committed to meeting FATF standards, including many that are not full members of the organization.
ZH: FATF持续监控犯罪和恐怖融资手法与趋势，200多辖区承诺遵守标准

[v7u_N001310|1310] Identifying high-risk jurisdictions: Where FATF has determined that a jurisdiction has failed to implement its standards, FATF can designate it as a jurisdiction under increased monitoring on the "grey list" or a high-risk jurisdiction on the "black list." FATF designations on the grey and black lists can have severe consequences since inclusion on these lists might lead to isolation from the global financial system.
ZH: FATF将未达标辖区列入灰名单或黑名单，可能导致金融孤立

[v7u_N001311|1311] FATF-style regional bodies (FSRB) are autonomous regional organizations that assist in implementing FATF’s standards. These bodies closely align with FATF objectives and have similar forms and functions but operate independently of FATF. FSRBs are also considered FATF associate members.
ZH: FATF式区域机构（FSRB）是协助实施FATF标准的自治区域组织

[v7u_N001312|1312] In setting standards, FATF depends on input from the FSRBs. However, FATF remains the only standard-setting body.
ZH: FATF依赖FSRB提供意见，但仍是唯一标准制定机构

[v7u_N001313|1313] FSRBs ensure global AML/CFT efforts remain effective by identifying and addressing threats to the financial system, facilitating regional cooperation, assisting with mutual evaluations, and providing technical assistance to their members.
ZH: FSRB通过识别威胁、促进合作、评估和技术援助确保全球反洗钱/反恐怖融资有效性

[v7u_N001314|1314] Each FSRB adopts and implements FATF’s 40 Recommendations against money laundering and terrorist financing.
ZH: 每个FSRB采纳并实施FATF的40项反洗钱和反恐怖融资建议

[v7u_N001315|1315] The FSRBs work with their respective members to identify regional issues, share their experiences, and develop solutions.
ZH: FSRB与成员合作识别区域问题、分享经验并制定解决方案

[v7u_N001316|1316] Note that the number of members belonging to each FSRB might vary based on political decisions and alliances.
ZH: 各FSRB成员数量因政治决策和联盟而异

[v7u_N001317|1317] Each FSRB has slightly different objectives. However, a common objective is to ensure member compliance with relevant international AML/CFT standards. To meet their objectives, FSRB's functions can include:
ZH: FSRB的共同目标是确保成员遵守国际反洗钱/反恐怖融资标准，其职能包括

[v7u_N001318|1318] Evaluating AML/CFT measures by conducting assessments and issuing recommendations.
ZH: FSRB通过评估和建议评价反洗钱/反恐怖融资措施

[v7u_N001319|1319] Strategizing priorities such as improving financial sector supervision, enhancing private sector compliance, and increasing effectiveness in convictions and asset confiscations.
ZH: FSRB制定优先事项，如改善金融监管、加强私营部门合规及提高定罪和资产没收效率

[v7u_N001320|1320] Publishing reports identifying AML/CFT typologies impacting FATF members.
ZH: FSRB发布报告识别影响FATF成员的反洗钱/反恐怖融资类型学

[v7u_N001321|1321] Collaborating with global institutions to strengthen AML/CFT frameworks.
ZH: 与全球机构合作加强反洗钱/反恐怖融资框架

[v7u_N001322|1322] The FATF Recommendations are among the most important resources that FATF uses to provide guidance and coordination in the fight against financial crime.
ZH: FATF建议是打击金融犯罪的关键指导资源

[v7u_N001323|1323] FATF expects its members to implement the Recommendations in their respective jurisdictions and assesses them on the extent of implementation and the effectiveness of their programs.
ZH: FATF要求成员国实施建议并接受评估

[v7u_N001324|1324] FATF also offers guidance and best practices to jurisdictions on how they should implement the Recommendations.
ZH: FATF提供实施建议的指导和最佳实践

[v7u_N001325|1325] The 40 Recommendations and 9 Special Recommendations address a wide range of topics, from high-level guidance to issues concerning specific sectors and topics. FATF groups the Recommendations into seven broad categories:
ZH: 40+9项建议涵盖广泛主题，FATF将其分为七大类

[v7u_N001326|1326] AML/CFT policies and coordination
ZH: 反洗钱/反恐怖融资政策与协调

[v7u_N001327|1327] Money laundering and confiscation
ZH: 洗钱与没收

[v7u_N001328|1328] Terrorist financing and financing of proliferation
ZH: 恐怖融资与扩散融资

[v7u_N001329|1329] Preventive measures
ZH: 预防措施

[v7u_N001330|1330] Transparency and beneficial ownership
ZH: 透明度与受益所有人

[v7u_N001331|1331] Powers and responsibilities of competent authorities and other institutional measures
ZH: 主管当局的权力与职责及其他制度措施

[v7u_N001332|1332] International cooperation
ZH: 国际合作

[v7u_N001333|1333] FATF intends for their member jurisdictions to implement the Recommendations in the form of legally binding law or regulation, which they can tailor to reflect their respective circumstances and legal structures. As a result, institutions receive the Recommendations as legal and regulatory requirements established within the jurisdictions in which they operate.
ZH: FATF建议以具有法律约束力的法律或法规形式实施，机构据此遵守

[v7u_N001334|1334] To assess member jurisdictions’ compliance with the Recommendations, FATF conducts periodic mutual evaluations through formal reviews by AML/CFT authorities from other jurisdictions.
ZH: FATF通过定期互评估审查成员国合规情况

[v7u_N001335|1335] The resulting mutual evaluation reports are public documents that provide an in-depth assessment of a member jurisdiction’s compliance with each Recommendation.
ZH: 互评估报告为公开文件，深入评估成员国合规情况

[v7u_N001336|1336] For each Recommendation, FATF gives a rating for technical compliance and effectiveness.
ZH: FATF对每项建议给出技术合规性和有效性评级

[v7u_N001337|1337] FATF then requires member jurisdictions to address any deficiencies and subjects them to post-assessment monitoring to ensure they address their issues.
ZH: FATF要求成员国整改缺陷并接受后续监测

[v7u_N001338|1338] Deficiencies can result in a member jurisdiction’s designation on the grey or black lists.
ZH: 缺陷可能导致成员国被列入灰名单或黑名单

[v7u_N001339|1339] These types of designations are likely to result in financial institutions flagging the member jurisdiction as high risk in their internal risk assessments.
ZH: 灰/黑名单认定导致金融机构在内部风险评估中将其标记为高风险
```

allowed_unit_ids:

```json
[
  "v7u_N001303",
  "v7u_N001304",
  "v7u_N001305",
  "v7u_N001306",
  "v7u_N001307",
  "v7u_N001308",
  "v7u_N001309",
  "v7u_N001310",
  "v7u_N001311",
  "v7u_N001312",
  "v7u_N001313",
  "v7u_N001314",
  "v7u_N001315",
  "v7u_N001316",
  "v7u_N001317",
  "v7u_N001318",
  "v7u_N001319",
  "v7u_N001320",
  "v7u_N001321",
  "v7u_N001322",
  "v7u_N001323",
  "v7u_N001324",
  "v7u_N001325",
  "v7u_N001326",
  "v7u_N001327",
  "v7u_N001328",
  "v7u_N001329",
  "v7u_N001330",
  "v7u_N001331",
  "v7u_N001332",
  "v7u_N001333",
  "v7u_N001334",
  "v7u_N001335",
  "v7u_N001336",
  "v7u_N001337",
  "v7u_N001338",
  "v7u_N001339"
]
```

## S2 Process IR

```json
{
  "section_id": "CH19-S01",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_001",
        "s1c_002",
        "s1c_003"
      ],
      "focal_question": "FATF如何通过互评估、评级和纠正措施确保成员合规，并基于缺陷进行名单指定？",
      "title": "FATF Mutual Evaluation and Deficiency Response Process",
      "card_nature": "assessment",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "FATF conducts periodic mutual evaluations and gives ratings for technical compliance and effectiveness",
          "evidence_unit_ids": [
            "v7u_N001334",
            "v7u_N001336",
            "v7u_N001308"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "decision",
          "label": "FATF determines whether jurisdictions have fully and effectively implemented standards and identifies deficiencies",
          "evidence_unit_ids": [
            "v7u_N001308"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "Mutual evaluation reports are public documents providing in-depth assessment",
          "evidence_unit_ids": [
            "v7u_N001335"
          ],
          "modality": null
        },
        {
          "element_id": "e004",
          "role": "action",
          "label": "FATF requires member jurisdictions to address any deficiencies",
          "evidence_unit_ids": [
            "v7u_N001337",
            "v7u_N001308"
          ],
          "modality": "required"
        },
        {
          "element_id": "e005",
          "role": "action",
          "label": "FATF subjects jurisdictions to post-assessment monitoring",
          "evidence_unit_ids": [
            "v7u_N001337",
            "v7u_N001308"
          ],
          "modality": "required"
        },
        {
          "element_id": "e006",
          "role": "outcome",
          "label": "FATF publicly reports progress on action plans",
          "evidence_unit_ids": [
            "v7u_N001308"
          ],
          "modality": null
        },
        {
          "element_id": "e007",
          "role": "decision",
          "label": "FATF designates jurisdiction on grey list or black list",
          "evidence_unit_ids": [
            "v7u_N001310",
            "v7u_N001338"
          ],
          "modality": "permitted"
        },
        {
          "element_id": "e008",
          "role": "outcome",
          "label": "Inclusion on lists might lead to isolation from global financial system",
          "evidence_unit_ids": [
            "v7u_N001310"
          ],
          "modality": null
        },
        {
          "element_id": "e009",
          "role": "outcome",
          "label": "Financial institutions likely flag the jurisdiction as high risk in internal risk assessments",
          "evidence_unit_ids": [
            "v7u_N001339"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e003",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001335"
          ],
          "source_quote": "The resulting mutual evaluation reports are public documents that provide an in-depth assessment of a member jurisdiction’s compliance with each Recommendation."
        },
        {
          "relation_id": "r002",
          "kind": "sequence",
          "before_element_id": "e001",
          "after_element_id": "e002",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001308"
          ],
          "source_quote": "FATF conducts periodic formal evaluations and other assessments to determine whether jurisdictions have fully and effectively implemented its standards."
        },
        {
          "relation_id": "r003",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e002",
          "process_element_id": "e004",
          "condition": "If FATF identifies deficiencies",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001308"
          ],
          "source_quote": "If FATF identifies deficiencies, it implements and monitors action plans and publicly reports progress."
        },
        {
          "relation_id": "r004",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e002",
          "process_element_id": "e005",
          "condition": "If FATF identifies deficiencies",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001308",
            "v7u_N001337"
          ],
          "source_quote": "FATF then requires member jurisdictions to address any deficiencies and subjects them to post-assessment monitoring to ensure they address their issues."
        },
        {
          "relation_id": "r005",
          "kind": "produce",
          "process_element_id": "e005",
          "outcome_element_id": "e006",
          "relation_type": null,
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001308"
          ],
          "source_quote": "it implements and monitors action plans and publicly reports progress."
        },
        {
          "relation_id": "r006",
          "kind": "trigger",
          "trigger_mode": "condition",
          "trigger_element_id": "e002",
          "process_element_id": "e007",
          "condition": "FATF has determined that a jurisdiction has failed to implement its standards",
          "relation_type": "conclusion_triggers_response",
          "qualifier": null,
          "evidence_unit_ids": [
            "v7u_N001310",
            "v7u_N001338"
          ],
          "source_quote": "Where FATF has determined that a jurisdiction has failed to implement its standards, FATF can designate it as a jurisdiction under increased monitoring on the \"grey list\" or a high-risk jurisdiction on the \"black list.\""
        },
        {
          "relation_id": "r007",
          "kind": "produce",
          "process_element_id": "e007",
          "outcome_element_id": "e008",
          "relation_type": null,
          "qualifier": "may_lead_to",
          "evidence_unit_ids": [
            "v7u_N001310"
          ],
          "source_quote": "inclusion on these lists might lead to isolation from the global financial system."
        },
        {
          "relation_id": "r008",
          "kind": "produce",
          "process_element_id": "e007",
          "outcome_element_id": "e009",
          "relation_type": null,
          "qualifier": "may_lead_to",
          "evidence_unit_ids": [
            "v7u_N001339"
          ],
          "source_quote": "These types of designations are likely to result in financial institutions flagging the member jurisdiction as high risk in their internal risk assessments."
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
      "reason": "该候选描述 FATF 的正式评估及基于缺陷采取行动和监控的流程，支持 episode 中的评估、判断和响应动作。"
    },
    {
      "candidate_id": "s1c_002",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "该候选描述 FATF 基于未达标事实指定名单及可能后果，支持 episode 中的名单指定决策和后果元素。"
    },
    {
      "candidate_id": "s1c_003",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "该候选提供互评估、评级、报告、要求纠正、监控、名单指定和 FI 标记等详细步骤，构成 episode 的主要流程。"
    },
    {
      "candidate_id": "s1c_gap_ch19_s01_monitoring_trends",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选描述 FATF 持续监控资金流动趋势并发布报告的事实，缺少触发条件或业务判断，属于描述性知识内容，不构成流程。"
    },
    {
      "candidate_id": "s1c_gap_ch19_s01_standard_setting_fsrb",
      "disposition": "excluded_nonprocedural",
      "episode_ids": [],
      "reason": "该候选描述 FATF 在标准制定中依赖 FSRB 并保持唯一制定机构地位的事实，属于状态声明，无业务处理或判断迁移，不构成流程。"
    }
  ],
  "skip_reason": null
}
```
