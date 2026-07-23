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

section_id: `CH15-S03`

section_title: `Money laundering risks associated with DNFBPs > Real estate sector risks`

section_text_with_unit_anchors:

```text
[v7u_N001092|1092] The real estate sector is inherently susceptible to money laundering due to the substantial sums involved in property transactions and the tangible nature of these assets.
ZH: 房地产行业因交易金额大和资产有形性而固有洗钱风险

[v7u_N001093|1093] Criminals can utilize real estate to integrate illicit funds into the legitimate economy by purchasing tangible assets, typically of significant value.
ZH: 犯罪分子通过购买高价值房地产将非法资金融入合法经济

[v7u_N001094|1094] The gains or profits are realized upon the sale of the asset, which, by then, is fully supported and legitimized in the paper trail of sale documentation, allowing money launderers to benefit from it.
ZH: 出售房地产时通过完整的文件记录使非法收益合法化

[v7u_N001095|1095] Real estate transactions often involve lawyers and other third parties, further legitimizing the movement of funds.
ZH: 房地产交易中律师等第三方的参与进一步使资金流动合法化

[v7u_N001096|1096] Buying, selling, or renting properties presents opportunities for criminals to disguise the origin of funds through obscured ownership structures.
ZH: 买卖或租赁房地产为犯罪分子通过模糊所有权结构掩饰资金来源提供机会

[v7u_N001097|1097] For example, properties acquired by corporate entities, trusts, or nominees without a clear justification as to why they were not purchased directly by an individual are red flags.
ZH: 由公司、信托或代名人购买房产且无合理解释是红旗信号信号

[v7u_N001098|1098] The lack of justification raises further concerns if the entity has minimal business activity.
ZH: 购买实体业务活动极少且无合理解释进一步引起担忧

[v7u_N001099|1099] It is also a concern if the entity is based in a jurisdiction known for its corporate secrecy for example, the Cayman Islands or the Bahamas.
ZH: 实体位于公司保密司法管辖区（如开曼群岛或巴哈马）也是风险信号

[v7u_N001100|1100] The global nature of the real estate market further complicates detection efforts. International buyers and cross-border transactions can mask illicit activities.
ZH: 房地产市场的全球性使检测工作更加复杂

[v7u_N001101|1101] A buyer from a high-risk or uncooperative jurisdiction, one lacking an established local presence or legitimate reason for purchasing property, poses an additional risk.
ZH: 来自高风险或未合作司法管辖区的买家构成额外洗钱风险

[v7u_N001102|1102] Cash transactions remain relatively common in some markets and increase the potential for money laundering, as cash is more challenging to trace than payments made through financial institutions.
ZH: 现金交易因难以追踪而增加洗钱风险

[v7u_N001103|1103] Red flags include buyers who pay entirely or primarily in cash, particularly in regions where bank financing is the norm.
ZH: 全部或主要用现金支付的买家是房地产洗钱红旗信号信号

[v7u_N001104|1104] Other red flags include buyers who exhibit little concern for the property's specifics, such as its condition or location, prioritizing the swift completion of the transaction instead.
ZH: 买家对房产细节漠不关心、只求快速成交是洗钱红旗信号信号

[v7u_N001105|1105] Properties that frequently change ownership or are involved in a series of rapid transactions should also raise suspicions.
ZH: 频繁或快速转手的房产应引起洗钱怀疑

[v7u_N001106|1106] Real estate professionals should collaborate with other DNFBPs to identify and prevent money laundering.
ZH: 房地产专业人士应与其他DNFBP合作预防洗钱

[v7u_N001107|1107] Lawyers and notaries can confirm the legitimacy of property ownership, ensure the validity of contracts, and examine the legality of the source of funds. They review transaction structures and the legitimacy of corporate buyers.
ZH: 律师和公证人可确认产权、合同有效性及资金来源合法性

[v7u_N001108|1108] Accountants can evaluate buyers' financial backgrounds, offering insights into the legitimacy of their wealth and compliance with local tax obligations.
ZH: 会计师可评估买家财务背景，判断财富合法性与税务合规

[v7u_N001109|1109] This collaboration enhances market integrity and transparency, supporting the mitigation of money laundering risks in the real estate sector.
ZH: DNFBP之间的合作可增强市场诚信与透明度，降低洗钱风险

[v7u_N001110|1110] Money laundering poses substantial risks in the accounting and auditing sectors due to professionals' access to sensitive financial information and their roles in financial management, reporting, and advising.
ZH: 会计与审计行业因接触敏感财务信息而面临重大洗钱风险

[v7u_N001111|1111] Accountants frequently find themselves in a position to detect suspicious activities, but they should remain vigilant to ensure they do not inadvertently facilitate illegal practices.
ZH: 会计师有责任发现可疑活动并避免无意中协助非法行为

[v7u_N001112|1112] Their involvement in handling financial records provides easy access to data, and their inability to detect suspicious activity might lead them to unwittingly create complex structures that enable illegal activities, such as structuring.
ZH: 会计师可能无意中创建复杂结构为非法活动（如拆分交易）提供便利

[v7u_N001113|1113] If an accountant designs overly complex or opaque transactions, it might raise a red flag for money laundering.
ZH: 会计师设计过于复杂或不透明的交易可能是洗钱红旗信号信号

[v7u_N001114|1114] One consequential risk for accountants is inadvertently supporting tax evasion, with subsequent transactions potentially serving as a conduit for money laundering.
ZH: 会计师可能无意中协助逃税，后续交易可能成为洗钱渠道

[v7u_N001115|1115] Tax avoidance involves legally minimizing tax liabilities, while tax evasion includes illegal actions, such as falsifying records or concealing income.
ZH: 税务规避是合法减少税负，逃税是非法行为如伪造记录或隐瞒收入

[v7u_N001116|1116] If accountants become complicit in illegal tax evasion schemes, they might also inadvertently assist in money laundering, as illicit funds are often concealed through fraudulent tax practices.
ZH: 会计师若参与非法逃税计划，可能无意中协助洗钱

[v7u_N001117|1117] Accountants provide various services, some of which are listed below. These services have corresponding money laundering risks.
ZH: 会计师提供的各类服务对应不同的洗钱风险

[v7u_N001118|1118] Money laundering is a prominent concern in the legal sector due to the influential role lawyers and notaries play in managing financial transactions, providing legal advice, and knowing their clients. Criminals often exploit the services of legal professionals to conceal illicit funds, facilitate fraudulent transactions, or structure deals in ways that obscure the origin of money.
ZH: 法律行业因律师和公证人管理金融交易而面临显著洗钱风险

[v7u_N001119|1119] Legal professionals provide various services, some of which are listed below. These services have corresponding money laundering risks.
ZH: 法律专业人士提供的各类服务对应不同的洗钱风险
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N001105"
    ],
    "proposition": "频繁或快速转手的房产应引起洗钱怀疑。",
    "source_quotes": [
      "Properties that frequently change ownership or are involved in a series of rapid transactions should also raise suspicions."
    ],
    "relation_cues": [
      "should",
      "also"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "房产频繁或快速转手"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "引起洗钱怀疑",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001105",
        "quote": "Properties that frequently change ownership or are involved in a series of rapid transactions should also raise suspicions."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N001106"
    ],
    "proposition": "房地产专业人士应与其他DNFBP合作以识别和预防洗钱。",
    "source_quotes": [
      "Real estate professionals should collaborate with other DNFBPs to identify and prevent money laundering."
    ],
    "relation_cues": [
      "should",
      "to"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "房地产专业人士与其他DNFBP合作",
      "outcomes_or_paths": [
        "识别和预防洗钱"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001106",
        "quote": "Real estate professionals should collaborate with other DNFBPs to identify and prevent money laundering."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N001111"
    ],
    "proposition": "会计师应保持警惕以确保不无意中协助非法活动。",
    "source_quotes": [
      "Accountants frequently find themselves in a position to detect suspicious activities, but they should remain vigilant to ensure they do not inadvertently facilitate illegal practices."
    ],
    "relation_cues": [
      "should",
      "to ensure"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "会计师处于发现可疑活动的位置"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "保持警惕",
      "outcomes_or_paths": [
        "确保不无意中协助非法活动"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001111",
        "quote": "Accountants frequently find themselves in a position to detect suspicious activities, but they should remain vigilant to ensure they do not inadvertently facilitate illegal practices."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N001113"
    ],
    "proposition": "会计师设计过于复杂或不透明的交易可能引起洗钱红旗信号。",
    "source_quotes": [
      "If an accountant designs overly complex or opaque transactions, it might raise a red flag for money laundering."
    ],
    "relation_cues": [
      "If",
      "might"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "会计师设计过于复杂或不透明的交易"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "可能引起洗钱红旗信号",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001113",
        "quote": "If an accountant designs overly complex or opaque transactions, it might raise a red flag for money laundering."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N001116"
    ],
    "proposition": "会计师若参与非法逃税计划，可能无意中协助洗钱。",
    "source_quotes": [
      "If accountants become complicit in illegal tax evasion schemes, they might also inadvertently assist in money laundering, as illicit funds are often concealed through fraudulent tax practices."
    ],
    "relation_cues": [
      "If",
      "might"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "会计师参与非法逃税计划"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "可能无意中协助洗钱",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001116",
        "quote": "If accountants become complicit in illegal tax evasion schemes, they might also inadvertently assist in money laundering, as illicit funds are often concealed through fraudulent tax practices."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
