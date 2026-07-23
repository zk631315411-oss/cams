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

section_id: `CH24-S02`

section_title: `US AML/CFT regulatory landscape > USA PATRIOT Act`

section_text_with_unit_anchors:

```text
[v7u_N001701|1701] In 2001, the US enacted the Uniting and Strengthening America by Providing Appropriate Tools Required to Intercept and Obstruct Terrorism Act (USA PATRIOT Act).
ZH: 2001年美国颁布《爱国者法案》

[v7u_N001702|1702] This Act introduced significant AFC regulatory obligations that have influenced global financial regulations. It strengthened AML/CFT measures, impacting financial institutions worldwide.
ZH: 《爱国者法案》引入重大金融犯罪防控义务，强化反洗钱与反恐怖融资措施

[v7u_N001703|1703] Key global obligations derived from the USA PATRIOT Act include the following topics.
ZH: 《爱国者法案》衍生的关键全球义务列表导引

[v7u_N001704|1704] CDD and KYC: Financial institutions must verify customer identities, monitor transactions, and assess risks associated with business relationships. This requirement has influenced global AML frameworks, such as the FATF Recommendations.
ZH: 金融机构须验证客户身份、监控交易并评估风险，影响全球反洗钱框架

[v7u_N001705|1705] Jurisdictions of primary money laundering concern: Under section 311, the US Department of the Treasury can designate foreign jurisdictions, institutions, or transactions as money laundering risks, prompting actions by financial institutions. Designating a jurisdiction or financial organization forces banks to halt financial dealings with the designee.
ZH: 美国财政部可指定外国司法管辖区或机构为洗钱风险，迫使银行停止交易

[v7u_N001706|1706] EDD for foreign correspondent banking: Section 313 prohibits relationships with shell banks and Section 312 mandates EDD for correspondent accounts held by foreign financial institutions, affecting cross-border banking practices. Section 312 also applies to private banking accounts for non-US persons.
ZH: 第313条禁止与空壳银行往来，第312条要求对外国金融机构代理账户实施强化尽职调查

[v7u_N001707|1707] Forfeiture from US correspondent account: This Act permits the US government to seize funds from a correspondent account in the US that a foreign bank has opened and maintained. The owner of the funds may contest the seizure.
ZH: 允许美国政府扣押外国银行在美国代理账户中的资金，资金所有者可提出异议

[v7u_N001708|1708] Information sharing: Section 314 allows banks to cooperate with each other, law enforcement, and international agencies to combat financial crime. It provides institutions with safe harbor liability protections for sharing information.
ZH: 第314条允许银行与执法机构及国际机构共享信息，并提供安全港保护

[v7u_N001709|1709] Records relating to correspondent accounts for foreign banks: This Act allows the US government to request the production of various types of records, provides subpoena authority for correspondent accounts of foreign banks, and requires foreign banks to designate a registered agent in the US.
ZH: 美国政府可要求外国银行提供代理账户记录，并指定在美国的注册代理人
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N001705"
    ],
    "proposition": "根据第311条，美国财政部可将外国司法管辖区、机构或交易指定为洗钱风险，迫使银行停止与该指定方的金融往来。",
    "source_quotes": [
      "Under section 311, the US Department of the Treasury can designate foreign jurisdictions, institutions, or transactions as money laundering risks, prompting actions by financial institutions. Designating a jurisdiction or financial organization forces banks to halt financial dealings with the designee."
    ],
    "relation_cues": [
      "designate",
      "forces"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "外国机构或交易被指定为洗钱风险"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "美国财政部指定为洗钱风险",
      "outcomes_or_paths": [
        "银行停止与该指定方的金融往来"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001705",
        "quote": "Under section 311, the US Department of the Treasury can designate foreign jurisdictions, institutions, or transactions as money laundering risks, prompting actions by financial institutions. Designating a jurisdiction or financial organization forces banks to halt financial dealings with the designee."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N001706"
    ],
    "proposition": "第312条要求对外国金融机构持有的代理账户实施强化尽职调查。",
    "source_quotes": [
      "Section 312 mandates EDD for correspondent accounts held by foreign financial institutions"
    ],
    "relation_cues": [
      "mandates"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "外国金融机构持有的代理账户"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "要求实施强化尽职调查（EDD）",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001706",
        "quote": "Section 312 mandates EDD for correspondent accounts held by foreign financial institutions"
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N001707"
    ],
    "proposition": "根据该法，美国政府可扣押外国银行在美国代理账户中的资金，资金所有者可对该扣押提出异议。",
    "source_quotes": [
      "This Act permits the US government to seize funds from a correspondent account in the US that a foreign bank has opened and maintained. The owner of the funds may contest the seizure."
    ],
    "relation_cues": [
      "seize",
      "may contest"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "外国银行在美国的代理账户中存在资金"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "美国政府扣押代理账户资金",
      "outcomes_or_paths": [
        "资金所有者可提出异议"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001707",
        "quote": "This Act permits the US government to seize funds from a correspondent account in the US that a foreign bank has opened and maintained. The owner of the funds may contest the seizure."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N001708"
    ],
    "proposition": "第314条允许银行之间及与执法机构共享信息以打击金融犯罪，并为共享信息提供安全港责任保护。",
    "source_quotes": [
      "Section 314 allows banks to cooperate with each other, law enforcement, and international agencies to combat financial crime. It provides institutions with safe harbor liability protections for sharing information."
    ],
    "relation_cues": [
      "allows",
      "provides"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "为打击金融犯罪"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "允许信息共享并提供安全港保护",
      "outcomes_or_paths": [
        "安全港责任保护"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001708",
        "quote": "Section 314 allows banks to cooperate with each other, law enforcement, and international agencies to combat financial crime. It provides institutions with safe harbor liability protections for sharing information."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N001709"
    ],
    "proposition": "该法允许美国政府要求外国银行提供代理账户记录、发出传票，并要求外国银行指定在美国的注册代理人。",
    "source_quotes": [
      "This Act allows the US government to request the production of various types of records, provides subpoena authority for correspondent accounts of foreign banks, and requires foreign banks to designate a registered agent in the US."
    ],
    "relation_cues": [
      "allows",
      "provides",
      "requires"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "美国政府行使请求或传票权力"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "要求外国银行提供记录、接受传票并指定代理人",
      "outcomes_or_paths": [
        "外国银行指定在美国的注册代理人"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001709",
        "quote": "This Act allows the US government to request the production of various types of records, provides subpoena authority for correspondent accounts of foreign banks, and requires foreign banks to designate a registered agent in the US."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
