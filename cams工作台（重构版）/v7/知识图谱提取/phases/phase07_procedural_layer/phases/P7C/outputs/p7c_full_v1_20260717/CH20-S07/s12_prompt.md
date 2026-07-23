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

section_id: `CH20-S07`

section_title: `AFC guidance from leading international organizations > Wolfsberg Group AFC guidance`

section_text_with_unit_anchors:

```text
[v7u_N001563|1563] The Wolfsberg Group is an association of global banks that develop policies and guidance for managing financial crime risk.
ZH: 沃尔夫斯堡集团是由全球银行组成的协会，制定金融犯罪风险管理政策与指引

[v7u_N001564|1564] The group first came together in 2000 at the Château Wolfsberg in Switzerland, as part of a collaborative effort with representatives of Transparency International.
ZH: 沃尔夫斯堡集团于2000年在瑞士沃尔夫斯堡城堡成立，与透明国际合作

[v7u_N001565|1565] The group is made up of senior financial crime compliance personnel from member banks, representing the US, the UK, Switzerland, Germany, France, the Netherlands, Italy, Spain, and Japan.
ZH: 沃尔夫斯堡集团成员来自美国、英国、瑞士等九国的资深金融犯罪合规人员

[v7u_N001566|1566] The Wolfsberg Group issues guidelines to assist members in managing their risks, helping them make sound decisions about clients to protect their operations from criminal abuse.
ZH: 沃尔夫斯堡集团发布指引协助成员管理风险，保护业务免受犯罪滥用

[v7u_N001567|1567] Note that the group has no enforcement powers; therefore, its publications are designed to be adapted to its members’ needs and serve as guidance notes for financial institutions depending on their organizational risk, regulatory standards, and business profile.
ZH: 沃尔夫斯堡集团无执法权，其出版物为金融机构提供可调整的指引

[v7u_N001568|1568] The Wolfsberg Group routinely revises these principles to outline best practices for financial institutions to detect and mitigate risks associated with high-net-worth clients, PEPs, and offshore entities.
ZH: 沃尔夫斯堡集团定期修订原则，为高净值客户、政治敏感人物和离岸实体风险提供最佳实践

[v7u_N001569|1569] Key provisions include:
ZH: 沃尔夫斯堡集团指引的关键条款列表

[v7u_N001570|1570] KYC: Banks should verify client identities and assess their risk profiles.
ZH: 了解你的客户要求银行核实客户身份并评估风险状况

[v7u_N001571|1571] Due diligence: Banks should apply enhanced scrutiny for high-risk customers, particularly PEPs.
ZH: 对高风险客户特别是政治敏感人物应加强尽职调查

[v7u_N001572|1572] Source of wealth and funds: Banks should investigate and document how clients acquired their wealth.
ZH: 银行应调查并记录客户财富来源与资金来源

[v7u_N001573|1573] Ongoing monitoring: Banks should conduct continuous reviews of transactions to detect suspicious activities.
ZH: 银行应持续监控交易以发现可疑活动

[v7u_N001574|1574] It emphasizes that financial institutions should allocate resources based on the level of risk posed by a customer, transaction, or jurisdiction.
ZH: 金融机构应根据客户、交易或司法管辖区的风险水平分配资源

[v7u_N001575|1575] In 2014, the Wolfsberg Group published . Since its publication, the Wolfsberg Group has updated the principles that establish best practices for financial institutions engaging in cross-border banking relationships. The best practices include:
ZH: 沃尔夫斯堡集团2014年发布并更新跨境银行关系最佳实践原则

[v7u_N001576|1576] Considering 11 specific risk indicators when conducting due diligence. This includes assessing the risk of correspondent relationships, considering factors like jurisdiction, ownership structure, and regulatory compliance.
ZH: 尽职调查中考虑11项具体风险指标，包括司法管辖区、所有权结构和监管合规

[v7u_N001577|1577] Applying stricter scrutiny to high-risk relationships, such as those involving shell banks or offshore financial centers.
ZH: 对涉及空壳银行或离岸金融中心的高风险关系实施更严格审查
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N001570"
    ],
    "proposition": "银行在KYC中应核实客户身份并评估风险状况。",
    "source_quotes": [
      "KYC: Banks should verify client identities and assess their risk profiles."
    ],
    "relation_cues": [
      "should"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "KYC"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "核实客户身份并评估风险状况",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001570",
        "quote": "KYC: Banks should verify client identities and assess their risk profiles."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N001571"
    ],
    "proposition": "在尽职调查中，银行应对高风险客户特别是政治敏感人物实施加强审查。",
    "source_quotes": [
      "Due diligence: Banks should apply enhanced scrutiny for high-risk customers, particularly PEPs."
    ],
    "relation_cues": [
      "should",
      "particularly"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "尽职调查"
      ],
      "basis_or_condition": [
        "高风险客户，特别是PEPs"
      ],
      "focal_handling_or_judgment": "实施加强审查",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001571",
        "quote": "Due diligence: Banks should apply enhanced scrutiny for high-risk customers, particularly PEPs."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N001572"
    ],
    "proposition": "银行应调查并记录客户如何获取财富。",
    "source_quotes": [
      "Source of wealth and funds: Banks should investigate and document how clients acquired their wealth."
    ],
    "relation_cues": [
      "should"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "财富来源与资金来源"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "调查并记录客户财富来源",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001572",
        "quote": "Source of wealth and funds: Banks should investigate and document how clients acquired their wealth."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N001573"
    ],
    "proposition": "银行应持续监控交易以发现可疑活动。",
    "source_quotes": [
      "Ongoing monitoring: Banks should conduct continuous reviews of transactions to detect suspicious activities."
    ],
    "relation_cues": [
      "should",
      "to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "持续监控"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "对交易进行持续审查",
      "outcomes_or_paths": [
        "发现可疑活动"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001573",
        "quote": "Ongoing monitoring: Banks should conduct continuous reviews of transactions to detect suspicious activities."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N001574"
    ],
    "proposition": "金融机构应根据客户、交易或司法管辖区的风险水平分配资源。",
    "source_quotes": [
      "It emphasizes that financial institutions should allocate resources based on the level of risk posed by a customer, transaction, or jurisdiction."
    ],
    "relation_cues": [
      "should",
      "based on"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "分配资源"
      ],
      "basis_or_condition": [
        "基于客户、交易或司法管辖区的风险水平"
      ],
      "focal_handling_or_judgment": "金融机构分配资源",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001574",
        "quote": "It emphasizes that financial institutions should allocate resources based on the level of risk posed by a customer, transaction, or jurisdiction."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N001576"
    ],
    "proposition": "在进行尽职调查时，银行应考虑11项特定风险指标，包括司法管辖区、所有权结构和监管合规等。",
    "source_quotes": [
      "Considering 11 specific risk indicators when conducting due diligence. This includes assessing the risk of correspondent relationships, considering factors like jurisdiction, ownership structure, and regulatory compliance."
    ],
    "relation_cues": [
      "when",
      "including"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "进行尽职调查时"
      ],
      "basis_or_condition": [
        "11项特定风险指标，包括司法管辖区、所有权结构、监管合规等"
      ],
      "focal_handling_or_judgment": "考虑风险指标",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001576",
        "quote": "Considering 11 specific risk indicators when conducting due diligence. This includes assessing the risk of correspondent relationships, considering factors like jurisdiction, ownership structure, and regulatory compliance."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_007",
    "unit_ids": [
      "v7u_N001577"
    ],
    "proposition": "对于高风险关系，如涉及空壳银行或离岸金融中心，应实施更严格审查。",
    "source_quotes": [
      "Applying stricter scrutiny to high-risk relationships, such as those involving shell banks or offshore financial centers."
    ],
    "relation_cues": [
      "stricter",
      "such as"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "高风险关系，如涉及空壳银行或离岸金融中心"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "实施更严格审查",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001577",
        "quote": "Applying stricter scrutiny to high-risk relationships, such as those involving shell banks or offshore financial centers."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
