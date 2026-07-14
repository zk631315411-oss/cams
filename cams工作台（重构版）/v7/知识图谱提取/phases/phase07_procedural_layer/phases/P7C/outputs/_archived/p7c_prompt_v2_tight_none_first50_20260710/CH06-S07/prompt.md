# P7C Section-Local Incremental Directed Card Extraction Prompt v2

## 角色

你是P7C局部有向关系提取器。任务不是重复基础知识图谱，而是从单个section中提取基础KG无法表达、且能支持CAMS题目选项判断的增量有向关系。

`flow_nodes + flow_edges`是知识正本。只输出严格JSON，不输出Markdown或解释。准确率优先于card数量。

## 基础KG边界

基础KG能够保存定义、分类、事实、例子、案例、风险指标、规则、控制措施和后果，并标注其语义角色；还能表达CP之间的包含、举例、铺垫、并列、对比、总结和基础关系。

基础KG不能表达具体情境、动作、判断和结果之间的细粒度有向关系。

如果section只有定义、分类、普通案例、孤立红旗、控制措施列表、框架组成、历史背景或机构介绍，必须跳过。不得包装成“入口→评估/实施→列表→分类/产物”。

如果原文明确连接“适用情境→判断或动作→具体结果”，或者包含组合条件、阈值、差异化结论、职责分工、后续应对、控制效果或反馈机制，可以进入P7。

单句规则、单句因果、单句机制说明，若基础KG可直接保存并用于检索，不进入P7。只有跨多个动作、角色、阶段、条件分支、记录/交接或反馈循环的结构才进入P7。

## P7增量关系

只提取以下关系：

- 明确步骤顺序
- 条件分支
- 事件、发现或结论触发应对
- 行动产生结果、记录、状态变化或交接
- 机制或原因导致、解释或增加后果
- 行动参照并受到标准约束
- 事件或结果触发复核、更新、调优或再次处理
- 因素在明确条件下导向差异化结论

## 强制验收门

生成每张card前，内部回答：

1. 能否写出“A通过什么关系，在何种条件下（如有），导向B”？
2. 该关系是否超出基础KG的定义、分类、列表、普通风险指标或组成关系？
3. 该关系能否判断选项的顺序、条件、因果、义务、应对或适用范围？
4. source、target及关系方向是否都有当前section的unit证据？

四项必须全部为“是”，否则不生成card。`needs_review`不能绕过验收门。

## 证据与KG使用

`section_text_with_unit_anchors`是唯一事实证据。只能引用`allowed_unit_ids`中的unit_id。

`base_kg_section_summary`只包含：core_point_id、title、unit_ids、unit role摘要、CP边界和CP间基础关系。它只能用于覆盖审查和判断是否重复KG，不得作为节点或边的事实证据，不得补造原文没有的条件、顺序、结果或关系。

不得虚构“需要进行评估”“机构希望降低风险”“对象接受审查”等通用入口；不得虚构“风险得到管理”“持续合规义务”“框架建立完成”等通用出口。

入口、出口和核心边都必须有原文直接证据或强功能依赖。若缺少自然且有证据的入口或出口，跳过，不得补造。

## 覆盖审查

按自然段落、转折、主体变化、对象变化和`base_kg_section_summary`中的CP边界检查整个section。

对每个局部主题分别判断：仅属基础KG则跳过；存在增量有向关系则生成card；与已有card重复则合并。不得因前文已有card而忽略后文新的对象、业务线、控制场景或应对链。

## 构图原则

一张card只表达一个局部闭合判断链。保留if、when、unless、may、should、must、only、not、potentially、depending on等限定词。

案例只能提取案例中实际发生的顺序或因果，不得推广为一般规则。

普通红旗由KG承接；只有复合条件、阈值、差异化结论或后续应对进入P7。如果风险指标被原文明确用于判断特定对象是否异常、可疑、高风险或需要特定处理，也可以进入P7。

