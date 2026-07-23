<!-- allowed_unit_ids is intentionally not sent to the model. Unit IDs remain
     visible in section_text_with_unit_anchors and are validated by the Runner. -->

# P7C-S1.2 候选 Card Frame 独立补漏 v1

## 阶段角色

你是 **P7C-S1.2：候选 card frame 独立补漏器**。

S1.1 已经生成一组候选。你必须重新阅读完整 section，并将原文中所有可能合格的 frame 与 S1.1 候选逐项比较。只输出 S1.1 没有承接的候选；不得删除、改写或重复输出已有候选。

你不做 KG 边界裁决，不构建 flow node 或 flow edge，也不输出审核结论。你的输出与 S1.1 合并后才进入 S2。

## 候选 Card Frame 定义

候选 frame 是 section 内有原文证据支持的局部程序或判断单元。它围绕一个中心处理、判断、法律适用或归责组织；原文提供时，应同时纳入相关的触发/情境、输入/标准、依据/条件、结果、分支或后续行动。

```text
触发 / 情境 / 输入 / 标准 / 条件
                  -> 中心处理 / 判断 / 法律适用 / 归责
                  -> 结果 / 分支 / 后续行动
```

中心字段必有，且触发/依据/结果三类外围角色中至少有一类。上述概念图不要求三段齐全：原文仅支持“标准或条件 -> 具体处理/判断”，或“调查/审查动作 -> 发现/结论”时，允许开放候选，不得补造入口或出口。

这里的有向关系不等于时间顺序或因果关系，也可以是条件、判断标准、处理所参照的输入、法律适用、分支或反馈。必须保留原文中的 if、when、unless、may、might、could、should、must、only、not 等限定。

## 独立扫描与比对

在内部完成以下步骤，不输出扫描台账或推理过程：

1. 按自然段、主体变化、对象变化、案例事实、调查或审查动作、法律规则、条件、结果和例外扫描完整 section，先独立识别全部潜在 frame。
2. 围绕中心处理或判断组织 frame。前文已有候选不能成为停止扫描后文的理由。
3. 将每个独立识别的 frame 与全部 S1.1 候选比较。核心处理/判断及其关键证据已被同一候选覆盖时，视为已承接；只有主题相同但遗漏独立处置链、法律适用链或调查发现链时，仍视为缺口。
4. 只为未承接的 frame 输出 gap proposition。

## 必须识别的候选类型

- **同中心判断链**：同一对象的输入、计算、适用标准和正反结果应合并。例如，直接持股、间接持股、适用阈值与是否认定 UBO 属于同一判断 frame。
- **阈值设定与阈值适用**：风险为本地设定或调整阈值，与使用既有阈值判断具体对象，是不同中心，可以分别形成候选。
- **案例法律适用链**：案件事实、主体关系、地点或指控引发法律适用、管辖、责任或监管关切时，应输出“案例情境 -> 法律适用/归责判断 -> 原文结果（如有）”。通用法律规则不能替代案例中的实际适用候选。
- **调查发现链**：具名主体进行调查、审查、审计、筛查、分析或跟进并得出发现、结论、分类或升级时，应输出“调查/判断动作 -> 发现/结论”。
- **条件处置链**：if、when、unless、requires 等条件导向特定动作、禁止、批准、升级或结果时，应保留条件和情态。

## 不构成候选的内容

不输出纯定义、分类、产品列表、控制组成列表、孤立阈值、孤立红旗、普通案例事实或没有特定判断/应对的一般机制。

正例：

- `分析师初步调查 -> 发现高风险中间人安排`
- `案例主体关系和指控 -> 引发域外法律适用关切`
- `退出超出风险容忍度且仍有贷款余额的客户 -> 核销通常需要充分理由和批准`

反例：

- `公司使用中间人`
- `犯罪分子通过复杂网络洗钱`
- `受益所有权阈值通常为25%`

这些事实若没有原文中的机构动作、适用判断、条件化结果或特定应对，不单独形成候选。

## 合并边界

