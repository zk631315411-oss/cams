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

section_id: `CH17-S01`

section_title: `Providing financial services to embassies, foreign consulates, and missions`

section_text_with_unit_anchors:

```text
[v7u_N001250|1250] Foreign embassies, foreign consulates, and missions are commonly seen in host countries.
ZH: 外国大使馆、领事馆和使团在东道国普遍存在

[v7u_N001251|1251] An embassy is usually located in the host country's capital city and contains the office of the foreign ambassador, the diplomatic representatives, and their staff. It handles political and economic matters between the two countries, facilitating communication and negotiation.
ZH: 大使馆通常位于东道国首都，包含大使办公室、外交代表及工作人员，处理两国政治经济事务

[v7u_N001252|1252] Consulates act as branches of embassies and are typically located in major cities of the host country. They provide various administrative and governmental functions, such as issuing visas and handling immigration matters, similar to what an embassy provides but on a smaller scale.
ZH: 领事馆是大使馆的分支机构，通常位于东道国主要城市，提供签证和移民等行政服务

[v7u_N001253|1253] A foreign mission refers to a group of people that conducts diplomatic business in a foreign country to serve the interests of their home country. A foreign mission can include embassies and consulates.
ZH: 外国使团指在外国从事外交事务以服务本国利益的一群人，包括大使馆和领事馆

[v7u_N001254|1254] These organizations require access to financial services to meet their daily financial responsibilities. Services can range from operational expenses, such as payroll, rent, and utilities, to intergovernmental and intragovernmental transactions, such as commercial and military purchase payments.
ZH: 大使馆和使团需要金融服务以满足日常财务责任，包括运营开支和政府间交易

[v7u_N001255|1255] Some banks also offer ancillary services or accounts to government personnel, including embassy staff, their families, and former foreign officials.
ZH: 一些银行还向政府人员（包括使馆工作人员及其家属和前外国官员）提供辅助服务或账户

[v7u_N001256|1256] Each of these governmental relationships poses different levels of risk to the bank because the individuals involved are usually classified as PEPs in most host countries.
ZH: 使馆相关政府关系因涉及政治敏感人物而给银行带来不同程度的风险

[v7u_N001257|1257] A PEP is an individual in a prominent political function, or their immediate family or close associates, who could be at higher risk for involvement in bribery and corruption.
ZH: 政治敏感人物指担任显要公职的个人及其直系亲属或密切关联人，可能面临更高的贿赂和腐败风险

[v7u_N001258|1258] Additionally, embassy, foreign consulate, and mission accounts can pose a higher risk in certain circumstances, including:
ZH: 大使馆、领事馆和使团账户在某些情况下可能构成更高风险

[v7u_N001259|1259] Accounts held in jurisdictions designated as higher money laundering or corruption risk by FATF or other regulatory bodies.
ZH: 账户位于FATF或其他监管机构认定的洗钱或腐败高风险管辖区

[v7u_N001260|1260] Substantial cash transactions, which might indicate potential illicit activities.
ZH: 大额现金交易可能表明潜在的非法活动

[v7u_N001261|1261] Account activity that is not consistent with the account’s purpose, or transactions that do not align with anticipated activities, such as unusual amounts or types of transactions.
ZH: 账户活动与账户目的不一致，或交易金额/类型异常，属于风险指标。

[v7u_N001262|1262] Accounts directly funding personal expenses of foreign nationals, including, but not limited to, expenses for education fees, which might mix official and personal finances.
ZH: 直接为外国国民个人开支（如教育费）提供资金的账户，可能混淆官方与个人财务。

[v7u_N001263|1263] Official embassy business conducted through personal accounts, raising concerns about the transparency and legitimacy of transactions.
ZH: 通过个人账户进行使馆官方业务，引发交易透明度和合法性问题。
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N001256"
    ],
    "proposition": "使馆相关政府关系因涉及政治敏感人物（PEPs）而给银行带来不同程度的风险。",
    "source_quotes": [
      "Each of these governmental relationships poses different levels of risk to the bank because the individuals involved are usually classified as PEPs in most host countries."
    ],
    "relation_cues": [
      "because",
      "poses"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "使馆相关政府关系"
      ],
      "basis_or_condition": [
        "因个体通常被分类为PEPs"
      ],
      "focal_handling_or_judgment": "对银行构成不同风险水平",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001256",
        "quote": "Each of these governmental relationships poses different levels of risk to the bank because the individuals involved are usually classified as PEPs in most host countries."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N001258",
      "v7u_N001259",
      "v7u_N001260",
      "v7u_N001261",
      "v7u_N001262",
      "v7u_N001263"
    ],
    "proposition": "大使馆、领事馆和使团账户在某些情况下可能构成更高风险，包括账户位于高风险管辖区、大额现金交易、活动不一致、资助个人开支、通过个人账户进行官方业务等。",
    "source_quotes": [
      "Additionally, embassy, foreign consulate, and mission accounts can pose a higher risk in certain circumstances, including:",
      "Accounts held in jurisdictions designated as higher money laundering or corruption risk by FATF or other regulatory bodies.",
      "Substantial cash transactions, which might indicate potential illicit activities.",
      "Account activity that is not consistent with the account’s purpose, or transactions that do not align with anticipated activities, such as unusual amounts or types of transactions.",
      "Accounts directly funding personal expenses of foreign nationals, including, but not limited to, expenses for education fees, which might mix official and personal finances.",
      "Official embassy business conducted through personal accounts, raising concerns about the transparency and legitimacy of transactions."
    ],
    "relation_cues": [
      "can pose",
      "higher risk",
      "including"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "大使馆、领事馆和使团账户"
      ],
      "basis_or_condition": [
        "账户位于FATF或其他监管机构认定的洗钱或腐败高风险管辖区",
        "大额现金交易",
        "账户活动与目的不一致或交易异常",
        "直接为外国国民个人开支提供资金",
        "通过个人账户进行使馆官方业务"
      ],
      "focal_handling_or_judgment": "可能构成更高风险",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001258",
        "quote": "Additionally, embassy, foreign consulate, and mission accounts can pose a higher risk in certain circumstances, including:"
      },
      {
        "unit_id": "v7u_N001259",
        "quote": "Accounts held in jurisdictions designated as higher money laundering or corruption risk by FATF or other regulatory bodies."
      },
      {
        "unit_id": "v7u_N001260",
        "quote": "Substantial cash transactions, which might indicate potential illicit activities."
      },
      {
        "unit_id": "v7u_N001261",
        "quote": "Account activity that is not consistent with the account’s purpose, or transactions that do not align with anticipated activities, such as unusual amounts or types of transactions."
      },
      {
        "unit_id": "v7u_N001262",
        "quote": "Accounts directly funding personal expenses of foreign nationals, including, but not limited to, expenses for education fees, which might mix official and personal finances."
      },
      {
        "unit_id": "v7u_N001263",
        "quote": "Official embassy business conducted through personal accounts, raising concerns about the transparency and legitimacy of transactions."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
