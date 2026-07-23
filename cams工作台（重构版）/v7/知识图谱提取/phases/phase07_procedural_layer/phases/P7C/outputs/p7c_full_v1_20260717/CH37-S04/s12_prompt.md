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

section_id: `CH37-S04`

section_title: `Enterprise-wide risk assessment > Residual risks action plan`

section_text_with_unit_anchors:

```text
[v7u_N002787|2787] Residual risk is computed based on an understanding of the inherent risk and the effectiveness of the control mitigating that risk.
ZH: 剩余风险基于固有风险和控制有效性计算

[v7u_N002788|2788] Once an organization understands its residual risks, it can determine whether the risk is within its tolerance levels or if an action plan is required to mitigate those risks.
ZH: 根据剩余风险判断是否在容忍度内或需要行动计划

[v7u_N002789|2789] For example, if a traditional financial institution realizes it has many customers making transfers to cryptoasset service providers in high-risk jurisdictions and no additional controls exist, the residual risk is high. The organization will need to develop a control to mitigate this risk, so the residual risk is within risk appetite. This may include a process of prohibiting transactions to certain known, unlicensed providers, or increasing the monitoring where the risk is high, even if it is within a licensing regime.
ZH: 向高风险地区加密资产服务商转账的剩余风险高，需加强控制

[v7u_N002790|2790] To develop a residual risks action plan, the organization must understand where the inherent risk originates and how mitigation measures can control the risk.
ZH: 制定剩余风险行动计划需了解固有风险来源及缓解措施

[v7u_N002791|2791] The organization should identify which risks existing AFC controls cannot mitigate.
ZH: 组织应识别现有金融犯罪防控控制无法缓解的风险

[v7u_N002792|2792] It should then evaluate whether other control measures, such as reducing transaction limits or limiting the number of products offered, would minimize the risks.
ZH: 评估其他控制措施如降低交易限额或限制产品数量

[v7u_N002793|2793] Ideally, the action plan would include a response strategy, such as additional monitoring or limiting transaction, in case the risk escalates.
ZH: 行动计划应包含风险升级时的应对策略，如额外监控或限制交易

[v7u_N002794|2794] The action plan consists of actions that the organization needs to implement across a range of residual risks. Some actions may address more than one residual risk.
ZH: 行动计划包含针对一系列剩余风险需实施的行动，一项行动可应对多个风险

[v7u_N002795|2795] A comprehensive plan would identify business owners, operational owners, due dates, and a process and frequency for reviewing and evaluating the risks associated with specific products or customer segments and their impact on the organization.
ZH: 全面计划应明确业务负责人、运营负责人、截止日期及审查频率

[v7u_N002796|2796] The plan would document who in the organization will be sponsoring the plan, and in which governance forum involved parties would report and escalate issues.
ZH: 计划需记录计划发起人及报告升级的治理论坛
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002788"
    ],
    "proposition": "基于对剩余风险的了解，组织可以判断风险是否在容忍度内或是否需要行动计划。",
    "source_quotes": [
      "Once an organization understands its residual risks, it can determine whether the risk is within its tolerance levels or if an action plan is required to mitigate those risks."
    ],
    "relation_cues": [
      "Once",
      "determine",
      "required"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "组织了解其剩余风险"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "判断风险是否在容忍度内或是否需要行动计划",
      "outcomes_or_paths": [
        "风险在容忍度内：无需行动计划",
        "风险不在容忍度内：需要行动计划"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002788",
        "quote": "Once an organization understands its residual risks, it can determine whether the risk is within its tolerance levels or if an action plan is required to mitigate those risks."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002789"
    ],
    "proposition": "传统金融机构在处理向高风险地区加密资产服务商转账且无额外控制时，剩余风险高，需要开发控制措施以将风险降至风险偏好内，例如禁止交易或加强监控。",
    "source_quotes": [
      "For example, if a traditional financial institution realizes it has many customers making transfers to cryptoasset service providers in high-risk jurisdictions and no additional controls exist, the residual risk is high. The organization will need to develop a control to mitigate this risk, so the residual risk is within risk appetite. This may include a process of prohibiting transactions to certain known, unlicensed providers, or increasing the monitoring where the risk is high, even if it is within a licensing regime."
    ],
    "relation_cues": [
      "if",
      "high",
      "need to",
      "may include"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "传统金融机构发现许多客户向高风险地区加密资产服务商转账且无额外控制"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "判断剩余风险高，需开发控制措施",
      "outcomes_or_paths": [
        "开发控制措施使剩余风险在风险偏好内",
        "控制措施可能包括禁止交易或加强监控"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002789",
        "quote": "For example, if a traditional financial institution realizes it has many customers making transfers to cryptoasset service providers in high-risk jurisdictions and no additional controls exist, the residual risk is high. The organization will need to develop a control to mitigate this risk, so the residual risk is within risk appetite. This may include a process of prohibiting transactions to certain known, unlicensed providers, or increasing the monitoring where the risk is high, even if it is within a licensing regime."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002790",
      "v7u_N002791",
      "v7u_N002792"
    ],
    "proposition": "制定剩余风险行动计划需要先了解固有风险来源及缓解措施如何控制风险，然后识别现有控制无法缓解的风险，再评估其他控制措施（如降低交易限额或限制产品数量）能否降低风险。",
    "source_quotes": [
      "To develop a residual risks action plan, the organization must understand where the inherent risk originates and how mitigation measures can control the risk.",
      "The organization should identify which risks existing AFC controls cannot mitigate.",
      "It should then evaluate whether other control measures, such as reducing transaction limits or limiting the number of products offered, would minimize the risks."
    ],
    "relation_cues": [
      "To",
      "must",
      "identify",
      "should",
      "evaluate"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "制定剩余风险行动计划"
      ],
      "basis_or_condition": [
        "了解固有风险来源及缓解措施如何控制风险"
      ],
      "focal_handling_or_judgment": "识别现有控制无法缓解的风险并评估其他控制措施",
      "outcomes_or_paths": [
        "识别出无法缓解的风险",
        "评估其他控制措施的有效性"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002790",
        "quote": "To develop a residual risks action plan, the organization must understand where the inherent risk originates and how mitigation measures can control the risk."
      },
      {
        "unit_id": "v7u_N002791",
        "quote": "The organization should identify which risks existing AFC controls cannot mitigate."
      },
      {
        "unit_id": "v7u_N002792",
        "quote": "It should then evaluate whether other control measures, such as reducing transaction limits or limiting the number of products offered, would minimize the risks."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
