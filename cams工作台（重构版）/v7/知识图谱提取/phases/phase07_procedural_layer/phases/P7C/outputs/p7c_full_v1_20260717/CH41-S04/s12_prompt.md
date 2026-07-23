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

section_id: `CH41-S04`

section_title: `Governance and oversight > Governance committees and their functions`

section_text_with_unit_anchors:

```text
[v7u_N002930|2930] Governance committees provide strategic oversight, decision-making authority, and accountability in an organization’s financial crime compliance framework. They ensure that AFC policies and procedures are aligned with regulatory requirements and risk management objectives, while supporting effective escalation, review, and enforcement processes.
ZH: 治理委员会在金融犯罪合规框架中提供战略监督、决策权和问责制，确保金融犯罪防控政策与监管要求和风险管理目标一致。

[v7u_N002931|2931] Governance committees must be structured based on an organization’s risk profile, regulatory obligations, and operational needs.
ZH: 治理委员会必须根据组织的风险状况、监管义务和运营需求进行构建。

[v7u_N002932|2932] Each committee must operate under a terms-of-reference document, which outlines its mandate, responsibilities, and authority.
ZH: 每个委员会必须依据职权范围文件运作，该文件概述其任务、职责和权力。

[v7u_N002933|2933] The committee must formally record meeting minutes for regulatory audits and internal governance reviews.
ZH: 委员会必须正式记录会议纪要，以供监管审计和内部治理审查。

[v7u_N002934|2934] Meeting minutes typically include decisions made, objections raised, and how the objections were dealt with.
ZH: 会议纪要通常包括做出的决定、提出的反对意见以及如何处理这些反对意见。

[v7u_N002935|2935] Examples of key committees include the:
ZH: 列举关键委员会的示例。

[v7u_N002936|2936] Board risk committee: This committee is typically led by one or more board members. It provides strategic oversight of AFC risks, ensuring policies align with global and jurisdictional regulations. The terms and the chair may escalate items for the board’s attention.
ZH: 董事会风险委员会由一名或多名董事会成员领导，提供金融犯罪防控风险的战略监督，确保政策符合全球和司法管辖区法规。

[v7u_N002937|2937] AML governance committee: This committee may be led by the second line and oversees enterprise-wide AML/CFT risk management, internal controls, and AML/CFT program effectiveness. It considers progress in reviewing alerts, volumes, and categories of alerts that resulted in SARs, results of audits and assurance reviews, and emerging risks.
ZH: 反洗钱治理委员会由第二道防线领导，监督企业范围内的反洗钱/反恐怖融资风险管理、内部控制及项目有效性。

[v7u_N002938|2938] High-risk customer review committee: This committee assesses onboarding and ongoing due diligence for PEPs, correspondent banks, and other high-risk clients. It is typically led by business leaders, with AFC compliance teams forming part of the quorum.
ZH: 高风险客户审查委员会评估政治敏感人物、代理行及其他高风险客户的准入和持续尽职调查，通常由业务负责人领导，金融犯罪防控合规团队构成法定人数。

[v7u_N002939|2939] Sanctions oversight committee: While AFC committees typically include sanctions oversight, there may be a need for a separate committee based on the organization’s risk exposure. It ensures compliance with global sanctions programs, watchlist screening, and escalation procedures.
ZH: 制裁监督委员会确保遵守全球制裁计划、观察名单筛查和升级程序，可根据风险暴露单独设立。

[v7u_N002940|2940] Quora for governance committees typically include:
ZH: 列举治理委员会的典型法定人数构成。

[v7u_N002941|2941] Board members or senior executives to provide strategic oversight and resource allocation for AFC compliance.
ZH: 董事会或高管为金融犯罪防控提供战略监督和资源分配

[v7u_N002942|2942] The chief compliance officer, MLRO, or their delegates to lead AFC policy execution, risk assessments, and regulatory engagement.
ZH: 首席合规官、MLRO或其代表领导金融犯罪防控政策执行、风险评估和监管沟通

[v7u_N002943|2943] The first line of defense risk owner and operational leaders who implement AFC policies in daily operations.
ZH: 第一道防线的风险负责人和运营负责人负责在日常运营中实施金融犯罪防控政策

[v7u_N002944|2944] The second line of defense to provide independent oversight, policy enforcement, and risk assessments (in addition to the MLRO, if needed).
ZH: 第二道防线提供独立监督、政策执行和风险评估

[v7u_N002945|2945] The third line of defense to report independent audits and ensure compliance effectiveness, where appropriate, while maintaining independence.
ZH: 第三道防线报告独立审计并确保合规有效性，同时保持独立性

[v7u_N002946|2946] By ensuring structured, well-documented, and effective governance committees, financial institutions strengthen AFC compliance, regulatory engagement, and risk management oversight.
ZH: 治理委员会通过结构化、文档化和有效的运作来加强金融犯罪防控合规

[v7u_N002947|2947] During regulatory exams, the robustness of the governance structure demonstrates the strength of the AML programs.
ZH: 治理结构的稳健性可作为反洗钱项目实力的指标

[v7u_N002948|2948] Examiners may request terms of reference and inputs via papers and meeting minutes, and present them as evidence of the effectiveness of the AFC program.
ZH: 监管机构可通过职权范围、会议纪要等文件评估金融犯罪防控项目的有效性
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_CH41-S04_1",
    "unit_ids": [
      "v7u_N002931"
    ],
    "proposition": "治理委员会必须根据组织的风险状况、监管义务和运营需求进行构建。",
    "source_quotes": [
      "Governance committees must be structured based on an organization’s risk profile, regulatory obligations, and operational needs."
    ],
    "relation_cues": [
      "must",
      "based on"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "组织的风险状况、监管义务和运营需求"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "构建治理委员会",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002931",
        "quote": "Governance committees must be structured based on an organization’s risk profile, regulatory obligations, and operational needs."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_CH41-S04_2",
    "unit_ids": [
      "v7u_N002932"
    ],
    "proposition": "每个委员会必须依据职权范围文件运作，该文件概述其任务、职责和权力。",
    "source_quotes": [
      "Each committee must operate under a terms-of-reference document, which outlines its mandate, responsibilities, and authority."
    ],
    "relation_cues": [
      "must",
      "under"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "职权范围文件概述其任务、职责和权力"
      ],
      "focal_handling_or_judgment": "委员会依据职权范围文件运作",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002932",
        "quote": "Each committee must operate under a terms-of-reference document, which outlines its mandate, responsibilities, and authority."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_CH41-S04_3",
    "unit_ids": [
      "v7u_N002933"
    ],
    "proposition": "委员会必须正式记录会议纪要，以供监管审计和内部治理审查。",
    "source_quotes": [
      "The committee must formally record meeting minutes for regulatory audits and internal governance reviews."
    ],
    "relation_cues": [
      "must",
      "for"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "正式记录会议纪要",
      "outcomes_or_paths": [
        "供监管审计和内部治理审查"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002933",
        "quote": "The committee must formally record meeting minutes for regulatory audits and internal governance reviews."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
