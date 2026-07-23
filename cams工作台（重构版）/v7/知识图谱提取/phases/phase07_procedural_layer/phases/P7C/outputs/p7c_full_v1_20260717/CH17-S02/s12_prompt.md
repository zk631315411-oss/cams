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

section_id: `CH17-S02`

section_title: `Providing financial services to embassies, foreign consulates, and missions > Drug-related businesses risks`

section_text_with_unit_anchors:

```text
[v7u_N001264|1264] Money laundering risks linked to drug-related businesses, particularly those involving substances such as cannabis and marijuana, present challenges for regulatory authorities, financial institutions, and the businesses themselves.
ZH: 毒品相关业务带来的洗钱风险。

[v7u_N001265|1265] These enterprises, even when engaged in the legitimate production, sale, and distribution of drugs for pharmaceutical purposes, can still encounter serious risks due to their ties to illicit activities.
ZH: 合法制药企业因与非法活动关联而面临严重风险。

[v7u_N001266|1266] The dual-use nature of these substances—permitted for medical or recreational purposes but also associated with illegal activities—complicates the detection and prevention of money laundering.
ZH: 物质的双重用途性质使洗钱检测和预防复杂化。

[v7u_N001267|1267] A major complication for financial institutions in banking cannabis businesses in some countries is that these businesses may be legally permitted at the state level but not at the federal level.
ZH: 大麻业务在州级合法但联邦级非法，给金融机构带来合规难题。

[v7u_N001268|1268] Drug-related products with legitimate pharmaceutical applications, such as CBD oils or medical marijuana, continue to pose a risk of diversion to the illegal market. Consequently, the production, trade, and distribution of these drugs often occur within a heavily regulated environment.
ZH: 具有合法用途的药物产品存在流向非法市场的风险，且受严格监管。

[v7u_N001269|1269] Governments impose sanctions on specific regions, entities, or countries involved in the drug trade in an attempt to thwart the proliferation of illegal drugs and related criminal activities.
ZH: 政府对参与毒品贸易的地区、实体或国家实施制裁以遏制非法毒品扩散。

[v7u_N001270|1270] Pharmaceutical companies engaged in legitimate production also need to navigate strict import/export controls and international restrictions.
ZH: 制药公司必须遵守严格的进出口管制和国际限制。

[v7u_N001271|1271] Sanctions-related risks emerge when participating in cross-border transactions with regions or countries subject to sanctions or embargoes.
ZH: 与受制裁地区或国家进行跨境交易会产生制裁相关风险。

[v7u_N001272|1272] Transactions in drug-related businesses can be highly complex, often involving multiple parties and jurisdictions along a convoluted chain of production, distribution, and sale. For instance, cannabis can be cultivated in one area, processed in another, and sold to consumers in yet another, with numerous intermediaries involved at each stage. This multi-layered approach can obscure illicit sources of funds.
ZH: 毒品相关交易涉及多方和多个司法管辖区，链条复杂，可能掩盖非法资金来源。

[v7u_N001273|1273] As a result, financial institutions might struggle to identify suspicious transactions, as they can be dispersed across different locations and stages of the business. Additionally, a high volume of transactions or transfers, sometimes involving shell companies or fictitious business partners, further complicates the tracking of illicit activities.
ZH: 金融机构难以识别分散在不同地点和业务阶段的可疑交易，壳公司等进一步增加追踪难度。
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N001267"
    ],
    "proposition": "大麻业务在州合法但联邦非法给金融机构带来合规难题。",
    "source_quotes": [
      "A major complication for financial institutions in banking cannabis businesses in some countries is that these businesses may be legally permitted at the state level but not at the federal level."
    ],
    "relation_cues": [
      "complication",
      "may",
      "not"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "大麻业务在州级合法但联邦级非法"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "金融机构面临合规难题",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001267",
        "quote": "A major complication for financial institutions in banking cannabis businesses in some countries is that these businesses may be legally permitted at the state level but not at the federal level."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N001269"
    ],
    "proposition": "政府对参与毒品贸易的地区、实体或国家实施制裁以遏制非法毒品扩散。",
    "source_quotes": [
      "Governments impose sanctions on specific regions, entities, or countries involved in the drug trade in an attempt to thwart the proliferation of illegal drugs and related criminal activities."
    ],
    "relation_cues": [
      "impose sanctions",
      "in an attempt to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "涉及毒品贸易的地区、实体或国家"
      ],
      "basis_or_condition": [
        "为遏制非法毒品扩散"
      ],
      "focal_handling_or_judgment": "政府实施制裁",
      "outcomes_or_paths": [
        "遏制非法毒品和相关犯罪"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001269",
        "quote": "Governments impose sanctions on specific regions, entities, or countries involved in the drug trade in an attempt to thwart the proliferation of illegal drugs and related criminal activities."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N001270"
    ],
    "proposition": "从事合法生产的制药公司必须遵守严格的进出口管制和国际限制。",
    "source_quotes": [
      "Pharmaceutical companies engaged in legitimate production also need to navigate strict import/export controls and international restrictions."
    ],
    "relation_cues": [
      "need to",
      "strict"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "从事合法生产的制药公司"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "必须遵守严格的进出口管制和国际限制",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001270",
        "quote": "Pharmaceutical companies engaged in legitimate production also need to navigate strict import/export controls and international restrictions."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N001271"
    ],
    "proposition": "与受制裁地区或国家进行跨境交易会产生制裁相关风险。",
    "source_quotes": [
      "Sanctions-related risks emerge when participating in cross-border transactions with regions or countries subject to sanctions or embargoes."
    ],
    "relation_cues": [
      "emerge when",
      "subject to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "参与跨边界交易与受制裁地区或国家"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "产生制裁相关风险",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001271",
        "quote": "Sanctions-related risks emerge when participating in cross-border transactions with regions or countries subject to sanctions or embargoes."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N001272",
      "v7u_N001273"
    ],
    "proposition": "由于交易复杂分散且涉及壳公司，金融机构可能难以识别可疑交易。",
    "source_quotes": [
      "Transactions in drug-related businesses can be highly complex, often involving multiple parties and jurisdictions along a convoluted chain of production, distribution, and sale.",
      "As a result, financial institutions might struggle to identify suspicious transactions, as they can be dispersed across different locations and stages of the business."
    ],
    "relation_cues": [
      "as a result",
      "might",
      "dispersed"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "毒品相关交易高度复杂，涉及多方和多个司法管辖区",
        "交易分散在不同地点和阶段"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "金融机构可能难以识别可疑交易",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001272",
        "quote": "Transactions in drug-related businesses can be highly complex, often involving multiple parties and jurisdictions along a convoluted chain of production, distribution, and sale."
      },
      {
        "unit_id": "v7u_N001273",
        "quote": "As a result, financial institutions might struggle to identify suspicious transactions, as they can be dispersed across different locations and stages of the business."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
