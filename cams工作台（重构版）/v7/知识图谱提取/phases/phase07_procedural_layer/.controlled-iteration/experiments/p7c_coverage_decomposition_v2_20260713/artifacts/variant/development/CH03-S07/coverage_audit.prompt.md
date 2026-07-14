# P7C Proposition-Level Coverage Audit Prompt v2

## 角色

你是P7C命题级覆盖审查器。首次抽取器已经输出`original_json`，但它可能漏掉命题、把P7C关系误判为KG内容，或只覆盖主题而没有完整表达方向、条件、限定词和结果。

本调用只建立覆盖命题台账，不生成card、flow_node或flow_edge。只输出严格JSON，不输出Markdown或解释。

## P7C边界

基础KG能够表达定义、分类、事实、普通案例、孤立风险指标、一般规则、控制措施、普通控制效果、普通机制因果、组成关系和普通知识点关系。

P7C只增量表达对CAMS选项判断有用的局部有向命题：业务情境、事件、线索、输入或标准如何关联到反洗钱、反金融犯罪、合规、监管、FIU或执法主体及其控制流程的识别、评估、决策或应对，以及在相应条件下产生的独立结论、记录、分类、状态变化、分支或后续行动。

## P7C命题硬门槛

命题必须同时通过四项，才能标记为`p7_incremental`：

1. 至少存在一个反洗钱/合规/监管/调查主体的操作性动作或判断，或者一个明确的制度性控制流程动作。
2. 该动作或判断与另一个语义节点之间存在原文明示的输入参照、标准约束、条件触发、判断结果、独立产出或后续应对关系。
3. 这条关系能够判断选项中的主体、条件、方向、限定词、分类结果、应对或适用范围。
4. 基础KG即使保存整句话或各个事实，仍不能充分表达上述细粒度有向结构。

只有一个动作节点而没有第二个语义节点和可靠关系，不得进入P7C。只有主题相关性、教材相邻顺序或推测出的业务常识，不得进入P7C。

## 必须交给KG的内容

以下即使语法上含有因果词、情态词或动作词，通常仍为`kg_only`：

- 产品、工具、犯罪手法或组织特征导致、增加或掩盖风险的一般机制；
- “某控制可以降低风险、帮助管理风险、提高效率、防范犯罪”等普通控制效果；
- 普通案例事实、犯罪操作步骤、调查困难、当局受到阻碍，但没有由此形成判断、应对、分支或程序结果；
- 总结性倡议、抽象义务或“应维护诚信、持续更新、理解风险很重要”等表述，但原文没有明确连接其输入、条件、标准或独立结果；
- 定义、分类、阈值数字、组成列表、孤立红旗和一般法律后果。

不得把“当局调查时常受腐败官员阻碍”包装成“调查产生受阻状态”；这是调查困难和犯罪机制，由KG承接。

不得把“控制可以降低风险”自动包装成`process PRODUCES 风险降低`。只有具体识别、评估、核实、分类或监控动作产生原文明示且可单独判断的结果时，才可能属于P7C。例如“CDD有助于确保客户按照预期和历史交易模式正确细分”包含具体评估动作、参照维度和限定性分类结果，不是抽象的风险降低口号。

## 两类不得漏掉的开放或示例关系

1. 原文以`based on, according to, using, considering, require`等形式说明制度性动作明确参照输入、经验、线索、阈值或标准时，即使没有独立出口，也属于可审查的P7C开放关系。例如“创建、修改或删除检测规则时基于历史可疑活动和实际事件经验”应登记为动作参照经验，而不能仅因该句位于定义段落就交给KG。
2. 原文给出计算或比较过程，并明确导向相反的分类结果时，案例事实由KG保存，但“计算输入→比较阈值→分类”的判断结构属于P7C。例如合计直接和间接持股后明确认定或不认定UBO，应分别检查分类出口是否进入图。

## 审查方法

按自然段落、unit、转折、主体、对象和条件变化完整扫描section。先写出完整命题，再依次执行硬门槛、KG排除项和覆盖比较。

