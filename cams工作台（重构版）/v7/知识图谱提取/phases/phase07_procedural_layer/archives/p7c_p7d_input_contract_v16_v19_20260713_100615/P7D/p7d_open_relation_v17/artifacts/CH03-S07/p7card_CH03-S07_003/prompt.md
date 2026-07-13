# P7D Flow Edge Evidence Review Prompt v1

## 角色与边界

你是P7D独立边级证据审核器。P7C已经生成候选card；你的任务是逐条审核card中的现有`flow_edge`，不是重新抽取card。

不得新增、删除、改写、拆分或连接card、node或edge。不得修改P7C正本。不得读取或假设具体题目、选项、参考答案或其他section内容。只输出严格JSON，不输出Markdown或解释。

`section_text_with_unit_anchors`和`section_units`是唯一事实证据。只能引用`allowed_unit_ids`中的unit_id。P7C card、label、source_quote、derivation以及旧版evidence_strength都只是待审核声明，不能反过来充当证据。

## 逐边审核问题

对每条现有edge分别检查：

1. `source_node_support`：source节点表达的主体、对象、动作、状态或结论是否有当前section依据。
2. `target_node_support`：target节点是否有当前section依据。
3. `direction_support`：原文是否支持source到target的方向；反向是否同样可能。
4. `condition_support`：edge的condition是否被原文明示支持。没有condition时填`not_applicable`。
5. `qualifier_support`：must、should、may、might、could、often、only、not、unless、potentially等限定是否被保留，是否被强化或弱化。没有相关限定时可以填`not_applicable`。
6. `parallel_or_correlation_check`：是否把并列来源、共同结果、相关关系、教材叙述顺序或一般主题关系错误写成`PRECEDES`、`PRODUCES`、`DECIDES`或`FEEDBACK`。

每项`status`只能是：`supported, pending, unsupported, not_applicable`。每项必须用中文填写`reason`。

## edge_type审核口径

- `PRECEDES`：只有原文明示顺序，或交换方向会违反唯一必要功能依赖时才成立。共同出现和教材顺序不成立。
- `REFERENCES`：只表达process对非时序输入、线索、标准或判断维度的参照，不表达先后或产出。
- `PRODUCES`：process必须产生target结果；揭示既存状态不等于产生该状态。
- `DECIDES`：必须存在真实条件分流，condition有原文证据；单一条件应对不自动构成分支。
- `FEEDBACK`：结果或事件必须触发复核、补充、更新、调优、监控或再次处理。

相邻句中的冻结、查封、调查、起诉、定罪、监禁和罚款不自动形成单链。多个线索、标准、情报来源或共同结果不因排列顺序形成先后边。

## derivation与建议

`derivation`只描述这条边如何由证据得到，不能用来代替审核结论：

- `explicit_text`：原文明示关系及方向。
- `llm_inference`：两端均有证据，但关系或方向依赖必要功能推理。
- `unsupported`：至少一端、关系、方向或条件缺少依据。

`llm_recommendation`只能是：

- `accepted`：所有必要检查均有充分支持。
- `pending`：存在歧义，或关系依赖必要功能推理，需要人工判断。
- `rejected`：至少一个关键检查明确不成立。

不要为了保留card而接受边。也不要因为边来自P7C或标为`explicit`就默认接受。

## 输出合同

必须覆盖输入card中的每一条edge，edge_id不得遗漏、增加或重复。顺序与输入保持一致。

```json
{
  "section_id": "CH03-S07",
  "card_id": "<card_id>",
  "edge_reviews": [
    {
      "edge_id": "<existing edge_id>",
      "derivation": "explicit_text",
      "llm_recommendation": "accepted",
      "checks": {
        "source_node_support": {"status": "supported", "reason": "<中文>"},
        "target_node_support": {"status": "supported", "reason": "<中文>"},
        "direction_support": {"status": "supported", "reason": "<中文>"},
        "condition_support": {"status": "not_applicable", "reason": "该边没有condition。"},
        "qualifier_support": {"status": "supported", "reason": "<中文>"},
        "parallel_or_correlation_check": {"status": "supported", "reason": "<中文>"}
      },
      "evidence_unit_ids": ["<allowed unit id>"],
      "source_quotes": ["<当前section原文短引>"],
      "reason": "<中文总判断>"
    }
  ]
}
```

## 当前section与card

section_id: `CH03-S07`
section_title: `Examples of predicate crimes > Case example: Mr. Wolfe’s scheme`

section_text_with_unit_anchors:
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

