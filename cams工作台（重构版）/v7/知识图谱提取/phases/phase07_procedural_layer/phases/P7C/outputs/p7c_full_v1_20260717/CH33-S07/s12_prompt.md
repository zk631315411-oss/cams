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

section_id: `CH33-S07`

section_title: `Introduction > Case study: Failure to update an EWRA at a wealth management firm`

section_text_with_unit_anchors:

```text
[v7u_N002617|2617] The Monetary Authority of Singapore (MAS) took enforcement action against Swiss-Asia Financial Services Pte Ltd (SAFS), imposing a S$2.5 million penalty for AML/CFT violations. The wealth and fund management firm failed to update its enterprise-wide risk assessment (EWRA), despite rapid business expansion over a three-year period. This exposed SAFS to new and increased risks of financial crime.
ZH: 新加坡金管局因SAFS未更新企业级风险评估而处以250万新元罚款

[v7u_N002618|2618] MAS uncovered the following AML/CFT breaches:
ZH: MAS发现的反洗钱/反恐怖融资违规行为列表

[v7u_N002619|2619] Failure to conduct EWRA updates: SAFS did not reassess its risk framework despite a significant increase in assets under management and onboarding of high-risk clients. A static risk model exposed the firm to undetected financial crime risks.
ZH: SAFS未更新企业级风险评估，静态风险模型导致未检测的金融犯罪风险

[v7u_N002620|2620] Weak customer due diligence controls: The firm onboarded high-risk customers without conducting enhanced due diligence, failing to verify sources of wealth or screen ultimate beneficial owners against watchlists.
ZH: SAFS客户尽职调查控制薄弱，未对高风险客户进行强化尽职调查

[v7u_N002621|2621] Inadequate transaction monitoring controls: The firm’s transaction monitoring system lacked risk segmentation and failed to flag suspicious transactions, leading to missed red flags and delayed suspicious activity reports.
ZH: 交易监控系统缺乏风险分层，导致漏报可疑交易和延迟提交可疑交易报告

[v7u_N002622|2622] Management oversight failures: Senior management failed to ensure that AML/CFT controls kept pace with business expansion. The firm lacked riskbased governance and experienced internal audit failures.
ZH: 高级管理层未能确保反洗钱/反恐怖融资控制措施跟上业务扩张步伐

[v7u_N002623|2623] The breaches had a negative impact on the firm’s business and its managers.
ZH: 违规行为对公司及其管理人员产生负面影响

[v7u_N002624|2624] For example, in addition to imposing the S$2.5 million fine, MAS required the firm to enhance its AML compliance program and conduct independent risk reviews.
ZH: 新加坡金融管理局除罚款外还要求公司加强反洗钱合规计划并开展独立风险审查

[v7u_N002625|2625] The resulting reputational damage caused client withdrawals and investor concerns, which impacted revenue and business growth.
ZH: 声誉损害导致客户撤资和投资者担忧，影响收入和业务增长

[v7u_N002626|2626] Senior management was officially reprimanded, highlighting the need for executive accountability in AML/CFT oversight.
ZH: 高级管理层受到正式训诫，强调高管在反洗钱/反恐怖融资监督中的问责制

[v7u_N002627|2627] The financial crime EWRA lies at the heart of understanding financial crime risks of the organization.
ZH: 金融犯罪企业风险评估是理解组织金融犯罪风险的核心

[v7u_N002628|2628] If the risk assessment misses key risks or is not repeated as the risk profile of the organization changes, repercussions can be felt in multiple control failures.
ZH: 风险评估遗漏关键风险或未随风险状况更新会导致多重控制失效

[v7u_N002629|2629] Poor EWRA could lead to weaker due diligence controls and poor management oversight if the risks are not understood, documented, and managed.
ZH: 不良的企业风险评估可能导致尽职调查控制薄弱和管理监督不力
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002617",
      "v7u_N002618",
      "v7u_N002619",
      "v7u_N002620",
      "v7u_N002621",
      "v7u_N002622",
      "v7u_N002623",
      "v7u_N002624",
      "v7u_N002625",
      "v7u_N002626"
    ],
    "proposition": "MAS因SAFS未更新EWRA而处以罚款并要求整改，管理人受训诫，产生业务负面影响。",
    "source_quotes": [
      "imposing a S$2.5 million penalty for AML/CFT violations. The wealth and fund management firm failed to update its enterprise-wide risk assessment",
      "MAS uncovered the following AML/CFT breaches:",
      "Failure to conduct EWRA updates: SAFS did not reassess its risk framework",
      "Weak customer due diligence controls: The firm onboarded high-risk customers without conducting enhanced due diligence",
      "Inadequate transaction monitoring controls: The firm’s transaction monitoring system lacked risk segmentation and failed to flag suspicious transactions",
      "Management oversight failures: Senior management failed to ensure that AML/CFT controls kept pace with business expansion",
      "The breaches had a negative impact on the firm’s business and its managers.",
      "in addition to imposing the S$2.5 million fine, MAS required the firm to enhance its AML compliance program and conduct independent risk reviews.",
      "The resulting reputational damage caused client withdrawals and investor concerns",
      "Senior management was officially reprimanded, highlighting the need for executive accountability in AML/CFT oversight."
    ],
    "relation_cues": [
      "penalty",
      "failed to update",
      "uncovered",
      "Failure",
      "Weak",
      "Inadequate",
      "failures",
      "negative impact",
      "required",
      "reprimanded",
      "accountability"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "SAFS failed to update its EWRA despite rapid business expansion",
        "MAS uncovered AML/CFT breaches"
      ],
      "basis_or_condition": [
        "failure to conduct EWRA updates",
        "weak customer due diligence controls",
        "inadequate transaction monitoring controls",
        "management oversight failures"
      ],
      "focal_handling_or_judgment": "MAS imposed a S$2.5 million penalty and required enhanced compliance and independent risk reviews; senior management reprimanded",
      "outcomes_or_paths": [
        "negative impact on business and managers",
        "client withdrawals and investor concerns",
        "reputational damage"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002617",
        "quote": "imposing a S$2.5 million penalty for AML/CFT violations. The wealth and fund management firm failed to update its enterprise-wide risk assessment"
      },
      {
        "unit_id": "v7u_N002618",
        "quote": "MAS uncovered the following AML/CFT breaches:"
      },
      {
        "unit_id": "v7u_N002619",
        "quote": "Failure to conduct EWRA updates: SAFS did not reassess its risk framework"
      },
      {
        "unit_id": "v7u_N002620",
        "quote": "Weak customer due diligence controls: The firm onboarded high-risk customers without conducting enhanced due diligence"
      },
      {
        "unit_id": "v7u_N002621",
        "quote": "Inadequate transaction monitoring controls: The firm’s transaction monitoring system lacked risk segmentation and failed to flag suspicious transactions"
      },
      {
        "unit_id": "v7u_N002622",
        "quote": "Management oversight failures: Senior management failed to ensure that AML/CFT controls kept pace with business expansion"
      },
      {
        "unit_id": "v7u_N002623",
        "quote": "The breaches had a negative impact on the firm’s business and its managers."
      },
      {
        "unit_id": "v7u_N002624",
        "quote": "in addition to imposing the S$2.5 million fine, MAS required the firm to enhance its AML compliance program and conduct independent risk reviews."
      },
      {
        "unit_id": "v7u_N002625",
        "quote": "The resulting reputational damage caused client withdrawals and investor concerns"
      },
      {
        "unit_id": "v7u_N002626",
        "quote": "Senior management was officially reprimanded, highlighting the need for executive accountability in AML/CFT oversight."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002628",
      "v7u_N002629"
    ],
    "proposition": "如果风险评估未更新或不完整，会导致多重控制失效，包括弱的尽职调查和管理监督不力。",
    "source_quotes": [
      "If the risk assessment misses key risks or is not repeated as the risk profile of the organization changes, repercussions can be felt in multiple control failures.",
      "Poor EWRA could lead to weaker due diligence controls and poor management oversight if the risks are not understood, documented, and managed."
    ],
    "relation_cues": [
      "If",
      "misses",
      "not repeated",
      "repercussions",
      "could lead to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "风险评估遗漏关键风险或未随风险状况更新"
      ],
      "basis_or_condition": [
        "风险未被理解、记录和管理"
      ],
      "focal_handling_or_judgment": "风险评估不足导致多重控制失效",
      "outcomes_or_paths": [
        "多重控制失效",
        "弱的尽职调查控制",
        "管理监督不力"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002628",
        "quote": "If the risk assessment misses key risks or is not repeated as the risk profile of the organization changes, repercussions can be felt in multiple control failures."
      },
      {
        "unit_id": "v7u_N002629",
        "quote": "Poor EWRA could lead to weaker due diligence controls and poor management oversight if the risks are not understood, documented, and managed."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
