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

section_id: `CH36-S01`

section_title: `Types of risk assessment > The importance of risk assessment in AFC`

section_text_with_unit_anchors:

```text
[v7u_N002630|2630] FATF Recommendation 1 states, “Countries should identify, assess, and understand the money laundering and terrorist financing risks for the country, and should take action, including designating an authority or mechanism to coordinate actions to assess risks, and apply resources, aimed at ensuring the risks are mitigated effectively.”
ZH: FATF建议1要求各国识别、评估并了解洗钱和恐怖融资风险，并采取协调行动

[v7u_N002631|2631] Risk assessments and the risk-based approach (RBA) are important for understanding and analyzing risks.
ZH: 风险评估和风险为本方法对于理解与分析风险至关重要

[v7u_N002632|2632] Taking necessary measures to mitigate risks minimizes their effects on a country or entity.
ZH: 采取必要措施减轻风险可最小化其对国家或实体的影响

[v7u_N002633|2633] The FATF Interpretive Note to Recommendation 1 also highlights the importance of the RBA.
ZH: FATF建议1的释义说明强调了风险为本方法的重要性

[v7u_N002634|2634] National risk assessment (NRA)
ZH: 国家风险评估（NRA）作为风险评估类型之一

[v7u_N002635|2635] Sectoral risk assessment (SRA)
ZH: 行业风险评估（SRA）作为风险评估类型之一

[v7u_N002636|2636] Enterprise-wide risk assessment (EWRA)
ZH: 企业风险评估（EWRA）作为风险评估类型之一

[v7u_N002637|2637] Risks can vary in their nature, scale, and impact.
ZH: 风险在性质、规模和影响上可能各不相同

[v7u_N002638|2638] An RBA requires countries and financial institutions to prioritize risks and apply appropriate measures based on their level of exposure.
ZH: 风险为本方法要求国家和金融机构根据风险暴露程度优先排序并采取适当措施

[v7u_N002639|2639] Not every risk applies to every institution.
ZH: 并非所有风险都适用于每个机构

[v7u_N002640|2640] Understanding these factors will allow financial institutions to make informed decisions to balance risk and reward.
ZH: 理解这些因素使金融机构能够做出平衡风险与回报的明智决策

[v7u_N002641|2641] Three main types of risk assessments are national risk assessments (NRA), sectoral risk assessments (SRA), and enterprise-wide risk assessments (EWRA).
ZH: 三种主要风险评估类型：国家风险评估、行业风险评估和企业全面风险评估

[v7u_N002642|2642] NRAs identify national-level money laundering and terror financing threats and risks. These assessments review sectors and areas with higher risks.
ZH: 国家风险评估识别国家层面的洗钱与恐怖融资威胁和风险，并审查高风险行业

[v7u_N002643|2643] Financial institutions are required to apply enhanced measures to mitigate these risks.
ZH: 金融机构必须采取强化措施以缓解风险

[v7u_N002644|2644] SRAs are performed by national authorities, supervisory bodies, regulators, and international organizations. These assessments identify, assess, and analyze money laundering and terror financing risks specific to an industry or sector.
ZH: 行业风险评估由国家机关、监管机构等执行，识别并分析特定行业的洗钱与恐怖融资风险

[v7u_N002645|2645] EWRAs analyze and evaluate money laundering and terror financing risks identified within an organization.
ZH: 企业全面风险评估分析并评估组织内部识别的洗钱与恐怖融资风险

[v7u_N002646|2646] These assessments are tailored to the specific organization conducting the assessment and consider customer characteristics, jurisdictions, products, and delivery channels.
ZH: 企业全面风险评估根据组织自身情况定制，考虑客户、地域、产品和渠道特征

[v7u_N002647|2647] The process begins by establishing inherent risks, assessing the effectiveness of controls, computing the residual risk, and obtaining a clear action plan on mitigating the highest risks.
ZH: 企业全面风险评估流程：确定固有风险、评估控制有效性、计算剩余风险、制定行动计划

[v7u_N002648|2648] Business leaders can use the EWRA to assess potential risks and estimate the cost to serve. This helps them make informed decisions about whether to expand or pursue new ventures.
ZH: 企业领导者可利用企业全面风险评估评估潜在风险和成本，辅助业务扩张决策

[v7u_N002649|2649] For example, when entering high-risk areas, the business unit’s EWRA helps evaluate the financial and operational impact, enabling leaders to understand the costs involved to be compliant. EWRAs should include consideration of the risks identified in the NRAs and SRAs for any jurisdiction in which they do business or plan to do business. NRAs and SRAs help organizations manage internal risks by using insights from national and sector-specific risk assessments. By conducting these risk assessments, organizations can:
ZH: 企业全面风险评估应纳入国家风险评估和行业风险评估的见解，以管理内部风险

[v7u_N002650|2650] Allocate resources efficiently by making informed decisions based on risk levels.
ZH: 根据风险水平做出明智决策，有效分配资源

[v7u_N002651|2651] Manage risks associated with customers, jurisdictions, products, and delivery channels by applying targeted measures according to regulatory expectations.
ZH: 通过针对客户、地域、产品和渠道采取针对性措施管理风险

[v7u_N002652|2652] Enhance AFC controls by identifying vulnerabilities and exposures and safeguarding institutions against regulatory enforcements.
ZH: 通过识别漏洞和风险敞口加强金融犯罪防控，保护机构免受监管执法

[v7u_N002653|2653] These risk assessments should be interrelated to foster an effective, riskbased AFC framework.
ZH: 各类风险评估应相互关联，以形成有效的基于风险的金融犯罪防控框架
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002630"
    ],
    "proposition": "FATF建议1要求各国识别、评估和理解洗钱与恐怖融资风险，并指定协调机构、应用资源以有效缓解风险。",
    "source_quotes": [
      "FATF Recommendation 1 states, “Countries should identify, assess, and understand the money laundering and terrorist financing risks for the country, and should take action, including designating an authority or mechanism to coordinate actions to assess risks, and apply resources, aimed at ensuring the risks are mitigated effectively.”"
    ],
    "relation_cues": [
      "should"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "需要应对洗钱和恐怖融资风险"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "国家识别、评估并理解风险",
      "outcomes_or_paths": [
        "指定协调机构，应用资源，确保风险有效缓解"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002630",
        "quote": "FATF Recommendation 1 states, “Countries should identify, assess, and understand the money laundering and terrorist financing risks for the country, and should take action, including designating an authority or mechanism to coordinate actions to assess risks, and apply resources, aimed at ensuring the risks are mitigated effectively.”"
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002638"
    ],
    "proposition": "风险为本方法要求国家和金融机构根据风险暴露程度优先排序风险并采取适当措施。",
    "source_quotes": [
      "An RBA requires countries and financial institutions to prioritize risks and apply appropriate measures based on their level of exposure."
    ],
    "relation_cues": [
      "requires",
      "based on"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "需要管理风险"
      ],
      "basis_or_condition": [
        "基于风险暴露程度"
      ],
      "focal_handling_or_judgment": "优先排序风险并应用适当措施",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002638",
        "quote": "An RBA requires countries and financial institutions to prioritize risks and apply appropriate measures based on their level of exposure."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002642",
      "v7u_N002643"
    ],
    "proposition": "国家风险评估识别高风险领域后，金融机构需采取强化措施缓解风险。",
    "source_quotes": [
      "NRAs identify national-level money laundering and terror financing threats and risks. These assessments review sectors and areas with higher risks.",
      "Financial institutions are required to apply enhanced measures to mitigate these risks."
    ],
    "relation_cues": [
      "review",
      "required to apply"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "需要识别国家层面的洗钱和恐怖融资风险"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "进行国家风险评估，审查高风险行业",
      "outcomes_or_paths": [
        "金融机构需采取强化措施缓解风险"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002642",
        "quote": "NRAs identify national-level money laundering and terror financing threats and risks. These assessments review sectors and areas with higher risks."
      },
      {
        "unit_id": "v7u_N002643",
        "quote": "Financial institutions are required to apply enhanced measures to mitigate these risks."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N002645",
      "v7u_N002646",
      "v7u_N002647",
      "v7u_N002648",
      "v7u_N002649"
    ],
    "proposition": "企业全面风险评估（EWRA）分析组织内部风险，流程包括确定固有风险、评估控制有效性、计算剩余风险和制定行动计划；领导者可用其评估潜在风险和成本以支持决策；EWRA应考虑国家风险评估和行业风险评估的发现。",
    "source_quotes": [
      "EWRAs analyze and evaluate money laundering and terror financing risks identified within an organization.",
      "These assessments are tailored to the specific organization conducting the assessment and consider customer characteristics, jurisdictions, products, and delivery channels.",
      "The process begins by establishing inherent risks, assessing the effectiveness of controls, computing the residual risk, and obtaining a clear action plan on mitigating the highest risks.",
      "Business leaders can use the EWRA to assess potential risks and estimate the cost to serve. This helps them make informed decisions about whether to expand or pursue new ventures.",
      "For example, when entering high-risk areas, the business unit’s EWRA helps evaluate the financial and operational impact, enabling leaders to understand the costs involved to be compliant. EWRAs should include consideration of the risks identified in the NRAs and SRAs for any jurisdiction in which they do business or plan to do business."
    ],
    "relation_cues": [
      "analyze",
      "evaluate",
      "begins by",
      "assess",
      "estimate",
      "helps",
      "should include"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "组织需要评估其洗钱和恐怖融资风险"
      ],
      "basis_or_condition": [
        "考虑客户、地域、产品和渠道特征",
        "考虑NRA和SRA的发现"
      ],
      "focal_handling_or_judgment": "进行企业全面风险评估，包括评估控制、计算剩余风险",
      "outcomes_or_paths": [
        "获得行动计划",
        "支持业务扩张决策",
        "评估进入高风险地区的财务和运营影响"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002645",
        "quote": "EWRAs analyze and evaluate money laundering and terror financing risks identified within an organization."
      },
      {
        "unit_id": "v7u_N002646",
        "quote": "These assessments are tailored to the specific organization conducting the assessment and consider customer characteristics, jurisdictions, products, and delivery channels."
      },
      {
        "unit_id": "v7u_N002647",
        "quote": "The process begins by establishing inherent risks, assessing the effectiveness of controls, computing the residual risk, and obtaining a clear action plan on mitigating the highest risks."
      },
      {
        "unit_id": "v7u_N002648",
        "quote": "Business leaders can use the EWRA to assess potential risks and estimate the cost to serve. This helps them make informed decisions about whether to expand or pursue new ventures."
      },
      {
        "unit_id": "v7u_N002649",
        "quote": "For example, when entering high-risk areas, the business unit’s EWRA helps evaluate the financial and operational impact, enabling leaders to understand the costs involved to be compliant. EWRAs should include consideration of the risks identified in the NRAs and SRAs for any jurisdiction in which they do business or plan to do business."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
