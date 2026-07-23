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

section_id: `CH12-S02`

section_title: `Money laundering risks associated with insurance, securities, brokerage, and custodian services > Case example: Investment product misuse`

section_text_with_unit_anchors:

```text
[v7u_N000893|893] Peter, a recent retiree living in the Cayman Islands, received a lump-sum pension payment of US$100,000. Seeking to invest, he approached his broker, Tom, who recommended an investment-linked insurance (ILI) policy with premium financing. Tom highlighted the appeal of ILIs, which combine insurance protection with investment potential.
ZH: 案例：退休人员Peter获得10万美元养老金，经纪人Tom推荐投资连结保险并采用保费融资

[v7u_N000894|894] The policy was valued at US$100,000, but Peter only needed to contribute US$30,000 upfront. The remaining US$70,000 would be financed at a 10% annual interest rate.
ZH: 保单价值10万美元，Peter仅需预付3万美元，剩余7万美元以年利率10%融资

[v7u_N000895|895] Tom noted that many clients used this structure to enhance returns.
ZH: Tom称许多客户使用此结构来提高回报

[v7u_N000896|896] The investment fund linked to the policy had reportedly delivered 15% annual returns in the past.
ZH: 该保单挂钩的投资基金过去曾实现15%的年回报率

[v7u_N000897|897] Peter believed the gains would cover the interest and yield a profit.
ZH: Peter相信收益能覆盖利息并产生利润

[v7u_N000898|898] However, a year later, Peter discovered his investment had lost 50% of its value. He tried contacting Tom without success and eventually escalated his complaint to the insurance company. The matter reached Mary, the compliance manager, who had recently strengthened the company’s AML and AFC framework and was actively monitoring for suspicious activity.
ZH: 一年后投资亏损50%，Peter投诉至保险公司，合规经理Mary已加强反洗钱框架并监控可疑活动

[v7u_N000899|899] Mary’s analytics had already flagged Tom’s transactions as unusual. Peter’s complaint confirmed her concerns and triggered a deeper investigation. Several red flags emerged:
ZH: Mary的分析已标记Tom的交易异常，Peter的投诉确认了担忧并触发深入调查，出现若干红旗信号信号

[v7u_N000900|900] Tom’s brother owned the finance company providing premium loans to Tom’s clients.
ZH: Tom的兄弟拥有为Tom客户提供保费贷款的金融公司

[v7u_N000901|901] Tom and his wife owned an offshore investment firm managing the policy funds, which appeared unlicensed.
ZH: Tom与妻子拥有一家离岸投资公司，管理保单资金，该公司似乎无牌经营。

[v7u_N000902|902] The promised 15% returns were inconsistent with market norms.
ZH: 承诺15%的回报率与市场常态不符。

[v7u_N000903|903] Recognizing the risks, Mary reported her findings and recommended immediate actions:
ZH: Mary识别风险后报告发现并建议立即采取行动。

[v7u_N000904|904] Apply enhanced due diligence to brokers and affiliated entities involved in ILIs.
ZH: 对涉及投资连结保险的经纪人和关联实体实施强化尽职调查。

[v7u_N000905|905] Monitor ownership structures to detect conflicts of interest and prevent collusion.
ZH: 监控所有权结构以发现利益冲突并防止串通。

[v7u_N000906|906] Require employees and agents to declare external business interests, including those of close associates.
ZH: 要求员工和代理人申报外部商业利益，包括密切关联方的利益。

[v7u_N000907|907] Provide targeted AML training to brokers, emphasizing red flags and compliance obligations.
ZH: 向经纪人提供针对性的反洗钱培训，强调红旗信号信号和合规义务。

[v7u_N000908|908] Tom was ultimately dismissed following evidence of collusion and misrepresentation.
ZH: Tom因串通和虚假陈述的证据最终被解雇。
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N000899"
    ],
    "proposition": "Mary的分析已标记Tom的交易异常，Peter的投诉确认了担忧并触发深入调查。",
    "source_quotes": [
      "Mary’s analytics had already flagged Tom’s transactions as unusual. Peter’s complaint confirmed her concerns and triggered a deeper investigation."
    ],
    "relation_cues": [
      "flagged",
      "confirmed",
      "triggered"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "交易已被标记为异常",
        "投诉确认了担忧"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "触发深入调查",
      "outcomes_or_paths": [
        "若干红旗信号出现"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000899",
        "quote": "Mary’s analytics had already flagged Tom’s transactions as unusual. Peter’s complaint confirmed her concerns and triggered a deeper investigation."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N000903",
      "v7u_N000904",
      "v7u_N000905",
      "v7u_N000906",
      "v7u_N000907"
    ],
    "proposition": "Mary识别风险后报告发现并建议立即采取行动，包括强化尽职调查、监控所有权、要求申报和提供培训。",
    "source_quotes": [
      "Recognizing the risks, Mary reported her findings and recommended immediate actions:",
      "Apply enhanced due diligence to brokers and affiliated entities involved in ILIs.",
      "Monitor ownership structures to detect conflicts of interest and prevent collusion.",
      "Require employees and agents to declare external business interests, including those of close associates.",
      "Provide targeted AML training to brokers, emphasizing red flags and compliance obligations."
    ],
    "relation_cues": [
      "Recognizing",
      "reported",
      "recommended"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "识别出风险（红旗信号）"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "报告发现并建议立即行动",
      "outcomes_or_paths": [
        "对涉及投资连结保险的经纪人和关联实体实施强化尽职调查",
        "监控所有权结构以发现利益冲突并防止串通",
        "要求员工和代理人申报外部商业利益",
        "向经纪人提供针对性的反洗钱培训"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000903",
        "quote": "Recognizing the risks, Mary reported her findings and recommended immediate actions:"
      },
      {
        "unit_id": "v7u_N000904",
        "quote": "Apply enhanced due diligence to brokers and affiliated entities involved in ILIs."
      },
      {
        "unit_id": "v7u_N000905",
        "quote": "Monitor ownership structures to detect conflicts of interest and prevent collusion."
      },
      {
        "unit_id": "v7u_N000906",
        "quote": "Require employees and agents to declare external business interests, including those of close associates."
      },
      {
        "unit_id": "v7u_N000907",
        "quote": "Provide targeted AML training to brokers, emphasizing red flags and compliance obligations."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N000908"
    ],
    "proposition": "Tom因串通和虚假陈述的证据最终被解雇。",
    "source_quotes": [
      "Tom was ultimately dismissed following evidence of collusion and misrepresentation."
    ],
    "relation_cues": [
      "dismissed",
      "following"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "有串通和虚假陈述的证据"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "Tom被解雇",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000908",
        "quote": "Tom was ultimately dismissed following evidence of collusion and misrepresentation."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
