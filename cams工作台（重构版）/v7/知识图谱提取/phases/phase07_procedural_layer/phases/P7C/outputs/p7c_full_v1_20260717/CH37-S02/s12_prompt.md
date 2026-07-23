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

section_id: `CH37-S02`

section_title: `Enterprise-wide risk assessment > Determining inherent risks`

section_text_with_unit_anchors:

```text
[v7u_N002736|2736] Inherent risk is the level of financial crime risk in place before an organization applies any mitigation controls.
ZH: 固有风险是指在应用任何缓解控制措施之前，金融犯罪风险的水平。

[v7u_N002737|2737] Inherent risk is the starting point of most risk assessments.
ZH: 固有风险是大多数风险评估的起点。

[v7u_N002738|2738] Once an organization establishes inherent risk, it considers the likelihood and impact of that risk occurring, typically using a matrix to understand the highest risks.
ZH: 确定固有风险后，组织需考虑风险发生的可能性和影响，通常使用矩阵识别最高风险。

[v7u_N002739|2739] The process for determining inherent risk varies depending on the organization and its risk assessment framework.
ZH: 固有风险的确定过程因组织和风险评估框架而异。

[v7u_N002740|2740] While the process may begin with a qualitative understanding of the risk, it is important to back it up with quantitative data to establish relevance.
ZH: 固有风险评估虽可从定性理解开始，但需用定量数据支撑以确立相关性。

[v7u_N002741|2741] Generally, the following steps are recommended to determine an organization’s inherent risk.
ZH: 确定固有风险的推荐步骤

[v7u_N002742|2742] First, identify and gather relevant information. Collect data on customers, jurisdictions, products, and channels, including customer profiles, country risk assessments, product specifications, and channel characteristics.
ZH: 第一步：识别并收集客户、地域、产品和渠道的相关信息

[v7u_N002743|2743] At this point in the risk assessment process, it is important to understand national and sectoral risk assessments that apply to the industry sector and jurisdictions in which the organizations operate.
ZH: 理解适用于行业和地域的国家及行业风险评估

[v7u_N002744|2744] Next, analyze and assess the risk factors associated with each category.
ZH: 分析并评估每个类别的风险因素

[v7u_N002745|2745] For customers, risk rating generally considers their industry, transaction volume, corruption index, and geographic location.
ZH: 客户风险评级考虑行业、交易量、腐败指数和地理位置

[v7u_N002746|2746] Determining jurisdiction risk might involve assessing political stability, the regulatory environment, and sanctions status.
ZH: 地域风险评估涉及政治稳定性、监管环境和制裁状况

[v7u_N002747|2747] To determine product risk, consider the complexity, potential misuse, or attractiveness of the product for illicit activities.
ZH: 产品风险评估考虑复杂性、潜在滥用或对非法活动的吸引力

[v7u_N002748|2748] To assess channel risk, you might evaluate vulnerabilities in the delivery or communication channels.
ZH: 渠道风险评估评估交付或沟通渠道的脆弱性

[v7u_N002749|2749] Categorize inherent risk using the inherent risk matrix.
ZH: 使用固有风险矩阵对固有风险进行分类

[v7u_N002750|2750] The level of risk increases in tandem with the probability and severity of the risk materializing. If there is high probability of the risk, and its impact is high, the inherent risk is also high.
ZH: 风险水平随风险发生的概率和严重程度而增加

[v7u_N002751|2751] Applying a risk-based approach refers to prioritizing risks that have high probability and severe impact.
ZH: 基于风险的方法是指优先处理高概率和严重影响的风险

[v7u_N002752|2752] This does not mean an organization will not address other risks. It just means the organization will apply more resources, effort, and investment to building controls for the highest risks.
ZH: 基于风险的方法并非忽略其他风险，而是对最高风险投入更多资源

[v7u_N002753|2753] The inherent risk assessment process should clearly prioritize the highest risks for the organization.
ZH: 固有风险评估应明确优先考虑组织的最高风险

[v7u_N002754|2754] A scoring mechanism may be used to identify the top risks.
ZH: 可使用评分机制识别最高风险

[v7u_N002755|2755] Inherent risk matrix and key
ZH: 固有风险矩阵及其图例

[v7u_N002756|2756] Controlling risk is critical to the overall success of an institution.
ZH: 控制风险对机构的整体成功至关重要

[v7u_N002757|2757] Financial crime risk assessments help to develop control strategies to mitigate and monitor the identified risks.
ZH: 金融犯罪风险评估有助于制定控制策略以减轻和监控已识别风险

[v7u_N002758|2758] Some examples of these control strategies are policies and procedures, training, four-eyes checks, and segregation of duties.
ZH: 控制策略示例包括政策与程序、培训、四眼检查和职责分离

[v7u_N002759|2759] These controls fall into three categories: preventive, detective, and corrective.
ZH: 控制措施分为预防性、检测性和纠正性三类

[v7u_N002760|2760] The internal control framework refers to the set of standards, processes, and structures that provide the basis for carrying out internal control across the organization.
ZH: 内部控制框架是组织内实施内部控制的标准、流程和结构基础

[v7u_N002761|2761] This framework should align with the organization's risk appetite.
ZH: 风险框架应与组织的风险偏好保持一致

[v7u_N002762|2762] A risk assessment begins by identifying inherent risks the organization may be exposed to if there are no controls. The organization categorizes the inherent risks based on the probability and impact of them occurring. This helps to prioritize the highest risks.
ZH: 固有风险评估的步骤：识别、分类和排序

[v7u_N002763|2763] Control activities in financial crime prevention include preventive, detective, and corrective controls.
ZH: 金融犯罪防控控制活动的类型：预防性、侦测性和纠正性

[v7u_N002764|2764] Preventive controls involve measures to prevent financial crime from occurring and include robust due diligence, recordkeeping, and record retention.
ZH: 预防性控制包括尽职调查、记录保存等措施

[v7u_N002765|2765] Detective controls involve measures to detect financial crime as soon as possible after it has occurred, such as identifying and reporting suspicious activity to the appropriate authorities.
ZH: 侦测性控制旨在尽早发现金融犯罪，如识别和报告可疑活动

[v7u_N002766|2766] Corrective controls involve measures to remediate instances of financial crime after they have been detected, such as exiting a customer relationship and performing reviews to understand if any risks were missed.
ZH: 纠正性控制包括退出客户关系、审查遗漏风险等补救措施

[v7u_N002767|2767] Organizations assess the effectiveness of controls in multiple ways. Initially, the teams operating the controls carry out these assessments by demonstrating adherence to key performance indicators, key risk indicators, and service level agreements. Once the controls are in operation, the teams assess their effectiveness and identify remedial actions to ensure they remain effective.
ZH: 通过KPI、KRI和SLA评估控制有效性，并采取补救措施

[v7u_N002768|2768] Assurance functions within the business or compliance lines monitor the effectiveness of controls by testing whether team members have properly observed and applied all policies, procedures, and controls. The internal audit team may also carry out assessments for critical controls.
ZH: 业务或合规部门的保证职能以及内部审计监控控制有效性
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002738"
    ],
    "proposition": "确定固有风险后，考虑风险发生的可能性和影响，使用矩阵识别最高风险。",
    "source_quotes": [
      "Once an organization establishes inherent risk, it considers the likelihood and impact of that risk occurring, typically using a matrix to understand the highest risks."
    ],
    "relation_cues": [
      "Once",
      "considers",
      "using"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "已确定固有风险"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "评估可能性和影响并使用矩阵识别最高风险",
      "outcomes_or_paths": [
        "识别出最高风险"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002738",
        "quote": "Once an organization establishes inherent risk, it considers the likelihood and impact of that risk occurring, typically using a matrix to understand the highest risks."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002742",
      "v7u_N002743",
      "v7u_N002744",
      "v7u_N002745",
      "v7u_N002746",
      "v7u_N002747",
      "v7u_N002748",
      "v7u_N002749"
    ],
    "proposition": "确定固有风险的推荐步骤包括：识别和收集客户、地域、产品和渠道的相关信息；分析每个类别的风险因素；使用固有风险矩阵进行分类。",
    "source_quotes": [
      "First, identify and gather relevant information. Collect data on customers, jurisdictions, products, and channels, including customer profiles, country risk assessments, product specifications, and channel characteristics.",
      "At this point in the risk assessment process, it is important to understand national and sectoral risk assessments that apply to the industry sector and jurisdictions in which the organizations operate.",
      "Next, analyze and assess the risk factors associated with each category.",
      "For customers, risk rating generally considers their industry, transaction volume, corruption index, and geographic location.",
      "Determining jurisdiction risk might involve assessing political stability, the regulatory environment, and sanctions status.",
      "To determine product risk, consider the complexity, potential misuse, or attractiveness of the product for illicit activities.",
      "To assess channel risk, you might evaluate vulnerabilities in the delivery or communication channels.",
      "Categorize inherent risk using the inherent risk matrix."
    ],
    "relation_cues": [
      "First",
      "Next",
      "generally",
      "might",
      "using"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "需要进行固有风险评估"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "识别信息、分析风险因素并分类",
      "outcomes_or_paths": [
        "完成固有风险分类"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002742",
        "quote": "First, identify and gather relevant information. Collect data on customers, jurisdictions, products, and channels, including customer profiles, country risk assessments, product specifications, and channel characteristics."
      },
      {
        "unit_id": "v7u_N002743",
        "quote": "At this point in the risk assessment process, it is important to understand national and sectoral risk assessments that apply to the industry sector and jurisdictions in which the organizations operate."
      },
      {
        "unit_id": "v7u_N002744",
        "quote": "Next, analyze and assess the risk factors associated with each category."
      },
      {
        "unit_id": "v7u_N002745",
        "quote": "For customers, risk rating generally considers their industry, transaction volume, corruption index, and geographic location."
      },
      {
        "unit_id": "v7u_N002746",
        "quote": "Determining jurisdiction risk might involve assessing political stability, the regulatory environment, and sanctions status."
      },
      {
        "unit_id": "v7u_N002747",
        "quote": "To determine product risk, consider the complexity, potential misuse, or attractiveness of the product for illicit activities."
      },
      {
        "unit_id": "v7u_N002748",
        "quote": "To assess channel risk, you might evaluate vulnerabilities in the delivery or communication channels."
      },
      {
        "unit_id": "v7u_N002749",
        "quote": "Categorize inherent risk using the inherent risk matrix."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002751",
      "v7u_N002752"
    ],
    "proposition": "基于风险的方法是指优先处理高概率和严重影响的风险，但并不忽略其他风险，而是对最高风险投入更多资源。",
    "source_quotes": [
      "Applying a risk-based approach refers to prioritizing risks that have high probability and severe impact.",
      "This does not mean an organization will not address other risks. It just means the organization will apply more resources, effort, and investment to building controls for the highest risks."
    ],
    "relation_cues": [
      "refers to",
      "does not mean",
      "just means"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "识别出不同水平风险"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "采用基于风险的方法优先处理高风险并投入更多资源",
      "outcomes_or_paths": [
        "高风险获得更多控制资源"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002751",
        "quote": "Applying a risk-based approach refers to prioritizing risks that have high probability and severe impact."
      },
      {
        "unit_id": "v7u_N002752",
        "quote": "This does not mean an organization will not address other risks. It just means the organization will apply more resources, effort, and investment to building controls for the highest risks."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N002767",
      "v7u_N002768"
    ],
    "proposition": "组织通过团队展示KPI/KRI/SLA来初步评估控制有效性，随后评估并采取补救措施；保证职能和内部审计通过测试监控控制有效性。",
    "source_quotes": [
      "Organizations assess the effectiveness of controls in multiple ways. Initially, the teams operating the controls carry out these assessments by demonstrating adherence to key performance indicators, key risk indicators, and service level agreements. Once the controls are in operation, the teams assess their effectiveness and identify remedial actions to ensure they remain effective.",
      "Assurance functions within the business or compliance lines monitor the effectiveness of controls by testing whether team members have properly observed and applied all policies, procedures, and controls. The internal audit team may also carry out assessments for critical controls."
    ],
    "relation_cues": [
      "Initially",
      "Once",
      "by",
      "also"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "控制已设计或已运行"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "评估和监控控制有效性",
      "outcomes_or_paths": [
        "识别补救措施",
        "保证控制持续有效"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002767",
        "quote": "Organizations assess the effectiveness of controls in multiple ways. Initially, the teams operating the controls carry out these assessments by demonstrating adherence to key performance indicators, key risk indicators, and service level agreements. Once the controls are in operation, the teams assess their effectiveness and identify remedial actions to ensure they remain effective."
      },
      {
        "unit_id": "v7u_N002768",
        "quote": "Assurance functions within the business or compliance lines monitor the effectiveness of controls by testing whether team members have properly observed and applied all policies, procedures, and controls. The internal audit team may also carry out assessments for critical controls."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
