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
  "section_id": "CH05-S04",
  "section_title": "Financial crime risks in relation to other types of risks > Operational, legal, concentration, and reputational risks",
  "base_kg_section_summary": {
    "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
    "covered_topics": [
      {
        "title_zh": "主要风险类型：运营、法律、集中度、声誉",
        "title_en": "Key risk types: operational, legal, concentration, reputational",
        "covered_units": [
          {
            "unit_id": "v7u_N000369",
            "unit_type": "classification",
            "kg_role": "classifies"
          }
        ]
      },
      {
        "title_zh": "运营风险：定义与监管挑战",
        "title_en": "Operational risk: definition and regulatory challenges",
        "covered_units": [
          {
            "unit_id": "v7u_N000370",
            "unit_type": "definition",
            "kg_role": "defines"
          },
          {
            "unit_id": "v7u_N000375",
            "unit_type": "definition",
            "kg_role": "explains"
          },
          {
            "unit_id": "v7u_N000376",
            "unit_type": "process",
            "kg_role": "explains"
          },
          {
            "unit_id": "v7u_N000377",
            "unit_type": "risk_indicator",
            "kg_role": "explains"
          },
          {
            "unit_id": "v7u_N000378",
            "unit_type": "rule",
            "kg_role": "prescribes_measure"
          }
        ]
      },
      {
        "title_zh": "法律风险：来源、后果及AFC保护",
        "title_en": "Legal risk: sources, consequences, and AFC protection",
        "covered_units": [
          {
            "unit_id": "v7u_N000371",
            "unit_type": "definition",
            "kg_role": "defines"
          },
          {
            "unit_id": "v7u_N000379",
            "unit_type": "definition",
            "kg_role": "explains"
          },
          {
            "unit_id": "v7u_N000381",
            "unit_type": "rule",
            "kg_role": "prescribes_measure"
          },
          {
            "unit_id": "v7u_N000380",
            "unit_type": "fact",
            "kg_role": "states_consequence"
          }
        ]
      },
      {
        "title_zh": "集中度风险：过度敞口、缓解与管理",
        "title_en": "Concentration risk: over-exposure, mitigation, and management",
        "covered_units": [
          {
            "unit_id": "v7u_N000372",
            "unit_type": "definition",
            "kg_role": "defines"
          },
          {
            "unit_id": "v7u_N000382",
            "unit_type": "rule",
            "kg_role": "prescribes_measure"
          },
          {
            "unit_id": "v7u_N000384",
            "unit_type": "fact",
            "kg_role": "explains"
          },
          {
            "unit_id": "v7u_N000385",
            "unit_type": "fact",
            "kg_role": "indicates_risk"
          },
          {
            "unit_id": "v7u_N000383",
            "unit_type": "fact",
            "kg_role": "prescribes_measure"
          }
        ]
      },
      {
        "title_zh": "声誉风险：特征与信任因素",
        "title_en": "Reputational risk: characteristics and trust factor",
        "covered_units": [
          {
            "unit_id": "v7u_N000373",
            "unit_type": "definition",
            "kg_role": "defines"
          },
          {
            "unit_id": "v7u_N000386",
            "unit_type": "fact",
            "kg_role": "explains"
          },
          {
            "unit_id": "v7u_N000387",
            "unit_type": "fact",
            "kg_role": "explains"
          },
          {
            "unit_id": "v7u_N000388",
            "unit_type": "fact",
            "kg_role": "explains"
          }
        ]
      }
    ],
    "covered_relations": [
      {
        "source_title": "主要风险类型：运营、法律、集中度、声誉",
        "target_title": "运营风险：定义与监管挑战",
        "relation_type": "contains"
      },
      {
        "source_title": "主要风险类型：运营、法律、集中度、声誉",
        "target_title": "法律风险：来源、后果及AFC保护",
        "relation_type": "contains"
      },
      {
        "source_title": "主要风险类型：运营、法律、集中度、声誉",
        "target_title": "集中度风险：过度敞口、缓解与管理",
        "relation_type": "contains"
      },
      {
        "source_title": "主要风险类型：运营、法律、集中度、声誉",
        "target_title": "声誉风险：特征与信任因素",
        "relation_type": "contains"
      }
    ]
  },
  "section_text_with_unit_anchors": "[v7u_N000369|369] Key risks that organizations face include: Operational, legal, concentration, and reputational.\nZH: 组织面临的主要风险类型包括：运营风险、法律风险、集中度风险和声誉风险。\n\n[v7u_N000370|370] Operational risk is direct or indirect loss of operations due to inadequate or failed internal processes, people, or systems, or as a result of external events.\nZH: 运营风险是因内部流程、人员、系统不完善或外部事件导致直接或间接损失的风险。\n\n[v7u_N000371|371] Legal risk is the possibility that criminal penalties, lawsuits, or contracts that cannot be enforced might harm an organization.\nZH: 法律风险是指刑事处罚、诉讼或不可执行合同可能损害组织的可能性。\n\n[v7u_N000372|372] Concentration risk stems from over-exposure to a single customer or group of related customers.\nZH: 集中度风险源于对单一客户或关联客户群体的过度敞口。\n\n[v7u_N000373|373] Reputational risk comes when an institution known to have weak controls is then targeted by criminals or avoided by stakeholders who lose confidence in the institution.\nZH: 声誉风险是指机构因控制薄弱而被犯罪分子利用或利益相关者失去信心而回避的风险。\n\n[v7u_N000374|374] Although these risks are usually managed by non-AFC risk management teams, understanding the correlation with financial crime risk is indispensable.\nZH: 尽管这些风险通常由非金融犯罪防控团队管理，但理解其与金融犯罪风险的关联至关重要。\n\n[v7u_N000375|375] Operational risk is complex and includes an organization’s ability to maintain AFC controls in an evolving regulatory environment across multiple jurisdictions.\nZH: 运营风险复杂，包括组织在多个司法管辖区不断变化的监管环境中维持金融犯罪防控控制的能力。\n\n[v7u_N000376|376] Typically, a global organization makes the policies of its home regulator its base standard. The organization will then adjust to each host country’s laws.\nZH: 全球组织通常以母国监管机构政策为基础标准，再根据东道国法律进行调整。\n\n[v7u_N000377|377] Evolving regulations might become misaligned with current business models and controls.\nZH: 不断演变的法规可能与现有业务模式和控制措施产生错位。\n\n[v7u_N000378|378] Compliance programs must continually be updated.\nZH: 合规计划必须持续更新。\n\n[v7u_N000379|379] Legal risk stems from potential violation of regulations, laws, and ethical practices.\nZH: 法律风险源于可能违反法规、法律和道德实践。\n\n[v7u_N000380|380] Governments might issue administrative penalties or fines. Third parties, such as customers who feel damaged, might file lawsuits.\nZH: 政府可能处以行政处罚或罚款，受损客户等第三方可能提起诉讼。\n\n[v7u_N000381|381] Adequate AFC controls add protection from crime and inappropriate relationships.\nZH: 充分的金融犯罪防控措施可防范犯罪及不当关系\n\n[v7u_N000382|382] Concentration risk can be reduced by AFC controls and strategic diversification.\nZH: 金融犯罪防控与战略多元化可降低集中度风险\n\n[v7u_N000383|383] Customer due diligence, enabled by technology, helps manage exposure.\nZH: 借助技术的客户尽职调查有助于管理风险敞口\n\n[v7u_N000384|384] Concentration could occur in borrowing, funding, purchasing, provision of key services, or any other business relationship.\nZH: 集中度可能出现在借贷、融资、采购、关键服务提供等业务关系中\n\n[v7u_N000385|385] Risk could increase through actions by a customer, or external actions involving a customer.\nZH: 风险可能因客户行为或涉及客户的外部行为而增加\n\n[v7u_N000386|386] Reputational risk is difficult to quantify.\nZH: 声誉风险难以量化\n\n[v7u_N000387|387] Trust takes a long time to earn but can be lost quickly. A single news story—even fake news—can drive away customers and investors.\nZH: 信任建立缓慢但易丧失，一条新闻即可驱离客户与投资者\n\n[v7u_N000388|388] Many organizations deserve their reputations, good or bad, based on their chosen business practices and ethics.\nZH: 组织的声誉源于其商业实践与道德选择",
  "allowed_unit_ids": [
    "v7u_N000369",
    "v7u_N000370",
    "v7u_N000371",
    "v7u_N000372",
    "v7u_N000373",
    "v7u_N000374",
    "v7u_N000375",
    "v7u_N000376",
    "v7u_N000377",
    "v7u_N000378",
    "v7u_N000379",
    "v7u_N000380",
    "v7u_N000381",
    "v7u_N000382",
    "v7u_N000383",
    "v7u_N000384",
    "v7u_N000385",
    "v7u_N000386",
    "v7u_N000387",
    "v7u_N000388"
  ],
  "original_json": {
    "section_id": "CH05-S04",
    "section_title": "Financial crime risks in relation to other types of risks > Operational, legal, concentration, and reputational risks",
    "coverage_audit": [
      {
        "candidate_id": "cand_001",
        "unit_ids": [
          "v7u_N000376"
        ],
        "proposition": "全球组织通常以母国监管机构政策为基础标准，然后根据各东道国法律进行调整",
        "decision": "p7c_card",
        "card_id": "p7card_CH05-S04_001",
        "reason": "原文明示顺序性程序结构：先设定基础标准，再根据各地法律调整，包含有向动作序列，超出基础KG的简单事实保存范围。"
      },
      {
        "candidate_id": "cand_002",
        "unit_ids": [
          "v7u_N000369"
        ],
        "proposition": "组织面临的主要风险类型包括运营、法律、集中度、声誉风险",
        "decision": "kg_only",
        "card_id": null,
        "reason": "纯分类列表，无有向条件-动作结构，基础KG可充分表达。"
      },
      {
        "candidate_id": "cand_003",
        "unit_ids": [
          "v7u_N000370"
        ],
        "proposition": "运营风险是因内部流程、人员、系统不完善或外部事件导致直接或间接损失的风险",
        "decision": "kg_only",
        "card_id": null,
        "reason": "定义性陈述，无程序性或判断性有向关系。"
      },
      {
        "candidate_id": "cand_004",
        "unit_ids": [
          "v7u_N000371"
        ],
        "proposition": "法律风险是指刑事处罚、诉讼或不可执行合同可能损害组织的可能性",
        "decision": "kg_only",
        "card_id": null,
        "reason": "定义性陈述，无具体动作链。"
      },
      {
        "candidate_id": "cand_005",
        "unit_ids": [
          "v7u_N000372"
        ],
        "proposition": "集中度风险源于对单一客户或关联客户群体的过度敞口",
        "decision": "kg_only",
        "card_id": null,
        "reason": "定义性陈述。"
      },
      {
        "candidate_id": "cand_006",
        "unit_ids": [
          "v7u_N000373"
        ],
        "proposition": "声誉风险是因控制薄弱被犯罪分子利用或利益相关者丧失信心而回避的风险",
        "decision": "kg_only",
        "card_id": null,
        "reason": "定义性陈述。"
      },
      {
        "candidate_id": "cand_007",
        "unit_ids": [
          "v7u_N000374"
        ],
        "proposition": "虽然这些风险通常由非AFC团队管理，但理解其与金融犯罪风险的关联必不可少",
        "decision": "kg_only",
        "card_id": null,
        "reason": "仅陈述管理归属和重要性，无具体条件-动作有向链。"
      },
      {
        "candidate_id": "cand_008",
        "unit_ids": [
          "v7u_N000375"
        ],
        "proposition": "运营风险复杂，包括在多个司法管辖区不断变化的监管环境中维持AFC控制的能力",
        "decision": "kg_only",
        "card_id": null,
        "reason": "对运营风险复杂性的补充说明，未形成指向特定判断或应对的有向结构。"
      },
      {
        "candidate_id": "cand_009",
        "unit_ids": [
          "v7u_N000377",
          "v7u_N000378"
        ],
        "proposition": "当法规演变可能与现有业务模式和控制错位时，合规计划必须持续更新",
        "decision": "kg_only",
        "card_id": null,
        "reason": "两句之间无明确因果或条件连接词，原文未明示法规错位直接触发更新义务，仅为独立的风险陈述与一般性义务陈述，基础KG可分别保存。"
      },
      {
        "candidate_id": "cand_010",
        "unit_ids": [
          "v7u_N000379"
        ],
        "proposition": "法律风险源于可能违反法规、法律和道德实践",
        "decision": "kg_only",
        "card_id": null,
        "reason": "风险来源说明，无程序性结构。"
      },
      {
        "candidate_id": "cand_011",
        "unit_ids": [
          "v7u_N000380"
        ],
        "proposition": "政府可能处以行政罚款，受损第三方可能提起诉讼",
        "decision": "kg_only",
        "card_id": null,
        "reason": "列举法律风险的可能后果，属一般事实，基础KG可保存。"
      },
      {
        "candidate_id": "cand_012",
        "unit_ids": [
          "v7u_N000381"
        ],
        "proposition": "充分的AFC控制可防范犯罪及不当关系",
        "decision": "kg_only",
        "card_id": null,
        "reason": "控制效益的一般性声明，无特定条件-动作链。"
      },
      {
        "candidate_id": "cand_013",
        "unit_ids": [
          "v7u_N000382",
          "v7u_N000383"
        ],
        "proposition": "通过AFC控制和战略多元化及借助技术的客户尽职调查，可降低集中度风险并管理敞口",
        "decision": "kg_only",
        "card_id": null,
        "reason": "一般性缓解措施说明，未形成有向判断或行动步骤。"
      },
      {
        "candidate_id": "cand_014",
        "unit_ids": [
          "v7u_N000384",
          "v7u_N000385"
        ],
        "proposition": "集中度可能出现在借贷、融资等多种业务关系中，风险可能因客户或外部行动而增加",
        "decision": "kg_only",
        "card_id": null,
        "reason": "列举风险发生场景和增加因素，属知识性事实，无程序性结构。"
      },
      {
        "candidate_id": "cand_015",
        "unit_ids": [
          "v7u_N000386",
          "v7u_N000387",
          "v7u_N000388"
        ],
        "proposition": "声誉风险难以量化，信任易失，组织声誉源于商业实践与道德选择",
        "decision": "kg_only",
        "card_id": null,
        "reason": "声誉风险特征的一般说明，无具体动作或判断链。"
      }
    ],
    "cards": [
      {
        "card_id": "p7card_CH05-S04_001",
        "section_id": "CH05-S04",
        "card_nature": "execution",
        "title": "全球组织以母国标准为基础并适应东道国法律",
        "flow_nodes": [
          {
            "node_id": "P1",
            "node_category": "process",
            "node_type": "P8_constrained_action",
            "label": "全球组织通常以母国监管机构政策为基础标准",
            "evidence_unit_ids": [
              "v7u_N000376"
            ],
            "evidence_strength": "explicit"
          },
          {
            "node_id": "P2",
            "node_category": "process",
            "node_type": "P8_constrained_action",
            "label": "全球组织然后根据各东道国法律进行调整",
            "evidence_unit_ids": [
              "v7u_N000376"
            ],
            "evidence_strength": "explicit"
          },
          {
            "node_id": "S1",
            "node_category": "auxiliary",
            "node_type": "standard",
            "label": "母国监管机构政策",
            "evidence_unit_ids": [
              "v7u_N000376"
            ],
            "evidence_strength": "explicit"
          },
          {
            "node_id": "S2",
            "node_category": "auxiliary",
            "node_type": "standard",
            "label": "各东道国法律",
            "evidence_unit_ids": [
              "v7u_N000376"
            ],
            "evidence_strength": "explicit"
          }
        ],
        "flow_edges": [
          {
            "edge_id": "e1",
            "edge_type": "REFERENCES",
            "source": "P1",
            "target": "S1",
            "evidence_unit_ids": [
              "v7u_N000376"
            ],
            "derivation": "explicit_text",
            "relation_type": "standard_constrains_action"
          },
          {
            "edge_id": "e2",
            "edge_type": "REFERENCES",
            "source": "P2",
            "target": "S2",
            "evidence_unit_ids": [
              "v7u_N000376"
            ],
            "derivation": "explicit_text",
            "relation_type": "standard_constrains_action"
          },
          {
            "edge_id": "e3",
            "edge_type": "PRECEDES",
            "source": "P1",
            "target": "P2",
            "evidence_unit_ids": [
              "v7u_N000376"
            ],
            "derivation": "explicit_text"
          }
        ],
        "source_unit_ids": [
          "v7u_N000376"
        ],
        "candidate_status": "candidate",
        "review_notes": "增量命题：全球组织先以母国政策为基础标准，再根据东道国法律进行调整（顺序性）；KG不足：基础KG只能将该实践保存为一条事实，无法表达“先……然后……”的有向动作序列；选项判断：可据以判断或排除涉及全球化组织政策制定顺序的选项；LLM推理：无。"
      }
    ],
    "skip_reason": null
  }
}
```
