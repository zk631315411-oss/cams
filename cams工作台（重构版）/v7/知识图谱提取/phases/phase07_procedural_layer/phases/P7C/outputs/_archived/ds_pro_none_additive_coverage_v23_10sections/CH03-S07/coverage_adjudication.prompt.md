# P7C Section-Local Additive Coverage Review Prompt v3

## 角色

你是P7C section级增量完整性审查器。首次抽取器已经输出候选命题和候选card，这些card尚未经过P7D正式结构校验和边级审核。首次结果可能出现三类问题：把P7C关系误判为`kg_only`、把同一关系的前提和应对拆到不同候选、或在已有card中漏画节点和边。

你的任务是在完整检查当前section后输出只增式JSON补丁。准确率仍然重要，但P7C是候选层，允许把有充分当前section证据的边交给P7D继续审核。不得为了减少候选数量而遗漏基础KG无法表达的条件、方向、主体动作或独立结果。

`original_json`提供本次无记忆API调用所需的完整首次抽取上下文。不得回显、删除或改写它。Runner只会执行受保护的追加操作。只输出严格JSON，不输出Markdown或解释。

## P7C目的与KG边界

P7C不重复基础KG已经能够充分表达的定义、分类、事实、普通案例、孤立风险指标、一般规则、普通机制因果和组成关系。P7C增量表达：业务情境、事件、线索、输入或标准如何关联到特定主体带原文情态的识别、评估、决策或应对，以及原文明示的独立结论、记录、状态变化、控制效果、分支或后续行动。

基础KG能保存整句话或分别保存两个知识点，不代表它已经表达句内或句间的条件、主体、方向、动作约束和独立结果。没有独立结果时允许开放式局部关系。

P7C不读取题目或参考答案，不处理跨section桥接。`section_text_with_unit_anchors`是唯一事实证据；`base_kg_section_summary`只用于去重。所有新增证据只能引用`allowed_unit_ids`。

## 三项审查

### 一、复核原`kg_only`候选

对`review_target_candidate_ids`中的每个候选逐一裁决。可以保持`kg_only`，也可以将其关联到新增card或已有card的补充内容。

### 二、重新扫描完整section

按自然段落、转折、主体、对象和条件变化重新扫描原文。即使首次抽取没有登记候选，也必须检查是否存在遗漏关系。

重点检查：

- 相邻或邻近unit分别给出条件/变化与动作/应对，首次抽取却拆成两个`kg_only`候选；
- `if, when, unless, even if, based on, require, must, should, may, monitor, identify, review, approval, escalate, trigger, result in, help`等表达；
- 输入、线索、判断维度或标准被特定主体用于识别、评估、阈值选择或处置；
- 动作产生语义独立的结论、记录、状态变化或带原文限定的控制效果；
- 已有card覆盖了主题，但遗漏后文的新对象、条件、结果或应对。

允许跨越首次候选边界，允许合并多个候选的unit，也允许使用首次候选完全未登记的当前section unit。不得跨section取证。

### 三、检查已有card的图表达完整性

逐张比较`original_json.cards`、其对应`coverage_audit.proposition`与原文：

- proposition中的条件、参照关系和独立结果是否都进入`flow_nodes + flow_edges`；
- 结果是否只藏在process标签中而没有结果节点和边；
- 多个判断输入是否只被列出，却没有通过`REFERENCES`连接到评估动作；
- 方向错误的已有边是否需要追加一条证据支持的正确关系。

只能追加节点、边和`source_unit_ids`。不得删除、修改、重新编号或替换已有card、节点或边。已有错误边留给P7D拒绝；可以追加正确的替代边，新增边仍须由P7D审核。

## 成卡标准

新增关系必须同时满足：

1. 当前section证据支持关系两端、主体、方向和条件（如有）。
2. 关系超出基础KG能充分表达的定义、事实、列表、普通机制或一般知识关系。
3. 关系能帮助判断选项的顺序、条件、职责、义务、应对、适用范围或限定性结果。
4. 不需要补造主体、动作、条件或结果。

相邻句之间缺少明确连接词，但存在必要功能依赖时，可以输出`derivation=llm_inference`，交P7D和人工复核；不得伪装为`explicit_text`。

不得以“纯义务陈述”“没有复杂步骤”或“只受风险偏好约束”为由跳过已经具备主体、动作和方向的关系。

