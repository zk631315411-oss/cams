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

section_id: `CH24-S08`

section_title: `US AML/CFT regulatory landscape > EU AML package`

section_text_with_unit_anchors:

```text
[v7u_N001800|1800] In 2024, the EU adopted a package of AML legislation known as the “Single Rulebook.” The package consists of:
ZH: 2024年欧盟通过反洗钱立法包“单一规则手册”，包含以下内容。

[v7u_N001801|1801] Directive (EU) 2024/1640, also called 6AMLD.
ZH: 欧盟第六反洗钱指令（6反洗钱D）

[v7u_N001802|1802] Regulation (EU) 2024/1624, also called AMLR.
ZH: 欧盟反洗钱条例（反洗钱R）

[v7u_N001803|1803] Regulation (EU) 2024/1620, also called AMLA-R.
ZH: 欧盟反洗钱管理局条例（反洗钱A-R）

[v7u_N001804|1804] Regulation (EU) 2023/1113, also called FTR.
ZH: 欧盟资金转移条例（FTR）

[v7u_N001805|1805] 6AMLD builds on previous AMLDs, such as Directive (EU) 2015/849 (4AMLD).
ZH: 6反洗钱D建立在先前反洗钱指令基础上

[v7u_N001806|1806] The 6AMLD requires financial institutions and other obligated entities to implement comprehensive CDD procedures, maintain central registers of beneficial ownership information, and conduct risk assessments on state and supranational levels.
ZH: 6反洗钱D要求义务实体实施全面的客户尽职调查、维护受益所有人中央登记册并开展风险评估

[v7u_N001807|1807] 6AMLD enhances the role of FIUs and strengthens cooperation between national FIUs and other AML authorities.
ZH: 6反洗钱D强化了金融情报机构（FIU）的作用并加强了合作

[v7u_N001808|1808] The EU requires its member states to transpose 6AMLD provisions into law.
ZH: 欧盟要求成员国将6反洗钱D条款转化为国内法

[v7u_N001809|1809] The goal of AMLR is to harmonize CDD and risk assessment requirements across member states.
ZH: 反洗钱R旨在统一各成员国的客户尽职调查和风险评估要求

[v7u_N001810|1810] This regulation sets a €10,000 limit for cash-based transactions and strengthens rules on PEPs, beneficial ownership, and beneficial owner disclosure obligations for firms in developing nations purchasing high-worth vehicles and real estate assets.
ZH: 反洗钱R设定现金交易1万欧元限额，并加强政治敏感人物、受益所有人及披露规则

[v7u_N001811|1811] AMLR requires obliged entities to assess all AML staff for skills, good repute, honesty, and integrity.
ZH: 反洗钱R要求义务实体评估反洗钱人员的技能、声誉、诚实和正直

[v7u_N001812|1812] It also strengthens rules on SARs and penalties for violations.
ZH: 反洗钱R加强了可疑交易报告（SAR）规则和违规处罚

[v7u_N001813|1813] AMLR expands the perimeter of obliged entities to include soccer agents, professional football clubs, and investment migration operators.
ZH: 反洗钱R将义务实体范围扩展至足球经纪人、职业足球俱乐部和投资移民运营商

[v7u_N001814|1814] Provisions relating to the football sector, the creation of a single access point to real estate information, and the interconnection of bank account registers go into effect after the majority of provisions in AMLR.
ZH: 反洗钱R中关于足球行业、房地产信息单一接入点和银行账户登记互联的条款稍后生效

[v7u_N001815|1815] AMLA-R establishes an EU Anti-Money Laundering Authority (AML Authority, known as AMLA in Europe), which is responsible for the direct supervision of selected obliged entities in the financial sector.
ZH: 反洗钱A-R设立欧盟反洗钱管理局（反洗钱A），负责直接监督部分金融行业义务实体

[v7u_N001816|1816] These obliged entities are selected based on the high residual risk profile.
ZH: 义务实体根据高剩余风险状况被选为直接监督对象

[v7u_N001817|1817] Additionally, AMLA-R coordinates supervision of NCAs and drafts level-2 regulations and guidelines.
ZH: 反洗钱A-R协调国家主管机构（NCA）的监督并起草二级法规和指南

[v7u_N001818|1818] The majority of AMLA-R went into effect in July 2025.
ZH: 反洗钱A-R大部分条款于2025年7月生效

[v7u_N001819|1819] FTR implements FATF’s recommendations on cryptoassets and prohibits anonymous cryptoasset accounts and transactions.
ZH: FTR落实FATF关于加密资产的建议，禁止匿名加密资产账户和交易

[v7u_N001820|1820] FTR is a recast of the Regulation (EU) 2015/847 on information accompanying transfers of funds.
ZH: FTR是对资金转移信息条例（EU 2015/847）的重订

[v7u_N001821|1821] Together with the Markets in Cryptoassets Regulation (MiCA), FTR went into effect in December 2024.
ZH: FTR与MiCA于2024年12月生效
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N001806"
    ],
    "proposition": "6AMLD要求金融机构及其他义务实体实施全面的客户尽职调查程序、维护受益所有人中央登记册并开展风险评估。",
    "source_quotes": [
      "The 6AMLD requires financial institutions and other obligated entities to implement comprehensive CDD procedures, maintain central registers of beneficial ownership information, and conduct risk assessments on state and supranational levels."
    ],
    "relation_cues": [
      "requires"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "金融机构及其他义务实体"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "实施全面的CDD程序、维护受益所有人中央登记册并开展风险评估",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001806",
        "quote": "The 6AMLD requires financial institutions and other obligated entities to implement comprehensive CDD procedures, maintain central registers of beneficial ownership information, and conduct risk assessments on state and supranational levels."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N001808"
    ],
    "proposition": "欧盟要求成员国将6AMLD条款转化为国内法。",
    "source_quotes": [
      "The EU requires its member states to transpose 6AMLD provisions into law."
    ],
    "relation_cues": [
      "requires"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "欧盟要求"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "成员国将6AMLD条款转化为国内法",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001808",
        "quote": "The EU requires its member states to transpose 6AMLD provisions into law."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N001810"
    ],
    "proposition": "AMLR设定现金交易限额为10,000欧元，并加强政治敏感人物、受益所有人及披露规则。",
    "source_quotes": [
      "This regulation sets a €10,000 limit for cash-based transactions and strengthens rules on PEPs, beneficial ownership, and beneficial owner disclosure obligations for firms in developing nations purchasing high-worth vehicles and real estate assets."
    ],
    "relation_cues": [
      "sets",
      "strengthens"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "现金交易"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "设定10,000欧元限额并加强相关规则",
      "outcomes_or_paths": [
        "现金交易限额为10,000欧元"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001810",
        "quote": "This regulation sets a €10,000 limit for cash-based transactions and strengthens rules on PEPs, beneficial ownership, and beneficial owner disclosure obligations for firms in developing nations purchasing high-worth vehicles and real estate assets."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N001811"
    ],
    "proposition": "AMLR要求义务实体评估所有反洗钱人员的技能、声誉、诚实和正直。",
    "source_quotes": [
      "AMLR requires obliged entities to assess all AML staff for skills, good repute, honesty, and integrity."
    ],
    "relation_cues": [
      "requires"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "义务实体"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "评估所有反洗钱人员的技能、声誉、诚实和正直",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001811",
        "quote": "AMLR requires obliged entities to assess all AML staff for skills, good repute, honesty, and integrity."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N001813"
    ],
    "proposition": "AMLR将义务实体范围扩展至足球经纪人、职业足球俱乐部和投资移民运营商。",
    "source_quotes": [
      "AMLR expands the perimeter of obliged entities to include soccer agents, professional football clubs, and investment migration operators."
    ],
    "relation_cues": [
      "expands"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "义务实体范围"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "扩展义务实体范围",
      "outcomes_or_paths": [
        "包括足球经纪人、职业足球俱乐部和投资移民运营商"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001813",
        "quote": "AMLR expands the perimeter of obliged entities to include soccer agents, professional football clubs, and investment migration operators."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N001815",
      "v7u_N001816"
    ],
    "proposition": "AMLA-R设立欧盟反洗钱管理局，负责直接监督金融行业中基于高剩余风险选定的义务实体。",
    "source_quotes": [
      "AMLA-R establishes an EU Anti-Money Laundering Authority (AML Authority, known as AMLA in Europe), which is responsible for the direct supervision of selected obliged entities in the financial sector.",
      "These obliged entities are selected based on the high residual risk profile."
    ],
    "relation_cues": [
      "establishes",
      "responsible for",
      "based on"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "金融行业中"
      ],
      "basis_or_condition": [
        "基于高剩余风险状况"
      ],
      "focal_handling_or_judgment": "设立欧盟反洗钱管理局并直接监督选定的义务实体",
      "outcomes_or_paths": [
        "选定的义务实体由AMLA直接监督"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001815",
        "quote": "AMLA-R establishes an EU Anti-Money Laundering Authority (AML Authority, known as AMLA in Europe), which is responsible for the direct supervision of selected obliged entities in the financial sector."
      },
      {
        "unit_id": "v7u_N001816",
        "quote": "These obliged entities are selected based on the high residual risk profile."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_007",
    "unit_ids": [
      "v7u_N001819"
    ],
    "proposition": "FTR落实FATF关于加密资产的建议，并禁止匿名加密资产账户和交易。",
    "source_quotes": [
      "FTR implements FATF’s recommendations on cryptoassets and prohibits anonymous cryptoasset accounts and transactions."
    ],
    "relation_cues": [
      "implements",
      "prohibits"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "加密资产"
      ],
      "basis_or_condition": [
        "FATF建议"
      ],
      "focal_handling_or_judgment": "禁止匿名加密资产账户和交易",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001819",
        "quote": "FTR implements FATF’s recommendations on cryptoassets and prohibits anonymous cryptoasset accounts and transactions."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
