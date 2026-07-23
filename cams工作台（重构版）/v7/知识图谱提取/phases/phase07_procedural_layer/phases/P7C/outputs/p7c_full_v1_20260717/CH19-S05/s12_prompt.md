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

section_id: `CH19-S05`

section_title: `Financial Action Task Force > FATF 11 Immediate Outcomes`

section_text_with_unit_anchors:

```text
[v7u_N001382|1382] Mutual evaluation reports of member jurisdictions focus on two areas: technical compliance with the FATF Recommendations and the effectiveness of the jurisdiction's overall program.
ZH: FATF互评估报告关注技术合规性和反洗钱体系有效性两大领域。

[v7u_N001383|1383] FATF measures and rates effectiveness using 11 Immediate Outcomes (IOs), with each IO receiving an effectiveness rating of low, moderate, substantial, or high.
ZH: FATF使用11项直接目标（IO）评估有效性，评级分为低、中、显著、高。

[v7u_N001384|1384] For jurisdictions that FATF rates as having low or moderate effectiveness in IOs, FATF provides key recommended actions and tracks the jurisdiction's progress in meeting the recommendations.
ZH: FATF对有效性评级为低或中的司法管辖区提出关键建议并跟踪改进进展。

[v7u_N001385|1385] FATF’s IOs are not meant to be a checklist, but rather a starting point to assist assessors in determining the effectiveness of a jurisdiction's AML/CFT framework. FATF expects assessors to use their judgment and experience in determining their ratings.
ZH: FATF的直接目标并非检查清单，而是评估人员判断反洗钱/反恐怖融资框架有效性的起点。

[v7u_N001386|1386] The table below lists the area of focus and specific outcomes associated with each of the 11 IOs:
ZH: 表格列出了11项直接目标的重点领域和具体成果。

[v7u_N001387|1387] FATF mutual evaluations are peer reviews between FATF member jurisdictions that result in thorough reports that analyze AML procedures and their effectiveness.
ZH: FATF互评估是成员国之间的同行评审，生成分析反洗钱程序及其有效性的详细报告。

[v7u_N001388|1388] A typical report provides an in-depth description and analysis of a jurisdiction’s legal and regulatory framework for preventing criminal abuse of its financial system.
ZH: 典型互评估报告深入描述和分析司法管辖区防止金融系统被犯罪滥用的法律和监管框架。

[v7u_N001389|1389] The report also includes recommendations for jurisdictions to strengthen their capabilities.
ZH: 互评估报告还包括加强司法管辖区能力的建议。

[v7u_N001390|1390] Mutual evaluations are strict, meaning each jurisdiction is only deemed compliant when it can prove the same to other FATF members.
ZH: 互评估要求严格，司法管辖区必须向其他FATF成员证明其合规才能被视为合规。

[v7u_N001391|1391] FATF mutual evaluations have two basic components. The main component is effectiveness and is the focus of an on-site visit to the assessed jurisdiction. During the visit, the assessment team collects evidence demonstrating that the jurisdiction’s measures are operational and deliver the right results.
ZH: FATF互评估有两个基本组成部分，主要部分是有效性，通过现场访问收集证据。

[v7u_N001392|1392] The second component is technical compliance.
ZH: 互评估的第二部分是技术合规性。

[v7u_N001393|1393] The assessed member must provide information on its laws and regulations to combat money laundering and the proliferation of weapons of mass destruction.
ZH: 被评估成员必须提供其打击洗钱和大规模杀伤性武器扩散的法律法规信息。

[v7u_N001394|1394] The goal of technical compliance has been the main focus of FATF.
ZH: 技术合规性曾是FATF的主要关注点。

[v7u_N001395|1395] However, numerous money laundering scandals demonstrated that technical compliance was insufficient, and the main focus was shifted to AML effectiveness.
ZH: 多起洗钱丑闻表明技术合规性不足，FATF重点转向反洗钱有效性。

[v7u_N001396|1396] Expectations about FATF mutual evaluations differ from jurisdiction to jurisdiction, based on AML and other financial crime risks.
ZH: 对FATF互评估的期望因司法管辖区而异，取决于反洗钱及其他金融犯罪风险。

[v7u_N001397|1397] The organization has developed an elaborate assessment methodology to ensure consistent, fair assessments.
ZH: FATF制定了详细的评估方法以确保评估一致、公平。

[v7u_N001398|1398] A complete mutual evaluation takes an average of 18 months.
ZH: 一次完整的互评估平均需要18个月。

[v7u_N001399|1399] The mutual evaluation process has seven stages.
ZH: 互评估流程包含七个阶段。

[v7u_N001400|1400] Getting started:
ZH: 互评估流程的第一个阶段是“开始”。

[v7u_N001401|1401] Assessor training: Training for the experts who will perform assessment
ZH: 评估员培训：为执行评估的专家提供培训

[v7u_N001402|1402] Jurisdiction training: Training for representatives of the evaluated jurisdictions
ZH: 司法管辖区培训：为被评估司法管辖区的代表提供培训

[v7u_N001403|1403] Selection of assessors: Selection of the experts that form the assessment team
ZH: 评估员遴选：选择组成评估团队的专家

[v7u_N001404|1404] Technical review: Assessment team analyzes the jurisdiction’s laws and regulations
ZH: 技术审查：评估团队分析司法管辖区的法律法规

[v7u_N001405|1405] Scoping note: Assessment team identifies areas of focus for the on-site visit
ZH: 范围界定说明：评估团队确定现场访问的重点领域

[v7u_N001406|1406] On-site visit: Assessment team travels to the jurisdiction and reviews the effectiveness of AML regulations
ZH: 现场访问：评估团队前往司法管辖区审查反洗钱法规的有效性

[v7u_N001407|1407] Draft MER: Finalize mutual evaluation report
ZH: 起草互评估报告：完成互评估报告

[v7u_N001408|1408] FATF plenary adoption:
ZH: FATF全体会议通过：互评估报告提交全体会议审议

[v7u_N001409|1409] Plenary discussion: FATF plenary discusses the findings in the report and votes on the ratings
ZH: 全体会议讨论：FATF全体会议讨论报告中的发现并对评级进行投票

[v7u_N001410|1410] Final quality review: All jurisdictions review the report before publishing
ZH: 最终质量审查：所有司法管辖区在报告发布前进行审查

[v7u_N001411|1411] Publication and follow-up: Jurisdiction addresses issues and begins strengthening its AML measures
ZH: 发布与后续行动：司法管辖区解决问题并开始加强反洗钱措施
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N001384"
    ],
    "proposition": "FATF对IOs有效性评级低或中的司法管辖区提供关键建议并跟踪其改进进展。",
    "source_quotes": [
      "For jurisdictions that FATF rates as having low or moderate effectiveness in IOs, FATF provides key recommended actions and tracks the jurisdiction's progress in meeting the recommendations."
    ],
    "relation_cues": [
      "rates",
      "provides",
      "tracks"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "FATF对司法管辖区IOs有效性评级为低或中"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "FATF提供关键建议并跟踪该司法管辖区在满足建议方面的进展。",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001384",
        "quote": "For jurisdictions that FATF rates as having low or moderate effectiveness in IOs, FATF provides key recommended actions and tracks the jurisdiction's progress in meeting the recommendations."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N001385"
    ],
    "proposition": "FATF的直接目标作为起点，评估者使用判断和经验确定司法管辖区AML/CFT框架的有效性评级。",
    "source_quotes": [
      "FATF’s IOs are not meant to be a checklist, but rather a starting point to assist assessors in determining the effectiveness of a jurisdiction's AML/CFT framework. FATF expects assessors to use their judgment and experience in determining their ratings."
    ],
    "relation_cues": [
      "not meant",
      "starting point",
      "assist",
      "expects",
      "use"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "FATF的IOs作为评估起点"
      ],
      "basis_or_condition": [
        "评估者的判断和经验"
      ],
      "focal_handling_or_judgment": "评估者确定司法管辖区AML/CFT框架的有效性评级",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001385",
        "quote": "FATF’s IOs are not meant to be a checklist, but rather a starting point to assist assessors in determining the effectiveness of a jurisdiction's AML/CFT framework. FATF expects assessors to use their judgment and experience in determining their ratings."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N001390"
    ],
    "proposition": "司法管辖区只有向其他FATF成员证明其合规，才被视为合规。",
    "source_quotes": [
      "Mutual evaluations are strict, meaning each jurisdiction is only deemed compliant when it can prove the same to other FATF members."
    ],
    "relation_cues": [
      "strict",
      "only",
      "when"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "司法管辖区能够向其他FATF成员证明其合规"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "该司法管辖区被视为合规",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001390",
        "quote": "Mutual evaluations are strict, meaning each jurisdiction is only deemed compliant when it can prove the same to other FATF members."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N001391"
    ],
    "proposition": "现场访问期间，评估团队收集证据以证明司法管辖区的措施已运行并产生正确结果。",
    "source_quotes": [
      "During the visit, the assessment team collects evidence demonstrating that the jurisdiction’s measures are operational and deliver the right results."
    ],
    "relation_cues": [
      "during",
      "collects",
      "demonstrating"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "现场访问期间"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "评估团队收集证据证明司法管辖区的措施已运行并产生正确结果",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001391",
        "quote": "During the visit, the assessment team collects evidence demonstrating that the jurisdiction’s measures are operational and deliver the right results."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N001404"
    ],
    "proposition": "技术审查阶段，评估团队分析司法管辖区的法律法规。",
    "source_quotes": [
      "Technical review: Assessment team analyzes the jurisdiction’s laws and regulations"
    ],
    "relation_cues": [
      "analyzes"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "司法管辖区的法律法规"
      ],
      "focal_handling_or_judgment": "评估团队进行分析",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001404",
        "quote": "Technical review: Assessment team analyzes the jurisdiction’s laws and regulations"
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N001405"
    ],
    "proposition": "范围界定说明中，评估团队确定现场访问的重点领域。",
    "source_quotes": [
      "Scoping note: Assessment team identifies areas of focus for the on-site visit"
    ],
    "relation_cues": [
      "identifies"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "评估团队确定重点领域",
      "outcomes_or_paths": [
        "现场访问的重点领域"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001405",
        "quote": "Scoping note: Assessment team identifies areas of focus for the on-site visit"
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_007",
    "unit_ids": [
      "v7u_N001406"
    ],
    "proposition": "现场访问中，评估团队前往司法管辖区并审查反洗钱法规的有效性。",
    "source_quotes": [
      "On-site visit: Assessment team travels to the jurisdiction and reviews the effectiveness of AML regulations"
    ],
    "relation_cues": [
      "travels",
      "reviews"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "现场访问"
      ],
      "basis_or_condition": [
        "反洗钱法规"
      ],
      "focal_handling_or_judgment": "评估团队前往并审查有效性",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001406",
        "quote": "On-site visit: Assessment team travels to the jurisdiction and reviews the effectiveness of AML regulations"
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_008",
    "unit_ids": [
      "v7u_N001407"
    ],
    "proposition": "起草MER阶段完成互评估报告。",
    "source_quotes": [
      "Draft MER: Finalize mutual evaluation report"
    ],
    "relation_cues": [
      "Finalize"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "完成互评估报告",
      "outcomes_or_paths": [
        "互评估报告"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001407",
        "quote": "Draft MER: Finalize mutual evaluation report"
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_009",
    "unit_ids": [
      "v7u_N001409"
    ],
    "proposition": "全体会议讨论报告发现并对评级投票。",
    "source_quotes": [
      "Plenary discussion: FATF plenary discusses the findings in the report and votes on the ratings"
    ],
    "relation_cues": [
      "discusses",
      "votes on"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "FATF全体会议"
      ],
      "basis_or_condition": [
        "报告中的发现"
      ],
      "focal_handling_or_judgment": "讨论发现并对评级投票",
      "outcomes_or_paths": [
        "评级结果"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001409",
        "quote": "Plenary discussion: FATF plenary discusses the findings in the report and votes on the ratings"
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_010",
    "unit_ids": [
      "v7u_N001410"
    ],
    "proposition": "最终质量审查阶段，所有司法管辖区在报告发布前进行审查。",
    "source_quotes": [
      "Final quality review: All jurisdictions review the report before publishing"
    ],
    "relation_cues": [
      "review",
      "before publishing"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "报告发布前"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "所有司法管辖区审查报告",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001410",
        "quote": "Final quality review: All jurisdictions review the report before publishing"
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_011",
    "unit_ids": [
      "v7u_N001411"
    ],
    "proposition": "发布与后续行动阶段，司法管辖区解决问题并开始加强反洗钱措施。",
    "source_quotes": [
      "Publication and follow-up: Jurisdiction addresses issues and begins strengthening its AML measures"
    ],
    "relation_cues": [
      "addresses",
      "begins strengthening"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "报告发布后"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "司法管辖区解决问题并加强反洗钱措施",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001411",
        "quote": "Publication and follow-up: Jurisdiction addresses issues and begins strengthening its AML measures"
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