section_units:
[
  {
    "en_quote": "Mr. Wolfe, a wealthy businessman with radical political views, decided to conduct a terrorist financing scheme to support ISIS operations in Syria, in alignment with his ideology.",
    "knowledge_zh": "富商Wolfe先生策划恐怖融资计划支持叙利亚的ISIS行动",
    "pdf_page": 43,
    "printed_page": "38",
    "type": "case",
    "unit_id": "v7u_N000270",
    "unit_order": 270
  },
  {
    "en_quote": "Unlike traditional money laundering typologies, this type of terrorist financing scheme involved various funnel points and both legitimate and illicit financial streams.",
    "knowledge_zh": "该恐怖融资计划与传统洗钱类型不同，涉及多种漏斗点和合法及非法资金流",
    "pdf_page": 43,
    "printed_page": "38",
    "type": "classification",
    "unit_id": "v7u_N000271",
    "unit_order": 271
  },
  {
    "en_quote": "Mr. Wolfe utilized his import-export firms, travel agencies, and retail businesses to generate authentic income.",
    "knowledge_zh": "Wolfe利用其进出口公司、旅行社和零售业务产生真实收入",
    "pdf_page": 43,
    "printed_page": "38",
    "type": "case",
    "unit_id": "v7u_N000272",
    "unit_order": 272
  },
  {
    "en_quote": "However, he then concealed portions of these legitimate revenues through deceptive channels, such as privacy-centered cryptocurrencies, to ultimately reach terrorist organizations without detection.",
    "knowledge_zh": "Wolfe通过隐私加密货币等欺骗性渠道隐藏部分合法收入以资助恐怖组织",
    "pdf_page": 43,
    "printed_page": "38",
    "type": "case",
    "unit_id": "v7u_N000273",
    "unit_order": 273
  },
  {
    "en_quote": "Simultaneously, Mr. Wolfe’s criminal associates used explicitly illegal activities to raise funds.",
    "knowledge_zh": "Wolfe的犯罪同伙使用明确的非法活动筹集资金",
    "pdf_page": 43,
    "printed_page": "38",
    "type": "fact",
    "unit_id": "v7u_N000274",
    "unit_order": 274
  },
  {
    "en_quote": "Criminal operations, including cybercrimes such as ransomware attacks, financial institution hacking, and credit card fraud generated substantial illicit proceeds.",
    "knowledge_zh": "网络犯罪如勒索软件攻击、金融机构黑客攻击和信用卡欺诈产生大量非法收益",
    "pdf_page": 43,
    "printed_page": "38",
    "type": "case",
    "unit_id": "v7u_N000275",
    "unit_order": 275
  },
  {
    "en_quote": "They also used traditional criminal enterprises, such as narcotics trafficking and large-scale fraud schemes, and deliberately directed the funds toward terrorist networks.",
    "knowledge_zh": "他们还使用传统犯罪企业如毒品贩运和大规模欺诈，并故意将资金导向恐怖网络",
    "pdf_page": 43,
    "printed_page": "38",
    "type": "case",
    "unit_id": "v7u_N000276",
    "unit_order": 276
  },
  {
    "en_quote": "Once the financiers obtained the funds, facilitators employed sophisticated money laundering methods to obscure their origins and destinations to avoid detection.",
    "knowledge_zh": "资金提供者获得资金后，中间人使用复杂的洗钱方法掩盖资金来源和去向",
    "pdf_page": 43,
    "printed_page": "38",
    "type": "fact",
    "unit_id": "v7u_N000277",
    "unit_order": 277
  },
  {
    "en_quote": "The facilitators:",
    "knowledge_zh": "列举中间人所采取的具体洗钱手段",
    "pdf_page": 43,
    "printed_page": "38",
    "type": "classification",
    "unit_id": "v7u_N000278",
    "unit_order": 278
  },
  {
    "en_quote": "Committed trade-based money laundering involving false invoicing and fictitious commodity transactions through seemingly legitimate businesses.",
    "knowledge_zh": "通过看似合法的企业进行虚假发票和虚构商品交易的贸易洗钱",
    "pdf_page": 44,
    "printed_page": "39",
    "type": "fact",
    "unit_id": "v7u_N000279",
    "unit_order": 279
  },
  {
    "en_quote": "Layered funds through unregulated fintech platforms, cryptocurrencies, and peer-to-peer payment networks, using digital wallets to complicate traceability.",
    "knowledge_zh": "通过不受监管的金融科技平台、加密货币和点对点支付网络进行资金分层",
    "pdf_page": 44,
    "printed_page": "39",
    "type": "fact",
    "unit_id": "v7u_N000280",
    "unit_order": 280
  },
  {
    "en_quote": "Smuggled physical bulk cash, moving large amounts of money across borders outside conventional banking oversight.",
    "knowledge_zh": "走私实物现金，绕过传统银行监管跨境转移大额资金",
    "pdf_page": 44,
    "printed_page": "39",
    "type": "fact",
    "unit_id": "v7u_N000281",
    "unit_order": 281
  },
  {
    "en_quote": "Used hawala brokers to facilitate cross-border transfers, leveraging informal networks to obscure financial trails.",
    "knowledge_zh": "利用哈瓦拉经纪人进行跨境转账，通过非正规网络掩盖资金踪迹",
    "pdf_page": 44,
    "printed_page": "39",
    "type": "fact",
    "unit_id": "v7u_N000282",
    "unit_order": 282
  },
  {
    "en_quote": "Financial institutions first detected the illicit activity through transaction monitoring systems, which flagged structured deposits, rapid interjurisdictional layering, and anomalous fund movements linked to known terror-affiliated wallets.",
    "knowledge_zh": "金融机构通过交易监控系统发现可疑活动，包括结构化存款和异常资金流动",
    "pdf_page": 44,
    "printed_page": "39",
    "type": "process",
    "unit_id": "v7u_N000283",
    "unit_order": 283
  },
  {
    "en_quote": "Blockchain analytics firms provided forensic intelligence, mapping illicit cryptoasset flows through darknet marketplaces and high-risk exchanges.",
    "knowledge_zh": "区块链分析公司提供取证情报，追踪暗网市场和风险交易所的非法加密资产流动",
    "pdf_page": 44,
    "printed_page": "39",
    "type": "process",
    "unit_id": "v7u_N000284",
    "unit_order": 284
  },
  {
    "en_quote": "FIUs synthesized bank SARs with cross-border financial activity, triggering red flags within international regulatory networks.",
    "knowledge_zh": "金融情报机构综合银行可疑交易报告与跨境金融活动，触发国际监管网络红旗信号信号",
    "pdf_page": 44,
    "printed_page": "39",
    "type": "process",
    "unit_id": "v7u_N000285",
    "unit_order": 285
  },
  {
    "en_quote": "As FIUs escalated the case, law enforcement agencies, including Europol, Interpol, and national counterterrorism task forces, conducted targeted surveillance on Mr. Wolfe and his criminal associates. These individuals, designated as subjects of interest, were monitored to trace cash smugglers and hawala networks.",
    "knowledge_zh": "执法机构对Wolfe及其同伙进行针对性监控，追踪现金走私者和哈瓦拉网络",
    "pdf_page": 44,
    "printed_page": "39",
    "type": "case",
    "unit_id": "v7u_N000286",
    "unit_order": 286
  },
  {
    "en_quote": "They conducted coordinated asset freezes to disrupt financial channels, resulting in the seizure of digital wallets and the dismantling of Mr. Wolfe’s companies used to finance terrorism.",
    "knowledge_zh": "协调资产冻结以切断金融渠道，查封数字钱包并瓦解Wolfe用于资助恐怖主义的公司",
    "pdf_page": 44,
    "printed_page": "39",
    "type": "case",
    "unit_id": "v7u_N000287",
    "unit_order": 287
  },
  {
    "en_quote": "Mr. Wolfe and his associates all received lengthy prison sentences and heavy fines.",
    "knowledge_zh": "Wolfe及其同伙被判处长期监禁和巨额罚款",
    "pdf_page": 44,
    "printed_page": "39",
    "type": "case",
    "unit_id": "v7u_N000288",
    "unit_order": 288
  },
  {
    "en_quote": "Intelligenceled investigations, real-time interagency collaboration, and advanced analytics all played a key role in countering this terrorist financing network.",
    "knowledge_zh": "情报主导调查、实时机构间协作和高级分析在打击恐怖融资中发挥关键作用",
    "pdf_page": 44,
    "printed_page": "39",
    "type": "fact",
    "unit_id": "v7u_N000289",
    "unit_order": 289
  }
]

