# P7C Proposition Discovery v1

## 角色

你是 P7C 命题发现器。逐段扫描 section 全文，列出所有可能的局部程序性或判断性有向命题。

## 什么是候选命题

候选命题 = 原文中 "情境/条件/输入/标准 → 特定主体的动作或判断 [→ 独立结果]" 的有向关系。

条件可以为空，结果可以为空（开放关系）。只要原文中存在 "A 如何关联到 B" 并且 A 和 B 都能追溯到当前 section 的 unit 证据，就是一个候选命题。

## 不做什么

- 不判断基础 KG 是否已经能表达该关系（交给下一阶段 S2 处理）
- 不构图——不画节点、不建边、不选 node_type、不选 edge_type
- 不读题目或参考答案
- 不处理跨 section 关系
- 只使用 `allowed_unit_ids` 中的 unit 作为证据

## 扫描规则

按自然段落、转折、主体变化、对象变化、条件变化逐一检查整个 section。重点检查包含以下表达的 unit：

`if, when, unless, even if, based on, require, must, should, should not, may, might, could, monitor, identify, review, approval, escalate, trigger, result in, help`

对每个局部主题，尝试写出：在条件 C 下，A（情境/事件/线索/输入/标准）如何关联到特定主体 S 的识别/评估/决策/应对 B，并在有独立原文结果时产生 D。

具体规则：

- 相邻或邻近 unit 分别给出条件/变化与主体应对时，记录为一个候选（unit_ids 覆盖两端），不拆成两个独立命题
- 不因 "规则简单""纯义务陈述""没有复杂步骤""没有分支或反馈" 跳过命题
- 保留原文的 must/should/may/might/could/help/potentially/typically 等情态强度在 proposition 中
- 抽出第一条合格命题后继续扫描后续内容——同一 section 中彼此独立的命题分别列出
- 案例中实际发生的制度响应结构（检测、分析、升级、整改等）应进入候选；犯罪分子的洗钱手法本身通常不列
- 仅描述调查或机制受到阻碍的普通困难说明，不构成候选命题
- 纯定义、纯分类、纯事实陈述、普通案例机制、孤立风险指标——列出但标记为可能交给 KG
- 跨 unit 归纳分支：原文同时给出一般规则、正例和反例，且三者围绕同一判断标准时，
  归纳为一个完整命题（输入→处理→比较标准→互斥结果），不拆成独立命题。
  必须同时满足：
  (a) 存在共同的一般规则或判断标准（非孤立案例）；
  (b) 正反实例确实围绕该标准的不同结果；
  (c) unit_ids 和 source_quotes 覆盖规则、标准及两类结果。
  仅有孤立案例、没有共同标准时，不推广为一般分支——各案例作为独立命题列出。
  跨 unit 归纳出的命题必须填写 `induction=cross_unit`，供 S3 构图和 P7D 独立审核使用；S1 不判断边的 derivation。

宁可多列，不可遗漏。

## 输入

事实证据只从 `section_text_with_unit_anchors` 提取，只引用 `allowed_unit_ids` 中的 unit_id。

`base_kg_section_summary` 仅用于了解当前 section 的基础 KG 覆盖了哪些主题，不作为事实证据。

## 输出结构

只输出严格 JSON，不输出 Markdown 或解释。

```json
{
  "section_id": "<section_id>",
  "section_title": "<section_title>",
  "propositions": [
    {
      "candidate_id": "prop_001",
      "unit_ids": ["<unit_id>"],
      "proposition": "在条件 C 下，A --关系--> B [，产生 D]",
      "source_quotes": ["原文关键短引"],
      "relation_cues": ["when", "because"],
      "induction": "cross_unit"
    }
  ]
}
```

每个命题必填：`candidate_id`、`unit_ids`、`proposition`、`relation_cues`。
`relation_cues` 数组——保留原文中表达关系的关键词（because/if/when/due to/based on/requires/aimed to 等）。
不把 because 改写成"触发/导致/导向"；proposition 保持原文语序。
`source_quotes` 可选——用原文关键词帮助下一阶段快速定位，不需要完整句子。
`induction` 可选——仅当命题来自跨 unit 归纳（联合规则、正例、反例）时填 `"cross_unit"`。
没有发现任何候选命题时，`propositions` 为空数组，并输出 `skip_reason`。

## 当前section

section_id: `CH06-S10`

section_title: `Money Laundering Risks in Financial Services > Control and ownership for AML compliance`

base_kg_section_summary:

```json
{
  "covered_topics": [
    {
      "title_zh": "受益所有人（BO）与最终受益所有人（UBO）",
      "title_en": "Beneficial Owner (BO) vs Ultimate Beneficial Owner (UBO)"
    },
    {
      "title_zh": "UBO识别要求、门槛及特殊情况",
      "title_en": "UBO Identification Requirements, Thresholds, and Special Cases"
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000483|483] Control and ownership play a vital role in AML efforts, as they can often be obscured or concealed, allowing bad actors to disguise criminal activities and facilitate financial crime.
ZH: 控制权和所有权在反洗钱工作中至关重要

[v7u_N000484|484] A beneficial owner (BO) is defined as an individual or entity that possesses ownership of a legal entity, either through shareholding or other means.
ZH: 受益所有人（BO）的定义：通过持股或其他方式拥有法律实体的个人或实体

[v7u_N000485|485] In contrast, the ultimate beneficial owner (UBO) refers specifically to one or more natural persons who ultimately owns a substantial percentage of shareholding.
ZH: 最终受益所有人（UBO）的定义：最终持有重大比例股份的自然人

[v7u_N000486|486] It is important to note that a BO might appear to have ownership of a company but might not control the company. Conversely, a UBO might not directly hold shares but does exert ultimate control over it.
ZH: BO 可能拥有所有权但不控制公司，UBO 可能不直接持股但实施最终控制

[v7u_N000487|487] This distinction is crucial when it comes to regulatory requirements surrounding ownership structures.
ZH: BO 与 UBO 的区别对所有权结构的监管要求至关重要

[v7u_N000488|488] When reviewing ownership structures, there is a regulatory obligation to identify the UBO of a customer.
ZH: 监管要求审查所有权结构时必须识别客户的 UBO

[v7u_N000489|489] For AML purposes, most jurisdictions require beneficial ownership to be identified at a threshold of 25% or more. That means you need to know every entity or individual who owns at least 25% of a customer.
ZH: 多数司法管辖区要求识别持股 25% 或以上的受益所有人

[v7u_N000490|490] Your organization will set the appropriate threshold using a riskbased approach.
ZH: 机构应采用风险为本的方法设定受益所有权阈值

[v7u_N000491|491] For certain high-risk customers, the beneficial ownership threshold might be as low as 10% and could go as low as 5% for customers who pose a significantly higher risk.
ZH: 高风险客户的受益所有人阈值可能低至 10% 甚至 5%

[v7u_N000492|492] For example, high-risk financial institutions with correspondent banking relationships in a high-risk jurisdiction might set their threshold at 5%.
ZH: 示例：高风险司法管辖区的代理行关系可能设定 5% 的阈值

[v7u_N000493|493] In order to identify the UBOs of Company A, you need to identify indirect ownership stakes in addition to direct ownership.
ZH: 识别 UBO 需要同时考虑直接和间接持股

[v7u_N000494|494] Individual D owns 10% of Company A directly. They also own 72% of Company A indirectly, as they own 90% of shares of Company B, which owns 80% of Company A. Individual D is then considered a UBO with 82% shareholding of Company A.
ZH: 示例：个人 D 通过直接和间接持股合计 82%，成为 UBO

[v7u_N000495|495] Individual C, who owns 10% of Company A directly and an additional 8% indirectly via their 10% ownership of Company B, is not a UBO.
ZH: 示例：个人 C 直接持股 10% 加间接持股 8%，未达到 UBO 标准

[v7u_N000496|496] In companies where there is no natural beneficial owner, a controller or a notional beneficial owner should be identified and verified. This allows you to understand who is in control of the decision-making in the company when natural individual UBOs are not present.
ZH: 无自然人受益所有人时，应识别并核实控制人或名义受益所有人

[v7u_N000497|497] For example, for a company that is publicly listed on the stock exchange and has thousands of shareholders, a notional beneficial owner could be the president or chief executive officer, or equivalent.
ZH: 示例：上市公司可将总裁或 CEO 作为名义受益所有人
```

allowed_unit_ids:

```json
[
  "v7u_N000483",
  "v7u_N000484",
  "v7u_N000485",
  "v7u_N000486",
  "v7u_N000487",
  "v7u_N000488",
  "v7u_N000489",
  "v7u_N000490",
  "v7u_N000491",
  "v7u_N000492",
  "v7u_N000493",
  "v7u_N000494",
  "v7u_N000495",
  "v7u_N000496",
  "v7u_N000497"
]
```