不得因为已有card标题相近、节点含有相同主题词，或者某个主题已经成卡，就认定命题已经覆盖。对每个P7C命题逐项比较：

- 主体和动作是否存在；
- source、target和方向是否一致；
- 条件是否进入边或节点；
- `must, should, may, might, could, often, potentially, help, appeared, suggested, typically`等限定是否保留；
- 独立分类、结论、记录、状态变化或控制效果是否有节点和边；
- 开放式参照关系是否因“没有出口”而被错误跳过。

`coverage_status`判定：

- `covered`：已有card完整表达同一有向命题，包括主体、方向、条件和限定词。
- `partially_covered`：已有card只覆盖主题或部分端点，遗漏方向、条件、限定词、独立出口，或把可能性/帮助关系写成确定性结果。
- `missing`：已有card没有表达该P7C命题。
- `not_applicable`：该命题属于`kg_only`。

如果已有边写强、写反或漏掉限定词，应判为`partially_covered`，不能因为端点已经出现而判为`covered`。

## 输出合同

顶层必须且只能包含：`section_id, claims, scan_summary`。

每项claim必填：

```json
{
  "claim_id": "claim_001",
  "unit_ids": ["<当前section unit_id>"],
  "proposition": "<保留主体、方向、条件和限定词的完整中文命题>",
  "kg_boundary": "p7_incremental",
  "coverage_status": "partially_covered",
  "matched_card_ids": ["<已有card_id>"],
  "missing_part": "<具体缺少的方向、条件、限定词、节点或边；无则为null>",
  "condition": "<原文条件；无则为null>",
  "qualifier": "<原文情态或限定；无则为null>",
  "reason": "<必须说明四项硬门槛如何满足，或为何由KG承接>"
}
```

约束：

- `kg_boundary`只能是`kg_only`或`p7_incremental`。
- `kg_only`必须使用`coverage_status=not_applicable`，`matched_card_ids=[]`，`missing_part=null`。
- `p7_incremental + covered`必须至少匹配一张已有card，且`missing_part=null`。
- `p7_incremental + partially_covered`必须至少匹配一张已有card，并具体填写`missing_part`。
- `p7_incremental + missing`必须具体填写`missing_part`；`matched_card_ids`可以为空。
- 只能引用`allowed_unit_ids`和`original_json.cards`中存在的card ID。
- `scan_summary`用一句中文说明扫描范围、P7C缺口数量和KG排除数量。

## 当前section

运行器将在此处追加当前section原文、KG摘要、首次抽取JSON和允许的unit ID。

## 调用输入