普通控制或框架组成由KG承接；只有适用情境、执行关系、控制效果、先后或反馈进入P7。上位标准、法律、监管原则向机构制度或流程传导要求时，优先使用`standard_transmits_requirement`；具体操作标准限制某动作如何执行时，才使用`standard_constrains_action`。

## card_nature

只能使用：`execution`、`assessment`、`risk_indicator`、`control`。

## flow_node

每个节点必填：`node_id, node_category, node_type, label, evidence_unit_ids, evidence_strength`。

允许类型：

- entry：`E1_event_signal, E2_object_entry, E3_state_threshold, E4_handoff, E5_time_cycle, E6_change_exception, E7_external_command, E8_decision_finding`
- process：`P1_assessment, P2_execution, P3_branch_routing, P4_collection, P5_coordination, P6_feedback, P7_monitoring, P8_constrained_action, P9_planning, P10_sufficiency`
- exit：`X1_classification, X2_product, X3_state_change, X4_handoff, X5_config_change, X6_termination, X7_continuing_obligation`
- auxiliary：`input, standard`

每张card至少包含一个有证据的entry、process和exit。EDD、筛查、监控、调优、审查、报告等动作必须是process，不得写成standard。

## flow_edge

允许：`PRECEDES, REFERENCES, PRODUCES, DECIDES, FEEDBACK`。

`PRECEDES`只用于明确顺序或不可逆的功能先后；只有交换source和target会违反原文或业务依赖时才能使用。共同出现、教材顺序或“通常如此”不足以成边。

`REFERENCES`必须由process指向input或standard，不表达先后、产出或条件。`PRODUCES`必须由process指向exit。`DECIDES`必须由`P3_branch_routing`发出并填写`condition`。`FEEDBACK`只用于结果触发更新、补充、复核、调优或再次处理。

每条边必填：`edge_id, edge_type, source, target, evidence_unit_ids, evidence_strength`。
可选：`relation_type, condition, source_quote, review_status`。

不要输出`qualifier`或`modality`字段；如需表达限定词，写入`label`、`condition`、`source_quote`或`review_notes`。

## relation_type

允许：

`clue_supports_identification, mechanism_explains_risk, identification_leads_to_conclusion, conclusion_triggers_response, branch_condition_routes_path, component_assembles_product, standard_constrains_action, result_handoffs_stage, feedback_requests_completion, cycle_requires_monitoring, standard_transmits_requirement, parallel_alternative_no_sequence`。

`branch_condition_routes_path`只能用于带`condition`的`DECIDES`边。证据不足时省略`relation_type`，不得机械映射或硬贴。

## 证据与审核状态

P7C只输出`explicit, functional_dependency, needs_review`；不得输出`rejected`。

核心增量关系全部明确时，card为`accepted`。少量边存在有方向证据的功能依赖时，card为`needs_review`。入口、出口、方向或增量价值不成立时不输出card。

每张card的`review_notes`必填，格式为：
`增量命题：A --关系--> B（条件如有）；KG不足：基础KG不能表达什么；选项判断：可确认或排除什么选项。`

`review_notes`必须使用中文。`title`、`label`和`source_quote`可保留英文教材术语或原文关键词，但解释性内容必须使用中文，避免中英混写。

不得输出空`flow_nodes`或空`flow_edges`。

## 输出结构

每张card必填：
`card_id, section_id, card_nature, title, flow_nodes, flow_edges, source_unit_ids, review_status, review_notes`。

顶层必须输出：
`section_id, section_title, cards, skip_reason`。

没有合格card时输出：
{"section_id":"<section_id>","section_title":"<section_title>","cards":[],"skip_reason":"Only knowledge already representable by the base KG, or no evidence-supported incremental directed relation."}

## 当前section

section_id: `CH06-S07`

