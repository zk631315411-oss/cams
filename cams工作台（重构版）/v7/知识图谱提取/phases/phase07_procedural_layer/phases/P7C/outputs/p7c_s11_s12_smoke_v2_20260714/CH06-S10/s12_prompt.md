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

section_id: `CH06-S10`

section_title: `Money Laundering Risks in Financial Services > Control and ownership for AML compliance`

section_text_with_unit_anchors:

```text
[v7u_N000483|483] Control and ownership play a vital role in AML efforts, as they can often be obscured or concealed, allowing bad actors to disguise criminal activities and facilitate financial crime.
ZH: 控制权和所有权在反洗钱工作中至关重要

[v7u_N000484|484] A beneficial owner (BO) is defined as an individual or entity that possesses ownership of a legal entity, either through shareholding or other means.
ZH: 受益所有人（BO）的定义：通过持股或其他方式拥有法律实体的个人或实体

[v7u_N000485|485] In contrast, the ultimate beneficial owner (UBO) refers specifically to one or more natural persons who ultimately owns a substantial percentage of shareholding.
ZH: 最终受益所有人（UBO）的定义：最终持有重大比例股份的自然人

[v7u_N000486|486] It is important to note that a BO might appear to have ownership of a company but might not control the company. Conversely, a UBO might not directly hold shares but does exert ultimate control over it.
ZH: BO 可能拥有所有权但不控制公司，UBO 可能不直接持股但实施最终控制

[v7u_N000487|487] This distinction is crucial when it comes to regulatory requirements surrounding ownership structures.
ZH: BO 与 UBO 的区别对所有权结构的监管要求至关重要

[v7u_N000488|488] When reviewing ownership structures, there is a regulatory obligation to identify the UBO of a customer.
ZH: 监管要求审查所有权结构时必须识别客户的 UBO

[v7u_N000489|489] For AML purposes, most jurisdictions require beneficial ownership to be identified at a threshold of 25% or more. That means you need to know every entity or individual who owns at least 25% of a customer.
ZH: 多数司法管辖区要求识别持股 25% 或以上的受益所有人

[v7u_N000490|490] Your organization will set the appropriate threshold using a riskbased approach.
ZH: 机构应采用风险为本的方法设定受益所有权阈值

[v7u_N000491|491] For certain high-risk customers, the beneficial ownership threshold might be as low as 10% and could go as low as 5% for customers who pose a significantly higher risk.
ZH: 高风险客户的受益所有人阈值可能低至 10% 甚至 5%

[v7u_N000492|492] For example, high-risk financial institutions with correspondent banking relationships in a high-risk jurisdiction might set their threshold at 5%.
ZH: 示例：高风险司法管辖区的代理行关系可能设定 5% 的阈值

[v7u_N000493|493] In order to identify the UBOs of Company A, you need to identify indirect ownership stakes in addition to direct ownership.
ZH: 识别 UBO 需要同时考虑直接和间接持股

[v7u_N000494|494] Individual D owns 10% of Company A directly. They also own 72% of Company A indirectly, as they own 90% of shares of Company B, which owns 80% of Company A. Individual D is then considered a UBO with 82% shareholding of Company A.
ZH: 示例：个人 D 通过直接和间接持股合计 82%，成为 UBO

[v7u_N000495|495] Individual C, who owns 10% of Company A directly and an additional 8% indirectly via their 10% ownership of Company B, is not a UBO.
ZH: 示例：个人 C 直接持股 10% 加间接持股 8%，未达到 UBO 标准

[v7u_N000496|496] In companies where there is no natural beneficial owner, a controller or a notional beneficial owner should be identified and verified. This allows you to understand who is in control of the decision-making in the company when natural individual UBOs are not present.
ZH: 无自然人受益所有人时，应识别并核实控制人或名义受益所有人

[v7u_N000497|497] For example, for a company that is publicly listed on the stock exchange and has thousands of shareholders, a notional beneficial owner could be the president or chief executive officer, or equivalent.
ZH: 示例：上市公司可将总裁或 CEO 作为名义受益所有人
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N000488",
      "v7u_N000489",
      "v7u_N000493",
      "v7u_N000494",
      "v7u_N000495"
    ],
    "proposition": "审查所有权结构时，监管要求识别UBO；多数司法管辖区以25%为阈值，需同时考虑直接和间接持股；达到阈值认定为UBO，未达到则不认定。",
    "source_quotes": [
      "When reviewing ownership structures, there is a regulatory obligation to identify the UBO of a customer.",
      "For AML purposes, most jurisdictions require beneficial ownership to be identified at a threshold of 25% or more.",
      "In order to identify the UBOs of Company A, you need to identify indirect ownership stakes in addition to direct ownership.",
      "Individual D is then considered a UBO with 82% shareholding of Company A.",
      "Individual C, who owns 10% of Company A directly and an additional 8% indirectly via their 10% ownership of Company B, is not a UBO."
    ],
    "relation_cues": [
      "when",
      "require",
      "threshold",
      "in order to",
      "considered",
      "not"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "审查所有权结构时"
      ],
      "basis_or_condition": [
        "监管要求",
        "25%或以上阈值",
        "直接和间接持股合并计算"
      ],
      "focal_handling_or_judgment": "判断客户持股是否达到UBO认定标准",
      "outcomes_or_paths": [
        "达到阈值：认定为UBO",
        "未达到阈值：不认定为UBO"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000488",
        "quote": "When reviewing ownership structures, there is a regulatory obligation to identify the UBO of a customer."
      },
      {
        "unit_id": "v7u_N000489",
        "quote": "For AML purposes, most jurisdictions require beneficial ownership to be identified at a threshold of 25% or more."
      },
      {
        "unit_id": "v7u_N000493",
        "quote": "In order to identify the UBOs of Company A, you need to identify indirect ownership stakes in addition to direct ownership."
      },
      {
        "unit_id": "v7u_N000494",
        "quote": "Individual D is then considered a UBO with 82% shareholding of Company A."
      },
      {
        "unit_id": "v7u_N000495",
        "quote": "Individual C, who owns 10% of Company A directly and an additional 8% indirectly via their 10% ownership of Company B, is not a UBO."
      }
    ],
    "induction": "cross_unit",
    "cross_unit_basis": {
      "rule_unit_ids": [
        "v7u_N000488",
        "v7u_N000489",
        "v7u_N000493"
      ],
      "positive_example_unit_ids": [
        "v7u_N000494"
      ],
      "negative_example_unit_ids": [
        "v7u_N000495"
      ]
    }
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N000490",
      "v7u_N000491",
      "v7u_N000492"
    ],
    "proposition": "机构采用风险为本方法设定受益所有权阈值；高风险客户阈值可能低至10%甚至5%。",
    "source_quotes": [
      "Your organization will set the appropriate threshold using a riskbased approach.",
      "For certain high-risk customers, the beneficial ownership threshold might be as low as 10% and could go as low as 5% for customers who pose a significantly higher risk.",
      "For example, high-risk financial institutions with correspondent banking relationships in a high-risk jurisdiction might set their threshold at 5%."
    ],
    "relation_cues": [
      "riskbased approach",
      "might",
      "could",
      "for example"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "机构设定受益所有权阈值"
      ],
      "basis_or_condition": [
        "风险为本方法",
        "客户风险水平"
      ],
      "focal_handling_or_judgment": "设定适用的受益所有权阈值",
      "outcomes_or_paths": [
        "默认阈值",
        "高风险客户阈值10%",
        "显著更高风险客户阈值5%"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000490",
        "quote": "Your organization will set the appropriate threshold using a riskbased approach."
      },
      {
        "unit_id": "v7u_N000491",
        "quote": "For certain high-risk customers, the beneficial ownership threshold might be as low as 10% and could go as low as 5% for customers who pose a significantly higher risk."
      },
      {
        "unit_id": "v7u_N000492",
        "quote": "For example, high-risk financial institutions with correspondent banking relationships in a high-risk jurisdiction might set their threshold at 5%."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N000496",
      "v7u_N000497"
    ],
    "proposition": "无自然人受益所有人时，应识别并核实控制人或名义受益所有人；例如上市公司可将总裁或CEO作为名义受益所有人。",
    "source_quotes": [
      "In companies where there is no natural beneficial owner, a controller or a notional beneficial owner should be identified and verified.",
      "For example, for a company that is publicly listed on the stock exchange and has thousands of shareholders, a notional beneficial owner could be the president or chief executive officer, or equivalent."
    ],
    "relation_cues": [
      "where",
      "should",
      "for example",
      "could"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "公司不存在自然人受益所有人"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "识别并核实控制人或名义受益所有人",
      "outcomes_or_paths": [
        "控制人或名义受益所有人被记录"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000496",
        "quote": "In companies where there is no natural beneficial owner, a controller or a notional beneficial owner should be identified and verified."
      },
      {
        "unit_id": "v7u_N000497",
        "quote": "For example, for a company that is publicly listed on the stock exchange and has thousands of shareholders, a notional beneficial owner could be the president or chief executive officer, or equivalent."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
