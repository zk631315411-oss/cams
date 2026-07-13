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
  "section_id": "CH02-S04",
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

section_id: `CH02-S04`
section_title: `Types of financial crime > Case example: FullTechGlobal corruption scandal`

section_text_with_unit_anchors:
[v7u_N000131|131] Sophie is an AFC manager in the compliance department of a financial institution that has some global businesses as its customers.
ZH: Sophie 是金融机构合规部的金融犯罪防控经理。

[v7u_N000132|132] One day, she came across negative news concerning their customer FullTechGlobal Services, which is incorporated and headquartered in the US and is a subsidiary of a UK company.
ZH: Sophie 发现客户 FullTechGlobal Services 的负面新闻。

[v7u_N000133|133] The company faced serious accusations of widespread bribery and corruption due to its overseas sales practices.
ZH: 该公司因海外销售行为面临广泛贿赂和腐败的严重指控。

[v7u_N000134|134] This raised concerns under the extraterritorial provisions of the UK Bribery Act 2010.
ZH: 此事引发对《英国反贿赂法》域外条款的关切。

[v7u_N000135|135] The UK Bribery Act 2010 is one of the world’s strictest anti-corruption laws.
ZH: 《英国反贿赂法》是全球最严格的反腐败法律之一。

[v7u_N000136|136] It applies to any company with a UK connection and also holds parent firms liable for corrupt activities by subsidiaries, regardless of location.
ZH: 该法适用于任何与英国有关联的公司，母公司需对子公司腐败行为负责。

[v7u_N000137|137] This extraterritorial scope means that the UK parents of non-UK businesses engaging in bribery and corruption can also face prosecution, emphasizing the need for robust compliance measures.
ZH: 域外管辖意味着非英国企业的英国母公司也可能因贿赂腐败被起诉。

[v7u_N000138|138] Sophie’s initial investigation revealed that FullTechGlobal had strategically employed intermediaries in high-risk jurisdictions to secure lucrative contracts.
ZH: FullTechGlobal 在高风险司法管辖区战略性地雇佣中间人获取合同。

[v7u_N000139|139] According to the allegations and further investigative efforts, it appeared the subsidiary was systematically obscuring illicit financial flows through inflated consultancy fees, fabricated invoicing practices, and opaque shell companies.
ZH: 子公司通过虚增咨询费、伪造发票和壳公司掩盖非法资金流动。

[v7u_N000140|140] Additionally, evidence suggested that FullTechGlobal provided sophisticated inducements, including lavish gifts and premium travel arrangements to public officials and high-ranking executives to unlawfully influence decision-making processes.
ZH: FullTechGlobal 向公职人员和高级管理人员提供奢华礼品和旅行安排以影响决策。

[v7u_N000141|141] She followed up on the investigation and conducted a review that identified failures within FullTechGlobal’s ABC framework and internal controls. Her audit uncovered deficiencies in internal control mechanisms and inadequate oversight, which facilitated prolonged and undetected corrupt activities.
ZH: FullTechGlobal腐败案审计发现内部控制缺陷和监管不足

[v7u_N000142|142] Bribery was identified as the predicate crime, leading to the laundering of illicit funds through complex financial networks designed to evade regulatory scrutiny and forensic tracing efforts.
ZH: 贿赂作为上游犯罪，通过复杂金融网络洗钱

[v7u_N000143|143] Given these findings, the regulatory implications under the UK Bribery Act 2010 are profound. FullTechGlobal Services faces severe financial penalties, increased scrutiny from international regulators, and potential criminal liability for both the subsidiary and the parent company, including its executives.
ZH: FullTechGlobal面临英国《反贿赂法》下的严厉处罚和监管审查

[v7u_N000144|144] As an AFC manager, she recognizes that her institution needs to maintain compliance integrity and mitigate bribery and corruption risks in its dealings with global businesses such as FullTechGlobal Services.
ZH: 金融犯罪防控经理有义务维护合规诚信并降低贿赂风险