section_title: `Money Laundering Risks in Financial Services > Shell and shelf companies risks`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "core_points": [
    {
      "core_point_id": "cp_CH06_S07_001",
      "title_zh": "壳公司、现成公司和幌子公司的定义",
      "title_en": "Definitions of Shell, Shelf, and Front Companies",
      "anchor_unit_ids": [
        "v7u_N000426",
        "v7u_N000427",
        "v7u_N000429"
      ],
      "key_unit_ids": [
        "v7u_N000426",
        "v7u_N000427",
        "v7u_N000429",
        "v7u_N000428",
        "v7u_N000430"
      ],
      "support_unit_ids": [
        "v7u_N000428",
        "v7u_N000430"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000426",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000427",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000429",
          "unit_type": "definition",
          "cp_unit_role": "defines"
        },
        {
          "unit_id": "v7u_N000428",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000430",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        }
      ]
    },
    {
      "core_point_id": "cp_CH06_S07_002",
      "title_zh": "壳公司的风险和类型",
      "title_en": "Risks and Typologies of Shell Companies",
      "anchor_unit_ids": [
        "v7u_N000431",
        "v7u_N000432",
        "v7u_N000438",
        "v7u_N000439",
        "v7u_N000440",
        "v7u_N000441"
      ],
      "key_unit_ids": [
        "v7u_N000431",
        "v7u_N000432",
        "v7u_N000438",
        "v7u_N000439",
        "v7u_N000440"
      ],
      "support_unit_ids": [
        "v7u_N000433",
        "v7u_N000434",
        "v7u_N000435",
        "v7u_N000436",
        "v7u_N000437"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000431",
          "unit_type": "risk_indicator",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000432",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000438",
          "unit_type": "definition",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000439",
          "unit_type": "definition",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000440",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000441",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000433",
          "unit_type": "fact",
          "cp_unit_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000434",
          "unit_type": "classification",
          "cp_unit_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000435",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000436",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        },
        {
          "unit_id": "v7u_N000437",
          "unit_type": "fact",
          "cp_unit_role": "classifies"
        }
      ]
    },
    {
      "core_point_id": "cp_CH06_S07_003",
      "title_zh": "丹麦银行洗钱案例研究",
      "title_en": "Danske Bank Money Laundering Case Study",
      "anchor_unit_ids": [
        "v7u_N000442"
      ],
      "key_unit_ids": [
        "v7u_N000442",
        "v7u_N000444",
        "v7u_N000445",
        "v7u_N000446",
        "v7u_N000447"
      ],
      "support_unit_ids": [
        "v7u_N000443",
        "v7u_N000444",
        "v7u_N000445",
        "v7u_N000446",
        "v7u_N000447",
        "v7u_N000448",
        "v7u_N000449",
        "v7u_N000450",
        "v7u_N000451"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000442",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000444",
          "unit_type": "process",
          "cp_unit_role": "describes_process"
        },
        {
          "unit_id": "v7u_N000445",
          "unit_type": "process",
          "cp_unit_role": "describes_process"
        },
        {
          "unit_id": "v7u_N000446",
          "unit_type": "process",
          "cp_unit_role": "describes_process"
        },
        {
          "unit_id": "v7u_N000447",
          "unit_type": "process",
          "cp_unit_role": "describes_process"
        },
        {
          "unit_id": "v7u_N000443",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000448",
          "unit_type": "process",
          "cp_unit_role": "describes_process"
        },
        {
          "unit_id": "v7u_N000449",
          "unit_type": "fact",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000450",
          "unit_type": "case",
          "cp_unit_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N000451",
          "unit_type": "rule",
          "cp_unit_role": "prescribes_measure"
        }
      ]
    }
  ],
  "same_section_core_point_edges": [
    {
      "source_id": "cp_CH06_S07_001",
      "target_id": "cp_CH06_S07_002",
      "relation_type": "prepares",
      "reason": "CP1 defines shell, shelf, and front companies, providing foundational definitions that CP2 builds upon to discuss their risks and typologies."
    },
    {
      "source_id": "cp_CH06_S07_003",
      "target_id": "cp_CH06_S07_002",
      "relation_type": "illustrates",
      "reason": "CP3 is a case study that illustrates the risks and typologies of shell companies described in CP2."
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000426|426] A shell company or corporation is a company that, at the time of incorporation, has no significant assets or operations.
ZH: 壳公司（shell company）指成立时无重大资产或运营的公司

[v7u_N000427|427] A similarly named "shelf" company is a corporation that has had no activity. It has been created and put "on the shelf" so that it can be sold later to someone who prefers a previously registered corporation over a new one.
ZH: 现成公司（shelf company）是已注册但无活动的公司，可后续出售

[v7u_N000428|428] Both shell and shelf companies are generally kept dormant and used later to appear legitimate while usually masking the beneficial owner.
ZH: 壳公司和现成公司通常保持休眠，用于掩盖受益所有人

[v7u_N000429|429] A front company is an entity that conducts some legitimate business while also shielding another company from liability or scrutiny.
ZH: 幌子公司（front company）从事合法业务同时掩护另一公司

[v7u_N000430|430] Financial criminals might use a front company to conceal illicit activity. For example, they might operate a car wash to launder the profits of drug trafficking.
ZH: 幌子公司可用于洗钱，例如以洗车行掩盖毒品交易利润

[v7u_N000431|431] While there are legitimate uses for shell, shelf, and front companies, within the context of researching and accepting customers, they are considered high risk.
ZH: 壳公司、现成公司和幌公司在客户准入中视为高风险

[v7u_N000432|432] Shell companies can be established with the primary objective of claiming the proceeds of crime as legitimate revenue or commingling criminal proceeds with legitimate revenue. According to the Financial Action Task Force (FATF), the use of shell companies to facilitate financial crime is a well-documented typology.
ZH: 壳公司可用于将犯罪收益混入合法收入，FATF已记录此类型

[v7u_N000433|433] Shell companies can be set up in onshore and offshore locations.
ZH: 壳公司可在在岸和离岸地点设立

[v7u_N000434|434] Their ownership structures can take several forms:
ZH: 壳公司的所有权结构有多种形式

[v7u_N000435|435] Shares can be issued to a natural or legal person in registered or bearer form.
ZH: 股份可以记名或不记名形式发行给自然人或法人

[v7u_N000436|436] Some shell companies can be created for a single purpose or to hold a single asset.
ZH: 部分壳公司可为单一目的或持有单一资产而设立

[v7u_N000437|437] Some shell companies can be established as multipurpose entities.
ZH: 部分壳公司可设立为多用途实体

[v7u_N000438|438] Shell companies are often legally incorporated and registered by the criminal organization but have no legitimate business purpose. Often purchased from lawyers, accountants, or corporate service providers, they are convenient vehicles for bribery and corruption, money laundering, and sanctions evasion.
ZH: 壳公司常由犯罪组织合法注册但无正当商业目的，用于贿赂、洗钱和逃避制裁

[v7u_N000439|439] Sometimes, the stock of these shell corporations is issued in bearer shares, which means that whoever carries them is the purported owner.
ZH: 不记名股票（bearer shares）的持有者即为名义所有人

[v7u_N000440|440] Tax haven countries and their strict secrecy laws can further conceal the true ownership of shell corporations. In addition, the information may be held by professionals who claim secrecy.
ZH: 避税天堂的保密法及专业人士的保密义务可进一步隐藏壳公司真实所有权

[v7u_N000441|441] When FATF reviewed the rules and practices that impair the effectiveness of financial crime prevention and detection systems, it found in particular that shell corporations and nominees are widely used mechanisms to launder the proceeds from crime. As a result, shell companies are considered to represent a higher risk of financial crime.
ZH: FATF发现壳公司和名义人是洗钱高风险机制

[v7u_N000442|442] Danske Bank, Denmark's largest financial institution, became embroiled in a significant money laundering case centered around its Estonian branch. According to Reuters, between 2007 and 2015, approximately €200 billion of suspicious funds were funneled through the bank, primarily originating from Russia as well as Estonia, Latvia, Cyprus, and Great Britain. The scandal became known in 2018, unveiling the intricate use of shell and shelf companies to facilitate the laundering process.
ZH: 丹麦银行爱沙尼亚分行洗钱案涉及壳公司和现成公司

[v7u_N000443|443] One prominent example was the use of United Kingdom limited liability partnerships (LLP) and Scottish limited partnerships (SLP). These entities allowed for minimal disclosure requirements, enabling criminals to hide behind complex ownership structures. The shell companies conducted fictitious transactions and created false invoices to justify the movement of funds, making it difficult for authorities to trace the origins of the illicit money.
ZH: 英国LLP和SLP被用于洗钱，利用低披露要求隐藏所有权

[v7u_N000444|444] The laundering process in the Danske Bank scandal involved multiple steps to layer and integrate the illicit funds.
ZH: 丹麦银行洗钱过程包括多层放置、离析和融合

[v7u_N000445|445] Initially, money was deposited into accounts held by shell and shelf companies in Danske Bank's Estonian branch.
ZH: 资金最初存入丹麦银行爱沙尼亚分行的壳公司和现成公司账户

[v7u_N000446|446] These funds were then transferred through a complex web of transactions involving other shell companies, often spanning multiple jurisdictions.
ZH: 资金通过涉及其他壳公司的复杂交易网络跨境转移

[v7u_N000447|447] By moving the money through various entities and accounts, the criminals created a convoluted trail that was challenging to untangle.
ZH: 犯罪分子通过多个实体和账户转移资金制造混乱的追踪线索

[v7u_N000448|448] The use of false documentation, including fake contracts and invoices, provided legitimacy to the transactions.
ZH: 使用虚假合同和发票等伪造文件为交易提供合法性

[v7u_N000449|449] An additional finding of the scandal revealed that Danske Bank’s head office was unaware of the AML compliance failings, including the lack of an MLRO appointment for over a year, as they did not have adequate oversight and supervision of the Estonian branch and of the transactions that were being processed.
ZH: 丹麦银行总部对爱沙尼亚分行的反洗钱合规失败不知情

[v7u_N000450|450] The Danske Bank scandal had far-reaching consequences for the institution and the broader financial landscape. According to a press release by the US Department of Justice, Danske Bank faced significant regulatory scrutiny, leading to the resignation of several top executives. Danske Bank pleaded guilty to bank fraud conspiracy and paid substantial fines of more than US$2 billion.
ZH: 丹麦银行因洗钱丑闻认罪银行欺诈并支付超20亿美元罚款

[v7u_N000451|451] The scandal also reiterated the importance of robust AML controls and the need for enhanced transparency in financial transactions and adequate supervision of subsidiary businesses and operations if they are remote or overseas in higher-risk jurisdictions.
ZH: 丑闻重申了健全反洗钱控制和海外子公司监管的重要性
```

allowed_unit_ids:

```json
[
  "v7u_N000426",
  "v7u_N000427",
  "v7u_N000428",
  "v7u_N000429",
  "v7u_N000430",
  "v7u_N000431",
  "v7u_N000432",
  "v7u_N000433",
  "v7u_N000434",
  "v7u_N000435",
  "v7u_N000436",
  "v7u_N000437",
  "v7u_N000438",
  "v7u_N000439",
  "v7u_N000440",
  "v7u_N000441",
  "v7u_N000442",
  "v7u_N000443",
  "v7u_N000444",
  "v7u_N000445",
  "v7u_N000446",
  "v7u_N000447",
  "v7u_N000448",
  "v7u_N000449",
  "v7u_N000450",
  "v7u_N000451"
]
```
