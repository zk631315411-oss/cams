# P7C Section-Local Coverage Adjudication Prompt v1

## 角色

你是P7C覆盖裁决器。首次抽取器已经发现候选命题并生成通过结构校验的card；你的唯一任务是复核`coverage_audit`中原决定为`kg_only`的候选，判断它们是否因KG/P7C边界理解错误而漏成卡。

只输出完整严格JSON，不输出Markdown或解释。`flow_nodes + flow_edges`仍是知识正本；`coverage_adjudication`和`coverage_audit`只是诊断元数据。

## P7C目的

P7C在不重复基础KG已经能够充分表达的定义、分类、事实、普通案例、孤立风险指标和一般知识关系的前提下，从单个section中增量提取对CAMS题目选项判断有用的局部程序性或判断性有向结构：业务情境、事件、线索、输入或标准，如何关联到特定主体的识别、评估、决策或应对，并在相应条件下产生结论、义务、控制结果、分支或后续行动。

P7C不读取题目或参考答案，不处理跨section桥接。当前section原文是唯一事实证据；基础KG摘要只能用于去重，不能补造事实。

## 裁决对象

只复核`original_json.coverage_audit`中`decision=kg_only`的候选。不得新增候选，不得删除候选，不得修改候选的`candidate_id`、`unit_ids`或`proposition`。

原本为`p7c_card`的候选及其`card_id`必须保持不变。`original_json.cards`中的每张既有card必须完整保留，不得删除、改写、拆分、合并或重新编号。

## 裁决标准

将原`kg_only`候选提升为`p7c_card`，必须同时满足：

1. 当前section证据支持关系两端、特定主体、方向以及条件（如有）。
2. 候选内部存在“情境/事件/线索/输入/标准 → 主体动作或判断 → 结果/义务/控制效果”的局部结构。
3. 该方向结构能够帮助判断选项的顺序、条件、主体职责、义务、应对、因果或适用范围。
4. 基础KG只能保存整句话或各知识点，不能充分表达句内的主体、方向、条件及动作结果关系。

结构复杂度不是门槛。一个unit、一条路径、没有分支或反馈，都不能作为`kg_only`理由。entry是图中的关系起点，不要求是时间事件；业务对象、线索输入、风险阈值、监管要求或政策基准都可以承担有证据的入口角色。

以下通常应提升：

- 金融机构监控系统根据异常活动进行标记并形成识别结论。
- FIU综合SAR和跨境活动并形成红旗发现。
- 风险阈值和直接/间接持股被机构用于UBO判断并形成分类结论。
- 外部监管要求或上位标准触发机构调整控制、政策或职责。
- 明确条件触发拒绝、批准、升级、报告、监控、复核或持续义务。

以下保持`kg_only`：

- 纯定义、分类、阈值数值或组成列表，没有主体应用和结果关系。
- 普通犯罪方法、犯罪分子操作步骤或普通案例机制，没有机构、FIU、监管或执法主体的识别、判断或应对。
- 孤立红旗、后果、历史事实或抽象风险缓解目的。
- 只有主题相关性，或者必须补造主体、条件、方向、动作或结果才能闭合。

## 修改规则

对每个原`kg_only`候选，在顶层`coverage_adjudication`中新增一条记录：

```json
{
  "candidate_id": "cand_001",
  "original_decision": "kg_only",
  "final_decision": "kg_only",
  "reason": "<中文裁决理由>"
}
```

`final_decision`只能为`kg_only`或`p7c_card`。

保持`kg_only`时：原`coverage_audit`记录的`decision`仍为`kg_only`，`card_id`仍为`null`，可以更新中文`reason`。

提升为`p7c_card`时：

- 将原`coverage_audit`记录的`decision`改为`p7c_card`；
- 填入新增card的`card_id`；
- 更新中文`reason`，说明基础KG不能表达的方向结构；
- 在`cards`末尾追加一张有证据的局部card；
- 不得修改其他候选或已有card。

## 新增card规则

新增card必填：`card_id, section_id, card_nature, title, flow_nodes, flow_edges, source_unit_ids, review_status, review_notes`。

`card_nature`只能为：`execution, assessment, risk_indicator, control`。

每张新增card至少包含一个entry、process和exit，并存在entry经过process到exit的有向路径。

节点必填：`node_id, node_category, node_type, label, evidence_unit_ids, evidence_strength`。节点必须由原文明示，`evidence_strength`只能为`explicit`。

