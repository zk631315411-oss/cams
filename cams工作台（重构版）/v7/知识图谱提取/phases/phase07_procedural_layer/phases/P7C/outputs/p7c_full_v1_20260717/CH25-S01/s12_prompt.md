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

section_id: `CH25-S01`

section_title: `Other AFC regulations that impact organizations > Major ABC regulations`

section_text_with_unit_anchors:

```text
[v7u_N001963|1963] Anti-bribery and corruption (ABC) compliance is an important area of AFC compliance because corruption remains a major source of criminal proceeds and is a key predicate offense for money laundering.
ZH: 反贿赂与反腐败合规是金融犯罪防控的重要领域，腐败是洗钱的主要上游犯罪

[v7u_N001964|1964] Most jurisdictions criminalize bribery and corruption through domestic legislation, yet only a fraction of them have enacted ABC laws and regulations.
ZH: 大多数司法管辖区通过国内立法将贿赂和腐败定为犯罪，但只有少数制定了ABC法律

[v7u_N001965|1965] The US, UK, and France have their own legislative frameworks on ABC. All three frameworks have extraterritorial reach.
ZH: 美国、英国和法国拥有各自的ABC立法框架，且均具有域外效力

[v7u_N001966|1966] In 1997, the US enacted the Foreign Corrupt Practices Act (FCPA).
ZH: 美国于1997年颁布《反海外腐败法》

[v7u_N001967|1967] Under this law, it is illegal for all US persons and certain foreign securities issuers to make payments to foreign government officials to assist them in obtaining or retaining business.
ZH: FCPA禁止美国人和特定外国证券发行人向外国政府官员支付款项以获取或保留业务

[v7u_N001968|1968] Since 1998, it has also applied to foreign firms and persons who, directly or indirectly, cause acts of corruption within the US.
ZH: 自1998年起，FCPA也适用于在美国境内直接或间接实施腐败行为的外国公司和个人

[v7u_N001969|1969] In effect since July 2024, the Foreign Extortion Prevention Technical Corrections Act complements the FCPA by criminalizing the acceptance of bribes by foreign officials and their agents.
ZH: 《外国敲诈预防技术修正案》于2024年7月生效，将外国官员及其代理人收受贿赂定为犯罪

[v7u_N001970|1970] Unlike the UK and French legislation, the FCPA’s bribery provisions generally exempt facilitation payments if they are made solely to expedite a routine official action that would occur even without the payment.
ZH: FCPA的贿赂条款通常豁免仅为加快例行公务行动而支付的便利费

[v7u_N001971|1971] In 2011, the UK enacted the Bribery Act 2010.
ZH: 英国于2011年颁布《2010年反贿赂法》

[v7u_N001972|1972] This act sets out the five key UK bribery offenses.
ZH: 该法案规定了五项主要的英国贿赂罪行

[v7u_N001973|1973] It also introduced strict liability for commercial entities that engage in bribery through associated persons, unless the entity can demonstrate it has sufficient anti-bribery safeguards.
ZH: 该法案对通过关联人实施贿赂的商业实体引入严格责任，除非能证明有充分的防贿赂保障措施

[v7u_N001974|1974] According to the UK government’s statutory guidance, these safeguards must include proportionate procedures, senior management commitment, risk assessment, due diligence, communication that includes training, and monitoring and review.
ZH: 防贿赂保障措施必须包括相称程序、高层承诺、风险评估、尽职调查、培训沟通以及监测审查

[v7u_N001975|1975] In 2016, France enacted their anticorruption law known as Sapin II, named after the minister who initiated the law.
ZH: 法国于2016年颁布了名为Sapin II的反腐败法

[v7u_N001976|1976] For large companies and public entities, Sapin II introduced an obligation to have an anticorruption program meeting specific criteria.
ZH: Sapin II要求大型公司和公共实体制定符合特定标准的反腐败计划

[v7u_N001977|1977] This law also established the French Anticorruption Agency to oversee anticorruption efforts in both the private and public sectors.
ZH: 该法设立了法国反腐败局，负责监督私营和公共部门的反腐败工作

[v7u_N001978|1978] This agency can impose administrative penalties and refer findings to the National Financial Prosecutor’s Office.
ZH: 该局可实施行政处罚并将调查结果移送国家金融检察官办公室

[v7u_N001979|1979] Additionally, Sapin II created a novel mechanism for resolving corruption cases through deferred prosecution agreements.
ZH: Sapin II创建了通过暂缓起诉协议解决腐败案件的新机制
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N001967"
    ],
    "proposition": "FCPA禁止美国人和特定外国证券发行人向外国政府官员支付款项以获取或保留业务。",
    "source_quotes": [
      "Under this law, it is illegal for all US persons and certain foreign securities issuers to make payments to foreign government officials to assist them in obtaining or retaining business."
    ],
    "relation_cues": [
      "illegal",
      "to assist"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "为获取或保留业务"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "禁止向外国政府官员支付款项",
      "outcomes_or_paths": [
        "构成违法"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001967",
        "quote": "Under this law, it is illegal for all US persons and certain foreign securities issuers to make payments to foreign government officials to assist them in obtaining or retaining business."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N001968"
    ],
    "proposition": "自1998年起，FCPA也适用于在美国境内直接或间接实施腐败行为的外国公司和个人。",
    "source_quotes": [
      "Since 1998, it has also applied to foreign firms and persons who, directly or indirectly, cause acts of corruption within the US."
    ],
    "relation_cues": [
      "applied to",
      "within the US"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "外国公司或个人在美国境内直接或间接实施腐败行为"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "FCPA法律适用于该外国公司或个人",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001968",
        "quote": "Since 1998, it has also applied to foreign firms and persons who, directly or indirectly, cause acts of corruption within the US."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N001969"
    ],
    "proposition": "《外国敲诈预防技术修正案》将外国官员及其代理人收受贿赂定为犯罪。",
    "source_quotes": [
      "the Foreign Extortion Prevention Technical Corrections Act complements the FCPA by criminalizing the acceptance of bribes by foreign officials and their agents."
    ],
    "relation_cues": [
      "criminalizing"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "外国官员及其代理人收受贿赂"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "将该行为定为犯罪",
      "outcomes_or_paths": [
        "构成犯罪"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001969",
        "quote": "the Foreign Extortion Prevention Technical Corrections Act complements the FCPA by criminalizing the acceptance of bribes by foreign officials and their agents."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N001970"
    ],
    "proposition": "FCPA的贿赂条款通常豁免仅为加快例行公务行动而支付的便利费。",
    "source_quotes": [
      "the FCPA’s bribery provisions generally exempt facilitation payments if they are made solely to expedite a routine official action that would occur even without the payment."
    ],
    "relation_cues": [
      "exempt",
      "if",
      "solely to expedite"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "支付便利费以加快例行公务行动"
      ],
      "basis_or_condition": [
        "支付仅为加快例行公务行动且即使不支付也会发生"
      ],
      "focal_handling_or_judgment": "豁免该便利费，不适用FCPA贿赂条款",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001970",
        "quote": "the FCPA’s bribery provisions generally exempt facilitation payments if they are made solely to expedite a routine official action that would occur even without the payment."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N001973"
    ],
    "proposition": "英国《2010年反贿赂法》对通过关联人实施贿赂的商业实体引入严格责任，除非该实体能证明有充分的防贿赂保障措施。",
    "source_quotes": [
      "It also introduced strict liability for commercial entities that engage in bribery through associated persons, unless the entity can demonstrate it has sufficient anti-bribery safeguards."
    ],
    "relation_cues": [
      "strict liability",
      "unless",
      "demonstrate"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "商业实体通过关联人实施贿赂"
      ],
      "basis_or_condition": [
        "除非实体能证明有充分的防贿赂保障措施"
      ],
      "focal_handling_or_judgment": "商业实体承担严格责任",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001973",
        "quote": "It also introduced strict liability for commercial entities that engage in bribery through associated persons, unless the entity can demonstrate it has sufficient anti-bribery safeguards."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N001974"
    ],
    "proposition": "根据英国政府法定指导意见，反贿赂保障措施必须包括相称程序、高层承诺、风险评估、尽职调查、培训沟通以及监测审查。",
    "source_quotes": [
      "these safeguards must include proportionate procedures, senior management commitment, risk assessment, due diligence, communication that includes training, and monitoring and review."
    ],
    "relation_cues": [
      "must include"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "存在反贿赂保障措施要求"
      ],
      "basis_or_condition": [
        "英国政府法定指导意见"
      ],
      "focal_handling_or_judgment": "保障措施必须包含六大要素",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001974",
        "quote": "these safeguards must include proportionate procedures, senior management commitment, risk assessment, due diligence, communication that includes training, and monitoring and review."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_007",
    "unit_ids": [
      "v7u_N001976"
    ],
    "proposition": "Sapin II要求大型公司和公共实体制定符合特定标准的反腐败计划。",
    "source_quotes": [
      "For large companies and public entities, Sapin II introduced an obligation to have an anticorruption program meeting specific criteria."
    ],
    "relation_cues": [
      "obligation",
      "meeting specific criteria"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "大型公司和公共实体"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "必须制定符合特定标准的反腐败计划",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001976",
        "quote": "For large companies and public entities, Sapin II introduced an obligation to have an anticorruption program meeting specific criteria."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_008",
    "unit_ids": [
      "v7u_N001978"
    ],
    "proposition": "法国反腐败局可实施行政处罚并将调查结果移送国家金融检察官办公室。",
    "source_quotes": [
      "This agency can impose administrative penalties and refer findings to the National Financial Prosecutor’s Office."
    ],
    "relation_cues": [
      "can impose",
      "refer"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "存在腐败相关调查结果"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "法国反腐败局实施行政处罚或移送检察官",
      "outcomes_or_paths": [
        "行政处罚",
        "移送检察"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001978",
        "quote": "This agency can impose administrative penalties and refer findings to the National Financial Prosecutor’s Office."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_009",
    "unit_ids": [
      "v7u_N001979"
    ],
    "proposition": "Sapin II创建了通过暂缓起诉协议解决腐败案件的新机制。",
    "source_quotes": [
      "Sapin II created a novel mechanism for resolving corruption cases through deferred prosecution agreements."
    ],
    "relation_cues": [
      "created",
      "through"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "腐败案件"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "适用暂缓起诉协议机制解决",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001979",
        "quote": "Sapin II created a novel mechanism for resolving corruption cases through deferred prosecution agreements."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