section_units:
[
  {
    "en_quote": "Sophie is an AFC manager in the compliance department of a financial institution that has some global businesses as its customers.",
    "knowledge_zh": "Sophie 是金融机构合规部的金融犯罪防控经理。",
    "pdf_page": 31,
    "printed_page": "26",
    "type": "fact",
    "unit_id": "v7u_N000131",
    "unit_order": 131
  },
  {
    "en_quote": "One day, she came across negative news concerning their customer FullTechGlobal Services, which is incorporated and headquartered in the US and is a subsidiary of a UK company.",
    "knowledge_zh": "Sophie 发现客户 FullTechGlobal Services 的负面新闻。",
    "pdf_page": 31,
    "printed_page": "26",
    "type": "case",
    "unit_id": "v7u_N000132",
    "unit_order": 132
  },
  {
    "en_quote": "The company faced serious accusations of widespread bribery and corruption due to its overseas sales practices.",
    "knowledge_zh": "该公司因海外销售行为面临广泛贿赂和腐败的严重指控。",
    "pdf_page": 31,
    "printed_page": "26",
    "type": "case",
    "unit_id": "v7u_N000133",
    "unit_order": 133
  },
  {
    "en_quote": "This raised concerns under the extraterritorial provisions of the UK Bribery Act 2010.",
    "knowledge_zh": "此事引发对《英国反贿赂法》域外条款的关切。",
    "pdf_page": 31,
    "printed_page": "26",
    "type": "rule",
    "unit_id": "v7u_N000134",
    "unit_order": 134
  },
  {
    "en_quote": "The UK Bribery Act 2010 is one of the world’s strictest anti-corruption laws.",
    "knowledge_zh": "《英国反贿赂法》是全球最严格的反腐败法律之一。",
    "pdf_page": 31,
    "printed_page": "26",
    "type": "fact",
    "unit_id": "v7u_N000135",
    "unit_order": 135
  },
  {
    "en_quote": "It applies to any company with a UK connection and also holds parent firms liable for corrupt activities by subsidiaries, regardless of location.",
    "knowledge_zh": "该法适用于任何与英国有关联的公司，母公司需对子公司腐败行为负责。",
    "pdf_page": 31,
    "printed_page": "26",
    "type": "rule",
    "unit_id": "v7u_N000136",
    "unit_order": 136
  },
  {
    "en_quote": "This extraterritorial scope means that the UK parents of non-UK businesses engaging in bribery and corruption can also face prosecution, emphasizing the need for robust compliance measures.",
    "knowledge_zh": "域外管辖意味着非英国企业的英国母公司也可能因贿赂腐败被起诉。",
    "pdf_page": 31,
    "printed_page": "26",
    "type": "rule",
    "unit_id": "v7u_N000137",
    "unit_order": 137
  },
  {
    "en_quote": "Sophie’s initial investigation revealed that FullTechGlobal had strategically employed intermediaries in high-risk jurisdictions to secure lucrative contracts.",
    "knowledge_zh": "FullTechGlobal 在高风险司法管辖区战略性地雇佣中间人获取合同。",
    "pdf_page": 31,
    "printed_page": "26",
    "type": "case",
    "unit_id": "v7u_N000138",
    "unit_order": 138
  },
  {
    "en_quote": "According to the allegations and further investigative efforts, it appeared the subsidiary was systematically obscuring illicit financial flows through inflated consultancy fees, fabricated invoicing practices, and opaque shell companies.",
    "knowledge_zh": "子公司通过虚增咨询费、伪造发票和壳公司掩盖非法资金流动。",
    "pdf_page": 31,
    "printed_page": "26",
    "type": "case",
    "unit_id": "v7u_N000139",
    "unit_order": 139
  },
  {
    "en_quote": "Additionally, evidence suggested that FullTechGlobal provided sophisticated inducements, including lavish gifts and premium travel arrangements to public officials and high-ranking executives to unlawfully influence decision-making processes.",
    "knowledge_zh": "FullTechGlobal 向公职人员和高级管理人员提供奢华礼品和旅行安排以影响决策。",
    "pdf_page": 31,
    "printed_page": "26",
    "type": "case",
    "unit_id": "v7u_N000140",
    "unit_order": 140
  },
  {
    "en_quote": "She followed up on the investigation and conducted a review that identified failures within FullTechGlobal’s ABC framework and internal controls. Her audit uncovered deficiencies in internal control mechanisms and inadequate oversight, which facilitated prolonged and undetected corrupt activities.",
    "knowledge_zh": "FullTechGlobal腐败案审计发现内部控制缺陷和监管不足",
    "pdf_page": 31,
    "printed_page": "26",
    "type": "case",
    "unit_id": "v7u_N000141",
    "unit_order": 141
  },
  {
    "en_quote": "Bribery was identified as the predicate crime, leading to the laundering of illicit funds through complex financial networks designed to evade regulatory scrutiny and forensic tracing efforts.",
    "knowledge_zh": "贿赂作为上游犯罪，通过复杂金融网络洗钱",
    "pdf_page": 32,
    "printed_page": "27",
    "type": "fact",
    "unit_id": "v7u_N000142",
    "unit_order": 142
  },
  {
    "en_quote": "Given these findings, the regulatory implications under the UK Bribery Act 2010 are profound. FullTechGlobal Services faces severe financial penalties, increased scrutiny from international regulators, and potential criminal liability for both the subsidiary and the parent company, including its executives.",
    "knowledge_zh": "FullTechGlobal面临英国《反贿赂法》下的严厉处罚和监管审查",
    "pdf_page": 32,
    "printed_page": "27",
    "type": "fact",
    "unit_id": "v7u_N000143",
    "unit_order": 143
  },
  {
    "en_quote": "As an AFC manager, she recognizes that her institution needs to maintain compliance integrity and mitigate bribery and corruption risks in its dealings with global businesses such as FullTechGlobal Services.",
    "knowledge_zh": "金融犯罪防控经理有义务维护合规诚信并降低贿赂风险",
    "pdf_page": 32,
    "printed_page": "27",
    "type": "rule",
    "unit_id": "v7u_N000144",
    "unit_order": 144
  }
]

