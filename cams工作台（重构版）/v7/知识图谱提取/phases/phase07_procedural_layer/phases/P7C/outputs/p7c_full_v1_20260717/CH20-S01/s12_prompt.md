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

section_id: `CH20-S01`

section_title: `AFC guidance from leading international organizations > United Nations AFC guidance`

section_text_with_unit_anchors:

```text
[v7u_N001467|1467] The UN is a global organization consisting of many Member States.
ZH: 联合国是由众多会员国组成的全球组织

[v7u_N001468|1468] The UN’s agenda includes maintaining global peace and security, providing humanitarian assistance, upholding human rights, and maintaining international law.
ZH: 联合国议程包括维护和平与安全、人道援助、人权和国际法

[v7u_N001469|1469] While the UN promotes international cooperation, it is not a world government and does not make laws.
ZH: 联合国不是世界政府，不制定法律

[v7u_N001470|1470] The UN’s Office on Drugs and Crime (UNODC) assists member states in combating the threat of money laundering, terrorist financing, and other financial crimes.
ZH: 联合国毒品和犯罪问题办公室协助成员国打击洗钱、恐怖融资等金融犯罪

[v7u_N001471|1471] The agency also implements the UN program on terrorism and assists countries in criminal justice reform and in combating transnational organized crime and corruption.
ZH: UNODC还实施反恐项目，协助刑事司法改革和打击跨国有组织犯罪与腐败

[v7u_N001472|1472] The UN Office of Counter-Terrorism (UNOCT) includes CFT resources through programs at its Counter-Terrorism Centre.
ZH: 联合国反恐办公室通过其反恐中心提供反恐怖融资资源

[v7u_N001473|1473] The Global Programme Against Money Laundering (GPML) is an initiative by the UN General Assembly.
ZH: 全球反洗钱方案是联合国大会发起的一项倡议

[v7u_N001474|1474] It assists Member States in developing robust AML programs including comprehensive legal frameworks, institutional infrastructure, and technical skills to combat money laundering and terrorist financing.
ZH: GP洗钱协助成员国建立强有力的反洗钱计划，包括法律框架、机构基础设施和技术技能

[v7u_N001475|1475] The GPML is also responsible for coordinating national, regional, and international cooperation on AML issues.
ZH: GPML负责协调国家、区域和国际层面的反洗钱合作

[v7u_N001476|1476] The UN Vienna 1988 Convention addressed drug trafficking and defined money laundering offenses.
ZH: 联合国1988年维也纳公约涉及毒品贩运并定义了洗钱犯罪

[v7u_N001477|1477] The UN encourages cooperation of regulators across borders and sectors. This includes enhanced information sharing to close information gaps and identify fraud and illicit financial activity.
ZH: 联合国鼓励监管机构跨境跨部门合作，加强信息共享以识别欺诈和非法金融活动

[v7u_N001478|1478] As part of its risk management initiative, the UN Charter gives the UN Security Council the authority to impose various sanctions.
ZH: 联合国宪章授权安理会实施制裁

[v7u_N001479|1479] The UNODC also published a comprehensive study using real cases that demonstrate how international cooperation was used to fight organized crime and money laundering. The study is also used for sharing lessons learned and recommendations for greater collaboration among jurisdictions.
ZH: UNODC发布研究报告，展示国际合作打击有组织犯罪和洗钱的真实案例及经验教训

[v7u_N001480|1480] In addition, UNODC published step-by-step guidance for member jurisdictions to request legal assistance with drug-related cases to provide the widest level of mutual assistance in fighting transnational crime networks.
ZH: UNODC发布逐步指导，帮助成员国请求毒品案件法律协助以打击跨国犯罪网络

[v7u_N001481|1481] UNOCT provides guidance and capacity building for the implementation of the UN's Global Counter-Terrorism Coordination Compact and assists Member States in building capacity to address the threat of terrorism.
ZH: 联合国反恐办公室（UNOCT）提供反恐指导与能力建设
```

## S1.1 候选列表

```json
[]
```
