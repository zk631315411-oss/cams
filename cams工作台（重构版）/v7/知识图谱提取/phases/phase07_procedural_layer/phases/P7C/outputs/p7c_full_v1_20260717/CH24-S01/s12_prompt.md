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

section_id: `CH24-S01`

section_title: `US AML/CFT regulatory landscape > Bank Secrecy Act`

section_text_with_unit_anchors:

```text
[v7u_N001682|1682] The Bank Secrecy Act (BSA) is the US’s most important AML regulation.
ZH: 《银行保密法》是美国最重要的反洗钱法规

[v7u_N001683|1683] The US implemented it in 1970 in response to criminals using US banks and the financial system for money laundering and other illicit activities.
ZH: 《银行保密法》于1970年实施，旨在打击利用美国银行和金融系统进行的洗钱活动

[v7u_N001684|1684] The BSA introduced significant recordkeeping and reporting obligations for US banks and financial institutions. For instance, the BSA required banks to collect information on customers and their transactions.
ZH: 《银行保密法》为美国银行和金融机构引入了重要的记录保存和报告义务

[v7u_N001685|1685] These obligations helped ensure that law enforcement and supervisory agencies received the financial information and evidence they needed for their investigations and prosecutions.
ZH: 《银行保密法》义务旨在确保执法和监管机构获得调查和起诉所需的金融信息与证据

[v7u_N001686|1686] In 2001, the US extended the scope of the BSA to include counter-terrorist financing obligations introduced by the USA PATRIOT Act.
ZH: 2001年美国通过《爱国者法案》将《银行保密法》范围扩展至反恐怖融资义务

[v7u_N001687|1687] The BSA introduced several reporting requirements:
ZH: 《银行保密法》引入了多项报告要求

[v7u_N001688|1688] Currency transaction reports
ZH: 货币交易报告

[v7u_N001689|1689] Suspicious activity reports
ZH: 可疑活动报告

[v7u_N001690|1690] Foreign bank account reports for US citizens holding foreign accounts
ZH: 持有外国账户的美国公民需提交外国银行账户报告

[v7u_N001691|1691] Currency and monetary instrument reports for cash purchases of monetary instruments
ZH: 现金购买货币工具需提交货币与货币工具报告

[v7u_N001692|1692] The BSA requires obliged entities to develop, implement, and maintain an effective AML program based on five pillars:
ZH: 《银行保密法》要求义务实体基于五大支柱制定、实施和维护有效的反洗钱计划

[v7u_N001693|1693] Incorporate policies, procedures, and internal controls reasonably designed to assure compliance with regulatory requirements.
ZH: 制定合理设计的政策、程序和内部控制以确保合规

[v7u_N001694|1694] Designate an AML officer responsible for the day-to-day activities of the program.
ZH: 指定一名反洗钱官负责计划的日常活动

[v7u_N001695|1695] Provide education and training of employees concerning their responsibilities under the program.
ZH: 为员工提供关于其计划职责的教育和培训

[v7u_N001696|1696] Ensure independent audit to monitor and maintain an adequate program with a risk-based frequency.
ZH: 确保基于风险频率进行独立审计以监控和维护充分计划

[v7u_N001697|1697] Develop an ongoing CDD program using a risk-based approach.
ZH: 使用基于风险的方法制定持续的客户尽职调查计划

[v7u_N001698|1698] The BSA extends to non-US banks, MSBs, and cryptocurrency firms that deal with US customers or utilize the US financial system.
ZH: 《银行保密法》适用于与美国客户交易或使用美国金融体系的非美国银行、货币服务企业和加密货币公司

[v7u_N001699|1699] It requires US-based branches of foreign banks to comply with BSA requirements, as well as MSBs or cryptocurrency firms that engage in transactions with US customers.
ZH: 外国银行美国分行、与美国客户交易的货币服务企业和加密货币公司须遵守《银行保密法》要求

[v7u_N001700|1700] Foreign financial institutions that maintain correspondent bank accounts with US banks are subject to some BSA requirements, including recordkeeping and the obligation to provide records in response to requests from US authorities.
ZH: 在美国银行持有代理账户的外国金融机构须遵守部分《银行保密法》要求，包括记录保存和应要求提供记录
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N001692",
      "v7u_N001693",
      "v7u_N001694",
      "v7u_N001695",
      "v7u_N001696",
      "v7u_N001697"
    ],
    "proposition": "BSA要求义务实体基于五大支柱制定、实施和维护有效的反洗钱计划。",
    "source_quotes": [
      "The BSA requires obliged entities to develop, implement, and maintain an effective AML program based on five pillars:",
      "Incorporate policies, procedures, and internal controls reasonably designed to assure compliance with regulatory requirements.",
      "Designate an AML officer responsible for the day-to-day activities of the program.",
      "Provide education and training of employees concerning their responsibilities under the program.",
      "Ensure independent audit to monitor and maintain an adequate program with a risk-based frequency.",
      "Develop an ongoing CDD program using a risk-based approach."
    ],
    "relation_cues": [
      "requires",
      "based on"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "实体是BSA规定的义务实体"
      ],
      "basis_or_condition": [
        "五大支柱"
      ],
      "focal_handling_or_judgment": "制定、实施和维护有效的反洗钱计划",
      "outcomes_or_paths": [
        "制定合理设计的政策、程序和内部控制以确保合规",
        "指定一名反洗钱官负责计划的日常活动",
        "为员工提供关于其计划职责的教育和培训",
        "确保基于风险频率进行独立审计以监控和维护充分计划",
        "使用基于风险的方法制定持续的客户尽职调查计划"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001692",
        "quote": "The BSA requires obliged entities to develop, implement, and maintain an effective AML program based on five pillars:"
      },
      {
        "unit_id": "v7u_N001693",
        "quote": "Incorporate policies, procedures, and internal controls reasonably designed to assure compliance with regulatory requirements."
      },
      {
        "unit_id": "v7u_N001694",
        "quote": "Designate an AML officer responsible for the day-to-day activities of the program."
      },
      {
        "unit_id": "v7u_N001695",
        "quote": "Provide education and training of employees concerning their responsibilities under the program."
      },
      {
        "unit_id": "v7u_N001696",
        "quote": "Ensure independent audit to monitor and maintain an adequate program with a risk-based frequency."
      },
      {
        "unit_id": "v7u_N001697",
        "quote": "Develop an ongoing CDD program using a risk-based approach."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N001698"
    ],
    "proposition": "BSA适用于与美国客户交易或利用美国金融体系的非美国银行、货币服务企业和加密货币公司。",
    "source_quotes": [
      "The BSA extends to non-US banks, MSBs, and cryptocurrency firms that deal with US customers or utilize the US financial system."
    ],
    "relation_cues": [
      "extends to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "非美国银行、货币服务企业或加密货币公司"
      ],
      "basis_or_condition": [
        "与美国客户交易或利用美国金融体系"
      ],
      "focal_handling_or_judgment": "受BSA管辖",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001698",
        "quote": "The BSA extends to non-US banks, MSBs, and cryptocurrency firms that deal with US customers or utilize the US financial system."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N001699"
    ],
    "proposition": "BSA要求外国银行美国分行、以及与美国客户进行交易的货币服务企业和加密货币公司遵守BSA要求。",
    "source_quotes": [
      "It requires US-based branches of foreign banks to comply with BSA requirements, as well as MSBs or cryptocurrency firms that engage in transactions with US customers."
    ],
    "relation_cues": [
      "requires",
      "comply with"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "外国银行美国分行",
        "或与美国客户交易的货币服务企业/加密货币公司"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "遵守BSA要求",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001699",
        "quote": "It requires US-based branches of foreign banks to comply with BSA requirements, as well as MSBs or cryptocurrency firms that engage in transactions with US customers."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N001700"
    ],
    "proposition": "在美国银行持有代理账户的外国金融机构须遵守部分BSA要求，包括记录保存和应要求提供记录。",
    "source_quotes": [
      "Foreign financial institutions that maintain correspondent bank accounts with US banks are subject to some BSA requirements, including recordkeeping and the obligation to provide records in response to requests from US authorities."
    ],
    "relation_cues": [
      "subject to",
      "including"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "外国金融机构在美国银行持有代理账户"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "受部分BSA要求约束",
      "outcomes_or_paths": [
        "记录保存",
        "应美国当局要求提供记录"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001700",
        "quote": "Foreign financial institutions that maintain correspondent bank accounts with US banks are subject to some BSA requirements, including recordkeeping and the obligation to provide records in response to requests from US authorities."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
