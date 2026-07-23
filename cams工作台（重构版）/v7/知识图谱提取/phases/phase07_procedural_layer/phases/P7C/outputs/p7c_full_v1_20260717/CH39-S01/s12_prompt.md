<!-- allowed_unit_ids is intentionally not sent to the model. Unit IDs remain
     visible in section_text_with_unit_anchors and are validated by the Runner. -->

# P7C-S1.2 候选 Card Frame 独立补漏 v1

## 阶段角色

你是 **P7C-S1.2：候选 card frame 独立补漏器**。

S1.1 已经生成一组候选。你必须重新阅读完整 section，并将原文中所有可能合格的 frame 与 S1.1 候选逐项比较。只输出 S1.1 没有承接的候选；不得删除、改写或重复输出已有候选。

你不做 KG 边界裁决，不构建 flow node 或 flow edge，也不输出审核结论。你的输出与 S1.1 合并后才进入 S2。

## 候选 Card Frame 定义

候选 frame 是 section 内有原文证据支持的局部程序或判断单元。它围绕一个中心处理、判断、法律适用或归责组织；原文提供时，应同时纳入相关的触发/情境、输入/标准、依据/条件、结果、分支或后续行动。

```text
触发 / 情境 / 输入 / 标准 / 条件
                  -> 中心处理 / 判断 / 法律适用 / 归责
                  -> 结果 / 分支 / 后续行动
```

中心字段必有，且触发/依据/结果三类外围角色中至少有一类。上述概念图不要求三段齐全：原文仅支持“标准或条件 -> 具体处理/判断”，或“调查/审查动作 -> 发现/结论”时，允许开放候选，不得补造入口或出口。

这里的有向关系不等于时间顺序或因果关系，也可以是条件、判断标准、处理所参照的输入、法律适用、分支或反馈。必须保留原文中的 if、when、unless、may、might、could、should、must、only、not 等限定。

## 独立扫描与比对

在内部完成以下步骤，不输出扫描台账或推理过程：

1. 按自然段、主体变化、对象变化、案例事实、调查或审查动作、法律规则、条件、结果和例外扫描完整 section，先独立识别全部潜在 frame。
2. 围绕中心处理或判断组织 frame。前文已有候选不能成为停止扫描后文的理由。
3. 将每个独立识别的 frame 与全部 S1.1 候选比较。核心处理/判断及其关键证据已被同一候选覆盖时，视为已承接；只有主题相同但遗漏独立处置链、法律适用链或调查发现链时，仍视为缺口。
4. 只为未承接的 frame 输出 gap proposition。

## 必须识别的候选类型

- **同中心判断链**：同一对象的输入、计算、适用标准和正反结果应合并。例如，直接持股、间接持股、适用阈值与是否认定 UBO 属于同一判断 frame。
- **阈值设定与阈值适用**：风险为本地设定或调整阈值，与使用既有阈值判断具体对象，是不同中心，可以分别形成候选。
- **案例法律适用链**：案件事实、主体关系、地点或指控引发法律适用、管辖、责任或监管关切时，应输出“案例情境 -> 法律适用/归责判断 -> 原文结果（如有）”。通用法律规则不能替代案例中的实际适用候选。
- **调查发现链**：具名主体进行调查、审查、审计、筛查、分析或跟进并得出发现、结论、分类或升级时，应输出“调查/判断动作 -> 发现/结论”。
- **条件处置链**：if、when、unless、requires 等条件导向特定动作、禁止、批准、升级或结果时，应保留条件和情态。

## 不构成候选的内容

不输出纯定义、分类、产品列表、控制组成列表、孤立阈值、孤立红旗、普通案例事实或没有特定判断/应对的一般机制。

正例：

- `分析师初步调查 -> 发现高风险中间人安排`
- `案例主体关系和指控 -> 引发域外法律适用关切`
- `退出超出风险容忍度且仍有贷款余额的客户 -> 核销通常需要充分理由和批准`