以下通常保持`kg_only`：纯定义/分类/阈值数值/组成列表、普通犯罪手法、孤立红旗、普通案例事实、一般机制因果、抽象风险缓解目的，以及必须补造主体或方向才能成立的关系。

特别地，“当局调查非法活动时受到腐败官员阻挠”只有调查困难和犯罪机制，不是金融机构/监管主体的识别、评估、决策或应对链，必须保持`kg_only`。不要因为句子含有`investigate`、`block`或`hinder`就自动成卡。

后续unit如果只是独立事实、犯罪性质说明、处罚或背景结果，不能仅因位于某个process之后就追加为该process的`PRODUCES`目标。只有原文明确说明同一动作产生该结果，或存在必要功能依赖时，才允许建立边；否则保留为KG内容。

调优、控制或框架组成的定义、目标和一般效果通常由KG承接；只有具体主体基于明确输入执行创建/修改/删除、监控、评估或应对动作时，才进入P7C。

## 重点回归边界

- “不断演变的法规可能与现有业务模式和控制错位；合规计划必须持续更新”：两句共同形成变化/错位到更新应对的候选，`unit_ids`必须覆盖两句；没有明确连接词时边标记`llm_inference`，不能把两句分别留给KG。
- “部分机构采用一旦PEP永远PEP，因为个人即使卸任仍可能保持影响力”：不得写成“卸任`PRECEDES`机构采用方法”。应把“部分机构维持PEP分类”作为process，把“卸任后仍可能保有影响力”作为input并用`REFERENCES`表达理由/判断依据，同时保留“部分机构、即使、可能”。
- “其他机构考察个人影响力和PEP分类时间”：评估动作应通过`REFERENCES`连接两个判断输入，即使没有独立出口也可以成卡。
- “高风险客户的受益所有权阈值可能降至10%或5%”：高风险适用条件必须进入关系的`condition`或明确的条件节点和边，不能只埋在“适用阈值”节点标签中。
- “持续监控基于预定义标准标记交易，并有助于识别异常模式”：标准约束和带`help`限定的识别结果都应进入图。
- “资产管理人的CDD流程要求了解所有交易参与方”：CDD动作应通过`REFERENCES`连接所需参与方信息。

不得把“识别并核实控制人”再连接到“控制人已识别”这种主动式/被动式同义出口。不得把FIU红旗、案件升级、执法监控和资产冻结仅按教材顺序重新串成总链；只有原文明示的局部触发或结果边才可追加。

## 图规则

新增完整card和card补充使用相同图规则。

节点必填：`node_id, node_category, node_type, label, evidence_unit_ids, evidence_strength`。节点必须由原文明示，`evidence_strength`只能为`explicit`。

允许节点类型：

- entry：`E1_event_signal, E2_object_entry, E3_state_threshold, E4_handoff, E5_time_cycle, E6_change_exception, E7_external_command, E8_decision_finding`
- process：`P1_assessment, P2_execution, P3_branch_routing, P4_collection, P5_coordination, P6_feedback, P7_monitoring, P8_constrained_action, P9_planning, P10_sufficiency`
- exit：`X1_classification, X2_product, X3_state_change, X4_handoff, X5_config_change, X6_termination, X7_continuing_obligation`
- auxiliary：`input, standard`

边必填：`edge_id, edge_type, source, target, evidence_unit_ids, derivation`。允许：`PRECEDES, REFERENCES, PRODUCES, DECIDES, FEEDBACK`。

- `REFERENCES`只能由process指向auxiliary input或standard，不表达先后或产出。
- `PRODUCES`只能由process指向语义独立的exit。
- 单一路径条件使用带`condition`的`PRECEDES`；只有至少两条原文明示路径才使用`DECIDES`。
- `DECIDES`只能由`P3_branch_routing`发出。
- `derivation`只能为`explicit_text`或`llm_inference`。

静态适用对象、材料、因素、阈值、监管要求或风险偏好不得仅因语法顺序建成`entry --PRECEDES--> process`；应作为input/standard，由process通过`REFERENCES`指向。不得把同一谓词的主动式和被动式拆成动作和结果，不得把动作所需的批准、理由、标准或要求/义务写成`PRODUCES`。