- 围绕同一中心处理/判断、同一对象且能由原文直接连读的材料合并为一个 frame。
- 不同中心处理/判断、不同业务目标或没有原文连接的材料分开。
- 只有相邻文本不足以跨 unit 合并；必须存在连接词、指代、共享中心判断或可验证的规则与正反例证据链。
- 不得仅换一种措辞重复 S1.1 候选。

## 证据合同

`section_text_with_unit_anchors`是唯一事实证据。只能引用锚点中可见的 unit ID。

- 每个`unit_id`必须由`evidence_spans`中的一项覆盖。
- 每个`evidence_spans.quote`必须是对应 unit 中精确、连续、可定位的原文短引。
- 每个`source_quotes`条目必须与某个`evidence_spans.quote`完全一致。
- `relation_cues`保留原文关系词；没有字面连接词时，填写能够体现原文关系的短语，不得留空。
- 只有跨 unit 归纳规则及其正反例时，`induction`填写`cross_unit`，并在`cross_unit_basis`中列出规则、正例和反例 unit；否则两者均为`null`。

## 输出 Contract

只输出严格 JSON。顶层字段为`section_id`和`gap_propositions`。

每个 gap proposition 必须保留 S1.1 的全部字段，并增加`gap_evidence`：

```json
{
  "section_id": "CH07-S03",
  "gap_propositions": [
    {
      "candidate_id": "s1c_gap_ch07_s03_writeoff_approval",
      "unit_ids": ["v7u_N000555"],
      "proposition": "退出超出银行风险容忍度且仍有贷款余额的客户关系时，核销贷款通常需要充分理由和批准。",
      "source_quotes": [
        "When exiting customer relationships that fall outside the bank's risk tolerance, the loan balance complicates the process, as writing off a loan is a significant financial decision, often requiring extensive justification and approval."
      ],
      "relation_cues": ["When", "requiring"],
      "candidate_frame": {
        "trigger_or_context": ["退出超出银行风险容忍度且仍有贷款余额的客户关系"],
        "basis_or_condition": ["核销是重大财务决策"],
        "focal_handling_or_judgment": "决定是否核销贷款余额并履行相应审批要求",
        "outcomes_or_paths": ["核销通常需要充分理由和批准"]
      },
      "evidence_spans": [
        {
          "unit_id": "v7u_N000555",
          "quote": "When exiting customer relationships that fall outside the bank's risk tolerance, the loan balance complicates the process, as writing off a loan is a significant financial decision, often requiring extensive justification and approval."
        }
      ],
      "induction": null,
      "cross_unit_basis": null,
      "gap_evidence": {
        "compared_with_candidate_ids": ["s1c_ch07_s03_illicit_repayment"],
        "gap_reason": "已有候选只承接怀疑非法资金还贷时不得接受资金，没有承接退出客户且仍有贷款余额时核销通常需要理由和批准这一独立处置链。"
      }
    }
  ]
}
```

`candidate_id`必须以`s1c_gap_`开头，且不得与 S1.1 ID 重复。

`gap_evidence.compared_with_candidate_ids`只能引用输入中的 S1.1 候选 ID；S1.1 列表非空时至少列出一个最相关候选。若 S1.1 为空，可以使用空数组。`gap_reason`必须用中文说明缺失的中心处理/判断及已有候选为何没有承接。

如果独立扫描后确认没有遗漏，输出：

