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

section_id: `CH41-S03`

section_title: `Governance and oversight > Maintaining effective AFC policies and procedures`

section_text_with_unit_anchors:

```text
[v7u_N002917|2917] Regulated organizations are required to maintain written AFC policies and procedures that mitigate and manage the risks of money laundering and terrorist financing.
ZH: 受监管机构须制定书面金融犯罪防控政策和程序以管理和降低洗钱与恐怖融资风险。

[v7u_N002918|2918] Organizations should regularly review and update these policies and procedures, typically on an annual basis, although the nature of the risks the organization is encountering should drive the frequency.
ZH: 机构应定期（通常每年）审查和更新金融犯罪防控政策，频率应基于风险性质。

[v7u_N002919|2919] Organizations should also conduct reviews in response to events that might change their risk profile, such as a new business or jurisdiction, or the results of an audit or regulatory examination.
ZH: 机构还应在可能改变风险状况的事件（如新业务、新司法管辖区或审计结果）发生后进行审查。

[v7u_N002920|2920] Failure to update policies on a continuous basis might result in a failure to address new risks until the next scheduled review.
ZH: 未能持续更新政策可能导致新风险在下次定期审查前未被处理。

[v7u_N002921|2921] Additionally, organizations need to maintain awareness of emerging issues and regulatory activity. This “horizon scanning” is particularly important because the AFC environment is highly dynamic.
ZH: 由于金融犯罪防控环境高度动态，组织需要进行地平线扫描以关注新兴问题和监管动态。

[v7u_N002922|2922] It could take many months or even years to implement new processes.
ZH: 实施新流程可能需要数月甚至数年时间。

[v7u_N002923|2923] Proactive horizon scanning helps organizations plan, resource, and implement new policies in a timely and effective manner.
ZH: 主动的地平线扫描有助于组织及时有效地规划、资源配置和实施新政策。

[v7u_N002924|2924] The development and approval of policies should include the participation of legal counsel, other internal stakeholders, and external experts where appropriate.
ZH: 政策的制定和批准应包含法律顾问、其他内部利益相关方以及适当的外部专家参与。

[v7u_N002925|2925] Once approved, policies and procedures should be accessible to all employees on an ongoing basis.
ZH: 批准后的政策和程序应持续对所有员工开放可访问。

[v7u_N002926|2926] Organizations should approve, document, and promptly communicate to their staff any changes to policies and procedures.
ZH: 组织应批准、记录并及时向员工传达政策和程序的任何变更。

[v7u_N002927|2927] AFC policies and procedures should be tailored to the specific risk profile, risk appetite, and size of the organization.
ZH: 金融犯罪防控政策和程序应根据组织的具体风险状况、风险偏好和规模量身定制。

[v7u_N002928|2928] Global organizations should conduct gap analyses as part of their review and horizon scanning processes to ensure the policy covers relevant local regulations in the jurisdictions in which they operate.
ZH: 全球性组织应进行差距分析，确保政策涵盖其运营所在司法管辖区的相关当地法规。

[v7u_N002929|2929] This may also require regional or local policies and procedures to reflect the local laws, regulations, and risks, as long as they do not conflict with the organization's global policy.
ZH: 区域或地方政策可反映当地法律、法规和风险，前提是不与组织的全球政策冲突。
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002917"
    ],
    "proposition": "受监管机构必须制定书面金融犯罪防控政策和程序，以降低和管理洗钱与恐怖融资风险。",
    "source_quotes": [
      "Regulated organizations are required to maintain written AFC policies and procedures that mitigate and manage the risks of money laundering and terrorist financing."
    ],
    "relation_cues": [
      "required to",
      "mitigate and manage"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "受监管机构"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "制定书面金融犯罪防控政策和程序",
      "outcomes_or_paths": [
        "降低和管理洗钱与恐怖融资风险"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002917",
        "quote": "Regulated organizations are required to maintain written AFC policies and procedures that mitigate and manage the risks of money laundering and terrorist financing."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002918"
    ],
    "proposition": "机构应定期（通常每年）审查和更新金融犯罪防控政策和程序，审查频率由机构面临的风险性质决定。",
    "source_quotes": [
      "Organizations should regularly review and update these policies and procedures, typically on an annual basis, although the nature of the risks the organization is encountering should drive the frequency."
    ],
    "relation_cues": [
      "should",
      "typically",
      "although",
      "should drive"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "风险性质决定审查频率"
      ],
      "focal_handling_or_judgment": "定期审查和更新金融犯罪防控政策和程序",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002918",
        "quote": "Organizations should regularly review and update these policies and procedures, typically on an annual basis, although the nature of the risks the organization is encountering should drive the frequency."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002919"
    ],
    "proposition": "机构应在可能改变其风险状况的事件（如新业务、新司法管辖区或审计结果）发生后进行审查。",
    "source_quotes": [
      "Organizations should also conduct reviews in response to events that might change their risk profile, such as a new business or jurisdiction, or the results of an audit or regulatory examination."
    ],
    "relation_cues": [
      "should",
      "in response to",
      "might"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "可能改变风险状况的事件（新业务、新司法管辖区、审计或监管检查结果）"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "进行审查",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002919",
        "quote": "Organizations should also conduct reviews in response to events that might change their risk profile, such as a new business or jurisdiction, or the results of an audit or regulatory examination."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N002921",
      "v7u_N002923"
    ],
    "proposition": "由于金融犯罪防控环境高度动态，机构需要进行地平线扫描以关注新兴问题和监管动态，这有助于及时有效地规划、资源配置和实施新政策。",
    "source_quotes": [
      "Additionally, organizations need to maintain awareness of emerging issues and regulatory activity. This “horizon scanning” is particularly important because the AFC environment is highly dynamic.",
      "Proactive horizon scanning helps organizations plan, resource, and implement new policies in a timely and effective manner."
    ],
    "relation_cues": [
      "need to",
      "because",
      "helps"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "金融犯罪防控环境高度动态"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "进行地平线扫描，关注新兴问题和监管动态",
      "outcomes_or_paths": [
        "及时有效地规划、资源配置和实施新政策"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002921",
        "quote": "Additionally, organizations need to maintain awareness of emerging issues and regulatory activity. This “horizon scanning” is particularly important because the AFC environment is highly dynamic."
      },
      {
        "unit_id": "v7u_N002923",
        "quote": "Proactive horizon scanning helps organizations plan, resource, and implement new policies in a timely and effective manner."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N002924"
    ],
    "proposition": "政策的制定和批准应包含法律顾问、其他内部利益相关方以及适当的外部专家参与。",
    "source_quotes": [
      "The development and approval of policies should include the participation of legal counsel, other internal stakeholders, and external experts where appropriate."
    ],
    "relation_cues": [
      "should include",
      "where appropriate"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "政策的制定和批准"
      ],
      "basis_or_condition": [
        "适当情况下"
      ],
      "focal_handling_or_judgment": "包括法律顾问、内部利益相关方和外部专家参与",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002924",
        "quote": "The development and approval of policies should include the participation of legal counsel, other internal stakeholders, and external experts where appropriate."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N002925"
    ],
    "proposition": "批准后的政策和程序应持续对所有员工开放可访问。",
    "source_quotes": [
      "Once approved, policies and procedures should be accessible to all employees on an ongoing basis."
    ],
    "relation_cues": [
      "Once",
      "should be accessible"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "批准后"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "政策和程序应持续对所有员工开放可访问",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002925",
        "quote": "Once approved, policies and procedures should be accessible to all employees on an ongoing basis."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_007",
    "unit_ids": [
      "v7u_N002926"
    ],
    "proposition": "组织应批准、记录并及时向员工传达政策和程序的任何变更。",
    "source_quotes": [
      "Organizations should approve, document, and promptly communicate to their staff any changes to policies and procedures."
    ],
    "relation_cues": [
      "should",
      "communicate to"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "批准、记录并及时向员工传达政策和程序变更",
      "outcomes_or_paths": [
        "员工获知变更"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002926",
        "quote": "Organizations should approve, document, and promptly communicate to their staff any changes to policies and procedures."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_008",
    "unit_ids": [
      "v7u_N002927"
    ],
    "proposition": "金融犯罪防控政策和程序应根据组织的风险状况、风险偏好和规模量身定制。",
    "source_quotes": [
      "AFC policies and procedures should be tailored to the specific risk profile, risk appetite, and size of the organization."
    ],
    "relation_cues": [
      "should be tailored to"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "组织的具体风险状况、风险偏好和规模"
      ],
      "focal_handling_or_judgment": "量身定制金融犯罪防控政策和程序",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002927",
        "quote": "AFC policies and procedures should be tailored to the specific risk profile, risk appetite, and size of the organization."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_009",
    "unit_ids": [
      "v7u_N002928"
    ],
    "proposition": "全球性组织应在其审查和地平线扫描过程中进行差距分析，以确保政策涵盖其运营所在司法管辖区的相关当地法规。",
    "source_quotes": [
      "Global organizations should conduct gap analyses as part of their review and horizon scanning processes to ensure the policy covers relevant local regulations in the jurisdictions in which they operate."
    ],
    "relation_cues": [
      "should conduct",
      "as part of",
      "to ensure"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "审查和地平线扫描过程"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "进行差距分析",
      "outcomes_or_paths": [
        "确保政策涵盖相关当地法规"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002928",
        "quote": "Global organizations should conduct gap analyses as part of their review and horizon scanning processes to ensure the policy covers relevant local regulations in the jurisdictions in which they operate."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_010",
    "unit_ids": [
      "v7u_N002929"
    ],
    "proposition": "区域或地方政策可反映当地法律、法规和风险，前提是不与组织的全球政策冲突。",
    "source_quotes": [
      "This may also require regional or local policies and procedures to reflect the local laws, regulations, and risks, as long as they do not conflict with the organization's global policy."
    ],
    "relation_cues": [
      "may require",
      "as long as"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "不与全球政策冲突"
      ],
      "focal_handling_or_judgment": "区域或地方政策反映当地法律、法规和风险",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002929",
        "quote": "This may also require regional or local policies and procedures to reflect the local laws, regulations, and risks, as long as they do not conflict with the organization's global policy."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