允许节点类型：

- entry：`E1_event_signal, E2_object_entry, E3_state_threshold, E4_handoff, E5_time_cycle, E6_change_exception, E7_external_command, E8_decision_finding`
- process：`P1_assessment, P2_execution, P3_branch_routing, P4_collection, P5_coordination, P6_feedback, P7_monitoring, P8_constrained_action, P9_planning, P10_sufficiency`
- exit：`X1_classification, X2_product, X3_state_change, X4_handoff, X5_config_change, X6_termination, X7_continuing_obligation`
- auxiliary：`input, standard`

边必填：`edge_id, edge_type, source, target, evidence_unit_ids, evidence_strength`。允许：`PRECEDES, REFERENCES, PRODUCES, DECIDES, FEEDBACK`。

- `REFERENCES`只能由process指向auxiliary input或standard。
- `PRODUCES`只能由process指向exit。
- `DECIDES`只能由`P3_branch_routing`发出，至少两条分支，每条都有原文明示的`condition`。
- `functional_dependency`只允许用于边，且card必须为`needs_review`并在`review_notes`的“LLM推理”中说明。

默认省略`relation_type`。只有完全符合允许语义和端点约束时才填写，不得创造新类型。

必须保留`must, should, may, might, could, often, potentially, help`等情态强度。不得将“有助于缓解”强化为“风险已经消除”。

新增card只能引用对应候选`unit_ids`及同一局部命题必要的当前section unit。不得借裁决轮扩展到无关主题。

## 输出约束

返回完整顶层对象：

```text
section_id
section_title
coverage_adjudication
coverage_audit
cards
skip_reason
```

如果最终存在card，`skip_reason`必须为`null`。如果仍无card，保留合适的中文`skip_reason`。

## 当前section

section_id: `CH03-S07`

