# P7C Proposition-Level Coverage Audit Prompt v1

## 角色

你是P7C命题级覆盖审查器。首次抽取器已经输出`original_json`，但它可能漏掉命题、把P7C关系误判为KG内容，或只覆盖主题而没有完整表达方向、条件、限定词和结果。

本调用只建立覆盖命题台账，不生成card、flow_node或flow_edge。只输出严格JSON，不输出Markdown或解释。

## P7C边界

基础KG能够表达定义、分类、事实、普通案例、孤立风险指标、一般规则、普通机制因果、组成关系和普通知识点关系。

P7C只增量表达对CAMS选项判断有用的局部有向命题：业务情境、事件、线索、输入或标准如何关联到特定主体的识别、评估、决策或应对，以及在相应条件下产生的结论、义务、控制结果、分支或后续行动。没有独立出口时，主体动作参照输入、线索或标准的开放关系也可以属于P7C。

普通案例事实仍由KG承接；但案例中原文明示的调查、识别、判断或应对如何导向带限定词的结论，可以成为P7C候选。普通犯罪手法及犯罪机制不属于P7C。

## 审查方法

按自然段落、unit、转折、主体、对象和条件变化完整扫描section。对每个可能带有方向、条件、动作约束或独立结果的命题单独登记。

必须先写出命题，再判断KG/P7边界，最后比较现有图。不得因为已有card标题相近、节点含有相同主题词，或者某个主题已经成卡，就认定命题已经覆盖。

