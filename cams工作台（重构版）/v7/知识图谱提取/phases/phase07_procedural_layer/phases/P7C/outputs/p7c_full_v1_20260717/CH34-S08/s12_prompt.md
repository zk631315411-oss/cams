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

section_id: `CH34-S08`

section_title: `Three lines of defense > Case example: Financial crime functions' structure at Global Finance, Corp.`

section_text_with_unit_anchors:

```text
[v7u_N002487|2487] Global Finance Corp (GFC), a regional bank with business activities overseas, appointed a consultant to guide the streamlining of its AFC function structure.
ZH: Global Finance Corp 聘请顾问指导其金融犯罪防控职能结构优化

[v7u_N002488|2488] The bank faced significant regulatory scrutiny and wanted to improve its ability to detect and prevent money laundering and financial crime risks.
ZH: 该银行面临监管审查，希望提升洗钱和金融犯罪风险检测与预防能力

[v7u_N002489|2489] The existing structure was disorganized, with overlapping responsibilities and unclear communication channels.
ZH: 现有金融犯罪防控结构混乱，职责重叠且沟通渠道不清晰

[v7u_N002490|2490] The consultant analyzed GFC's second line of defense, which included several functions performing specific tasks, but lacking strong collaboration mechanisms. Different business segments face different risks, so the required controls also differ. For example, corporate banking is more complex than retail banking and therefore requires more human intervention. The consultant proposed a revised structure with clear roles, responsibilities, and communication channels for various functions, including:
ZH: 顾问分析了第二道防线，提出包含明确角色与沟通渠道的修订结构

[v7u_N002491|2491] AML advisory
ZH: 反洗钱咨询

[v7u_N002492|2492] Sanctions advisory
ZH: 制裁咨询

[v7u_N002493|2493] Transaction monitoring and review, including model risk management and data analytics
ZH: 交易监控与审查，包括模型风险管理和数据分析

[v7u_N002494|2494] Investigation
ZH: 调查

[v7u_N002495|2495] Policies management
ZH: 政策管理

[v7u_N002496|2496] Regulatory reporting and liaison
ZH: 监管报告与联络

[v7u_N002497|2497] Compliance testing
ZH: 合规测试

[v7u_N002498|2498] MLRO officer
ZH: 洗钱报告官

[v7u_N002499|2499] Regional, jurisdictional, and subsidiary management
ZH: 区域、司法管辖区及子公司管理

[v7u_N002500|2500] The new structure aimed to foster better collaboration, reduce regulatory risks, and improve financial crime risk management efficiency.
ZH: 新结构旨在促进协作、降低监管风险并提升金融犯罪风险管理效率

[v7u_N002501|2501] In addition to the revised structure, the consultant recommended regular communication sessions among functions to remain aligned on objectives and share insights on emerging financial crime trends.
ZH: 顾问建议各职能部门定期沟通以保持目标一致并分享新兴金融犯罪趋势洞察

[v7u_N002502|2502] After the GFC restructuring, the consultant worked with a recently acquired money services business (MSB) that struggled with regulatory compliance and operational inefficiency.
ZH: 顾问在GFC重组后协助一家合规与运营困难的货币服务企业（货币服务企业）

[v7u_N002503|2503] MSBs and payment service providers (PSP) often handle higher volumes of smaller transactions, which require a more automated approach to monitoring than corporate banks.
ZH: 货币服务企业和支付服务提供商（PSP）处理大量小额交易，需要比企业银行更自动化的监控方法

[v7u_N002504|2504] In a preliminary meeting with the MSB’s leadership, the consultant identified the complexities of managing compliance in the international remittance business. The consultant recognized the challenges of navigating various regulatory environments across countries and proposed a new structure for the MSB’s financial crime functions, including:
ZH: 顾问与货币服务企业领导层初步会议，识别国际汇款业务合规复杂性，并提出新金融犯罪职能结构

[v7u_N002505|2505] AML compliance officer: Oversee AML compliance program and ensure adherence to AML regulations across all jurisdictions where the MSB operates.
ZH: 反洗钱合规官负责监督反洗钱合规计划并确保在所有运营司法管辖区遵守反洗钱法规

[v7u_N002506|2506] Risk assessment: Conduct customer and transaction risk assessments, identify high-risk clients and transactions, and apply enhance due diligence (EDD).
ZH: 风险评估：进行客户和交易风险评估，识别高风险客户和交易，并应用强化尽职调查（EDD）

[v7u_N002507|2507] Transaction monitoring: Monitor transactions for suspicious activity, review alerts, and ensure proper follow-up on potential issues.
ZH: 交易监控：监控可疑交易活动，审查警报，并确保对潜在问题进行适当跟进

[v7u_N002508|2508] Sanctions compliance officer: Ensure adherence to sanctions regulations, manage relationships with sanctioned entities, and oversee compliance measures.
ZH: 制裁合规官：确保遵守制裁法规，管理与受制裁实体的关系，并监督合规措施

[v7u_N002509|2509] Training and awareness: Conduct staff AML/CFT training, ensuring they understand their responsibilities under AML/CFT regulations and the reporting structures for suspicious transactions.
ZH: 培训与意识：开展员工反洗钱/反恐怖融资培训，确保其理解反洗钱/反恐怖融资法规下的职责及可疑交易报告结构

[v7u_N002510|2510] Internal audit: Assess compliance program effectiveness, conduct regular audits, and report findings to the board.
ZH: 内部审计：评估合规计划有效性，进行定期审计，并向董事会报告结果

[v7u_N002511|2511] Regulatory liaison: Serve as the point of contact for regulatory bodies, ensure timely submission of required reports, and facilitate communication with regulators.
ZH: 监管联络：作为监管机构联络点，确保及时提交所需报告，并促进与监管机构的沟通

[v7u_N002512|2512] The consultant advised the MSB to implement this structured approach to enhance its compliance workflow and establish a culture of accountability and awareness for financial crime risks. By focusing on regulatory engagement, internal training, and transaction monitoring, the MSB significantly improved its management of risk. The consultant also ensured that the MSB’s policies, procedures, and processes aligned with the principles of the organization's AFC program.
ZH: 顾问建议货币服务企业实施结构化方法以增强合规工作流程并建立金融犯罪风险问责文化

[v7u_N002513|2513] Both the international bank and the MSB benefited from the consultant's expertise in restructuring their compliance frameworks. They enhanced their second line of defense capabilities by adopting a proactive approach to financial crime risk management that was aligned with regulatory expectations. This strategic improvement enabled sustainable growth and fortified their positions within the financial industry.
ZH: 案例总结：顾问帮助国际银行和货币服务企业重组合规框架，增强第二道防线能力
```

## S1.1 候选列表

```json
[]
```