`REFERENCES.condition`只限定input/standard适用于process的范围，不表达条件分支。单一路径`PRECEDES.condition`表达逻辑前提，不要求钟表式先后。

必须保留`must, should, may, might, could, often, potentially, help, typically`等情态和限定。`help mitigate`只能写成“有助于缓解”，不能写成必然降低。`must`本身不证明义务是持续、定期、永久或反复的。`X7_continuing_obligation`只用于原文明示新建立的独立持续义务，规范性动作仍保留在process中。

`escalate/escalation`默认写成“升级处理/升级处置”或保留英文，不得翻译为“上报/报告”；只有原文明示`report/notify/file/refer`及对象时才能写成报告或移交。

默认省略`relation_type`。只有完全符合允许语义和端点约束时才填写。

## 补丁合同

顶层必须且只能包含：

```text
section_id
coverage_adjudication
new_candidates
new_cards
card_supplements
```

### coverage_adjudication

对每个`review_target_candidate_ids`恰好输出一条：

```json
{
  "candidate_id": "cand_001",
  "original_decision": "kg_only",
  "final_decision": "kg_only",
  "card_id": null,
  "reason": "<中文>"
}
```

`final_decision`只能是`kg_only`或`p7c_card`。提升时`card_id`必须指向`new_cards`中的新card，或指向被`card_supplements`补充的已有card。多个候选可以共同指向同一card。

### new_candidates

用于记录跨候选关系、首次未登记的关系或已有card的遗漏关系。每项必填：

```json
{
  "candidate_id": "coverage_gap_001",
  "unit_ids": ["<当前section unit_id>"],
  "proposition": "<完整有向命题>",
  "decision": "p7c_card",
  "card_id": "<新增或被补充的card_id>",
  "reason": "<KG不能表达什么>",
  "origin_candidate_ids": ["<相关首次候选ID，可为空>" ]
}
```

新`candidate_id`不得与`original_json.coverage_audit`重复。`unit_ids`可以是多个原候选unit的并集，也可以包含首次未登记的当前section unit。

### new_cards

只放新增完整card。每张必填：`card_id, section_id, card_nature, title, flow_nodes, flow_edges, source_unit_ids, candidate_status, review_notes`。`card_nature`只能为`execution, assessment, risk_indicator, control`；不得输出`local_process`等自造值。`candidate_status`固定为`candidate`。card ID不得与已有card重复。每张新card必须被某条提升裁决或`new_candidates`引用。

### card_supplements

只用于给已有card追加内容：

```json
{
  "patch_id": "coverage_supplement_001",
  "card_id": "<已有card_id>",
  "reason": "<中文说明遗漏>",
  "origin_candidate_ids": ["<相关首次候选ID或本补丁new_candidate ID，可为空>"],
  "add_flow_nodes": [],
  "add_flow_edges": [],
  "add_source_unit_ids": []
}
```

至少新增一个节点或一条边。新增ID不得与该card已有ID重复。新增边可以连接已有节点和新增节点。所有新增节点、边的证据unit必须已经存在于card的`source_unit_ids`，或同时列入`add_source_unit_ids`。每个被补充的card必须由一条提升裁决或`new_candidates`引用。

没有某类修改时输出空数组。即使`review_target_candidate_ids`为空，仍必须扫描完整section、审核已有card，并输出五个顶层字段。

## 输出骨架

```json
{
  "section_id": "<section_id>",
  "coverage_adjudication": [],
  "new_candidates": [],
  "new_cards": [],
  "card_supplements": []
}
```

## 当前section

section_id: `CH03-S07`

section_title: `Examples of predicate crimes > Case example: Mr. Wolfe’s scheme`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "covered_topics": [
    {
      "title_zh": "恐怖融资案例分析：沃尔夫先生的计划",
      "title_en": "Terrorist Financing Case Study: Mr. Wolfe's Scheme",
      "covered_units": [
        {
          "unit_id": "v7u_N000270",
          "unit_type": "case",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000289",
          "unit_type": "fact",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000271",
          "unit_type": "classification",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000288",
          "unit_type": "case",
          "kg_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N000272",
          "unit_type": "case",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000273",
          "unit_type": "case",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000274",
          "unit_type": "fact",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000275",
          "unit_type": "case",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000276",
          "unit_type": "case",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000277",
          "unit_type": "fact",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000278",
          "unit_type": "classification",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000279",
          "unit_type": "fact",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000280",
          "unit_type": "fact",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000281",
          "unit_type": "fact",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000282",
          "unit_type": "fact",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000283",
          "unit_type": "process",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000284",
          "unit_type": "process",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000285",
          "unit_type": "process",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000286",
          "unit_type": "case",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000287",
          "unit_type": "case",
          "kg_role": "illustrates"
        }
      ]
    }
  ],
  "covered_relations": []
}
```

section_text_with_unit_anchors:

```text
[v7u_N000270|270] Mr. Wolfe, a wealthy businessman with radical political views, decided to conduct a terrorist financing scheme to support ISIS operations in Syria, in alignment with his ideology.
ZH: 富商Wolfe先生策划恐怖融资计划支持叙利亚的ISIS行动

