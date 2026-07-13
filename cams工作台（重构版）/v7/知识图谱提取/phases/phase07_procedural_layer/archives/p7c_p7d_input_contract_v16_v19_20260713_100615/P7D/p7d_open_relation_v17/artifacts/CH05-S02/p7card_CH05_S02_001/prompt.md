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
  "section_id": "CH05-S02",
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

section_id: `CH05-S02`
section_title: `Financial crime risks in relation to other types of risks > Case example: A lasting lesson`

section_text_with_unit_anchors:
[v7u_N000356|356] In 2012, HSBC was involved in a money laundering scandal that remains one of the most significant AML compliance failures in banking history. Due to inadequate transaction monitoring and an overall fragmented and ineffective compliance framework, HSBC allowed drug cartels to launder over US$880 million in its Mexico operations.
ZH: 汇丰银行因反洗钱合规失败卷入洗钱丑闻，允许贩毒集团洗钱超过8.8亿美元

[v7u_N000357|357] In response to the breach, US federal regulators imposed a record fine of US$1.9 billion, which was the largest AML penalty at that time, comprising US$665 million in civil penalties.
ZH: 美国监管机构对汇丰处以19亿美元创纪录反洗钱罚款

[v7u_N000358|358] The US Department of Justice entered into a five-year deferred prosecution agreement with HSBC, mandating a comprehensive overhaul of its global compliance operations.
ZH: 美国司法部与汇丰达成五年延期起诉协议，要求全面整改全球合规

[v7u_N000359|359] One critical outcome of the investigation was the forced resignation of several senior executives, including the Global Head of Compliance, reflecting the regulator’s strong criticism of the bank’s AFC culture.
ZH: 调查导致汇丰多名高管辞职，包括全球合规主管，反映监管对金融犯罪防控文化的批评

[v7u_N000360|360] Regulators highlighted that HSBC’s internal environment had often prioritized local business interests and profit over robust, centralized compliance controls.
ZH: 监管指出汇丰内部环境常将本地业务和利润置于合规控制之上

[v7u_N000361|361] The operational repercussions were profound. Not only did the scandal trigger an immediate regulatory and financial backlash, but it also inflicted lasting reputational damage. HSBC’s credibility was severely undermined, leading to a significant erosion of customer trust and a weakened market position.
ZH: 汇丰银行丑闻导致监管处罚、财务损失和声誉损害，削弱客户信任和市场地位。

[v7u_N000362|362] As a corrective measure, the bank was compelled to rebalance power dynamics within its organization, strengthening central oversight and compliance functions while limiting the autonomy of local business units. This restructuring aimed to restore the integrity of its financial crime risk management framework and reduce exposure to high-risk jurisdictions through a strategic de-risking process.
ZH: 汇丰银行采取纠正措施，加强中央监督和合规职能，限制地方业务部门自主权，并通过去风险化减少高风险司法管辖区敞口。

[v7u_N000363|363] Ultimately, the HSBC case offers a severe lesson on the operational and reputational risks associated with weak financial crime controls. It underscores the critical importance of maintaining a strong compliance culture and implementing robust AML controls. It also serves as an instructive example for financial institutions worldwide: neglect in these areas not only results in severe financial penalties and operational disruption but also irrevocably damages a bank’s reputation, ultimately undermining its long-term viability in the global market.
ZH: 汇丰案例警示：薄弱的金融犯罪控制会导致运营和声誉风险，强调强合规文化与反洗钱控制的重要性。

