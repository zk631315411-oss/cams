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

section_id: `CH41-S06`

section_title: `Governance and oversight > Regulatory reporting for AFC compliance`

section_text_with_unit_anchors:

```text
[v7u_N002960|2960] Regulatory reporting is a critical obligation for financial institutions worldwide, ensuring compliance with AFC laws, financial transparency, and risk mitigation.
ZH: 监管报告是全球金融机构确保金融犯罪防控合规、金融透明和风险缓解的关键义务

[v7u_N002961|2961] Each jurisdiction typically enforces unique reporting rules, filing deadlines, and disclosure requirements.
ZH: 各司法管辖区有独特的报告规则、截止日期和披露要求。

[v7u_N002962|2962] Non-compliance can lead to severe financial penalties, reputational harm, and regulatory enforcement actions.
ZH: 不合规会导致严重罚款、声誉损害和监管执法行动。

[v7u_N002963|2963] Types of AFC regulatory reports include, but are not limited to:
ZH: 金融犯罪防控监管报告类型的列表引导。

[v7u_N002964|2964] Ongoing reports: These include suspicious activity reports and current threshold reports, which are required when suspicion or certain thresholds are triggered.
ZH: 持续报告包括可疑活动报告和当前阈值报告，在触发怀疑或阈值时提交。

[v7u_N002965|2965] Periodic reports: These include annual MLRO reports and other regular reports for which regulatory bodies mandate cadence, format, and deadlines.
ZH: 定期报告包括年度MLRO报告及其他监管机构规定频率、格式和截止日期的常规报告。

[v7u_N002966|2966] Ongoing reports include, but are not limited to:
ZH: 持续报告子类型的列表引导。

[v7u_N002967|2967] SARs: These are required when a transaction appears unusual, lacks an economic rationale, or raises AFC concerns. Deadlines vary globally.
ZH: 可疑活动报告（SAR）在交易异常、缺乏经济理由或引发金融犯罪防控担忧时提交，截止日期因地区而异。

[v7u_N002968|2968] CTRs: These reports are mandated for cash transactions above countryspecific thresholds. For the US, the requirement is any cash transaction that exceeds US$10,000 in a single day. The EU and Middle East have varying limits.
ZH: 现金交易报告（CTR）针对超过国家特定阈值的现金交易，美国阈值为单日超过10,000美元，欧盟和中东各有不同。

[v7u_N002969|2969] Sanctions reports: These are filed when a customer, transaction, or entity is linked to a sanctioned individual, organization, or country based on UN, OFAC, EU, or national sanctions lists.
ZH: 制裁报告在客户、交易或实体与受制裁个人、组织或国家关联时提交，依据联合国、OFAC、欧盟或国家制裁名单。

[v7u_N002970|2970] Cross-border transfer reports: These are required for tracking international transactions exceeding defined thresholds to monitor illicit financial flows, trade-based money laundering, and terrorist financing.
ZH: 跨境转账报告用于追踪超过阈值的国际交易，以监控非法资金流动、贸易洗钱和恐怖融资。

[v7u_N002971|2971] Beneficial ownership reports: These are enforced in many jurisdictions to expose hidden ownership structures and shell company misuse.
ZH: 受益所有人报告在许多司法管辖区强制执行，以揭露隐藏的所有权结构和壳公司滥用。

[v7u_N002972|2972] Jurisdiction-specific examples of regulatory reports include, but are not limited to:
ZH: 各司法管辖区监管报告示例的列表引导。

[v7u_N002973|2973] European Union:
ZH: 欧盟（European Union）作为司法管辖区标签。

[v7u_N002974|2974] Markets in Financial Instruments Directive II (MiFID II) transaction reports: Describe financial transactions for market integrity monitoring.
ZH: MiFID II交易报告用于描述金融交易以监控市场诚信。

[v7u_N002975|2975] 6AMLD Reports: Focus on uniform definitions of predicate offenses and extended liability across member states.
ZH: 第6反洗钱指令（6AMLD）报告侧重于统一上游犯罪定义和成员国扩展责任。
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002964"
    ],
    "proposition": "当触发怀疑或达到特定阈值时，必须提交持续报告（包括可疑活动报告和当前阈值报告）。",
    "source_quotes": [
      "Ongoing reports: These include suspicious activity reports and current threshold reports, which are required when suspicion or certain thresholds are triggered."
    ],
    "relation_cues": [
      "when",
      "required"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "触发怀疑或达到特定阈值"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "提交持续报告（包括可疑活动报告和当前阈值报告）",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002964",
        "quote": "Ongoing reports: These include suspicious activity reports and current threshold reports, which are required when suspicion or certain thresholds are triggered."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002967"
    ],
    "proposition": "当交易异常、缺乏经济理由或引发金融犯罪防控担忧时，必须提交可疑活动报告（SAR）。",
    "source_quotes": [
      "SARs: These are required when a transaction appears unusual, lacks an economic rationale, or raises AFC concerns."
    ],
    "relation_cues": [
      "when",
      "required"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "交易异常、缺乏经济理由或引发金融犯罪防控担忧"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "提交可疑活动报告（SAR）",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002967",
        "quote": "SARs: These are required when a transaction appears unusual, lacks an economic rationale, or raises AFC concerns."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002968"
    ],
    "proposition": "对于超过国家特定阈值的现金交易，必须提交现金交易报告（CTR）；在美国，单日超过10,000美元的现金交易即触发该要求。",
    "source_quotes": [
      "CTRs: These reports are mandated for cash transactions above countryspecific thresholds. For the US, the requirement is any cash transaction that exceeds US$10,000 in a single day."
    ],
    "relation_cues": [
      "above",
      "mandated",
      "exceeds"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "现金交易超过国家特定阈值"
      ],
      "basis_or_condition": [
        "美国阈值为单日超过10,000美元"
      ],
      "focal_handling_or_judgment": "提交现金交易报告（CTR）",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002968",
        "quote": "CTRs: These reports are mandated for cash transactions above countryspecific thresholds. For the US, the requirement is any cash transaction that exceeds US$10,000 in a single day."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N002969"
    ],
    "proposition": "当客户、交易或实体与受制裁个人、组织或国家关联时，必须根据相关制裁名单提交制裁报告。",
    "source_quotes": [
      "Sanctions reports: These are filed when a customer, transaction, or entity is linked to a sanctioned individual, organization, or country based on UN, OFAC, EU, or national sanctions lists."
    ],
    "relation_cues": [
      "when",
      "linked",
      "based on"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "客户、交易或实体与受制裁方关联"
      ],
      "basis_or_condition": [
        "依据联合国、OFAC、欧盟或国家制裁名单"
      ],
      "focal_handling_or_judgment": "提交制裁报告",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002969",
        "quote": "Sanctions reports: These are filed when a customer, transaction, or entity is linked to a sanctioned individual, organization, or country based on UN, OFAC, EU, or national sanctions lists."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N002970"
    ],
    "proposition": "对于超过规定阈值的国际交易，必须提交跨境转账报告以监控非法资金流动、贸易洗钱和恐怖融资。",
    "source_quotes": [
      "Cross-border transfer reports: These are required for tracking international transactions exceeding defined thresholds to monitor illicit financial flows, trade-based money laundering, and terrorist financing."
    ],
    "relation_cues": [
      "exceeding",
      "required",
      "to monitor"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "国际交易超过规定阈值"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "提交跨境转账报告",
      "outcomes_or_paths": [
        "监控非法资金流动、贸易洗钱和恐怖融资"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002970",
        "quote": "Cross-border transfer reports: These are required for tracking international transactions exceeding defined thresholds to monitor illicit financial flows, trade-based money laundering, and terrorist financing."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
