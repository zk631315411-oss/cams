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

section_id: `CH36-S02`

section_title: `Types of risk assessment > Types of risk assessment within an organization`

section_text_with_unit_anchors:

```text
[v7u_N002654|2654] There are different types of risk assessments within organizations. The assessments vary, depending on the individual entity type, but their aim is to identify, assess, and mitigate various risks and apply appropriate controls.
ZH: 组织内部存在不同类型的风险评估，其目标均为识别、评估和缓解风险并应用适当控制

[v7u_N002655|2655] The purpose of the AFC risk assessments is to help organizations ensure compliance, enhance risk management, and maintain healthy, sustainable businesses.
ZH: 金融犯罪防控风险评估旨在确保合规、加强风险管理并维持健康可持续的业务

[v7u_N002656|2656] One main risk assessment is an EWRA, which assesses all types of risk an organization faces.
ZH: 企业全面风险评估是主要的风险评估类型，评估组织面临的所有风险

[v7u_N002657|2657] We will focus on the AFC portion of the EWRA, which considers financial crimes—money laundering, terrorism financing, sanctions, tax evasion, and bribery and corruption.
ZH: 企业全面风险评估中的金融犯罪防控部分涵盖洗钱、恐怖融资、制裁、逃税、贿赂与腐败

[v7u_N002658|2658] The anti-bribery and corruption (ABC) risk assessment aims to prevent, detect, and report bribery and corruption while identifying areas of higher risk.
ZH: 反贿赂与腐败风险评估旨在预防、发现和报告贿赂与腐败，并识别高风险领域

[v7u_N002659|2659] In 2023, the Wolfsberg Group updated its , which helps entities mitigate ABC risks.
ZH: 2023年沃尔夫斯堡集团更新了其反贿赂与腐败风险评估指引

[v7u_N002660|2660] The security risk assessment focuses on security threats and risks that could affect both the physical and digital assets of an entity.
ZH: 安全风险评估关注可能影响实体物理和数字资产的安全威胁与风险

[v7u_N002661|2661] The operational risk assessment focuses on risks derived from the failures of internal processes, disruptions of integrated systems, internal or external events, and staff misconduct.
ZH: 操作风险定义：关注内部流程、系统中断、内外部事件及员工不当行为导致的失败

[v7u_N002662|2662] It concentrates on business and operational continuity.
ZH: 操作风险评估侧重于业务和运营连续性

[v7u_N002663|2663] It helps entities to identify, assess, and mitigate these risks, and apply measures to sustain a continuing business, while minimizing disruptions.
ZH: 操作风险评估帮助实体识别、评估和缓解风险，维持业务持续运营

[v7u_N002664|2664] Fraud risks can be part of the operational risk assessment in some organizations.
ZH: 欺诈风险可纳入操作风险评估

[v7u_N002665|2665] With examiners increasingly requesting to see results of the fraud risk assessment, execution may be centralized with AML risk assessment.
ZH: 监管机构要求欺诈风险评估结果，可与反洗钱风险评估集中执行

[v7u_N002666|2666] The customer risk assessment (CRA) helps entities understand the AML/CTF risks inherent in a particular business relationship with a customer.
ZH: 客户风险评估（CRA）帮助实体理解与客户业务关系中的反洗钱/反恐怖融资风险

[v7u_N002667|2667] Based on the type of organization and risk exposure, an organization may need to carry out specific risk assessments, such as assessing exposure to proliferation financing.
ZH: 根据组织类型和风险暴露，可能需要进行特定风险评估，如扩散融资风险评估

[v7u_N002668|2668] In 2020, FATF revised its Recommendation 1 and its Interpretive Note, requiring countries and obliged entities to identify, assess, understand, and mitigate their proliferation financing risks. FATF also published guidance in June 2021 to assist countries and obliged entities to conduct effective proliferation financing risk assessments.
ZH: FATF修订建议1，要求各国和义务实体识别、评估并缓解扩散融资风险，并发布指南

[v7u_N002669|2669] Proliferation financing refers to the transfer and export of nuclear, chemical, or biological weapons, their delivery means, and related materials.
ZH: 扩散融资指核、化学或生物武器及其运载工具和相关材料的转让和出口

[v7u_N002670|2670] Non-proliferation risk refers to contributing to the proliferation of these weapons of mass destruction (WMD) wittingly or unwittingly.
ZH: 防扩散风险指有意或无意助长大规模杀伤性武器扩散的风险

[v7u_N002671|2671] Managing non-proliferation risk is important because it poses a significant threat to international peace and security.
ZH: 管理防扩散风险对国际和平与安全至关重要
```

## S1.1 候选列表

```json
[]
```