[v7u_N000271|271] Unlike traditional money laundering typologies, this type of terrorist financing scheme involved various funnel points and both legitimate and illicit financial streams.
ZH: 该恐怖融资计划与传统洗钱类型不同，涉及多种漏斗点和合法及非法资金流

[v7u_N000272|272] Mr. Wolfe utilized his import-export firms, travel agencies, and retail businesses to generate authentic income.
ZH: Wolfe利用其进出口公司、旅行社和零售业务产生真实收入

[v7u_N000273|273] However, he then concealed portions of these legitimate revenues through deceptive channels, such as privacy-centered cryptocurrencies, to ultimately reach terrorist organizations without detection.
ZH: Wolfe通过隐私加密货币等欺骗性渠道隐藏部分合法收入以资助恐怖组织

[v7u_N000274|274] Simultaneously, Mr. Wolfe’s criminal associates used explicitly illegal activities to raise funds.
ZH: Wolfe的犯罪同伙使用明确的非法活动筹集资金

[v7u_N000275|275] Criminal operations, including cybercrimes such as ransomware attacks, financial institution hacking, and credit card fraud generated substantial illicit proceeds.
ZH: 网络犯罪如勒索软件攻击、金融机构黑客攻击和信用卡欺诈产生大量非法收益

[v7u_N000276|276] They also used traditional criminal enterprises, such as narcotics trafficking and large-scale fraud schemes, and deliberately directed the funds toward terrorist networks.
ZH: 他们还使用传统犯罪企业如毒品贩运和大规模欺诈，并故意将资金导向恐怖网络

[v7u_N000277|277] Once the financiers obtained the funds, facilitators employed sophisticated money laundering methods to obscure their origins and destinations to avoid detection.
ZH: 资金提供者获得资金后，中间人使用复杂的洗钱方法掩盖资金来源和去向

[v7u_N000278|278] The facilitators:
ZH: 列举中间人所采取的具体洗钱手段

[v7u_N000279|279] Committed trade-based money laundering involving false invoicing and fictitious commodity transactions through seemingly legitimate businesses.
ZH: 通过看似合法的企业进行虚假发票和虚构商品交易的贸易洗钱

[v7u_N000280|280] Layered funds through unregulated fintech platforms, cryptocurrencies, and peer-to-peer payment networks, using digital wallets to complicate traceability.
ZH: 通过不受监管的金融科技平台、加密货币和点对点支付网络进行资金分层

[v7u_N000281|281] Smuggled physical bulk cash, moving large amounts of money across borders outside conventional banking oversight.
ZH: 走私实物现金，绕过传统银行监管跨境转移大额资金

[v7u_N000282|282] Used hawala brokers to facilitate cross-border transfers, leveraging informal networks to obscure financial trails.
ZH: 利用哈瓦拉经纪人进行跨境转账，通过非正规网络掩盖资金踪迹

[v7u_N000283|283] Financial institutions first detected the illicit activity through transaction monitoring systems, which flagged structured deposits, rapid interjurisdictional layering, and anomalous fund movements linked to known terror-affiliated wallets.
ZH: 金融机构通过交易监控系统发现可疑活动，包括结构化存款和异常资金流动

[v7u_N000284|284] Blockchain analytics firms provided forensic intelligence, mapping illicit cryptoasset flows through darknet marketplaces and high-risk exchanges.
ZH: 区块链分析公司提供取证情报，追踪暗网市场和风险交易所的非法加密资产流动

