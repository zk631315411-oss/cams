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
  跨 unit 归纳出的关系在 S2 构图时必须标记为 llm_inference。

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
      "source_quotes": ["原文关键短引"]
    }
  ]
}
```

每个命题必填：`candidate_id`、`unit_ids`、`proposition`。
`source_quotes` 可选——用原文关键词帮助下一阶段 S2 快速定位，不需要完整句子。
没有发现任何候选命题时，`propositions` 为空数组，并输出 `skip_reason`。

## 当前 section

section_id: `<section_id>`
section_title: `<section_title>`

base_kg_section_summary:
<BASE_KG_SUMMARY_JSON>

section_text_with_unit_anchors:
<SECTION_TEXT>

allowed_unit_ids:
<ALLOWED_UNIT_IDS>

## 当前section

section_id: `CH02-S04`

section_title: `Types of financial crime > Case example: FullTechGlobal corruption scandal`

base_kg_section_summary:

```json
{
  "covered_topics": [
    {
      "title_zh": "FullTechGlobal 案中的英国反贿赂法域外效力与合规教训",
      "title_en": "UK Bribery Act Extraterritoriality and Compliance Lessons from FullTechGlobal Case"
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000131|131] Sophie is an AFC manager in the compliance department of a financial institution that has some global businesses as its customers.
ZH: Sophie 是金融机构合规部的金融犯罪防控经理。

[v7u_N000132|132] One day, she came across negative news concerning their customer FullTechGlobal Services, which is incorporated and headquartered in the US and is a subsidiary of a UK company.
ZH: Sophie 发现客户 FullTechGlobal Services 的负面新闻。

[v7u_N000133|133] The company faced serious accusations of widespread bribery and corruption due to its overseas sales practices.
ZH: 该公司因海外销售行为面临广泛贿赂和腐败的严重指控。

[v7u_N000134|134] This raised concerns under the extraterritorial provisions of the UK Bribery Act 2010.
ZH: 此事引发对《英国反贿赂法》域外条款的关切。

[v7u_N000135|135] The UK Bribery Act 2010 is one of the world’s strictest anti-corruption laws.
ZH: 《英国反贿赂法》是全球最严格的反腐败法律之一。

[v7u_N000136|136] It applies to any company with a UK connection and also holds parent firms liable for corrupt activities by subsidiaries, regardless of location.
ZH: 该法适用于任何与英国有关联的公司，母公司需对子公司腐败行为负责。

[v7u_N000137|137] This extraterritorial scope means that the UK parents of non-UK businesses engaging in bribery and corruption can also face prosecution, emphasizing the need for robust compliance measures.
ZH: 域外管辖意味着非英国企业的英国母公司也可能因贿赂腐败被起诉。

[v7u_N000138|138] Sophie’s initial investigation revealed that FullTechGlobal had strategically employed intermediaries in high-risk jurisdictions to secure lucrative contracts.
ZH: FullTechGlobal 在高风险司法管辖区战略性地雇佣中间人获取合同。

[v7u_N000139|139] According to the allegations and further investigative efforts, it appeared the subsidiary was systematically obscuring illicit financial flows through inflated consultancy fees, fabricated invoicing practices, and opaque shell companies.
ZH: 子公司通过虚增咨询费、伪造发票和壳公司掩盖非法资金流动。

[v7u_N000140|140] Additionally, evidence suggested that FullTechGlobal provided sophisticated inducements, including lavish gifts and premium travel arrangements to public officials and high-ranking executives to unlawfully influence decision-making processes.
ZH: FullTechGlobal 向公职人员和高级管理人员提供奢华礼品和旅行安排以影响决策。

[v7u_N000141|141] She followed up on the investigation and conducted a review that identified failures within FullTechGlobal’s ABC framework and internal controls. Her audit uncovered deficiencies in internal control mechanisms and inadequate oversight, which facilitated prolonged and undetected corrupt activities.
ZH: FullTechGlobal腐败案审计发现内部控制缺陷和监管不足

[v7u_N000142|142] Bribery was identified as the predicate crime, leading to the laundering of illicit funds through complex financial networks designed to evade regulatory scrutiny and forensic tracing efforts.
ZH: 贿赂作为上游犯罪，通过复杂金融网络洗钱

[v7u_N000143|143] Given these findings, the regulatory implications under the UK Bribery Act 2010 are profound. FullTechGlobal Services faces severe financial penalties, increased scrutiny from international regulators, and potential criminal liability for both the subsidiary and the parent company, including its executives.
ZH: FullTechGlobal面临英国《反贿赂法》下的严厉处罚和监管审查

[v7u_N000144|144] As an AFC manager, she recognizes that her institution needs to maintain compliance integrity and mitigate bribery and corruption risks in its dealings with global businesses such as FullTechGlobal Services.
ZH: 金融犯罪防控经理有义务维护合规诚信并降低贿赂风险
```

allowed_unit_ids:

```json
[
  "v7u_N000131",
  "v7u_N000132",
  "v7u_N000133",
  "v7u_N000134",
  "v7u_N000135",
  "v7u_N000136",
  "v7u_N000137",
  "v7u_N000138",
  "v7u_N000139",
  "v7u_N000140",
  "v7u_N000141",
  "v7u_N000142",
  "v7u_N000143",
  "v7u_N000144"
]
```
