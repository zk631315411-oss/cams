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

section_id: `CH03-S03`

section_title: `Examples of predicate crimes > Drug trafficking`

base_kg_section_summary:

```json
{
  "covered_topics": [
    {
      "title_zh": "毒品贩卖定义与结构",
      "title_en": "Drug Trafficking Definition and Structure"
    },
    {
      "title_zh": "毒品贩卖中的洗钱阶段与方法",
      "title_en": "Money Laundering Stages and Methods in Drug Trafficking"
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000229|229] Drug trafficking involves the illegal production, distribution, and sale of controlled substances.
ZH: 毒品贩运涉及受控物质的非法生产、分销和销售。

[v7u_N000230|230] Commonly trafficked drugs include heroin, cocaine, cannabis, and synthetic drugs such as fentanyl and methamphetamine.
ZH: 常见贩毒品种包括海洛因、可卡因、大麻及芬太尼等合成毒品。

[v7u_N000231|231] The legal status of some of these drugs complicates enforcement and regulation efforts. For example, both fentanyl and cannabis have legal medicinal uses, and recreational cannabis use is permitted in certain jurisdictions, but illegal in others.
ZH: 部分毒品的法律地位复杂化执法工作，如大麻和芬太尼的合法医疗用途。

[v7u_N000232|232] Drug trafficking operates as a highly structured network, analogous to a multinational corporation, and can involve an extensive global supply chain.
ZH: 毒品贩运运作类似跨国公司，涉及广泛的全球供应链。

[v7u_N000233|233] Money laundering can occur during the sourcing, manufacturing, or distribution stages.
ZH: 洗钱可发生在毒品贩运的采购、制造或分销阶段。

[v7u_N000234|234] Criminal organizations utilize various methods to launder money at the sourcing stage when the raw material is obtained and refined.
ZH: 犯罪组织在采购阶段利用多种方法清洗资金。

[v7u_N000235|235] Payments for chemical precursors and logistics are often made on the basis of fraudulent trade invoices and routed through offshore shell companies, cryptocurrency mixing services, and hawala networks.
ZH: 化学前体和物流付款常通过虚假贸易发票、离岸壳公司、加密货币混合服务和哈瓦拉网络进行。

[v7u_N000236|236] This allows traffickers to obscure the origins of their funds from the beginning of the supply chain.
ZH: 贩毒者从供应链起点即掩盖资金来源。

[v7u_N000237|237] At the manufacturing stage, proceeds are funneled through agribusiness, real estate acquisitions, shell logistics firms, and TBML.
ZH: 制造阶段通过农业、房地产、壳物流公司和贸易洗钱转移收益。

[v7u_N000238|238] These methods help traffickers integrate illicit funds into the economy.
ZH: 这些方法帮助贩毒者将非法资金融入经济。

[v7u_N000239|239] According to FinCEN, criminal organizations also utilize the international trade system to launder proceeds from drug trafficking.
ZH: FinCEN指出犯罪组织利用国际贸易体系清洗毒品贩运收益。

[v7u_N000240|240] Colombian drug traffickers, for instance, have historically used the Colombian Black Market Peso Exchange (BMPE) to convert US dollars into Colombian pesos. This system allows traffickers to settle drug debts or purchase future shipments while obscuring the origins of their funds.
ZH: 哥伦比亚黑市比索兑换是贸易洗钱的典型案例。

[v7u_N000241|241] Once drugs are sold and distributed, traffickers launder the consolidated cash through shell companies to appear legitimate, integrating illicit funds into the financial system.
ZH: 贩毒者通过壳公司清洗毒品现金，将非法资金融入金融体系

[v7u_N000242|242] This process highlights the legal implications of drug trafficking as a predicate offense for money laundering, as the proceeds are considered "dirty money" that need to be concealed to avoid detection by law enforcement.
ZH: 毒品贩运作为洗钱的上游犯罪，其收益被视为需要隐藏的脏钱

[v7u_N000243|243] Integration methods include real estate acquisitions in global cities, luxury asset purchases such as art, gold, yachts, and rare diamonds, and crypto-laundering through exchanges and non-fungible token platforms.
ZH: 毒品资金的融合阶段方式包括全球城市房地产收购、奢侈品购买及加密货币洗钱
```

allowed_unit_ids:

```json
[
  "v7u_N000229",
  "v7u_N000230",
  "v7u_N000231",
  "v7u_N000232",
  "v7u_N000233",
  "v7u_N000234",
  "v7u_N000235",
  "v7u_N000236",
  "v7u_N000237",
  "v7u_N000238",
  "v7u_N000239",
  "v7u_N000240",
  "v7u_N000241",
  "v7u_N000242",
  "v7u_N000243"
]
```
