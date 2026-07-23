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

section_id: `CH06-S03`

section_title: `Money Laundering Risks in Financial Services > Case example: A new corporate banking role`

section_text_with_unit_anchors:

```text
[v7u_N000396|396] Elena is an experienced AML compliance officer in retail banking. She is starting a new role overseeing the AFC team within the corporate banking division of her financial institution. To succeed in her new role, she needs to understand the unique risks associated with this sector and implement effective controls to mitigate them.
ZH: Elena 新任企业银行金融犯罪防控团队主管，需了解行业风险

[v7u_N000397|397] Conducting a thorough risk assessment of her organization’s corporate banking products and services is an important first step. This involves identifying and evaluating the inherent risks associated with each product. She will also need to assess the customer base to understand the risks, including the industries they operate in, their geographical locations and the typical transaction activity.
ZH: 风险评估步骤：评估产品固有风险、客户行业、地域及交易活动

[v7u_N000398|398] She will then need to assess the systems and controls that are in place to determine if they are commensurate with the specific risks of money laundering and terrorist financing that the bank faces.
ZH: 需评估现有系统与控制是否与洗钱和恐怖融资风险相称

[v7u_N000399|399] Effective CDD is a critical component of any AFC program, but is particularly important in corporate banking.
ZH: 有效的客户尽职调查是企业银行金融犯罪防控计划的关键

[v7u_N000400|400] This is because the transactions are often of higher value, more complex, and might require the services of third parties such as lawyers and accountants if a deal involves multiple financial instructions.
ZH: 企业银行交易金额高、结构复杂、常涉及第三方，故客户尽职调查尤为重要

[v7u_N000401|401] As a result, corporate banking transactions will require a relatively robust transaction monitoring system that can analyze patterns and detect anomalies in a more effective manner.
ZH: 企业银行业务需要强大的交易监控系统以有效分析模式并检测异常

[v7u_N000402|402] It is also valuable for her to understand recent high-profile money laundering prosecutions to gain insights into the failings in the compliance programs at other banks.
ZH: 了解近期高调洗钱起诉案例有助于洞察其他银行合规计划的缺陷

[v7u_N000403|403] For example, in October 2024, TD Bank agreed to a historic US$3 billion settlement with the US government. This settlement was a result of the bank's failure to detect and prevent money laundering activities within its institution over nearly a decade.
ZH: TD银行因近十年未能发现和预防洗钱活动，于2024年达成30亿美元和解

[v7u_N000404|404] It is also considered best practice and in most jurisdictions an industry standard to invest in continuous AFC training for herself and her team. Attending industry seminars, workshops, and training sessions can help Elena stay up to date on the best practices in corporate banking compliance.
ZH: 持续进行金融犯罪防控培训是最佳实践和行业标准
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N000397"
    ],
    "proposition": "进行全面的风险评估是第一步，包括识别和评估产品固有风险、客户行业、地域和交易活动。",
    "source_quotes": [
      "Conducting a thorough risk assessment of her organization’s corporate banking products and services is an important first step. This involves identifying and evaluating the inherent risks associated with each product. She will also need to assess the customer base to understand the risks, including the industries they operate in, their geographical locations and the typical transaction activity."
    ],
    "relation_cues": [
      "first step",
      "involves",
      "need to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "开展企业银行产品与服务的全面风险评估"
      ],
      "basis_or_condition": [
        "识别和评估产品固有风险",
        "评估客户行业、地域和交易活动"
      ],
      "focal_handling_or_judgment": "进行风险评估",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000397",
        "quote": "Conducting a thorough risk assessment of her organization’s corporate banking products and services is an important first step. This involves identifying and evaluating the inherent risks associated with each product. She will also need to assess the customer base to understand the risks, including the industries they operate in, their geographical locations and the typical transaction activity."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N000398"
    ],
    "proposition": "评估现有系统与控制是否与银行面临的洗钱和恐怖融资风险相称。",
    "source_quotes": [
      "She will then need to assess the systems and controls that are in place to determine if they are commensurate with the specific risks of money laundering and terrorist financing that the bank faces."
    ],
    "relation_cues": [
      "then",
      "need to",
      "assess",
      "determine",
      "commensurate with"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "完成初步风险评估后"
      ],
      "basis_or_condition": [
        "银行面临的洗钱和恐怖融资风险"
      ],
      "focal_handling_or_judgment": "评估现有系统与控制是否相称",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000398",
        "quote": "She will then need to assess the systems and controls that are in place to determine if they are commensurate with the specific risks of money laundering and terrorist financing that the bank faces."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N000401"
    ],
    "proposition": "企业银行交易需要强大的交易监控系统，以分析模式并有效检测异常。",
    "source_quotes": [
      "As a result, corporate banking transactions will require a relatively robust transaction monitoring system that can analyze patterns and detect anomalies in a more effective manner."
    ],
    "relation_cues": [
      "require",
      "can"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "企业银行交易"
      ],
      "basis_or_condition": [
        "交易金额高、结构复杂、涉及第三方"
      ],
      "focal_handling_or_judgment": "需要强大的交易监控系统",
      "outcomes_or_paths": [
        "分析交易模式并有效检测异常"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000401",
        "quote": "As a result, corporate banking transactions will require a relatively robust transaction monitoring system that can analyze patterns and detect anomalies in a more effective manner."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N000403"
    ],
    "proposition": "TD Bank因近十年未能发现和预防洗钱活动，与美国政府达成30亿美元和解。",
    "source_quotes": [
      "For example, in October 2024, TD Bank agreed to a historic US$3 billion settlement with the US government. This settlement was a result of the bank's failure to detect and prevent money laundering activities within its institution over nearly a decade."
    ],
    "relation_cues": [
      "result of",
      "failure"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "TD Bank在近十年内未能发现和预防洗钱活动"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "银行的失败导致和解",
      "outcomes_or_paths": [
        "与美国政府达成30亿美元和解"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000403",
        "quote": "For example, in October 2024, TD Bank agreed to a historic US$3 billion settlement with the US government. This settlement was a result of the bank's failure to detect and prevent money laundering activities within its institution over nearly a decade."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