section_units:
[
  {
    "en_quote": "In 2012, HSBC was involved in a money laundering scandal that remains one of the most significant AML compliance failures in banking history. Due to inadequate transaction monitoring and an overall fragmented and ineffective compliance framework, HSBC allowed drug cartels to launder over US$880 million in its Mexico operations.",
    "knowledge_zh": "汇丰银行因反洗钱合规失败卷入洗钱丑闻，允许贩毒集团洗钱超过8.8亿美元",
    "pdf_page": 52,
    "printed_page": "47",
    "type": "case",
    "unit_id": "v7u_N000356",
    "unit_order": 356
  },
  {
    "en_quote": "In response to the breach, US federal regulators imposed a record fine of US$1.9 billion, which was the largest AML penalty at that time, comprising US$665 million in civil penalties.",
    "knowledge_zh": "美国监管机构对汇丰处以19亿美元创纪录反洗钱罚款",
    "pdf_page": 52,
    "printed_page": "47",
    "type": "fact",
    "unit_id": "v7u_N000357",
    "unit_order": 357
  },
  {
    "en_quote": "The US Department of Justice entered into a five-year deferred prosecution agreement with HSBC, mandating a comprehensive overhaul of its global compliance operations.",
    "knowledge_zh": "美国司法部与汇丰达成五年延期起诉协议，要求全面整改全球合规",
    "pdf_page": 52,
    "printed_page": "47",
    "type": "fact",
    "unit_id": "v7u_N000358",
    "unit_order": 358
  },
  {
    "en_quote": "One critical outcome of the investigation was the forced resignation of several senior executives, including the Global Head of Compliance, reflecting the regulator’s strong criticism of the bank’s AFC culture.",
    "knowledge_zh": "调查导致汇丰多名高管辞职，包括全球合规主管，反映监管对金融犯罪防控文化的批评",
    "pdf_page": 52,
    "printed_page": "47",
    "type": "fact",
    "unit_id": "v7u_N000359",
    "unit_order": 359
  },
  {
    "en_quote": "Regulators highlighted that HSBC’s internal environment had often prioritized local business interests and profit over robust, centralized compliance controls.",
    "knowledge_zh": "监管指出汇丰内部环境常将本地业务和利润置于合规控制之上",
    "pdf_page": 52,
    "printed_page": "47",
    "type": "fact",
    "unit_id": "v7u_N000360",
    "unit_order": 360
  },
  {
    "en_quote": "The operational repercussions were profound. Not only did the scandal trigger an immediate regulatory and financial backlash, but it also inflicted lasting reputational damage. HSBC’s credibility was severely undermined, leading to a significant erosion of customer trust and a weakened market position.",
    "knowledge_zh": "汇丰银行丑闻导致监管处罚、财务损失和声誉损害，削弱客户信任和市场地位。",
    "pdf_page": 52,
    "printed_page": "47",
    "type": "case",
    "unit_id": "v7u_N000361",
    "unit_order": 361
  },
  {
    "en_quote": "As a corrective measure, the bank was compelled to rebalance power dynamics within its organization, strengthening central oversight and compliance functions while limiting the autonomy of local business units. This restructuring aimed to restore the integrity of its financial crime risk management framework and reduce exposure to high-risk jurisdictions through a strategic de-risking process.",
    "knowledge_zh": "汇丰银行采取纠正措施，加强中央监督和合规职能，限制地方业务部门自主权，并通过去风险化减少高风险司法管辖区敞口。",
    "pdf_page": 52,
    "printed_page": "47",
    "type": "case",
    "unit_id": "v7u_N000362",
    "unit_order": 362
  },
  {
    "en_quote": "Ultimately, the HSBC case offers a severe lesson on the operational and reputational risks associated with weak financial crime controls. It underscores the critical importance of maintaining a strong compliance culture and implementing robust AML controls. It also serves as an instructive example for financial institutions worldwide: neglect in these areas not only results in severe financial penalties and operational disruption but also irrevocably damages a bank’s reputation, ultimately undermining its long-term viability in the global market.",
    "knowledge_zh": "汇丰案例警示：薄弱的金融犯罪控制会导致运营和声誉风险，强调强合规文化与反洗钱控制的重要性。",
    "pdf_page": 52,
    "printed_page": "47",
    "type": "case",
    "unit_id": "v7u_N000363",
    "unit_order": 363
  }
]

allowed_unit_ids:
[
  "v7u_N000356",
  "v7u_N000357",
  "v7u_N000358",
  "v7u_N000359",
  "v7u_N000360",
  "v7u_N000361",
  "v7u_N000362",
  "v7u_N000363"
]

p7c_card_under_review:
{
  "card_id": "p7card_CH05_S02_001",
  "section_id": "CH05-S02",
  "card_nature": "execution",
  "title": "汇丰银行纠正措施：加强中央监督、限制地方自主权与去风险化",
  "flow_nodes": [
    {
      "node_id": "E1",
      "node_category": "entry",
      "node_type": "E1_event_signal",
      "label": "HSBC洗钱丑闻曝光并遭受19亿美元罚款及五年延期起诉协议要求全面整改",
      "evidence_unit_ids": [
        "v7u_N000356",
        "v7u_N000357",
        "v7u_N000358"
      ],
      "evidence_strength": "explicit"
    },
    {
      "node_id": "P1",
      "node_category": "process",
      "node_type": "P2_execution",
      "label": "HSBC被迫执行纠正措施：重新平衡内部权力，加强中央监督和合规职能，限制地方业务部门自主权，并通过战略性去风险化减少高风险司法管辖区敞口",
      "evidence_unit_ids": [
        "v7u_N000362"
      ],
      "evidence_strength": "explicit"
    },
    {
      "node_id": "X1",
      "node_category": "exit",
      "node_type": "X5_config_change",
      "label": "HSBC金融犯罪风险管理框架重构：中央监督加强，地方自主权受限，去风险化实施（旨在恢复完整性并减少敞口）",
      "evidence_unit_ids": [
        "v7u_N000362"
      ],
      "evidence_strength": "explicit"
    }
  ],
  "flow_edges": [
    {
      "edge_id": "e1",
      "edge_type": "PRECEDES",
      "source": "E1",
      "target": "P1",
      "evidence_unit_ids": [
        "v7u_N000356",
        "v7u_N000357",
        "v7u_N000358",
        "v7u_N000362"
      ],
      "derivation": "explicit_text",
      "source_quote": "As a corrective measure, the bank was compelled to rebalance power dynamics... (v7u_N000362)"
    },
    {
      "edge_id": "e2",
      "edge_type": "PRODUCES",
      "source": "P1",
      "target": "X1",
      "evidence_unit_ids": [
        "v7u_N000362"
      ],
      "derivation": "explicit_text",
      "source_quote": "This restructuring aimed to restore the integrity of its financial crime risk management framework and reduce exposure to high-risk jurisdictions... (v7u_N000362)"
    }
  ],
  "source_unit_ids": [
    "v7u_N000356",
    "v7u_N000357",
    "v7u_N000358",
    "v7u_N000362"
  ],
  "candidate_status": "candidate",
  "review_notes": "增量命题：HSBC洗钱丑闻及监管处罚触发银行执行纠正措施，导致金融犯罪风险管理框架重构（加强中央监督、限制地方自主权、去风险化）。KG不足：基础KG可保存案例事实，但无法表达从外部事件到具体应对措施再到配置变化的有向判断链。选项判断：可确认或排除关于汇丰后丑闻应对措施、组织结构变化的选项。LLM推理：无。"
}
