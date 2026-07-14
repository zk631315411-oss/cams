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
      "source_quotes": ["原文关键短引"],
      "induction": "cross_unit"
    }
  ]
}
```

每个命题必填：`candidate_id`、`unit_ids`、`proposition`。
`source_quotes` 可选——用原文关键词帮助下一阶段 S2 快速定位，不需要完整句子。
`induction` 可选——仅当命题来自跨 unit 归纳（联合规则、正例、反例）时填 `"cross_unit"`；
非归纳命题不填此字段。S2 将根据此标记对各边做更细致的 derivation 判断。
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

section_id: `CH03-S02`

section_title: `Examples of predicate crimes > Environmental crime`

base_kg_section_summary:

```json
{
  "covered_topics": [
    {
      "title_zh": "环境犯罪的定义和范围",
      "title_en": "Definition and scope of environmental crime"
    },
    {
      "title_zh": "起诉环境犯罪的困难",
      "title_en": "Difficulties in prosecuting environmental crimes"
    },
    {
      "title_zh": "环境犯罪与洗钱",
      "title_en": "Environmental crimes and money laundering"
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000216|216] While all financial crime is troubling, environmental crimes are unique in terms of their lasting effects.
ZH: 环境犯罪具有独特的持久影响

[v7u_N000217|217] The Financial Crimes Enforcement Network (FinCEN) acknowledged this fact in its advisory on environmental crimes, defining them as “...illegal activity that harms human health, and harm nature and natural resources by damaging environmental quality. This can include driving biodiversity loss, and causing the overexploitation of natural resources, and thereby increasing carbon dioxide levels in the atmosphere.
ZH: FinCEN将环境犯罪定义为损害人类健康、自然和资源的非法活动

[v7u_N000218|218] Wildlife trafficking can be considered a subcategory of environmental crime due to its impact on nature. However, for enforcement purposes, it is a standalone crime.
ZH: 野生动物贩运既是环境犯罪子类也是独立犯罪

[v7u_N000219|219] Environmental crimes are complex. It is difficult to pursue criminal charges for the following reasons:
ZH: 环境犯罪复杂，刑事指控困难的原因

[v7u_N000220|220] They often involve transnational criminal organizations (TCOs).
ZH: 环境犯罪常涉及跨国犯罪组织

[v7u_N000221|221] They can be very difficult to detect prior to and during the activity.
ZH: 环境犯罪作为上游犯罪，在活动前和活动中难以被发现。

[v7u_N000222|222] They can involve several global criminal and noncriminal regulations.
ZH: 环境犯罪涉及多项全球刑事和非刑事法规。

[v7u_N000223|223] TCOs and other criminal organizations are constantly looking for ways to supplement their income, and environmental crimes offer the opportunity to both earn and launder funds simultaneously.
ZH: 环境犯罪为犯罪组织提供同时赚取和清洗资金的机会。

[v7u_N000224|224] For example, a TCO might be a part owner of a waste management and transportation front company.
ZH: 犯罪组织可能部分拥有废物管理和运输幌子公司。

[v7u_N000225|225] Their ownership would allow the TCO to inflate contracts to place illicit funds. It could then execute those contracts with complicit accountholders to layer the funds.
ZH: 犯罪组织通过虚增合同和共谋账户持有人进行离析阶段。

[v7u_N000226|226] If there is any actual hazardous waste disposal carried out, it is done in a way that minimizes overhead and increases profit, such as dumping chemical production byproducts in public drinking and bathing reservoirs.
ZH: 危险废物处置中通过最小化间接费用增加利润，如将化学副产品倾倒入公共水源。

[v7u_N000227|227] Similarly, TCOs might initiate or extort legitimate-appearing fishing, logging, and mining operations, either illegally harvesting natural resources or expanding the scope of a previously legitimate operation.
ZH: 犯罪组织发起或勒索看似合法的渔业、伐木和采矿业务。

[v7u_N000228|228] When authorities investigate the illicit activity, they often become hindered by corrupt government officials who have been bribed to block or hide the inquiry.
ZH: 腐败官员收受贿赂阻碍对非法活动的调查。
```

allowed_unit_ids:

```json
[
  "v7u_N000216",
  "v7u_N000217",
  "v7u_N000218",
  "v7u_N000219",
  "v7u_N000220",
  "v7u_N000221",
  "v7u_N000222",
  "v7u_N000223",
  "v7u_N000224",
  "v7u_N000225",
  "v7u_N000226",
  "v7u_N000227",
  "v7u_N000228"
]
```
