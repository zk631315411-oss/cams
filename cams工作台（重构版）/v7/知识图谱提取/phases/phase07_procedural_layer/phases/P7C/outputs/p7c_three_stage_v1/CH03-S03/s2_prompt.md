# P7C KG Boundary Adjudication v1

## 角色

你是 P7C KG 边界裁决器。S1 已经发现候选有向命题。你的唯一任务是逐个判断每个命题是否超出基础 KG 的充分表达能力。

## 输入

- S1 发现的命题列表（含 candidate_id、unit_ids、proposition、relation_cues）
- section_text_with_unit_anchors（验证证据用）
- base_kg_section_summary（去重参考，不作为事实证据）
- allowed_unit_ids

## 任务

对 S1 的每一个命题，逐个判断。**必须为每个命题输出恰好一条 boundary_decision。** candidate_id 必须使用 S1 给出的原始 ID（如 prop_001），不得自行生成新 ID。即使命题数量较多，也必须逐个处理，不得遗漏、不得合并、不得跳过。

- `p7c_candidate`：命题包含超出基础 KG 表达能力的局部程序性或判断性有向结构
- `kg_only`：命题已被基础 KG 充分表达

不构图，不创建节点和边，不选 node_type，不选 edge_type。

## KG 边界标准

基础 KG 已经能够充分表达：

- 定义、分类、事实和一般规则
- 普通例子或普通案例事实
- 孤立风险指标、红旗或控制措施
- 框架、产品、措施或标准的组成列表
- 一般概念关系、单纯主题相关性和普通机制因果
- CP 之间的包含、举例、铺垫、并列、对比和总结

以下结构可能属于 P7C 增量：

- 明确步骤、职责或交接顺序
- 条件、阈值或例外导向不同判断、分支或行动
- 事件、发现、结论或外部要求触发特定主体的应对
- 识别、评估、决策或执行动作产生与该动作语义独立的具体结论、记录、状态变化、控制结果或后续行动
- 线索或输入在特定判断中被采用，而不只是被列为风险指标
- 标准直接约束具体主体如何行动，或向机构制度、流程传导要求
- 结果触发复核、补充、更新、调优、监控或再次处理
- 案例中实际发生且未被基础 KG 充分表达的条件、决策、应对、交接或反馈链

单个 unit 可以成卡，只要其中完整存在上述增量结构。普通机制或原因导致后果仍由基础 KG 承接，只有它实际构成完整程序性或判断性有向结构的一部分时，才可进入 P7C。

基础 KG 能够把一条规则作为整体知识保存，不代表它已经表达了规则内部的条件、主体、动作、判断和结果之间的有向结构。遇到 `if/when/based on/must/should not/requires` 等规则时，检查其内部是否存在可支持选项判断的 P7C 增量结构。

结构复杂度不是成卡门槛。只要候选命题内部明确存在"情境/条件/标准/输入如何关联到特定主体的动作或判断"，即使它只有一个 unit、一条边、没有独立结果、没有分支或反馈，也判为 `p7c_candidate`。"规则简单""纯义务陈述""只是条件-动作链"不是跳过理由。

`kg_only` 只能表示基础 KG 已能表达候选的全部有效结构，例如纯定义、纯阈值事实、普通案例机制、孤立指标或一般知识关系；如果基础 KG 只能保存整句话，却不能表达句内的主体、方向、条件或动作结果关系，则仍属于 P7C 增量。

## 正反边界示例

以下属于 P7C 增量（p7c_candidate）：

- "机构必须遵守当地监管要求识别PEP"：有主体、动作和方向的约束关系，"纯义务"不是交给 KG 的理由
- "机构可根据风险偏好选择执行更高的PEP标准"：风险偏好条件导向机构可选的标准配置变化
- "如果银行知道或怀疑还贷资金非法，则不应接受"：条件 entry 导向具体应对动作
- "通常按25%识别UBO；高风险时阈值可能降至10%或5%"：阈值和例外条件导向差异化分类路径

以下通常只由基础 KG 承接（kg_only）：

- "调查环境犯罪可能受到被贿赂官员阻碍"：只有普通机制说明，没有完整的主体处置或判断结构
- "犯罪分子使用BMPE转换资金并掩饰来源"：普通案例机制，无条件、职责、判断或应对结构
- "某项措施维护合规诚信、降低风险"：只有抽象目的，没有证据支持的具体持续义务或独立结果

结构复杂度不是成卡门槛。只要命题明确了主体、动作和方向，即使只有一个 unit、没有独立结果，也判为 p7c_candidate。纯定义、纯阈值事实、普通案例机制、孤立风险指标才是 kg_only。

## 输出要求

**即使所有命题都是 kg_only，也必须为每个命题逐条输出 boundary_decision，不得输出空数组。** candidate_id 必须使用 S1 的原始 ID。

## 输出结构

```json
{
  "section_id": "<section_id>",
  "boundary_decisions": [
    {
      "candidate_id": "prop_001",
      "decision": "p7c_candidate",
      "reason": "<中文：为何超出 KG 表达能力>"
    },
    {
      "candidate_id": "prop_002",
      "decision": "kg_only",
      "reason": "<中文：为什么 KG 已能充分表达>"
    }
  ]
}
```

只输出 `boundary_decisions`，不输出 cards、coverage_audit、flow_nodes、flow_edges。

## 当前section

section_id: `CH03-S03`

section_title: `Examples of predicate crimes > Drug trafficking`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "covered_topics": [
    {
      "title_zh": "毒品贩卖定义与结构",
      "title_en": "Drug Trafficking Definition and Structure",
      "covered_units": [
        {
          "unit_id": "v7u_N000229",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000230",
          "unit_type": "case",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N000232",
          "unit_type": "fact",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N000231",
          "unit_type": "fact",
          "kg_role": "explains"
        }
      ]
    },
    {
      "title_zh": "毒品贩卖中的洗钱阶段与方法",
      "title_en": "Money Laundering Stages and Methods in Drug Trafficking",
      "covered_units": [
        {
          "unit_id": "v7u_N000233",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000234",
          "unit_type": "fact",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N000237",
          "unit_type": "case",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N000241",
          "unit_type": "process",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N000243",
          "unit_type": "case",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N000235",
          "unit_type": "case",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000236",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000238",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000239",
          "unit_type": "fact",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000240",
          "unit_type": "case",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000242",
          "unit_type": "fact",
          "kg_role": "states_consequence"
        }
      ]
    }
  ],
  "covered_relations": [
    {
      "source_title": "毒品贩卖定义与结构",
      "target_title": "毒品贩卖中的洗钱阶段与方法",
      "relation_type": "prepares"
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
