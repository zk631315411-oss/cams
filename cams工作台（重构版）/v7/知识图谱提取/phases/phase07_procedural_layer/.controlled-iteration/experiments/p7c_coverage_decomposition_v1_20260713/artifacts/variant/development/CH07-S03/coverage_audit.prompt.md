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
  "section_id": "CH07-S03",
  "section_title": "Money laundering risks associated with retail and commercial banking > Credit-related product risks",
  "base_kg_section_summary": {
    "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
    "covered_topics": [
      {
        "title_zh": "提前还贷作为洗钱手段",
        "title_en": "Early Loan Repayment as a Money Laundering Method",
        "covered_units": [
          {
            "unit_id": "v7u_N000552",
            "unit_type": "risk_indicator",
            "kg_role": "describes_process"
          }
        ]
      },
      {
        "title_zh": "关闭有未偿信贷账户的挑战",
        "title_en": "Challenges in Closing Accounts with Outstanding Credit Balances",
        "covered_units": [
          {
            "unit_id": "v7u_N000554",
            "unit_type": "fact",
            "kg_role": "indicates_risk"
          },
          {
            "unit_id": "v7u_N000555",
            "unit_type": "fact",
            "kg_role": "indicates_risk"
          },
          {
            "unit_id": "v7u_N000556",
            "unit_type": "fact",
            "kg_role": "states_consequence"
          },
          {
            "unit_id": "v7u_N000553",
            "unit_type": "classification",
            "kg_role": "provides_context"
          }
        ]
      }
    ],
    "covered_relations": [
      {
        "source_title": "提前还贷作为洗钱手段",
        "target_title": "关闭有未偿信贷账户的挑战",
        "relation_type": "prepares"
      }
    ]
  },
  "section_text_with_unit_anchors": "[v7u_N000546|546] Credit-related products are fundamental to customer propositions in retail and commercial banking.\nZH: 信贷相关产品是零售和商业银行客户服务的基础\n\n[v7u_N000547|547] Lending products, a subset of credit-related products, include personal loans, home ownership finance, and secured and unsecured loans.\nZH: 贷款产品包括个人贷款、住房融资及有担保和无担保贷款\n\n[v7u_N000548|548] Personal loans help banks build customer relationships, while home ownership finance and secured loans can be a significant source of revenue and capital, respectively.\nZH: 个人贷款有助于建立客户关系，住房融资和有担保贷款分别是重要的收入和资本来源\n\n[v7u_N000549|549] They are essential financial services that enable individuals and businesses to achieve their goals, drive economic growth, and promote financial stability.\nZH: 信贷相关产品是促进经济增长和金融稳定的基本金融服务\n\n[v7u_N000550|550] Secured and unsecured loans are crucial for businesses, offering the necessary capital to expand operations, invest in new projects, and manage cash flow effectively.\nZH: 有担保和无担保贷款为企业扩张、投资和现金流管理提供必要资本\n\n[v7u_N000551|551] However, credit-related products also present substantial money laundering risks.\nZH: 信贷相关产品也带来重大的洗钱风险\n\n[v7u_N000552|552] Early loan repayment is one method used by criminals to disguise the origin of illicit funds. By repaying loans ahead of schedule, criminals can convert illegal proceeds into ostensibly legitimate funds. This tactic complicates the detection of suspicious activity, as early repayments do not inherently indicate wrongdoing and can often be viewed as a sign of financial health.\nZH: 提前还贷是犯罪分子将非法资金伪装为合法资金的手段\n\n[v7u_N000553|553] Banks often face significant challenges when attempting to close customer accounts due to money laundering concerns, while the customer still owes money on credit-related products. One of the primary difficulties is the potential need to write off the loan balance, which creates a financial loss for the bank. This situation can lead to the following complications:\nZH: 因洗钱担忧关闭客户账户时，若客户仍有贷款余额，银行面临财务损失等挑战\n\n[v7u_N000554|554] Recovery of funds: If the bank knows or suspects the customer is using illicit funds to repay the loan, the risk of default becomes a secondary risk to manage. The bank should not accept funds for the purposes of loan\nZH: 若银行知道或怀疑客户使用非法资金还贷，不应接受该资金用于还贷\n\n[v7u_N000555|555] Risk appetite: When exiting customer relationships that fall outside the bank's risk tolerance, the loan balance complicates the process, as writing off a loan is a significant financial decision, often requiring extensive justification and approval.\nZH: 退出超出风险容忍度的客户关系时，贷款余额使核销成为重大财务决策\n\n[v7u_N000556|556] Reputational risk: Failure to effectively manage these challenges can damage the bank's reputation and erode trust with regulators and customers, impacting long-term business operations and compliance standing.\nZH: 未能有效管理这些挑战会损害银行声誉并削弱监管机构和客户的信任",
  "allowed_unit_ids": [
    "v7u_N000546",
    "v7u_N000547",
    "v7u_N000548",
    "v7u_N000549",
    "v7u_N000550",
    "v7u_N000551",
    "v7u_N000552",
    "v7u_N000553",
    "v7u_N000554",
    "v7u_N000555",
    "v7u_N000556"
  ],
  "original_json": {
    "section_id": "CH07-S03",
    "section_title": "Money laundering risks associated with retail and commercial banking > Credit-related product risks",
    "coverage_audit": [
      {
        "candidate_id": "cand_001",
        "unit_ids": [
          "v7u_N000552"
        ],
        "proposition": "提前还贷是犯罪分子将非法资金伪装为合法资金的手段",
        "decision": "kg_only",
        "card_id": null,
        "reason": "仅描述洗钱方法，无机构识别、评估或应对结构，基础KG可将其作为风险指标保存。"
      },
      {
        "candidate_id": "cand_002",
        "unit_ids": [
          "v7u_N000554"
        ],
        "proposition": "如果银行知道或怀疑客户使用非法资金还贷，则银行不应接受该资金用于还贷",
        "decision": "p7c_card",
        "card_id": "p7card_CH07-S03_001",
        "reason": "条件导向的明确应对动作，形成条件-禁止性行为的有向结构，超出基础KG的一般知识表达。"
      },
      {
        "candidate_id": "cand_003",
        "unit_ids": [
          "v7u_N000555"
        ],
        "proposition": "当退出超出风险容忍度的客户关系时，核销贷款通常需要充分理由和批准",
        "decision": "p7c_card",
        "card_id": "p7card_CH07-S03_002",
        "reason": "特定退出场景下核销动作的约束条件，形成有向的‘场景→动作约束’关系，基础KG无法表达该条件化链接。"
      },
      {
        "candidate_id": "cand_004",
        "unit_ids": [
          "v7u_N000553"
        ],
        "proposition": "因洗钱担忧关闭客户账户时，若客户仍有贷款余额，银行面临潜在核销和财务损失等挑战",
        "decision": "kg_only",
        "card_id": null,
        "reason": "仅陈述困难与后果，无明确动作或判断有向结构，属于背景性事实。"
      },
      {
        "candidate_id": "cand_005",
        "unit_ids": [
          "v7u_N000556"
        ],
        "proposition": "未能有效管理这些挑战会损害银行声誉并削弱监管机构和客户信任",
        "decision": "kg_only",
        "card_id": null,
        "reason": "一般风险后果陈述，无具体程序性或判断性有向链。"
      },
      {
        "candidate_id": "cand_006",
        "unit_ids": [
          "v7u_N000546",
          "v7u_N000547",
          "v7u_N000548",
          "v7u_N000549",
          "v7u_N000550",
          "v7u_N000551"
        ],
        "proposition": "信贷相关产品是基本金融服务，但也带来洗钱风险",
        "decision": "kg_only",
        "card_id": null,
        "reason": "主题引入与一般风险陈述，无局部程序性或判断性有向结构。"
      }
    ],
    "cards": [
      {
        "card_id": "p7card_CH07-S03_001",
        "section_id": "CH07-S03",
        "card_nature": "control",
        "title": "知道或怀疑非法资金还贷时银行不应接受还款",
        "flow_nodes": [
          {
            "node_id": "E1",
            "node_category": "entry",
            "node_type": "E8_decision_finding",
            "label": "银行知道或怀疑客户使用非法资金还贷",
            "evidence_unit_ids": [
              "v7u_N000554"
            ],
            "evidence_strength": "explicit"
          },
          {
            "node_id": "P1",
            "node_category": "process",
            "node_type": "P2_execution",
            "label": "银行不应接受该资金用于还贷",
            "evidence_unit_ids": [
              "v7u_N000554"
            ],
            "evidence_strength": "explicit"
          }
        ],
        "flow_edges": [
          {
            "edge_id": "E1_to_P1",
            "edge_type": "PRECEDES",
            "source": "E1",
            "target": "P1",
            "evidence_unit_ids": [
              "v7u_N000554"
            ],
            "derivation": "explicit_text",
            "condition": "银行知道或怀疑客户使用非法资金还贷",
            "source_quote": "If the bank knows or suspects the customer is using illicit funds to repay the loan, ... The bank should not accept funds for the purposes of loan"
          }
        ],
        "source_unit_ids": [
          "v7u_N000554"
        ],
        "candidate_status": "candidate",
        "review_notes": "增量命题：银行知道或怀疑非法资金还贷 → 银行不应接受该资金（条件触发禁止性动作）；KG不足：基础KG不能表达条件导向的具体应对动作的有向关系；选项判断：可确认在知道或怀疑非法资金时，银行应采取禁止接受还款的应对措施；LLM推理：无。"
      },
      {
        "card_id": "p7card_CH07-S03_002",
        "section_id": "CH07-S03",
        "card_nature": "control",
        "title": "退出超出风险容忍度的客户时核销贷款需充分理由和批准",
        "flow_nodes": [
          {
            "node_id": "P1",
            "node_category": "process",
            "node_type": "P2_execution",
            "label": "银行核销贷款",
            "evidence_unit_ids": [
              "v7u_N000555"
            ],
            "evidence_strength": "explicit"
          },
          {
            "node_id": "S1",
            "node_category": "auxiliary",
            "node_type": "standard",
            "label": "通常需要充分理由和批准",
            "evidence_unit_ids": [
              "v7u_N000555"
            ],
            "evidence_strength": "explicit"
          }
        ],
        "flow_edges": [
          {
            "edge_id": "P1_to_S1",
            "edge_type": "REFERENCES",
            "source": "P1",
            "target": "S1",
            "evidence_unit_ids": [
              "v7u_N000555"
            ],
            "derivation": "explicit_text",
            "relation_type": "standard_constrains_action",
            "condition": "退出超出风险容忍度的客户关系时",
            "source_quote": "When exiting customer relationships that fall outside the bank's risk tolerance, ... writing off a loan is a significant financial decision, often requiring extensive justification and approval."
          }
        ],
        "source_unit_ids": [
          "v7u_N000555"
        ],
        "candidate_status": "candidate",
        "review_notes": "增量命题：退出超出风险容忍度的客户时，银行核销贷款（动作）受约束于需要充分理由和批准（标准）；KG不足：基础KG可以表达核销需要理由这一事实，但不能表达该约束与特定退出场景的条件化关联；选项判断：可确认在退出超出容忍度的客户时，核销贷款需要额外审批要求；LLM推理：无。"
      }
    ],
    "skip_reason": null
  }
}
```
