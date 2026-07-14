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

section_id: `CH08-S05`

section_title: `Private banking and wealth management risks > Special purpose vehicle risks`

base_kg_section_summary:

```json
{
  "covered_topics": [
    {
      "title_zh": "SPV定义与合法用途",
      "title_en": "SPV Definition and Legitimate Uses"
    },
    {
      "title_zh": "SPV金融犯罪风险与红旗信号",
      "title_en": "SPV Financial Crime Risks and Red Flags"
    },
    {
      "title_zh": "集合投资工具（PIV）定义与风险",
      "title_en": "Pooled Investment Vehicle (PIV) Definition and Risks"
    },
    {
      "title_zh": "利用SPV和PIV的贸易洗钱",
      "title_en": "Trade-Based Money Laundering Using SPVs and PIVs"
    },
    {
      "title_zh": "强化尽职调查与客户尽职调查要求",
      "title_en": "Enhanced Due Diligence (EDD) and CDD Requirements"
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000642|642] Special purpose vehicles (SPVs) are legal entities created for specific and limited purposes.
ZH: 特殊目的载体（SPV）是为特定有限目的设立的法律实体

[v7u_N000643|643] SPVs can be used in mergers and acquisitions, joint ventures, real estate projects, infrastructure development, and energy projects.
ZH: SPV可用于并购、合资、房地产、基础设施和能源项目

[v7u_N000644|644] SPVs can also be used to manage and protect intellectual property assets including trademarks and copyrights.
ZH: SPV可用于管理和保护知识产权资产

[v7u_N000645|645] SPVs are often used in complex financial transactions and investments such as securities and asset-backed financing.
ZH: SPV常用于复杂金融交易和资产支持融资

[v7u_N000646|646] There are financial crime risks associated with SPVs.
ZH: SPV存在金融犯罪风险

[v7u_N000647|647] SPVs can have complex and opaque structures to disguise the true beneficial ownership.
ZH: SPV可能通过复杂不透明的结构掩盖真实受益所有人

[v7u_N000648|648] SPVs might be used to obscure the source of illicit funds. Criminals layer illicit proceeds through a series of transactions via the SPVs, transferring funds to or from financial institutions. This creates a complex web of
ZH: 犯罪分子通过SPV进行一系列交易来分层非法收益，掩盖资金来源

[v7u_N000649|649] There are several red flags that indicate attempts to disguise illicit funds or conduct fraudulent activities using SPVs. These include:
ZH: 列举利用SPV掩饰非法资金或欺诈活动的红旗信号信号

[v7u_N000650|650] Complex ownership structures involving multiple layers of companies
ZH: 涉及多层公司的复杂所有权结构是红旗信号

[v7u_N000651|651] Lack of transparency
ZH: 缺乏透明度是红旗信号

[v7u_N000652|652] Unclear purpose of the SPV
ZH: SPV目的不明确是红旗信号

[v7u_N000653|653] Criminals might select jurisdictions that have lenient regulatory oversight or tax-friendly environments. This enables them to hide their financial activities and minimize tax liabilities.
ZH: 犯罪分子选择监管宽松或税收优惠的司法管辖区以隐藏活动和避税

[v7u_N000654|654] Pooled investment vehicles (PIVs) are small investments pooled together from a large group of investors.
ZH: 集合投资工具（PIV）是从大量投资者汇集的小额投资

[v7u_N000655|655] PIVs can be used in Ponzi schemes and insider trading.
ZH: PIV可能被用于庞氏骗局和内幕交易

[v7u_N000656|656] Additionally, criminals might engage in trade-based money laundering using SPVs and PIVs. Criminals manipulate trade transactions between SPVs and PIVs by deflating or inflating prices.
ZH: 犯罪分子利用SPV和PIV进行贸易洗钱，操纵交易价格

[v7u_N000657|657] This process enables the movement of illicit funds while disguising it as legitimate trade activity.
ZH: 该过程将非法资金伪装成合法贸易活动进行转移

[v7u_N000658|658] Financial institutions must be vigilant in conducting enhanced due diligence (EDD) on SPVs and PIVs. It is important to ensure these investments comply with CDD regulations such as the Financial Crime Enforcement Network's CDD rule.
ZH: 金融机构必须对SPV和PIV进行强化尽职调查，遵守客户尽职调查规则

[v7u_N000659|659] Financial institutions must identify ultimate beneficial owners and understand the true purpose of these entities.
ZH: 金融机构必须识别最终受益所有人并了解实体真实目的

[v7u_N000660|660] This will help mitigate any potential financial crime risks associated with SPVs.
ZH: 这有助于减轻与SPV相关的金融犯罪风险
```

allowed_unit_ids:

```json
[
  "v7u_N000642",
  "v7u_N000643",
  "v7u_N000644",
  "v7u_N000645",
  "v7u_N000646",
  "v7u_N000647",
  "v7u_N000648",
  "v7u_N000649",
  "v7u_N000650",
  "v7u_N000651",
  "v7u_N000652",
  "v7u_N000653",
  "v7u_N000654",
  "v7u_N000655",
  "v7u_N000656",
  "v7u_N000657",
  "v7u_N000658",
  "v7u_N000659",
  "v7u_N000660"
]
```
