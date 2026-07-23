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

section_id: `CH38-S01`

section_title: `The importance of continuous risk assessment > Continuously assessing financial crime risk`

section_text_with_unit_anchors:

```text
[v7u_N002823|2823] Financial crime risks are dynamic and constantly evolving.
ZH: 金融犯罪风险是动态且不断演变的

[v7u_N002824|2824] Criminals will always attempt to move illicit funds through the financial sector undetected. They will use new technologies and trends, regardless of the controls that organizations establish. Criminals continuously search for loopholes to exploit and test the resilience of AFC frameworks.
ZH: 犯罪分子持续利用新技术寻找漏洞以不被察觉地转移非法资金

[v7u_N002825|2825] Organizations must reevaluate risks whenever there is a material change to their business. This could include higher-risk product offerings, entering a new market, or changes in jurisdictions where the organization operates.
ZH: 组织在业务发生重大变化时必须重新评估风险

[v7u_N002826|2826] Continuously assessing financial crime risk helps organizations adapt to evolving ML/TF techniques and threats, monitor transactions to detect patterns and significant changes, respond to emerging geographical risks, and meet regulations and international standards.
ZH: 持续评估金融犯罪风险有助于组织适应不断变化的洗钱/恐怖融资手法和威胁

[v7u_N002827|2827] FATF and regulatory bodies promote a proactive approach to risk management and reassessing risks as required. This approach, and regular risk assessments, enable organizations to divert their resources to high-risk areas to mitigate them effectively.
ZH: FATF和监管机构提倡主动风险管理，将资源转向高风险领域以有效缓解风险

[v7u_N002828|2828] In addition to conducting overarching enterprise-wide risk assessments regularly, organizations manage risk continually through CRAs.
ZH: 组织通过客户风险评估（CRA）持续管理风险

[v7u_N002829|2829] Organizations should conduct a CRA for every customer they onboard before establishing a business relationship with that customer. They should also review the CRA regularly and whenever there are changes in a customer’s behavior and risk profile. These changes might include:
ZH: 组织应在建立业务关系前对每位客户进行CRA，并定期或在客户行为变化时审查

[v7u_N002830|2830] Transaction pattern deviations.
ZH: 交易模式偏离是触发CRA审查的变化之一

[v7u_N002831|2831] Requests for new products or services.
ZH: 客户请求新产品或服务是触发CRA审查的变化之一

[v7u_N002832|2832] Reluctance to provide information or documentation.
ZH: 客户不愿提供信息或文件是触发CRA审查的变化之一

[v7u_N002833|2833] Increased exposure to high-risk jurisdictions.
ZH: 客户对高风险司法管辖区的敞口增加是触发CRA审查的变化之一

[v7u_N002834|2834] Changes in the customer’s sector.
ZH: 客户所在行业发生变化是触发CRA审查的变化之一

[v7u_N002835|2835] Changes in how the organization operates, such as changing product lines or shifting to online business operations.
ZH: 组织运营方式变化（如产品线变更或转向线上业务）是触发CRA审查的变化之一

[v7u_N002836|2836] CRAs enable organizations to detect changes in customer behavior and reassess risks.
ZH: CRA使组织能够检测客户行为变化并重新评估风险

[v7u_N002837|2837] For example, if an organization detects that a customer plans to extend its sales to high-risk jurisdictions, it might need to introduce enhanced measures such as increased third-party screening, request additional documentation, or increase transaction scrutiny.
ZH: 例如：客户扩展销售至高风险司法管辖区时，需采取增强措施如加强第三方筛查、要求额外文件或增加交易审查

[v7u_N002838|2838] Product and channel risk assessments enable organizations to detect deviations from the intended use of their products, helping to identify new threats or risks.
ZH: 产品和渠道风险评估有助于检测产品预期用途的偏离，识别新威胁或风险

[v7u_N002839|2839] Some risks might not be clear at product launch, but might be identified through ongoing monitoring.
ZH: 某些风险在产品推出时可能不明显，但可通过持续监控识别

[v7u_N002840|2840] For example, during COVID-19, organizations shifted to digital channels. This required aligning existing faceto-face channel controls to address emerging fraud risks, such as digital identity fraud, cross-border wire transfers, and new ways of verifying the authenticity of documentation.
ZH: 例如：疫情期间组织转向数字渠道，需调整现有面对面渠道控制以应对数字身份欺诈等新兴欺诈风险

[v7u_N002841|2841] These risk assessments help organizations continuously assess financial crime risks and enable them to take a holistic, proactive approach to manage and reassess risks as needed.
ZH: 风险持续评估帮助组织主动管理金融犯罪风险
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002825"
    ],
    "proposition": "当业务发生重大变化时，组织必须重新评估风险。",
    "source_quotes": [
      "Organizations must reevaluate risks whenever there is a material change to their business."
    ],
    "relation_cues": [
      "must",
      "whenever"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "业务发生重大变化"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "重新评估风险",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002825",
        "quote": "Organizations must reevaluate risks whenever there is a material change to their business."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002829",
      "v7u_N002830",
      "v7u_N002831",
      "v7u_N002832",
      "v7u_N002833",
      "v7u_N002834",
      "v7u_N002835"
    ],
    "proposition": "组织应在建立业务关系前对每位客户进行客户风险评估（CRA），并定期或在客户行为或风险状况变化时审查CRA。",
    "source_quotes": [
      "Organizations should conduct a CRA for every customer they onboard before establishing a business relationship with that customer. They should also review the CRA regularly and whenever there are changes in a customer’s behavior and risk profile.",
      "Transaction pattern deviations.",
      "Requests for new products or services.",
      "Reluctance to provide information or documentation.",
      "Increased exposure to high-risk jurisdictions.",
      "Changes in the customer’s sector.",
      "Changes in how the organization operates, such as changing product lines or shifting to online business operations."
    ],
    "relation_cues": [
      "should",
      "before",
      "whenever",
      "changes"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "建立业务关系前",
        "定期",
        "客户行为或风险状况变化"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "进行客户风险评估并审查",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002829",
        "quote": "Organizations should conduct a CRA for every customer they onboard before establishing a business relationship with that customer. They should also review the CRA regularly and whenever there are changes in a customer’s behavior and risk profile."
      },
      {
        "unit_id": "v7u_N002830",
        "quote": "Transaction pattern deviations."
      },
      {
        "unit_id": "v7u_N002831",
        "quote": "Requests for new products or services."
      },
      {
        "unit_id": "v7u_N002832",
        "quote": "Reluctance to provide information or documentation."
      },
      {
        "unit_id": "v7u_N002833",
        "quote": "Increased exposure to high-risk jurisdictions."
      },
      {
        "unit_id": "v7u_N002834",
        "quote": "Changes in the customer’s sector."
      },
      {
        "unit_id": "v7u_N002835",
        "quote": "Changes in how the organization operates, such as changing product lines or shifting to online business operations."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002837"
    ],
    "proposition": "如果发现客户计划将销售扩展至高危司法管辖区，则可能需要采取增强措施，如加强第三方筛查、要求额外文件或增加交易审查。",
    "source_quotes": [
      "For example, if an organization detects that a customer plans to extend its sales to high-risk jurisdictions, it might need to introduce enhanced measures such as increased third-party screening, request additional documentation, or increase transaction scrutiny."
    ],
    "relation_cues": [
      "if",
      "might",
      "such as"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "检测到客户计划扩展销售至高危司法管辖区"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "可能需要采取增强措施",
      "outcomes_or_paths": [
        "加强第三方筛查",
        "要求额外文件",
        "增加交易审查"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002837",
        "quote": "For example, if an organization detects that a customer plans to extend its sales to high-risk jurisdictions, it might need to introduce enhanced measures such as increased third-party screening, request additional documentation, or increase transaction scrutiny."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