```json
{
  "section_id": "CH03-S07",
  "section_title": "Examples of predicate crimes > Case example: Mr. Wolfe’s scheme",
  "base_kg_section_summary": {
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
  },
  "section_text_with_unit_anchors": "[v7u_N000270|270] Mr. Wolfe, a wealthy businessman with radical political views, decided to conduct a terrorist financing scheme to support ISIS operations in Syria, in alignment with his ideology.\nZH: 富商Wolfe先生策划恐怖融资计划支持叙利亚的ISIS行动\n\n[v7u_N000271|271] Unlike traditional money laundering typologies, this type of terrorist financing scheme involved various funnel points and both legitimate and illicit financial streams.\nZH: 该恐怖融资计划与传统洗钱类型不同，涉及多种漏斗点和合法及非法资金流\n\n[v7u_N000272|272] Mr. Wolfe utilized his import-export firms, travel agencies, and retail businesses to generate authentic income.\nZH: Wolfe利用其进出口公司、旅行社和零售业务产生真实收入\n\n[v7u_N000273|273] However, he then concealed portions of these legitimate revenues through deceptive channels, such as privacy-centered cryptocurrencies, to ultimately reach terrorist organizations without detection.\nZH: Wolfe通过隐私加密货币等欺骗性渠道隐藏部分合法收入以资助恐怖组织\n\n[v7u_N000274|274] Simultaneously, Mr. Wolfe’s criminal associates used explicitly illegal activities to raise funds.\nZH: Wolfe的犯罪同伙使用明确的非法活动筹集资金\n\n[v7u_N000275|275] Criminal operations, including cybercrimes such as ransomware attacks, financial institution hacking, and credit card fraud generated substantial illicit proceeds.\nZH: 网络犯罪如勒索软件攻击、金融机构黑客攻击和信用卡欺诈产生大量非法收益\n\n[v7u_N000276|276] They also used traditional criminal enterprises, such as narcotics trafficking and large-scale fraud schemes, and deliberately directed the funds toward terrorist networks.\nZH: 他们还使用传统犯罪企业如毒品贩运和大规模欺诈，并故意将资金导向恐怖网络\n\n[v7u_N000277|277] Once the financiers obtained the funds, facilitators employed sophisticated money laundering methods to obscure their origins and destinations to avoid detection.\nZH: 资金提供者获得资金后，中间人使用复杂的洗钱方法掩盖资金来源和去向\n\n[v7u_N000278|278] The facilitators:\nZH: 列举中间人所采取的具体洗钱手段\n\n[v7u_N000279|279] Committed trade-based money laundering involving false invoicing and fictitious commodity transactions through seemingly legitimate businesses.\nZH: 通过看似合法的企业进行虚假发票和虚构商品交易的贸易洗钱\n\n[v7u_N000280|280] Layered funds through unregulated fintech platforms, cryptocurrencies, and peer-to-peer payment networks, using digital wallets to complicate traceability.\nZH: 通过不受监管的金融科技平台、加密货币和点对点支付网络进行资金分层\n\n[v7u_N000281|281] Smuggled physical bulk cash, moving large amounts of money across borders outside conventional banking oversight.\nZH: 走私实物现金，绕过传统银行监管跨境转移大额资金\n\n[v7u_N000282|282] Used hawala brokers to facilitate cross-border transfers, leveraging informal networks to obscure financial trails.\nZH: 利用哈瓦拉经纪人进行跨境转账，通过非正规网络掩盖资金踪迹\n\n[v7u_N000283|283] Financial institutions first detected the illicit activity through transaction monitoring systems, which flagged structured deposits, rapid interjurisdictional layering, and anomalous fund movements linked to known terror-affiliated wallets.\nZH: 金融机构通过交易监控系统发现可疑活动，包括结构化存款和异常资金流动\n\n[v7u_N000284|284] Blockchain analytics firms provided forensic intelligence, mapping illicit cryptoasset flows through darknet marketplaces and high-risk exchanges.\nZH: 区块链分析公司提供取证情报，追踪暗网市场和风险交易所的非法加密资产流动\n\n[v7u_N000285|285] FIUs synthesized bank SARs with cross-border financial activity, triggering red flags within international regulatory networks.\nZH: 金融情报机构综合银行可疑交易报告与跨境金融活动，触发国际监管网络红旗信号信号\n\n[v7u_N000286|286] As FIUs escalated the case, law enforcement agencies, including Europol, Interpol, and national counterterrorism task forces, conducted targeted surveillance on Mr. Wolfe and his criminal associates. These individuals, designated as subjects of interest, were monitored to trace cash smugglers and hawala networks.\nZH: 执法机构对Wolfe及其同伙进行针对性监控，追踪现金走私者和哈瓦拉网络\n\n[v7u_N000287|287] They conducted coordinated asset freezes to disrupt financial channels, resulting in the seizure of digital wallets and the dismantling of Mr. Wolfe’s companies used to finance terrorism.\nZH: 协调资产冻结以切断金融渠道，查封数字钱包并瓦解Wolfe用于资助恐怖主义的公司\n\n[v7u_N000288|288] Mr. Wolfe and his associates all received lengthy prison sentences and heavy fines.\nZH: Wolfe及其同伙被判处长期监禁和巨额罚款\n\n[v7u_N000289|289] Intelligenceled investigations, real-time interagency collaboration, and advanced analytics all played a key role in countering this terrorist financing network.\nZH: 情报主导调查、实时机构间协作和高级分析在打击恐怖融资中发挥关键作用",
  "allowed_unit_ids": [
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
  ],
  "original_json": {
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
}
```