[v7u_N000285|285] FIUs synthesized bank SARs with cross-border financial activity, triggering red flags within international regulatory networks.
ZH: 金融情报机构综合银行可疑交易报告与跨境金融活动，触发国际监管网络红旗信号信号

[v7u_N000286|286] As FIUs escalated the case, law enforcement agencies, including Europol, Interpol, and national counterterrorism task forces, conducted targeted surveillance on Mr. Wolfe and his criminal associates. These individuals, designated as subjects of interest, were monitored to trace cash smugglers and hawala networks.
ZH: 执法机构对Wolfe及其同伙进行针对性监控，追踪现金走私者和哈瓦拉网络

[v7u_N000287|287] They conducted coordinated asset freezes to disrupt financial channels, resulting in the seizure of digital wallets and the dismantling of Mr. Wolfe’s companies used to finance terrorism.
ZH: 协调资产冻结以切断金融渠道，查封数字钱包并瓦解Wolfe用于资助恐怖主义的公司

[v7u_N000288|288] Mr. Wolfe and his associates all received lengthy prison sentences and heavy fines.
ZH: Wolfe及其同伙被判处长期监禁和巨额罚款

[v7u_N000289|289] Intelligenceled investigations, real-time interagency collaboration, and advanced analytics all played a key role in countering this terrorist financing network.
ZH: 情报主导调查、实时机构间协作和高级分析在打击恐怖融资中发挥关键作用
```

allowed_unit_ids:

```json
[
  "v7u_N000270",
  "v7u_N000271",
  "v7u_N000272",
  "v7u_N000273",
  "v7u_N000274",
  "v7u_N000275",
  "v7u_N000276",
  "v7u_N000277",
  "v7u_N000278",
  "v7u_N000279",
  "v7u_N000280",
  "v7u_N000281",
  "v7u_N000282",
  "v7u_N000283",
  "v7u_N000284",
  "v7u_N000285",
  "v7u_N000286",
  "v7u_N000287",
  "v7u_N000288",
  "v7u_N000289"
]
```

original_json:

```json
{
  "section_id": "CH03-S07",
  "section_title": "Examples of predicate crimes > Case example: Mr. Wolfe’s scheme",
  "coverage_audit": [
    {
      "candidate_id": "cand_001",
      "unit_ids": [
        "v7u_N000277"
      ],
      "proposition": "一旦资金提供者获得资金，中间人使用复杂洗钱方法掩盖来源和去向",
      "decision": "p7c_card",
      "card_id": "p7card_CH03-S07_001",
      "reason": "条件触发中间人动作，形成“一旦…就…”的有向链，基础KG无法表达该条件触发关系，可帮助判断中间人介入时机"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N000283"
      ],
      "proposition": "金融机构交易监控系统检测并标记特定异常交易活动（结构化存款、快速跨境分层、与已知恐怖钱包关联的异常资金流动）",
      "decision": "p7c_card",
      "card_id": "p7card_CH03-S07_002",
      "reason": "具体输入模式驱动检测动作并产生标记结果的有向结构，基础KG无法表达该依据与标记之间的链条，可帮助确认系统标记的活动类型"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N000284"
      ],
      "proposition": "区块链分析公司追踪暗网市场和高风险交易所的非法加密资产流，提供取证情报",
      "decision": "p7c_card",
      "card_id": "p7card_CH03-S07_003",
      "reason": "分析输入（特定加密资产流）与产出（取证情报）的有向关系，基础KG不能表达该分析链，可帮助回答分析对象或产出问题"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N000285"
      ],
      "proposition": "FIUs综合银行SARs和跨境金融活动，触发红旗信号",
      "decision": "p7c_card",
      "card_id": "p7card_CH03-S07_004",
      "reason": "FIUs分析动作基于明确输入产生红旗发现的有向链，基础KG不能表达该触发关系，可帮助判断FIU的分析依据与信号类型"
    },
    {
      "candidate_id": "cand_005",
      "unit_ids": [
        "v7u_N000286"
      ],
      "proposition": "FIUs升级案件后，执法机构开展针对性监控追踪现金走私者和哈瓦拉网络",
      "decision": "p7c_card",
      "card_id": "p7card_CH03-S07_005",
      "reason": "升级动作引发监控动作的明确先后触发链，基础KG无法表达该顺序关系，可帮助回答案件升级后的行动主体及内容"
    },
    {
      "candidate_id": "cand_006",
      "unit_ids": [
        "v7u_N000287"
      ],
      "proposition": "执法机构协调资产冻结，导致查封数字钱包和瓦解用于资助恐怖主义的公司",
      "decision": "p7c_card",
      "card_id": "p7card_CH03-S07_006",
      "reason": "资产冻结动作产生具体独立结果的有向因果链，基础KG不能表达该产出关系，可帮助确认资产冻结的直接后果"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH03-S07_001",
      "section_id": "CH03-S07",
      "card_nature": "execution",
      "title": "资金获得后中间人采用复杂洗钱方法",
      "flow_nodes": [
        {
          "node_id": "node_1",
          "node_category": "entry",
          "node_type": "E1_event_signal",
          "label": "资金提供者获得资金",
          "evidence_unit_ids": [
            "v7u_N000277"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "node_2",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "中间人采用复杂洗钱方法掩盖来源和去向",
          "evidence_unit_ids": [
            "v7u_N000277"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e1",
          "edge_type": "PRECEDES",
          "source": "node_1",
          "target": "node_2",
          "evidence_unit_ids": [
            "v7u_N000277"
          ],
          "derivation": "explicit_text",
          "condition": "一旦资金提供者获得资金"
        }
      ],
      "source_unit_ids": [
        "v7u_N000277"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：资金提供者获得资金（事件）触发中间人采用复杂洗钱方法（动作）；KG不足：基础KG可保存该事实但无法表达“一旦…就…”的条件导向关系；选项判断：可帮助确认或排除关于中间人介入时机的选项；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH03-S07_002",
      "section_id": "CH03-S07",
      "card_nature": "execution",
      "title": "金融机构交易监控系统检测并标记可疑活动",
      "flow_nodes": [
        {
          "node_id": "node_1",
          "node_category": "auxiliary",
          "node_type": "input",
          "label": "结构化存款、快速跨境分层及与已知恐怖钱包关联的异常资金流动",
          "evidence_unit_ids": [
            "v7u_N000283"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "node_2",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "金融机构交易监控系统检测并标记可疑活动",
          "evidence_unit_ids": [
            "v7u_N000283"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "node_3",
          "node_category": "exit",
          "node_type": "X1_classification",
          "label": "标记为可疑活动",
          "evidence_unit_ids": [
            "v7u_N000283"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e1",
          "edge_type": "REFERENCES",
          "source": "node_2",
          "target": "node_1",
          "evidence_unit_ids": [
            "v7u_N000283"
          ],
          "derivation": "explicit_text"
        },
        {
          "edge_id": "e2",
          "edge_type": "PRODUCES",
          "source": "node_2",
          "target": "node_3",
          "evidence_unit_ids": [
            "v7u_N000283"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N000283"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：金融机构交易监控系统将特定异常交易模式作为依据进行检测，并产生标记结果；KG不足：基础KG可保存“系统检测”事实，但不能表达检测所依据的具体输入模式和标记结果的有向关系；选项判断：可确认系统标记了哪些类型的活动，或系统基于何种输入产生标记；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH03-S07_003",
      "section_id": "CH03-S07",
      "card_nature": "assessment",
      "title": "区块链分析公司提供取证情报追踪非法加密资产流",
      "flow_nodes": [
        {
          "node_id": "node_1",
          "node_category": "auxiliary",
          "node_type": "input",
          "label": "暗网市场和高风险交易所的非法加密资产流",
          "evidence_unit_ids": [
            "v7u_N000284"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "node_2",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "区块链分析公司追踪并映射非法加密资产流",
          "evidence_unit_ids": [
            "v7u_N000284"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "node_3",
          "node_category": "exit",
          "node_type": "X2_product",
          "label": "取证情报",
          "evidence_unit_ids": [
            "v7u_N000284"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e1",
          "edge_type": "REFERENCES",
          "source": "node_2",
          "target": "node_1",
          "evidence_unit_ids": [
            "v7u_N000284"
          ],
          "derivation": "explicit_text"
        },
        {
          "edge_id": "e2",
          "edge_type": "PRODUCES",
          "source": "node_2",
          "target": "node_3",
          "evidence_unit_ids": [
            "v7u_N000284"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N000284"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：区块链分析公司基于暗网市场和高风险交易所的加密资产流进行追踪分析，产出取证情报；KG不足：基础KG可保存该事实但无法表达分析输入与产出的有向关系；选项判断：可帮助回答关于区块链分析公司作用或其分析对象的问题；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH03-S07_004",
      "section_id": "CH03-S07",
      "card_nature": "assessment",
      "title": "FIUs综合分析银行SARs和跨境活动触发红旗",
      "flow_nodes": [
        {
          "node_id": "node_1",
          "node_category": "auxiliary",
          "node_type": "input",
          "label": "银行可疑交易报告（SARs）与跨境金融活动",
          "evidence_unit_ids": [
            "v7u_N000285"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "node_2",
          "node_category": "process",
          "node_type": "P1_assessment",
          "label": "FIUs综合分析银行SARs与跨境金融活动",
          "evidence_unit_ids": [
            "v7u_N000285"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "node_3",
          "node_category": "exit",
          "node_type": "X1_classification",
          "label": "触发国际监管网络红旗信号",
          "evidence_unit_ids": [
            "v7u_N000285"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e1",
          "edge_type": "REFERENCES",
          "source": "node_2",
          "target": "node_1",
          "evidence_unit_ids": [
            "v7u_N000285"
          ],
          "derivation": "explicit_text"
        },
        {
          "edge_id": "e2",
          "edge_type": "PRODUCES",
          "source": "node_2",
          "target": "node_3",
          "evidence_unit_ids": [
            "v7u_N000285"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N000285"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：FIUs将银行SARs和跨境活动作为分析输入，产生红旗发现；KG不足：基础KG可保存分析事实，但不能表达输入与触发红旗的有向链条；选项判断：可确认FIU的分析依据及产生的信号类型；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH03-S07_005",
      "section_id": "CH03-S07",
      "card_nature": "execution",
      "title": "FIU升级案件后执法机构开展针对性监控",
      "flow_nodes": [
        {
          "node_id": "node_1",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "FIUs升级处置案件",
          "evidence_unit_ids": [
            "v7u_N000286"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "node_2",
          "node_category": "process",
          "node_type": "P7_monitoring",
          "label": "执法机构进行针对性监控以追踪现金走私者和哈瓦拉网络",
          "evidence_unit_ids": [
            "v7u_N000286"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e1",
          "edge_type": "PRECEDES",
          "source": "node_1",
          "target": "node_2",
          "evidence_unit_ids": [
            "v7u_N000286"
          ],
          "derivation": "explicit_text",
          "condition": "As FIUs escalated the case"
        }
      ],
      "source_unit_ids": [
        "v7u_N000286"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：FIUs升级案件的动作触发执法机构后续的监控行动；KG不足：基础KG可分别保存升级和监控事实，但无法表达升级触发监控的有向顺序；选项判断：可帮助回答关于案件升级后谁采取了什么行动，或执法机构行动的前提条件；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH03-S07_006",
      "section_id": "CH03-S07",
      "card_nature": "execution",
      "title": "执法机构协调资产冻结导致查封和瓦解",
      "flow_nodes": [
        {
          "node_id": "node_1",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "执法机构协调资产冻结",
          "evidence_unit_ids": [
            "v7u_N000287"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "node_2",
          "node_category": "exit",
          "node_type": "X3_state_change",
          "label": "查封数字钱包",
          "evidence_unit_ids": [
            "v7u_N000287"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "node_3",
          "node_category": "exit",
          "node_type": "X6_termination",
          "label": "瓦解用于资助恐怖主义的公司",
          "evidence_unit_ids": [
            "v7u_N000287"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e1",
          "edge_type": "PRODUCES",
          "source": "node_1",
          "target": "node_2",
          "evidence_unit_ids": [
            "v7u_N000287"
          ],
          "derivation": "explicit_text"
        },
        {
          "edge_id": "e2",
          "edge_type": "PRODUCES",
          "source": "node_1",
          "target": "node_3",
          "evidence_unit_ids": [
            "v7u_N000287"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N000287"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：执法机构的资产冻结动作直接导致查封数字钱包和瓦解公司的结果；KG不足：基础KG可保存冻结、查封和瓦解等事实，但不能表达冻结产生这些结果的有向因果链；选项判断：可帮助确认资产冻结的具体直接后果；LLM推理：无。"
    }
  ],
  "skip_reason": null
}
```

review_target_candidate_ids:

```json
[]
```