allowed_unit_ids:
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

p7c_card_under_review:
{
  "card_id": "p7card_CH03-S07_003",
  "section_id": "CH03-S07",
  "card_nature": "execution",
  "title": "案件升级触发执法监控",
  "flow_nodes": [
    {
      "node_id": "E1",
      "node_category": "entry",
      "node_type": "E4_handoff",
      "label": "FIUs 将案件升级处理",
      "evidence_unit_ids": [
        "v7u_N000286"
      ],
      "evidence_strength": "explicit"
    },
    {
      "node_id": "P1",
      "node_category": "process",
      "node_type": "P2_execution",
      "label": "执法机构 (包括欧洲刑警组织、国际刑警组织和国家反恐特遣队): 对 Mr. Wolfe 及其犯罪同伙进行定向监控，以追踪现金走私者和哈瓦拉网络",
      "evidence_unit_ids": [
        "v7u_N000286"
      ],
      "evidence_strength": "explicit"
    }
  ],
  "flow_edges": [
    {
      "edge_id": "E1",
      "edge_type": "PRECEDES",
      "source": "E1",
      "target": "P1",
      "evidence_unit_ids": [
        "v7u_N000286"
      ],
      "derivation": "explicit_text"
    }
  ],
  "source_unit_ids": [
    "v7u_N000286"
  ],
  "candidate_status": "candidate",
  "review_notes": "增量命题：FIU升级案件 → 执法机构进行定向监控。KG不足：基础KG可能单独描述FIU升级和执法监控，但无法表达升级事件直接触发监控行动的定向交接关系。选项判断：可确认升级行为是执法监控的前置步骤，排除其他触发路径。LLM推理：无。"
}