反例：

- `公司使用中间人`
- `犯罪分子通过复杂网络洗钱`
- `受益所有权阈值通常为25%`

这些事实若没有原文中的机构动作、适用判断、条件化结果或特定应对，不单独形成候选。

## 合并边界

- 围绕同一中心处理/判断、同一对象且能由原文直接连读的材料合并为一个 frame。
- 不同中心处理/判断、不同业务目标或没有原文连接的材料分开。
- 只有相邻文本不足以跨 unit 合并；必须存在连接词、指代、共享中心判断或可验证的规则与正反例证据链。
- 不得仅换一种措辞重复 S1.1 候选。

## 证据合同

`section_text_with_unit_anchors`是唯一事实证据。只能引用锚点中可见的 unit ID。

- 每个`unit_id`必须由`evidence_spans`中的一项覆盖。
- 每个`evidence_spans.quote`必须是对应 unit 中精确、连续、可定位的原文短引。
- 每个`source_quotes`条目必须与某个`evidence_spans.quote`完全一致。
- `relation_cues`保留原文关系词；没有字面连接词时，填写能够体现原文关系的短语，不得留空。
- 只有跨 unit 归纳规则及其正反例时，`induction`填写`cross_unit`，并在`cross_unit_basis`中列出规则、正例和反例 unit；否则两者均为`null`。

## 输出 Contract

只输出严格 JSON。顶层字段为`section_id`和`gap_propositions`。

每个 gap proposition 必须保留 S1.1 的全部字段，并增加`gap_evidence`：

```json
{
  "section_id": "CH07-S03",
  "gap_propositions": [
    {
      "candidate_id": "s1c_gap_ch07_s03_writeoff_approval",
      "unit_ids": ["v7u_N000555"],
      "proposition": "退出超出银行风险容忍度且仍有贷款余额的客户关系时，核销贷款通常需要充分理由和批准。",
      "source_quotes": [
        "When exiting customer relationships that fall outside the bank's risk tolerance, the loan balance complicates the process, as writing off a loan is a significant financial decision, often requiring extensive justification and approval."
      ],
      "relation_cues": ["When", "requiring"],
      "candidate_frame": {
        "trigger_or_context": ["退出超出银行风险容忍度且仍有贷款余额的客户关系"],
        "basis_or_condition": ["核销是重大财务决策"],
        "focal_handling_or_judgment": "决定是否核销贷款余额并履行相应审批要求",
        "outcomes_or_paths": ["核销通常需要充分理由和批准"]
      },
      "evidence_spans": [
        {
          "unit_id": "v7u_N000555",
          "quote": "When exiting customer relationships that fall outside the bank's risk tolerance, the loan balance complicates the process, as writing off a loan is a significant financial decision, often requiring extensive justification and approval."
        }
      ],
      "induction": null,
      "cross_unit_basis": null,
      "gap_evidence": {
        "compared_with_candidate_ids": ["s1c_ch07_s03_illicit_repayment"],
        "gap_reason": "已有候选只承接怀疑非法资金还贷时不得接受资金，没有承接退出客户且仍有贷款余额时核销通常需要理由和批准这一独立处置链。"
      }
    }
  ]
}
```

`candidate_id`必须以`s1c_gap_`开头，且不得与 S1.1 ID 重复。

`gap_evidence.compared_with_candidate_ids`只能引用输入中的 S1.1 候选 ID；S1.1 列表非空时至少列出一个最相关候选。若 S1.1 为空，可以使用空数组。`gap_reason`必须用中文说明缺失的中心处理/判断及已有候选为何没有承接。

如果独立扫描后确认没有遗漏，输出：

```json
{"section_id":"<section_id>","gap_propositions":[]}
```

## 当前section

section_id: `CH39-S01`

section_title: `Customer risk assessment versus enterprise-wide risk assessment`

section_text_with_unit_anchors:

```text
[v7u_N002842|2842] The CRA evaluates potential ML/TF risks associated with individual customers and business relationships. In contrast, the EWRA analyzes ML/TF risks that the organization as a whole faces.
ZH: 客户风险评估（CRA）与全机构风险评估（EWRA）的范围区别

[v7u_N002843|2843] According to FinCEN’s Assessing Customer Relationships and Conducting Customer Due Diligence, customer relationships present varying levels of financial crime risks.
ZH: FinCEN指出客户关系存在不同程度的金融犯罪风险

[v7u_N002844|2844] Organizations conduct CRAs to identify risk factors, assign risk ratings to customers, create risk profiles, and decide which level of CDD to apply.
ZH: 客户风险评估（CRA）用于识别风险因素、分配评级并决定客户尽职调查等级

[v7u_N002845|2845] The CRA considers information collected through KYC processes, such as documents, customer business activity, and requested products.
ZH: CRA考虑通过了解你的客户流程收集的客户信息

[v7u_N002846|2846] Higher-risk customers might require EDD, while lower-risk customers might qualify for simplified due diligence (SDD) in some jurisdictions.
ZH: 高风险客户需强化尽职调查（EDD），低风险客户可适用简化尽职调查（SDD）

[v7u_N002847|2847] Due diligence requirements vary depending on the jurisdiction.
ZH: 尽职调查要求因司法管辖区而异

[v7u_N002848|2848] The EWRA identifies inherent risks, assesses controls, and determines the residual risk that the organization faces. The process helps organizations design their AML/CFT framework, guides policy and procedure development, allocates resources toward higher-risk areas, and improves decision-making.
ZH: 全机构风险评估（EWRA）识别固有风险、评估控制并确定剩余风险，指导反洗钱/反恐怖融资框架设计

[v7u_N002849|2849] A product risk assessment helps organizations identify and understand the risks and threats associated with their financial products. It assesses how criminals might use these products to launder illicit funds. After identifying and assessing these risks and threats, organizations can implement measures to mitigate them.
ZH: 产品风险评估帮助识别金融产品相关的洗钱风险并制定缓释措施

[v7u_N002850|2850] To identify and understand risks, organizations should consider factors, including:
ZH: 组织应考虑多种因素以识别和理解风险

[v7u_N002851|2851] Inherent product characteristics: Features or attributes such as crossborder wire payments, third-party payments, anonymity, remote access, third-party access, unusual complexity and structure, minimal transaction oversight, and cash-intensive nature.
ZH: 固有产品特征包括跨境支付、匿名性、远程访问等风险属性

[v7u_N002852|2852] Transactional patterns of the product: Recurring behaviors and trends such as rapid movements, high volumes, frequent transactions, involvement of high-risk or sanctioned jurisdictions, and use by high-risk customers in high-risk sectors.
ZH: 产品交易模式包括快速流动、高交易量、涉及高风险司法管辖区等风险指标

[v7u_N002853|2853] Each product should receive a risk score based on the AML/CFT risks it presents.
ZH: 每个产品应根据其反洗钱/反恐怖融资风险获得风险评分

[v7u_N002854|2854] A clear, documented definition of each product and its risks helps organizations assess them appropriately.
ZH: 清晰记录每个产品的定义和风险有助于适当评估

[v7u_N002855|2855] Identified risks affect the EWRA and the RAS.
ZH: 已识别的风险影响全机构风险评估（EWRA）和风险偏好声明（RAS）

[v7u_N002856|2856] For example, if many products are deemed high-risk, this raises the overall EWRA risk score, prompting additional controls or measures.
ZH: 若多个产品被认定为高风险，将提高EWRA评分并触发额外控制措施

[v7u_N002857|2857] If a product’s risk assessment score exceeds the RAS, the organization might cease offering it.
ZH: 若产品风险评估得分超过风险偏好，组织可能停止提供该产品

[v7u_N002858|2858] A product risk assessment is also very useful in designing controls such as transaction monitoring to ensure adequate coverage of all products.
ZH: 产品风险评估有助于设计交易监控等控制措施以确保充分覆盖

[v7u_N002859|2859] Although the product risk assessment process might vary, depending on the organization’s size, it typically includes:
ZH: 产品风险评估流程因组织规模而异，通常包括以下步骤

[v7u_N002860|2860] Product development: Designs the product and provides specifications.
ZH: 产品开发部门设计产品并提供规格说明

[v7u_N002861|2861] IT: Provides necessary technological infrastructure.
ZH: IT部门为风险评估提供必要的技术基础设施。

[v7u_N002862|2862] Operations: Provides insights about product usage patterns
ZH: 运营部门提供产品使用模式的洞察。

[v7u_N002863|2863] Compliance: Identifies control measures and ensures compliance.
ZH: 合规部门识别控制措施并确保合规。

[v7u_N002864|2864] Legal: Provides legal assistance on applicable laws.
ZH: 法律部门就适用法律提供法律协助。

[v7u_N002865|2865] Compliance officers play an active role in overseeing the product risk assessment. They identify risks, assess relevant controls, and assign appropriate risk scores.
ZH: 合规官在产品风险评估中发挥积极作用，识别风险、评估控制并分配风险评分。

[v7u_N002866|2866] Because risk assessment is an ongoing process, organizations should review both new and existing products regularly. For new products, the assessment should be conducted before they are offered to customers. Once the product becomes available, it should be reviewed periodically and whenever significant product changes occur.
ZH: 组织应定期审查新产品和现有产品，新产品在推出前应进行评估，之后定期审查并在重大变更时审查。

[v7u_N002867|2867] A clear and well-structured risk assessment helps identify vulnerabilities and exposures.
ZH: 清晰且结构良好的风险评估有助于识别漏洞和风险敞口。

[v7u_N002868|2868] Sometimes, organizations might notice previously unidentified risks for a new or existing product.
ZH: 组织可能注意到新产品或现有产品中先前未识别的风险。

[v7u_N002869|2869] For example, a new prepaid card might show high volumes of rapid transactions from high-risk customers.
ZH: 例如，新的预付卡可能显示来自高风险客户的高频交易。

[v7u_N002870|2870] This might require revisiting the product risk assessment and setting thresholds for the number of transactions, volumes, or restricting the product to certain customer sectors.
ZH: 可能需要重新审视产品风险评估并设定交易数量、金额阈值或限制产品面向特定客户群体。
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002844",
      "v7u_N002845",
      "v7u_N002846"
    ],
    "proposition": "组织进行客户风险评估（CRA）以识别风险因素、分配风险评级并决定适用的客户尽职调查（CDD）等级：高风险客户可能需要强化尽职调查（EDD），低风险客户可能适用简化尽职调查（SDD）。",
    "source_quotes": [
      "Organizations conduct CRAs to identify risk factors, assign risk ratings to customers, create risk profiles, and decide which level of CDD to apply.",
      "The CRA considers information collected through KYC processes, such as documents, customer business activity, and requested products.",
      "Higher-risk customers might require EDD, while lower-risk customers might qualify for simplified due diligence (SDD) in some jurisdictions."
    ],
    "relation_cues": [
      "to",
      "decide",
      "might require",
      "might qualify"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "客户关系存在不同程度的金融犯罪风险"
      ],
      "basis_or_condition": [
        "通过KYC流程收集的信息"
      ],
      "focal_handling_or_judgment": "进行客户风险评估，识别风险因素并分配风险评级",
      "outcomes_or_paths": [
        "高风险客户需EDD",
        "低风险客户可适用SDD"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002844",
        "quote": "Organizations conduct CRAs to identify risk factors, assign risk ratings to customers, create risk profiles, and decide which level of CDD to apply."
      },
      {
        "unit_id": "v7u_N002845",
        "quote": "The CRA considers information collected through KYC processes, such as documents, customer business activity, and requested products."
      },
      {
        "unit_id": "v7u_N002846",
        "quote": "Higher-risk customers might require EDD, while lower-risk customers might qualify for simplified due diligence (SDD) in some jurisdictions."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002848"
    ],
    "proposition": "全机构风险评估（EWRA）识别固有风险、评估控制并确定剩余风险，进而指导AML/CFT框架设计、政策程序开发、资源分配和改进决策。",
    "source_quotes": [
      "The EWRA identifies inherent risks, assesses controls, and determines the residual risk that the organization faces. The process helps organizations design their AML/CFT framework, guides policy and procedure development, allocates resources toward higher-risk areas, and improves decision-making."
    ],
    "relation_cues": [
      "identifies",
      "assesses",
      "determines",
      "helps",
      "guides",
      "allocates",
      "improves"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "组织面临固有风险"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "进行全机构风险评估，识别固有风险、评估控制并确定剩余风险",
      "outcomes_or_paths": [
        "设计AML/CFT框架",
        "指导政策程序开发",
        "向高风险领域分配资源",
        "改进决策"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002848",
        "quote": "The EWRA identifies inherent risks, assesses controls, and determines the residual risk that the organization faces. The process helps organizations design their AML/CFT framework, guides policy and procedure development, allocates resources toward higher-risk areas, and improves decision-making."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002849",
      "v7u_N002853",
      "v7u_N002854",
      "v7u_N002858",
      "v7u_N002865"
    ],
    "proposition": "产品风险评估识别和理解产品风险与威胁，对每个产品基于AML/CFT风险分配风险评分，合规官识别风险、评估控制并分配评分，并据此设计交易监控等控制措施。",
    "source_quotes": [
      "A product risk assessment helps organizations identify and understand the risks and threats associated with their financial products. It assesses how criminals might use these products to launder illicit funds. After identifying and assessing these risks and threats, organizations can implement measures to mitigate them.",
      "Each product should receive a risk score based on the AML/CFT risks it presents.",
      "A clear, documented definition of each product and its risks helps organizations assess them appropriately.",
      "A product risk assessment is also very useful in designing controls such as transaction monitoring to ensure adequate coverage of all products.",
      "Compliance officers play an active role in overseeing the product risk assessment. They identify risks, assess relevant controls, and assign appropriate risk scores."
    ],
    "relation_cues": [
      "helps",
      "should receive",
      "useful in designing",
      "assign"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "金融产品存在风险与威胁"
      ],
      "basis_or_condition": [
        "产品定义及风险文档"
      ],
      "focal_handling_or_judgment": "进行产品风险评估，识别风险、分配风险评分",
      "outcomes_or_paths": [
        "实施风险缓释措施",
        "设计交易监控等控制措施"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002849",
        "quote": "A product risk assessment helps organizations identify and understand the risks and threats associated with their financial products. It assesses how criminals might use these products to launder illicit funds. After identifying and assessing these risks and threats, organizations can implement measures to mitigate them."
      },
      {
        "unit_id": "v7u_N002853",
        "quote": "Each product should receive a risk score based on the AML/CFT risks it presents."
      },
      {
        "unit_id": "v7u_N002854",
        "quote": "A clear, documented definition of each product and its risks helps organizations assess them appropriately."
      },
      {
        "unit_id": "v7u_N002858",
        "quote": "A product risk assessment is also very useful in designing controls such as transaction monitoring to ensure adequate coverage of all products."
      },
      {
        "unit_id": "v7u_N002865",
        "quote": "Compliance officers play an active role in overseeing the product risk assessment. They identify risks, assess relevant controls, and assign appropriate risk scores."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N002855",
      "v7u_N002856"
    ],
    "proposition": "产品风险评估中若许多产品被认定为高风险，则提高全机构风险评估（EWRA）评分，并触发额外控制措施。",
    "source_quotes": [
      "Identified risks affect the EWRA and the RAS.",
      "For example, if many products are deemed high-risk, this raises the overall EWRA risk score, prompting additional controls or measures."
    ],
    "relation_cues": [
      "affect",
      "if",
      "raises",
      "prompting"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "产品风险评估中多个产品被认定为高风险"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "多个产品高风险时提高EWRA风险评分",
      "outcomes_or_paths": [
        "触发额外控制或措施"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002855",
        "quote": "Identified risks affect the EWRA and the RAS."
      },
      {
        "unit_id": "v7u_N002856",
        "quote": "For example, if many products are deemed high-risk, this raises the overall EWRA risk score, prompting additional controls or measures."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N002857"
    ],
    "proposition": "若产品风险评估得分超过风险偏好声明（RAS），组织可能停止提供该产品。",
    "source_quotes": [
      "If a product’s risk assessment score exceeds the RAS, the organization might cease offering it."
    ],
    "relation_cues": [
      "If",
      "exceeds",
      "might"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "产品风险评估得分超过RAS"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "判断产品是否因风险过高而需停止提供",
      "outcomes_or_paths": [
        "可能停止提供该产品"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002857",
        "quote": "If a product’s risk assessment score exceeds the RAS, the organization might cease offering it."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N002866"
    ],
    "proposition": "组织应定期审查新产品和现有产品：新产品在推出前应进行评估，之后定期审查，并在发生重大产品变更时审查。",
    "source_quotes": [
      "Because risk assessment is an ongoing process, organizations should review both new and existing products regularly. For new products, the assessment should be conducted before they are offered to customers. Once the product becomes available, it should be reviewed periodically and whenever significant product changes occur."
    ],
    "relation_cues": [
      "should review",
      "should be conducted",
      "should be reviewed"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "新产品推出前或产品发生重大变更时"
      ],
      "basis_or_condition": [
        "风险评估是一个持续过程"
      ],
      "focal_handling_or_judgment": "对产品进行定期审查与评估",
      "outcomes_or_paths": [
        "新产品在推出前评估",
        "现有产品定期审查",
        "重大变更时审查"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002866",
        "quote": "Because risk assessment is an ongoing process, organizations should review both new and existing products regularly. For new products, the assessment should be conducted before they are offered to customers. Once the product becomes available, it should be reviewed periodically and whenever significant product changes occur."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_007",
    "unit_ids": [
      "v7u_N002868",
      "v7u_N002869",
      "v7u_N002870"
    ],
    "proposition": "若发现新产品或现有产品存在先前未识别的风险（如高风险客户的高频交易），可能需要重新审视产品风险评估并设定交易数量、金额阈值或限制产品面向特定客户群体。",
    "source_quotes": [
      "Sometimes, organizations might notice previously unidentified risks for a new or existing product.",
      "For example, a new prepaid card might show high volumes of rapid transactions from high-risk customers.",
      "This might require revisiting the product risk assessment and setting thresholds for the number of transactions, volumes, or restricting the product to certain customer sectors."
    ],
    "relation_cues": [
      "might notice",
      "might require",
      "revisiting",
      "setting"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "发现新产品或现有产品存在先前未识别的风险"
      ],
      "basis_or_condition": [
        "例如高风险客户的高频交易"
      ],
      "focal_handling_or_judgment": "重新审视产品风险评估并调整阈值或限制",
      "outcomes_or_paths": [
        "设定交易数量/金额阈值",
        "限制产品面向特定客户群体"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002868",
        "quote": "Sometimes, organizations might notice previously unidentified risks for a new or existing product."
      },
      {
        "unit_id": "v7u_N002869",
        "quote": "For example, a new prepaid card might show high volumes of rapid transactions from high-risk customers."
      },
      {
        "unit_id": "v7u_N002870",
        "quote": "This might require revisiting the product risk assessment and setting thresholds for the number of transactions, volumes, or restricting the product to certain customer sectors."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