section_title: `Examples of predicate crimes > Case example: Mr. Wolfe’s scheme`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "core_points": [
    {
      "core_point_id": "cp_CH03_S07_001",
      "title_zh": "恐怖融资案例分析：沃尔夫先生的计划",
      "title_en": "Terrorist Financing Case Study: Mr. Wolfe's Scheme",
      "anchor_unit_ids": [
        "v7u_N000270",
        "v7u_N000289"
      ],
      "key_unit_ids": [
        "v7u_N000270",
        "v7u_N000289",
        "v7u_N000271",
        "v7u_N000288",
        "v7u_N000272"
      ],
      "support_unit_ids": [
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
        "v7u_N000288"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000270",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000289",
          "unit_type": "fact",
          "cp_unit_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000271",
          "unit_type": "classification",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000288",
          "unit_type": "case",
          "cp_unit_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N000272",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000273",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000274",
          "unit_type": "fact",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000275",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000276",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000277",
          "unit_type": "fact",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000278",
          "unit_type": "classification",
          "cp_unit_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000279",
          "unit_type": "fact",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000280",
          "unit_type": "fact",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000281",
          "unit_type": "fact",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000282",
          "unit_type": "fact",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000283",
          "unit_type": "process",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000284",
          "unit_type": "process",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000285",
          "unit_type": "process",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000286",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000287",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        }
      ]
    }
  ],
  "same_section_core_point_edges": []
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
        "v7u_N000283"
      ],
      "proposition": "金融机构通过交易监控系统标记结构化存款、快速分层和与已知恐怖钱包关联的异常资金流动，从而检测到非法活动",
      "decision": "kg_only",
      "card_id": null,
      "reason": "基础KG可存储该检测事实，缺乏明确的程序性入口和判断条件，仅描述了监控系统标记的行为。"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N000284"
      ],
      "proposition": "区块链分析公司提供取证情报，映射非法加密资产流动",
      "decision": "kg_only",
      "card_id": null,
      "reason": "基础KG可存储该支持情报活动，无明确触发和程序性结构。"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N000285"
      ],
      "proposition": "FIU综合银行SAR与跨境金融活动，触发国际监管网络的红旗信号",
      "decision": "kg_only",
      "card_id": null,
      "reason": "基础KG可表达FIU的分析动作及其结果，缺乏明确的触发入口形成完整有向链。"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N000286",
        "v7u_N000287"
      ],
      "proposition": "当FIU升级案件时，执法机构执行定向监控以追踪走私网络，然后协调资产冻结，查封数字钱包并瓦解相关公司",
      "decision": "p7c_card",
      "card_id": "p7card_CH03-S07_001",
      "reason": "存在明确的升级触发、监控和冻结的动作序列及具体结果，形成程序性有向结构，超出基础KG的一般描述。"
    },
    {
      "candidate_id": "cand_005",
      "unit_ids": [
        "v7u_N000288"
      ],
      "proposition": "Wolfe及其同伙被判处长期监禁和巨额罚款",
      "decision": "kg_only",
      "card_id": null,
      "reason": "基础KG可存储案例司法结果，无增量有向结构。"
    },
    {
      "candidate_id": "cand_006",
      "unit_ids": [
        "v7u_N000289"
      ],
      "proposition": "情报主导调查、实时机构间协作和高级分析在打击该恐怖融资网络中发挥关键作用",
      "decision": "kg_only",
      "card_id": null,
      "reason": "基础KG可表达总结性评价，无具体程序性步骤。"
    },
    {
      "candidate_id": "cand_007",
      "unit_ids": [
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
        "v7u_N000282"
      ],
      "proposition": "犯罪分子生成、转移和隐藏资金的方法描述",
      "decision": "kg_only",
      "card_id": null,
      "reason": "基础KG可存储这些案例具体犯罪手法，无内部程序性有向结构。"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH03-S07_001",
      "section_id": "CH03-S07",
      "card_nature": "control",
      "title": "FIU升级触发执法机构监控和资产冻结",
      "flow_nodes": [
        {
          "node_id": "n1",
          "node_category": "entry",
          "node_type": "E4_handoff",
          "label": "FIU升级案件",
          "evidence_unit_ids": [
            "v7u_N000286"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n2",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "执法机构执行定向监控",
          "evidence_unit_ids": [
            "v7u_N000286"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n3",
          "node_category": "exit",
          "node_type": "X1_classification",
          "label": "识别关注对象并追踪现金走私者和哈瓦拉网络",
          "evidence_unit_ids": [
            "v7u_N000286"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n4",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "执法机构协调资产冻结",
          "evidence_unit_ids": [
            "v7u_N000287"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n5",
          "node_category": "exit",
          "node_type": "X3_state_change",
          "label": "数字钱包被查封，Wolfe公司被瓦解",
          "evidence_unit_ids": [
            "v7u_N000287"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e1",
          "edge_type": "PRECEDES",
          "source": "n1",
          "target": "n2",
          "evidence_unit_ids": [
            "v7u_N000286"
          ],
          "evidence_strength": "explicit",
          "condition": "As FIUs escalated the case",
          "source_quote": "As FIUs escalated the case, law enforcement agencies, including Europol, Interpol, and national counterterrorism task forces, conducted targeted surveillance on Mr. Wolfe and his criminal associates."
        },
        {
          "edge_id": "e2",
          "edge_type": "PRODUCES",
          "source": "n2",
          "target": "n3",
          "evidence_unit_ids": [
            "v7u_N000286"
          ],
          "evidence_strength": "explicit"
        },
        {
          "edge_id": "e3",
          "edge_type": "PRECEDES",
          "source": "n3",
          "target": "n4",
          "evidence_unit_ids": [
            "v7u_N000287"
          ],
          "evidence_strength": "functional_dependency"
        },
        {
          "edge_id": "e4",
          "edge_type": "PRODUCES",
          "source": "n4",
          "target": "n5",
          "evidence_unit_ids": [
            "v7u_N000287"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "source_unit_ids": [
        "v7u_N000286",
        "v7u_N000287"
      ],
      "review_status": "needs_review",
      "review_notes": "增量命题：FIU升级案件 → 执法机构执行定向监控 → 识别关注对象并追踪网络 → 执法机构执行资产冻结 → 查封钱包瓦解公司；KG不足：基础KG不能表达这一系列响应中明确的机构间交接、条件触发的监控行动以及后续控制措施的先后顺序和依赖关系；选项判断：可确认当FIU升级案件后，执法机构会采取监控和资产冻结等行动，并且监控先于冻结；LLM推理：边e3（监控识别到资产冻结）为functional_dependency，原文未明确说明监控结果直接触发资产冻结，但根据执法流程和连续叙述，该顺序是实现切断金融渠道功能所必需的。"
    }
  ],
  "skip_reason": null
}
```
