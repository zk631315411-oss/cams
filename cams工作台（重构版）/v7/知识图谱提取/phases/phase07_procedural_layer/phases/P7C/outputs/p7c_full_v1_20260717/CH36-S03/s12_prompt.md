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

section_id: `CH36-S03`

section_title: `Types of risk assessment > The risk-based approach`

section_text_with_unit_anchors:

```text
[v7u_N002672|2672] A risk-based approach (RBA) is the process of identifying, assessing, and understanding the ML/TF risks to which organizations are exposed and taking appropriate measures to mitigate those risks effectively.
ZH: 风险为本方法（RBA）定义：识别、评估和理解洗钱/恐怖融资风险并采取适当缓解措施

[v7u_N002673|2673] The concept of an RBA emerged when FATF published the first version of guidance for an RBA in 2007.
ZH: 风险为本方法概念源于FATF 2007年发布的指南

[v7u_N002674|2674] Every organization has its own risk appetite, which determines the type of customers it will accept, the product types it will offer, and the jurisdictions and channels in which it will operate.
ZH: 风险偏好定义：决定组织接受的客户类型、产品类型及运营的司法管辖区和渠道

[v7u_N002675|2675] Once the organization establishes its risk appetite, it establishes boundaries for its business.
ZH: 风险偏好为业务设定边界

[v7u_N002676|2676] For example, a payment processor may decide it is not in a position to offer its service in jurisdictions with elevated risk of sanctions.
ZH: 示例：支付处理商决定不在制裁风险高的司法管辖区提供服务

[v7u_N002677|2677] The risk appetite statement is codified in policies and procedures.
ZH: 风险偏好声明被编入政策和程序

[v7u_N002678|2678] In conducting a CRA, each customer is categorized and risk rated.
ZH: 客户风险评估（CRA）中对每位客户进行分类和风险评级

[v7u_N002679|2679] For example, an individual customer with a regular job and salary who opens a savings account is considered low risk, assuming the source of funds can be corroborated and there is no relevant, negative news.
ZH: 示例：有固定工作和薪水的个人开储蓄账户，资金来源可核实且无负面新闻，视为低风险

[v7u_N002680|2680] A PEP is considered higher risk.
ZH: 政治敏感人物（政治敏感人物）被视为较高风险

[v7u_N002681|2681] Products, jurisdictions, and channels also present varying risk levels.
ZH: 产品、司法管辖区和渠道呈现不同风险水平

[v7u_N002682|2682] A customer representing higher risk may be subject to enhanced due diligence and heightened monitoring, thereby allowing the organization to allocate resources effectively by classifying customers based on their potential financial crime risk.
ZH: 高风险客户需接受强化尽职调查和加强监控

[v7u_N002683|2683] These decisions determine the level and frequency of customer research and updates to customer profiles.
ZH: 风险决策决定客户调查的级别和频率

[v7u_N002684|2684] Risk assessment has become more important as the fight against financial crime has evolved, with regulators emphasizing the need for a risk-based approach in all customer interactions.
ZH: 风险识别在打击金融犯罪中日益重要

[v7u_N002685|2685] Accurately judging a customer’s potential involvement in financial crime is an important prerequisite for the RBA.
ZH: 准确判断客户金融犯罪风险是风险为本方法的前提

[v7u_N002686|2686] Organizations should conduct due diligence on business operations, industries, customer characteristics, and geographic exposure to obtain adequate, complete, and truthful customer information for analysis.
ZH: 机构应对业务、行业、客户特征和地域进行尽职调查

[v7u_N002687|2687] An RBA focuses effort with the greatest need and impact.
ZH: 风险为本方法将精力集中于最需要和影响最大的领域

[v7u_N002688|2688] It requires the full commitment and support of senior management, and the active cooperation of all employees.
ZH: 风险为本方法需要高级管理层承诺和全员配合

[v7u_N002689|2689] Adopting a risk-based approach requires a risk management process to handle financial crime. This process encompasses recognizing the risks, assessing them, and developing control strategies to mitigate and monitor them.
ZH: 采用风险为本方法需要风险管理流程：识别、评估、控制
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002676"
    ],
    "proposition": "支付处理商可能决定不在制裁风险高的司法管辖区提供服务。",
    "source_quotes": [
      "a payment processor may decide it is not in a position to offer its service in jurisdictions with elevated risk of sanctions"
    ],
    "relation_cues": [
      "may decide",
      "elevated risk"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "jurisdictions with elevated risk of sanctions"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "决定不提供服务",
      "outcomes_or_paths": [
        "不提供服务"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002676",
        "quote": "a payment processor may decide it is not in a position to offer its service in jurisdictions with elevated risk of sanctions"
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002678"
    ],
    "proposition": "进行客户风险评估时，对每位客户进行分类和风险评级。",
    "source_quotes": [
      "In conducting a CRA, each customer is categorized and risk rated"
    ],
    "relation_cues": [
      "In conducting"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "进行客户风险评估"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "对每位客户进行分类和风险评级",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002678",
        "quote": "In conducting a CRA, each customer is categorized and risk rated"
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002679"
    ],
    "proposition": "有固定工作和薪水、开储蓄账户、资金来源可核实且无负面新闻的个人客户视为低风险。",
    "source_quotes": [
      "an individual customer with a regular job and salary who opens a savings account is considered low risk, assuming the source of funds can be corroborated and there is no relevant, negative news"
    ],
    "relation_cues": [
      "is considered",
      "assuming"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "个人客户有固定工作和薪水，开储蓄账户"
      ],
      "basis_or_condition": [
        "资金来源可核实，且无相关负面新闻"
      ],
      "focal_handling_or_judgment": "视为低风险",
      "outcomes_or_paths": [
        "低风险归类"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002679",
        "quote": "an individual customer with a regular job and salary who opens a savings account is considered low risk, assuming the source of funds can be corroborated and there is no relevant, negative news"
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N002680"
    ],
    "proposition": "政治敏感人物被视为较高风险。",
    "source_quotes": [
      "A PEP is considered higher risk"
    ],
    "relation_cues": [
      "considered"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "政治敏感人物"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "视为较高风险",
      "outcomes_or_paths": [
        "较高风险归类"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002680",
        "quote": "A PEP is considered higher risk"
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N002682"
    ],
    "proposition": "高风险客户需接受强化尽职调查和加强监控，从而有效分配资源。",
    "source_quotes": [
      "A customer representing higher risk may be subject to enhanced due diligence and heightened monitoring, thereby allowing the organization to allocate resources effectively by classifying customers based on their potential financial crime risk"
    ],
    "relation_cues": [
      "may be subject to",
      "thereby"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "客户代表较高风险"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "实施强化尽职调查和加强监控",
      "outcomes_or_paths": [
        "有效分配资源"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002682",
        "quote": "A customer representing higher risk may be subject to enhanced due diligence and heightened monitoring, thereby allowing the organization to allocate resources effectively by classifying customers based on their potential financial crime risk"
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N002686"
    ],
    "proposition": "机构应对业务、行业、客户特征和地域进行尽职调查，以获取充分、完整、真实的客户信息用于分析。",
    "source_quotes": [
      "Organizations should conduct due diligence on business operations, industries, customer characteristics, and geographic exposure to obtain adequate, complete, and truthful customer information for analysis"
    ],
    "relation_cues": [
      "should",
      "to obtain"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "对业务、行业、客户特征和地域进行尽职调查",
      "outcomes_or_paths": [
        "获取充分、完整、真实的客户信息用于分析"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002686",
        "quote": "Organizations should conduct due diligence on business operations, industries, customer characteristics, and geographic exposure to obtain adequate, complete, and truthful customer information for analysis"
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