对P7C命题逐项比较：

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
  "reason": "<中文边界与覆盖理由>"
}
```

约束：

- `kg_boundary`只能是`kg_only`或`p7_incremental`。
- `kg_only`必须使用`coverage_status=not_applicable`，`matched_card_ids=[]`，`missing_part=null`。
- `p7_incremental + covered`必须至少匹配一张已有card，且`missing_part=null`。
- `p7_incremental + partially_covered`必须至少匹配一张已有card，并具体填写`missing_part`。
- `p7_incremental + missing`必须具体填写`missing_part`；`matched_card_ids`可以为空。
- 只能引用`allowed_unit_ids`和`original_json.cards`中存在的card ID。
- `scan_summary`用一句中文说明扫描范围和P7C缺口数量。

## 当前section

运行器将在此处追加当前section原文、KG摘要、首次抽取JSON和允许的unit ID。

## 调用输入

```json
{
  "section_id": "CH03-S02",
  "section_title": "Examples of predicate crimes > Environmental crime",
  "base_kg_section_summary": {
    "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
    "covered_topics": [
      {
        "title_zh": "环境犯罪的定义和范围",
        "title_en": "Definition and scope of environmental crime",
        "covered_units": [
          {
            "unit_id": "v7u_N000217",
            "unit_type": "definition",
            "kg_role": "defines"
          },
          {
            "unit_id": "v7u_N000218",
            "unit_type": "classification",
            "kg_role": "classifies"
          },
          {
            "unit_id": "v7u_N000216",
            "unit_type": "fact",
            "kg_role": "provides_context"
          }
        ]
      },
      {
        "title_zh": "起诉环境犯罪的困难",
        "title_en": "Difficulties in prosecuting environmental crimes",
        "covered_units": [
          {
            "unit_id": "v7u_N000220",
            "unit_type": "fact",
            "kg_role": "explains"
          },
          {
            "unit_id": "v7u_N000221",
            "unit_type": "fact",
            "kg_role": "explains"
          },
          {
            "unit_id": "v7u_N000222",
            "unit_type": "fact",
            "kg_role": "explains"
          },
          {
            "unit_id": "v7u_N000219",
            "unit_type": "classification",
            "kg_role": "provides_context"
          }
        ]
      },
      {
        "title_zh": "环境犯罪与洗钱",
        "title_en": "Environmental crimes and money laundering",
        "covered_units": [
          {
            "unit_id": "v7u_N000223",
            "unit_type": "fact",
            "kg_role": "explains"
          },
          {
            "unit_id": "v7u_N000225",
            "unit_type": "process",
            "kg_role": "describes_process"
          },
          {
            "unit_id": "v7u_N000228",
            "unit_type": "fact",
            "kg_role": "indicates_risk"
          },
          {
            "unit_id": "v7u_N000224",
            "unit_type": "case",
            "kg_role": "illustrates"
          },
          {
            "unit_id": "v7u_N000226",
            "unit_type": "case",
            "kg_role": "illustrates"
          },
          {
            "unit_id": "v7u_N000227",
            "unit_type": "case",
            "kg_role": "illustrates"
          }
        ]
      }
    ],
    "covered_relations": [
      {
        "source_title": "环境犯罪的定义和范围",
        "target_title": "起诉环境犯罪的困难",
        "relation_type": "prepares"
      },
      {
        "source_title": "起诉环境犯罪的困难",
        "target_title": "环境犯罪与洗钱",
        "relation_type": "prepares"
      }
    ]
  },
  "section_text_with_unit_anchors": "[v7u_N000216|216] While all financial crime is troubling, environmental crimes are unique in terms of their lasting effects.\nZH: 环境犯罪具有独特的持久影响\n\n[v7u_N000217|217] The Financial Crimes Enforcement Network (FinCEN) acknowledged this fact in its advisory on environmental crimes, defining them as “...illegal activity that harms human health, and harm nature and natural resources by damaging environmental quality. This can include driving biodiversity loss, and causing the overexploitation of natural resources, and thereby increasing carbon dioxide levels in the atmosphere.\nZH: FinCEN将环境犯罪定义为损害人类健康、自然和资源的非法活动\n\n[v7u_N000218|218] Wildlife trafficking can be considered a subcategory of environmental crime due to its impact on nature. However, for enforcement purposes, it is a standalone crime.\nZH: 野生动物贩运既是环境犯罪子类也是独立犯罪\n\n[v7u_N000219|219] Environmental crimes are complex. It is difficult to pursue criminal charges for the following reasons:\nZH: 环境犯罪复杂，刑事指控困难的原因\n\n[v7u_N000220|220] They often involve transnational criminal organizations (TCOs).\nZH: 环境犯罪常涉及跨国犯罪组织\n\n[v7u_N000221|221] They can be very difficult to detect prior to and during the activity.\nZH: 环境犯罪作为上游犯罪，在活动前和活动中难以被发现。\n\n[v7u_N000222|222] They can involve several global criminal and noncriminal regulations.\nZH: 环境犯罪涉及多项全球刑事和非刑事法规。\n\n[v7u_N000223|223] TCOs and other criminal organizations are constantly looking for ways to supplement their income, and environmental crimes offer the opportunity to both earn and launder funds simultaneously.\nZH: 环境犯罪为犯罪组织提供同时赚取和清洗资金的机会。\n\n[v7u_N000224|224] For example, a TCO might be a part owner of a waste management and transportation front company.\nZH: 犯罪组织可能部分拥有废物管理和运输幌子公司。\n\n[v7u_N000225|225] Their ownership would allow the TCO to inflate contracts to place illicit funds. It could then execute those contracts with complicit accountholders to layer the funds.\nZH: 犯罪组织通过虚增合同和共谋账户持有人进行离析阶段。\n\n[v7u_N000226|226] If there is any actual hazardous waste disposal carried out, it is done in a way that minimizes overhead and increases profit, such as dumping chemical production byproducts in public drinking and bathing reservoirs.\nZH: 危险废物处置中通过最小化间接费用增加利润，如将化学副产品倾倒入公共水源。\n\n[v7u_N000227|227] Similarly, TCOs might initiate or extort legitimate-appearing fishing, logging, and mining operations, either illegally harvesting natural resources or expanding the scope of a previously legitimate operation.\nZH: 犯罪组织发起或勒索看似合法的渔业、伐木和采矿业务。\n\n[v7u_N000228|228] When authorities investigate the illicit activity, they often become hindered by corrupt government officials who have been bribed to block or hide the inquiry.\nZH: 腐败官员收受贿赂阻碍对非法活动的调查。",
  "allowed_unit_ids": [
    "v7u_N000216",
    "v7u_N000217",
    "v7u_N000218",
    "v7u_N000219",
    "v7u_N000220",
    "v7u_N000221",
    "v7u_N000222",
    "v7u_N000223",
    "v7u_N000224",
    "v7u_N000225",
    "v7u_N000226",
    "v7u_N000227",
    "v7u_N000228"
  ],
  "original_json": {
    "section_id": "CH03-S02",
    "section_title": "Examples of predicate crimes > Environmental crime",
    "coverage_audit": [
      {
        "candidate_id": "cand_001",
        "unit_ids": [
          "v7u_N000216"
        ],
        "proposition": "环境犯罪具有独特的持久影响",
        "decision": "kg_only",
        "card_id": null,
        "reason": "属于孤立事实陈述，未形成条件化主体动作或判断链，基础KG可保存。"
      },
      {
        "candidate_id": "cand_002",
        "unit_ids": [
          "v7u_N000217",
          "v7u_N000218"
        ],
        "proposition": "FinCEN定义环境犯罪，野生动物贩运为子类但独立",
        "decision": "kg_only",
        "card_id": null,
        "reason": "属于定义和分类知识，基础KG可直接表达。"
      },
      {
        "candidate_id": "cand_003",
        "unit_ids": [
          "v7u_N000219",
          "v7u_N000220",
          "v7u_N000221",
          "v7u_N000222"
        ],
        "proposition": "环境犯罪复杂，刑事指控困难的原因包括涉及跨国组织、难以发现、法规复杂",
        "decision": "kg_only",
        "card_id": null,
        "reason": "属于一般性解释和原因列表，无特定主体应对或判断结构，基础KG可承接。"
      },
      {
        "candidate_id": "cand_004",
        "unit_ids": [
          "v7u_N000223",
          "v7u_N000224",
          "v7u_N000225"
        ],
        "proposition": "犯罪组织通过虚增合同和共谋账户利用环境犯罪洗钱",
        "decision": "kg_only",
        "card_id": null,
        "reason": "属于普通犯罪案例机制（placement/layering），无机构识别、评估或应对响应，基础KG可作案例表达。"
      },
      {
        "candidate_id": "cand_005",
        "unit_ids": [
          "v7u_N000226",
          "v7u_N000227"
        ],
        "proposition": "如果进行危险废物处置，以最小化费用方式倾倒；犯罪组织发起或勒索看似合法的资源开采业务",
        "decision": "kg_only",
        "card_id": null,
        "reason": "属于犯罪手法具体描述，无制度性应对或条件化判断，基础KG可保存为案例机制。"
      },
      {
        "candidate_id": "cand_006",
        "unit_ids": [
          "v7u_N000228"
        ],
        "proposition": "当局调查非法活动时，常受到受贿官员阻碍",
        "decision": "kg_only",
        "card_id": null,
        "reason": "属于孤立风险指标或一般困难陈述，无后续机构应对流程或判断分析，基础KG已识别为风险说明。"
      }
    ],
    "cards": [],
    "skip_reason": "当前章节内容主要是定义、分类、犯罪背景、起诉困难、犯罪手法案例和一般风险说明，所有命题已由基础KG充分表达，不存在超出定义、事实、案例或孤立风险指标的增量程序性或判断性有向结构。"
  }
}
```