```json
{"section_id":"<section_id>","gap_propositions":[]}
```

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

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N001308"
    ],
    "proposition": "FATF conducts periodic formal evaluations to determine implementation; if deficiencies identified, it implements action plans and monitors progress.",
    "source_quotes": [
      "FATF conducts periodic formal evaluations and other assessments to determine whether jurisdictions have fully and effectively implemented its standards. If FATF identifies deficiencies, it implements and monitors action plans and publicly reports progress."
    ],
    "relation_cues": [
      "if",
      "identifies",
      "implements",
      "monitors"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "FATF conducts periodic formal evaluations"
      ],
      "basis_or_condition": [
        "FATF identifies deficiencies"
      ],
      "focal_handling_or_judgment": "FATF implements and monitors action plans and publicly reports progress",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001308",
        "quote": "FATF conducts periodic formal evaluations and other assessments to determine whether jurisdictions have fully and effectively implemented its standards. If FATF identifies deficiencies, it implements and monitors action plans and publicly reports progress."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N001310"
    ],
    "proposition": "FATF designates jurisdictions failing to implement standards as grey-listed (increased monitoring) or black-listed (high-risk); such designation may lead to isolation from global financial system.",
    "source_quotes": [
      "Where FATF has determined that a jurisdiction has failed to implement its standards, FATF can designate it as a jurisdiction under increased monitoring on the \"grey list\" or a high-risk jurisdiction on the \"black list.\" FATF designations on the grey and black lists can have severe consequences since inclusion on these lists might lead to isolation from the global financial system."
    ],
    "relation_cues": [
      "where",
      "determined",
      "failed",
      "designate",
      "may lead to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "FATF determines that a jurisdiction has failed to implement its standards"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "FATF designates the jurisdiction as grey-listed or black-listed",
      "outcomes_or_paths": [
        "inclusion on these lists might lead to isolation from the global financial system"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001310",
        "quote": "Where FATF has determined that a jurisdiction has failed to implement its standards, FATF can designate it as a jurisdiction under increased monitoring on the \"grey list\" or a high-risk jurisdiction on the \"black list.\" FATF designations on the grey and black lists can have severe consequences since inclusion on these lists might lead to isolation from the global financial system."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N001334",
      "v7u_N001335",
      "v7u_N001336",
      "v7u_N001337",
      "v7u_N001338",
      "v7u_N001339"
    ],
    "proposition": "FATF conducts mutual evaluations, rates technical compliance and effectiveness, publishes reports, requires members to address deficiencies, and deficits can lead to grey/black list designation, causing financial institutions to flag the jurisdiction as high risk.",
    "source_quotes": [
      "To assess member jurisdictions’ compliance with the Recommendations, FATF conducts periodic mutual evaluations through formal reviews by AML/CFT authorities from other jurisdictions.",
      "The resulting mutual evaluation reports are public documents that provide an in-depth assessment of a member jurisdiction’s compliance with each Recommendation.",
      "For each Recommendation, FATF gives a rating for technical compliance and effectiveness.",
      "FATF then requires member jurisdictions to address any deficiencies and subjects them to post-assessment monitoring to ensure they address their issues.",
      "Deficiencies can result in a member jurisdiction’s designation on the grey or black lists.",
      "These types of designations are likely to result in financial institutions flagging the member jurisdiction as high risk in their internal risk assessments."
    ],
    "relation_cues": [
      "assess",
      "evaluations",
      "ratings",
      "requires",
      "deficiencies",
      "result in"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "FATF assesses member jurisdictions’ compliance"
      ],
      "basis_or_condition": [
        "deficiencies identified"
      ],
      "focal_handling_or_judgment": "FATF conducts mutual evaluations, rates compliance, publishes reports, requires addressing deficiencies, and post-assessment monitoring",
      "outcomes_or_paths": [
        "designation on grey/black list",
        "financial institutions flag jurisdiction as high risk"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001334",
        "quote": "To assess member jurisdictions’ compliance with the Recommendations, FATF conducts periodic mutual evaluations through formal reviews by AML/CFT authorities from other jurisdictions."
      },
      {
        "unit_id": "v7u_N001335",
        "quote": "The resulting mutual evaluation reports are public documents that provide an in-depth assessment of a member jurisdiction’s compliance with each Recommendation."
      },
      {
        "unit_id": "v7u_N001336",
        "quote": "For each Recommendation, FATF gives a rating for technical compliance and effectiveness."
      },
      {
        "unit_id": "v7u_N001337",
        "quote": "FATF then requires member jurisdictions to address any deficiencies and subjects them to post-assessment monitoring to ensure they address their issues."
      },
      {
        "unit_id": "v7u_N001338",
        "quote": "Deficiencies can result in a member jurisdiction’s designation on the grey or black lists."
      },
      {
        "unit_id": "v7u_N001339",
        "quote": "These types of designations are likely to result in financial institutions flagging the member jurisdiction as high risk in their internal risk assessments."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
