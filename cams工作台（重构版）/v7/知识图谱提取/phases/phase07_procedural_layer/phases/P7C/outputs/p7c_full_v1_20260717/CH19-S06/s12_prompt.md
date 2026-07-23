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

section_id: `CH19-S06`

section_title: `Financial Action Task Force > FATF high-risk and noncooperative jurisdictions`

section_text_with_unit_anchors:

```text
[v7u_N001412|1412] FATF identifies high-risk and noncooperative jurisdictions through a comprehensive review process. FATF’s International Cooperation Review Group oversees this process and assesses a jurisdiction's AML/CFT measures to identify threats, vulnerabilities, and risks.
ZH: FATF通过全面审查流程识别高风险和不合作司法管辖区

[v7u_N001413|1413] FATF reviews jurisdictions for many reasons it deems indicative of noncooperation. Specifically, FATF will review a jurisdiction when it:
ZH: FATF因多种原因审查司法管辖区，具体情形包括

[v7u_N001414|1414] Does not participate in an FSRB.
ZH: 不参与区域性反洗钱组织

[v7u_N001415|1415] Delays or does not allow an FSRB to publish mutual evaluation results.
ZH: 延迟或不允许区域性反洗钱组织发布互评估结果

[v7u_N001416|1416] Is nominated by a FATF member or an FSRB that identifies money laundering, terrorist financing, or proliferation financing risks or threats.
ZH: 被FATF成员或区域性反洗钱组织提名存在洗钱、恐怖融资或扩散融资风险

[v7u_N001417|1417] Achieves poor results in its mutual evaluation, such as:
ZH: 互评估结果不佳，例如

[v7u_N001418|1418] Having 20 or more noncompliant or partially compliant ratings for technical compliance.
ZH: 技术合规性方面有20项或更多不合规或部分合规评级

[v7u_N001419|1419] Receiving ratings of noncompliant or partially compliant on three or more of Recommendations 3, 5, 6, 10, 11, and 20.
ZH: 建议3、5、6、10、11和20中有三项或更多被评为不合规或部分合规

[v7u_N001420|1420] Having a low or moderate level of effectiveness for 9 or more of the 11 IOs, with a minimum of two lows.
ZH: 11项立即成果中有9项或更多有效性评级为低或中等，且至少两项为低

[v7u_N001421|1421] Having a low level of effectiveness for 6 or more of the 11 IOs.
ZH: FATF 11项有效性指标中6项以上评级低的司法管辖区

[v7u_N001422|1422] FATF provides 25 criteria that help identify relevant detrimental rules and practices that are inconsistent with the 40 Recommendations. The criteria are categorized into four broad areas:
ZH: FATF 25条标准分为四大类，用于识别与40项建议不一致的规则和做法

[v7u_N001423|1423] Loopholes in financial regulations
ZH: 金融监管漏洞是FATF识别的有害规则之一

[v7u_N001424|1424] Obstacles raised by other regulatory requirements
ZH: 其他监管要求造成的障碍是FATF识别的有害规则之一

[v7u_N001425|1425] Obstacles to international cooperation
ZH: 国际合作障碍是FATF识别的有害规则之一

[v7u_N001426|1426] Inadequate resources for preventing and detecting money laundering activities
ZH: 预防和检测洗钱活动的资源不足是FATF识别的有害规则之一

[v7u_N001427|1427] Based on these criteria, FATF officially identifies noncooperative jurisdictions and territories in two public documents it publishes three times a year.
ZH: FATF根据25条标准每年三次发布不合作司法管辖区名单

[v7u_N001428|1428] The list is called the "grey list." It identifies jurisdictions with strategic deficiencies in their AML/CFT systems that are actively working with FATF to address these issues.
ZH: FATF灰名单指在反洗钱/反恐怖融资体系存在战略缺陷但正积极整改的司法管辖区

[v7u_N001429|1429] The list is called the "black list." It identifies jurisdictions with significant AML/CFT deficiencies, prompting all FATF members to apply enhanced due diligence (EDD) and potentially take countermeasures against them.
ZH: FATF黑名单指反洗钱/反恐怖融资缺陷严重，需采取强化尽职调查和反制措施的司法管辖区
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N001412",
      "v7u_N001413",
      "v7u_N001414",
      "v7u_N001415",
      "v7u_N001416",
      "v7u_N001417",
      "v7u_N001418",
      "v7u_N001419",
      "v7u_N001420",
      "v7u_N001421"
    ],
    "proposition": "FATF通过审查流程识别高风险和不合作司法管辖区；当司法管辖区不参与FSRB、延迟公布互评估结果、被提名存在风险、互评估结果不佳（如20+不合规、部分建议3+不合规、有效性低等）时启动审查。",
    "source_quotes": [
      "FATF identifies high-risk and noncooperative jurisdictions through a comprehensive review process. FATF’s International Cooperation Review Group oversees this process and assesses a jurisdiction's AML/CFT measures to identify threats, vulnerabilities, and risks.",
      "FATF reviews jurisdictions for many reasons it deems indicative of noncooperation. Specifically, FATF will review a jurisdiction when it:",
      "Does not participate in an FSRB.",
      "Delays or does not allow an FSRB to publish mutual evaluation results.",
      "Is nominated by a FATF member or an FSRB that identifies money laundering, terrorist financing, or proliferation financing risks or threats.",
      "Achieves poor results in its mutual evaluation, such as:",
      "Having 20 or more noncompliant or partially compliant ratings for technical compliance.",
      "Receiving ratings of noncompliant or partially compliant on three or more of Recommendations 3, 5, 6, 10, 11, and 20.",
      "Having a low or moderate level of effectiveness for 9 or more of the 11 IOs, with a minimum of two lows.",
      "Having a low level of effectiveness for 6 or more of the 11 IOs."
    ],
    "relation_cues": [
      "identifies",
      "reviews",
      "does not",
      "delays",
      "is nominated",
      "achieves poor results",
      "having",
      "receiving"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "FATF的全面审查流程"
      ],
      "basis_or_condition": [
        "不参与FSRB",
        "延迟或不允许FSRB发布互评估结果",
        "被FATF成员或FSRB提名存在洗钱、恐怖融资或扩散融资风险",
        "互评估结果不佳，包括：技术合规20+不合规/部分合规",
        "建议3,5,6,10,11,20中3+不合规/部分合规",
        "11项IO中9+低或中等且至少2低",
        "11项IO中6+低"
      ],
      "focal_handling_or_judgment": "审查并识别高风险和不合作司法管辖区",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001412",
        "quote": "FATF identifies high-risk and noncooperative jurisdictions through a comprehensive review process. FATF’s International Cooperation Review Group oversees this process and assesses a jurisdiction's AML/CFT measures to identify threats, vulnerabilities, and risks."
      },
      {
        "unit_id": "v7u_N001413",
        "quote": "FATF reviews jurisdictions for many reasons it deems indicative of noncooperation. Specifically, FATF will review a jurisdiction when it:"
      },
      {
        "unit_id": "v7u_N001414",
        "quote": "Does not participate in an FSRB."
      },
      {
        "unit_id": "v7u_N001415",
        "quote": "Delays or does not allow an FSRB to publish mutual evaluation results."
      },
      {
        "unit_id": "v7u_N001416",
        "quote": "Is nominated by a FATF member or an FSRB that identifies money laundering, terrorist financing, or proliferation financing risks or threats."
      },
      {
        "unit_id": "v7u_N001417",
        "quote": "Achieves poor results in its mutual evaluation, such as:"
      },
      {
        "unit_id": "v7u_N001418",
        "quote": "Having 20 or more noncompliant or partially compliant ratings for technical compliance."
      },
      {
        "unit_id": "v7u_N001419",
        "quote": "Receiving ratings of noncompliant or partially compliant on three or more of Recommendations 3, 5, 6, 10, 11, and 20."
      },
      {
        "unit_id": "v7u_N001420",
        "quote": "Having a low or moderate level of effectiveness for 9 or more of the 11 IOs, with a minimum of two lows."
      },
      {
        "unit_id": "v7u_N001421",
        "quote": "Having a low level of effectiveness for 6 or more of the 11 IOs."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N001422",
      "v7u_N001423",
      "v7u_N001424",
      "v7u_N001425",
      "v7u_N001426"
    ],
    "proposition": "FATF提供25条标准，分为四类，用于识别与40项建议不一致的有害规则和做法：金融监管漏洞、其他监管要求造成的障碍、国际合作障碍、预防和检测洗钱活动资源不足。",
    "source_quotes": [
      "FATF provides 25 criteria that help identify relevant detrimental rules and practices that are inconsistent with the 40 Recommendations. The criteria are categorized into four broad areas:",
      "Loopholes in financial regulations",
      "Obstacles raised by other regulatory requirements",
      "Obstacles to international cooperation",
      "Inadequate resources for preventing and detecting money laundering activities"
    ],
    "relation_cues": [
      "provides",
      "help identify",
      "categorized into"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "需要识别与40项建议不一致的有害规则和做法"
      ],
      "basis_or_condition": [
        "25条标准，分为四类：金融监管漏洞、其他监管要求造成的障碍、国际合作障碍、预防和检测洗钱活动资源不足"
      ],
      "focal_handling_or_judgment": "根据25条标准识别有害规则和做法",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001422",
        "quote": "FATF provides 25 criteria that help identify relevant detrimental rules and practices that are inconsistent with the 40 Recommendations. The criteria are categorized into four broad areas:"
      },
      {
        "unit_id": "v7u_N001423",
        "quote": "Loopholes in financial regulations"
      },
      {
        "unit_id": "v7u_N001424",
        "quote": "Obstacles raised by other regulatory requirements"
      },
      {
        "unit_id": "v7u_N001425",
        "quote": "Obstacles to international cooperation"
      },
      {
        "unit_id": "v7u_N001426",
        "quote": "Inadequate resources for preventing and detecting money laundering activities"
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N001427",
      "v7u_N001428",
      "v7u_N001429"
    ],
    "proposition": "FATF根据25条标准每年三次发布不合作司法管辖区名单：灰名单（AML/CFT体系有战略缺陷但正积极整改）和黑名单（缺陷严重，要求所有成员强化尽调并可能采取反制措施）。",
    "source_quotes": [
      "Based on these criteria, FATF officially identifies noncooperative jurisdictions and territories in two public documents it publishes three times a year.",
      "The list is called the \"grey list.\" It identifies jurisdictions with strategic deficiencies in their AML/CFT systems that are actively working with FATF to address these issues.",
      "The list is called the \"black list.\" It identifies jurisdictions with significant AML/CFT deficiencies, prompting all FATF members to apply enhanced due diligence (EDD) and potentially take countermeasures against them."
    ],
    "relation_cues": [
      "Based on",
      "identifies",
      "prompting"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "根据25条标准"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "发布不合作司法管辖区名单（灰名单和黑名单）",
      "outcomes_or_paths": [
        "灰名单：有战略缺陷但积极整改",
        "黑名单：重大缺陷，要求强化尽调和可能反制"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001427",
        "quote": "Based on these criteria, FATF officially identifies noncooperative jurisdictions and territories in two public documents it publishes three times a year."
      },
      {
        "unit_id": "v7u_N001428",
        "quote": "The list is called the \"grey list.\" It identifies jurisdictions with strategic deficiencies in their AML/CFT systems that are actively working with FATF to address these issues."
      },
      {
        "unit_id": "v7u_N001429",
        "quote": "The list is called the \"black list.\" It identifies jurisdictions with significant AML/CFT deficiencies, prompting all FATF members to apply enhanced due diligence (EDD) and potentially take countermeasures against them."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
