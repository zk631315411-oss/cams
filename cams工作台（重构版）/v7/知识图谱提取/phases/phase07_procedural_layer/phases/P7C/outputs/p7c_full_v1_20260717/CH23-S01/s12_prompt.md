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

section_id: `CH23-S01`

section_title: `Case example: Drafting policies for an AFC department based in APAC`

section_text_with_unit_anchors:

```text
[v7u_N001665|1665] Understand risks
ZH: 案例步骤标签：了解风险

[v7u_N001666|1666] Identify regulations and guidance
ZH: 案例步骤标签：识别法规与指引

[v7u_N001667|1667] Map requirements and draft policies
ZH: 案例步骤标签：映射要求并起草政策

[v7u_N001668|1668] Implement policies
ZH: 案例步骤标签：实施政策

[v7u_N001669|1669] Hiroshi is working for a newly incorporated financial institution based in the Asia-Pacific (APAC) region and was asked to set up policies and procedures for the AFC department. One of his tasks is to identify relevant reports and guidance papers that would impact AFC controls.
ZH: Hiroshi受命为APAC新设金融机构建立金融犯罪防控政策和程序

[v7u_N001670|1670] To begin, Hiroshi must understand the financial crime risks his organization will face. He asks himself if his organization is exposed to corruption, fraud, money laundering, or sanctions risks. He also begins listing the laws and regulations that combat these risks, including CDD and other AML standards.
ZH: Hiroshi首先评估组织面临的金融犯罪风险，包括腐败、欺诈、洗钱和制裁

[v7u_N001671|1671] During Hiroshi's research, he identifies several guidance papers that could apply to his work.
ZH: Hiroshi在研究过程中识别出多份可适用的指引文件

[v7u_N001672|1672] Because his organization will be active in cross-border transactions, he needs to consider regulations and standards within the APAC region as well as other jurisdictions.
ZH: 因涉及跨境交易，需考虑APAC及其他司法管辖区的法规

[v7u_N001673|1673] Hiroshi references the AFC regulations in both the US and EU because some of the cross-border transactions involve those jurisdictions.
ZH: Hiroshi参考美国和欧盟的金融犯罪防控法规，因跨境交易涉及这些地区

[v7u_N001674|1674] And because his organization conducts transactions in virtual assets, he also considers regulations related to this sector.
ZH: 因涉及虚拟资产交易，Hiroshi考虑相关虚拟资产法规

[v7u_N001675|1675] Additionally, since cross-border transactions involve customers’ data, Hiroshi must account for data-related regulations in his organization's policies and procedures.
ZH: 跨境交易涉及客户数据，Hiroshi必须在政策中考虑数据相关法规

[v7u_N001676|1676] For example, he remembers that the EU’s General Data Protection Regulation sets a higher data standard than those of most of the APAC jurisdictions.
ZH: 欧盟《通用数据保护条例》的数据标准高于大多数APAC司法管辖区

[v7u_N001677|1677] Similarly, the Chinese Data Security Law prohibits organizations from transferring certain commercial data out of China.
ZH: 中国数据安全法禁止将特定商业数据转移出中国

[v7u_N001678|1678] Hiroshi's research does not stop there. He also considers emerging compliance topics such as the environmental, social, and governance framework and the use of AI in AFC efforts.
ZH: Hiroshi还考虑ESG框架和AI在金融犯罪防控中的应用等新兴合规议题

[v7u_N001679|1679] Once Hiroshi has identified the relevant regulations and regulatory authorities to include in his work, he determines which business products and services these controls will affect.
ZH: Hiroshi确定相关法规和监管机构后，识别受影响的业务产品和服务

[v7u_N001680|1680] In his proposed policies, he states that continuously reviewing and monitoring relevant guidance, enforcement actions, and proposed policy changes from relevant sources are the keys to success.
ZH: Hiroshi提出持续审查和监控相关指引、执法行动和政策变化是成功关键

[v7u_N001681|1681] Hiroshi also mentions that his organization should incorporate the results of ongoing regulatory reviews into other AFC processes as appropriate, including the enterprise-wide risk assessment, training plan, and new business due diligence processes.
ZH: 将监管审查结果纳入其他金融犯罪防控流程
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N001672"
    ],
    "proposition": "因组织活跃于跨境交易，需考虑APAC及其他司法管辖区的法规。",
    "source_quotes": [
      "Because his organization will be active in cross-border transactions, he needs to consider regulations and standards within the APAC region as well as other jurisdictions."
    ],
    "relation_cues": [
      "because",
      "needs to consider"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "组织活跃于跨境交易"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "考虑APAC及其他司法管辖区的法规和标准",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001672",
        "quote": "Because his organization will be active in cross-border transactions, he needs to consider regulations and standards within the APAC region as well as other jurisdictions."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N001673"
    ],
    "proposition": "因跨境交易涉及美欧，参考美国和欧盟的金融犯罪防控法规。",
    "source_quotes": [
      "Hiroshi references the AFC regulations in both the US and EU because some of the cross-border transactions involve those jurisdictions."
    ],
    "relation_cues": [
      "because",
      "references"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "跨境交易涉及美国和欧盟"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "参考美国和欧盟的AFC法规",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001673",
        "quote": "Hiroshi references the AFC regulations in both the US and EU because some of the cross-border transactions involve those jurisdictions."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N001674"
    ],
    "proposition": "因组织从事虚拟资产交易，需考虑相关虚拟资产法规。",
    "source_quotes": [
      "And because his organization conducts transactions in virtual assets, he also considers regulations related to this sector."
    ],
    "relation_cues": [
      "because",
      "considers"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "组织从事虚拟资产交易"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "考虑虚拟资产相关法规",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001674",
        "quote": "And because his organization conducts transactions in virtual assets, he also considers regulations related to this sector."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N001675"
    ],
    "proposition": "因跨境交易涉及客户数据，必须考虑数据相关法规并纳入政策程序。",
    "source_quotes": [
      "Additionally, since cross-border transactions involve customers’ data, Hiroshi must account for data-related regulations in his organization's policies and procedures."
    ],
    "relation_cues": [
      "since",
      "must account for"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "跨境交易涉及客户数据"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "在组织的政策和程序中考虑数据相关法规",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001675",
        "quote": "Additionally, since cross-border transactions involve customers’ data, Hiroshi must account for data-related regulations in his organization's policies and procedures."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N001679"
    ],
    "proposition": "识别相关法规和监管机构后，确定这些控制将影响的业务产品和服务。",
    "source_quotes": [
      "Once Hiroshi has identified the relevant regulations and regulatory authorities to include in his work, he determines which business products and services these controls will affect."
    ],
    "relation_cues": [
      "once",
      "determines"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "已识别相关法规和监管机构"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "确定受控制的业务产品和服务",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001679",
        "quote": "Once Hiroshi has identified the relevant regulations and regulatory authorities to include in his work, he determines which business products and services these controls will affect."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N001681"
    ],
    "proposition": "应将持续监管审查的结果适当地纳入其他金融犯罪防控流程，包括全机构风险评估、培训计划和新业务尽职调查。",
    "source_quotes": [
      "Hiroshi also mentions that his organization should incorporate the results of ongoing regulatory reviews into other AFC processes as appropriate, including the enterprise-wide risk assessment, training plan, and new business due diligence processes."
    ],
    "relation_cues": [
      "should incorporate",
      "as appropriate"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "进行持续监管审查"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "将审查结果纳入其他AFC流程",
      "outcomes_or_paths": [
        "全机构风险评估",
        "培训计划",
        "新业务尽职调查"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001681",
        "quote": "Hiroshi also mentions that his organization should incorporate the results of ongoing regulatory reviews into other AFC processes as appropriate, including the enterprise-wide risk assessment, training plan, and new business due diligence processes."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