allowed_unit_ids:
[
  "v7u_N000131",
  "v7u_N000132",
  "v7u_N000133",
  "v7u_N000134",
  "v7u_N000135",
  "v7u_N000136",
  "v7u_N000137",
  "v7u_N000138",
  "v7u_N000139",
  "v7u_N000140",
  "v7u_N000141",
  "v7u_N000142",
  "v7u_N000143",
  "v7u_N000144"
]

p7c_card_under_review:
{
  "card_id": "p7card_CH02-S04_001",
  "section_id": "CH02-S04",
  "card_nature": "execution",
  "title": "基于负面新闻的调查审计发现客户贿赂行为与内控缺陷",
  "flow_nodes": [
    {
      "node_id": "N1",
      "node_category": "entry",
      "node_type": "E1_event_signal",
      "label": "Sophie (金融机构AFC经理) 发现客户FullTechGlobal的负面新闻",
      "evidence_unit_ids": [
        "v7u_N000132"
      ],
      "evidence_strength": "explicit"
    },
    {
      "node_id": "N2",
      "node_category": "process",
      "node_type": "P2_execution",
      "label": "Sophie对FullTechGlobal进行调查与审计 (初步调查及后续审查)",
      "evidence_unit_ids": [
        "v7u_N000138",
        "v7u_N000141"
      ],
      "evidence_strength": "explicit"
    },
    {
      "node_id": "N3",
      "node_category": "exit",
      "node_type": "X1_classification",
      "label": "发现FullTechGlobal使用中间人、虚增费用、提供奢华礼品等贿赂行为",
      "evidence_unit_ids": [
        "v7u_N000138",
        "v7u_N000139",
        "v7u_N000140"
      ],
      "evidence_strength": "explicit"
    },
    {
      "node_id": "N4",
      "node_category": "exit",
      "node_type": "X1_classification",
      "label": "发现FullTechGlobal的ABC框架和内部控制缺陷",
      "evidence_unit_ids": [
        "v7u_N000141"
      ],
      "evidence_strength": "explicit"
    }
  ],
  "flow_edges": [
    {
      "edge_id": "E1",
      "edge_type": "PRECEDES",
      "source": "N1",
      "target": "N2",
      "evidence_unit_ids": [
        "v7u_N000132",
        "v7u_N000138"
      ],
      "derivation": "explicit_text"
    },
    {
      "edge_id": "E2",
      "edge_type": "PRODUCES",
      "source": "N2",
      "target": "N3",
      "evidence_unit_ids": [
        "v7u_N000138",
        "v7u_N000139",
        "v7u_N000140"
      ],
      "derivation": "explicit_text"
    },
    {
      "edge_id": "E3",
      "edge_type": "PRODUCES",
      "source": "N2",
      "target": "N4",
      "evidence_unit_ids": [
        "v7u_N000141"
      ],
      "derivation": "explicit_text"
    }
  ],
  "source_unit_ids": [
    "v7u_N000132",
    "v7u_N000138",
    "v7u_N000139",
    "v7u_N000140",
    "v7u_N000141"
  ],
  "candidate_status": "candidate",
  "review_notes": "增量命题：发现负面新闻 →（调查审计）→ 发现贿赂行为和控制缺陷；KG不足：基础KG不能表达从具体触发事件到调查行动再到具体发现的有向程序链；选项判断：可确认或排除关于合规经理在发现客户负面新闻后应采取调查并可能发现什么的选项；LLM推理：无。"
}
