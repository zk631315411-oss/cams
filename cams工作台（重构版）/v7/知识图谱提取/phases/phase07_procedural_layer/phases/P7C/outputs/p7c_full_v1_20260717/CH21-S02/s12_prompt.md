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

section_id: `CH21-S02`

section_title: `AFC guidance from other organizations > Transparency International AFC guidance`

section_text_with_unit_anchors:

```text
[v7u_N001609|1609] Transparency International (TI) is a non-governmental organization committed to stopping corruption and promoting transparency, accountability, and integrity at both national and international levels.
ZH: 透明国际（TI）是致力于制止腐败的非政府组织

[v7u_N001610|1610] Founded in 1993, TI operates in approximately 100 countries.
ZH: 透明国际成立于1993年，在约100个国家开展活动

[v7u_N001611|1611] TI advocates for policies that hold powerful people and organizations accountable.
ZH: 透明国际倡导追究权力人物和组织的责任

[v7u_N001612|1612] It conducts research to understand the causes of corruption and initiates innovative, scalable, evidence-based projects that provide solutions to prevent and stop corruption.
ZH: 透明国际开展腐败成因研究并推动创新项目以预防和制止腐败

[v7u_N001613|1613] TI has two featured priorities:
ZH: 透明国际的两大重点优先事项

[v7u_N001614|1614] Political integrity: Ensuring political power is held accountable
ZH: 政治诚信：确保政治权力被问责

[v7u_N001615|1615] Dirty money: Identifying and closing loopholes in the global financial system that allow for corruption and money laundering
ZH: 脏钱：识别并堵住全球金融体系中允许腐败和洗钱的漏洞

[v7u_N001616|1616] Other AFC priorities include:
ZH: 透明国际金融犯罪防控指南的其他重点领域

[v7u_N001617|1617] Asset recovery and theft of public money.
ZH: 资产追回和公共资金盗窃是金融犯罪防控重点

[v7u_N001618|1618] Business integrity.
ZH: 商业诚信是金融犯罪防控的重要领域

[v7u_N001619|1619] Extractive industries.
ZH: 采掘业是金融犯罪防控的关注行业

[v7u_N001620|1620] Foreign bribery enforcement.
ZH: 海外贿赂执法是金融犯罪防控的重点

[v7u_N001621|1621] Grand corruption.
ZH: 重大腐败是透明国际金融犯罪防控指南关注的重点领域之一。

[v7u_N001622|1622] Judiciary and law enforcement.
ZH: 司法与执法是透明国际金融犯罪防控指南涵盖的关键领域。

[v7u_N001623|1623] Whistleblowing.
ZH: 举报机制是透明国际金融犯罪防控指南的重要组成部分。

[v7u_N001624|1624] The TI Corruption Perceptions Index (CPI) is a globally recognized ranking that assesses perceived levels of public sector corruption in jurisdictions worldwide.
ZH: 透明国际腐败感知指数（CPI）是全球公认的公共部门腐败水平排名。

[v7u_N001625|1625] Established in 1995, the CPI scores approximately 180 jurisdictions on a scale from 0 (highly corrupt) to 100 (very clean), based on expert assessments and business surveys.
ZH: CPI自1995年起对约180个司法管辖区评分，0分代表高度腐败，100分代表非常清廉。

[v7u_N001626|1626] Each jurisdiction's score is calculated using data from 13 possible sources measuring factors such as bribery, misuse of public office, and weak anti-corruption measures.
ZH: CPI评分基于13个数据源，衡量贿赂、滥用公职和反腐败措施薄弱等因素。

[v7u_N001627|1627] The CPI ranks countries based on their scores, indicating each country’s level of perceived corruption compared to other countries in the index.
ZH: CPI根据得分对国家进行排名，反映各国感知腐败水平的相对位置。

[v7u_N001628|1628] The index provides valuable insights for policymakers, investors, and organizations by highlighting governance challenges and accountability gaps.
ZH: CPI为政策制定者、投资者和组织提供关于治理挑战和问责差距的宝贵见解。

[v7u_N001629|1629] The CPI helps raise awareness and encourages reforms to strengthen transparency worldwide, making it a key tool in the fight against corruption.
ZH: CPI有助于提高认识并推动改革以加强全球透明度，是反腐败的关键工具。

[v7u_N001630|1630] TI’s Bribe Payers Index (BPI) ranks the leading exporting countries according to their propensity to bribe.
ZH: 透明国际行贿指数（BPI）根据主要出口国的行贿倾向进行排名。

[v7u_N001631|1631] TI’s annual Global Corruption Report combines the CPI and the BPI and ranks each country by its overall level of corruption.
ZH: 透明国际年度《全球腐败报告》结合CPI和BPI，对各国的总体腐败水平进行排名。

[v7u_N001632|1632] The lists help financial institutions determine the risk associated with a particular jurisdiction.
ZH: 这些列表帮助金融机构评估特定司法管辖区的风险。
```

## S1.1 候选列表

```json
[]
```
