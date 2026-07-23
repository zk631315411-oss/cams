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

section_id: `CH21-S03`

section_title: `AFC guidance from other organizations > Basel Institute on Governance AFC guidance`

section_text_with_unit_anchors:

```text
[v7u_N001633|1633] The core mission of the Basel Institute on Governance is to contribute to global efforts to prevent and combat corruption and strengthen governance.
ZH: 巴塞尔治理研究所的核心使命是预防和打击腐败并加强治理。

[v7u_N001634|1634] It is an independent organization and an associated institute of the University of Basel.
ZH: 巴塞尔治理研究所是一个独立组织，也是巴塞尔大学的附属机构。

[v7u_N001635|1635] Its staff are mostly practitioners with years of anti-corruption prevention or law enforcement experience.
ZH: 巴塞尔治理研究所的员工多为具有多年反腐败预防或执法经验的从业者。

[v7u_N001636|1636] The Institute’s main areas of expertise include:
ZH: 巴塞尔治理研究所的主要专业领域包括以下方面。

[v7u_N001637|1637] Asset recovery assistance, capacity building, and policy guidance.
ZH: 巴塞尔治理研究所提供资产追回援助、能力建设和政策指导。

[v7u_N001638|1638] Anti-corruption research, training, and assessments.
ZH: 巴塞尔治理研究所开展反腐败研究、培训和评估。

[v7u_N001639|1639] Anti-corruption engagement with the private sector.
ZH: 巴塞尔治理研究所与私营部门合作开展反腐败工作。

[v7u_N001640|1640] Countering corruption that impacts the environment.
ZH: 巴塞尔治理研究所致力于打击影响环境的腐败行为。

[v7u_N001641|1641] Technical assistance for public finance management.
ZH: 巴塞尔治理研究所提供公共财政管理技术援助。

[v7u_N001642|1642] The International Centre for Asset Recovery (ICAR), established in 2006, is a specialized division of the Basel Institute on Governance. It works through four main lines of intervention:
ZH: 巴塞尔治理研究所下设国际资产追回中心（ICAR），通过四条主要干预线开展工作。

[v7u_N001643|1643] Case advice, mentoring, and facilitation of international cooperation
ZH: ICAR提供案件咨询、指导及促进国际合作。

[v7u_N001644|1644] Capacity building and training
ZH: ICAR开展能力建设与培训。

[v7u_N001645|1645] Institutional development and legal and policy advice
ZH: ICAR提供机构发展及法律政策咨询。

[v7u_N001646|1646] Global policy dialogue and innovation
ZH: ICAR推动全球政策对话与创新。

[v7u_N001647|1647] The Basel AML Index is an independent ranking and risk assessment tool that evaluates a country's vulnerability to money laundering and related financial crimes and its capacity to counter these threats. The Index does not measure the actual amount of money laundering activity. Developed by the Basel Institute through ICAR, the Index helps policymakers, regulators, and researchers understand vulnerabilities and enhance AML efforts worldwide. It assigns risk scores to jurisdictions using a composite methodology, with 17 indicators in five domains in line with key factors considered to contribute to a high-risk score. The five domains are:
ZH: 巴塞尔反洗钱指数是评估国家洗钱脆弱性和应对能力的独立排名工具，包含五大领域17项指标。

[v7u_N001648|1648] AML/CFT and counter-proliferation financing framework quality.
ZH: 巴塞尔反洗钱指数评估反洗钱/反恐怖融资及防扩散融资框架质量。

[v7u_N001649|1649] Corruption and fraud risks.
ZH: 巴塞尔AML指数评估腐败与欺诈风险。

[v7u_N001650|1650] Financial transparency.
ZH: 巴塞尔AML指数评估金融透明度。

[v7u_N001651|1651] Public transparency and accountability.
ZH: 巴塞尔AML指数评估公共透明度与问责制。

[v7u_N001652|1652] Legal and political risks.
ZH: 巴塞尔AML指数评估法律与政治风险。

[v7u_N001653|1653] The Index uses data sources including FATF mutual evaluation reports, US State Department International Narcotics Control Strategy Report, and Transparency International.
ZH: 巴塞尔AML指数数据来源包括FATF互评估报告、美国国务院国际 narcotics 控制战略报告和透明国际。
```

## S1.1 候选列表

```json
[]
```
