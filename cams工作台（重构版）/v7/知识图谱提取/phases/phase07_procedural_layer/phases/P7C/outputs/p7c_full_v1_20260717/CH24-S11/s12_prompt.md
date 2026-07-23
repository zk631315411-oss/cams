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

section_id: `CH24-S11`

section_title: `US AML/CFT regulatory landscape > Local AML regulations and crossjurisdictional impact`

section_text_with_unit_anchors:

```text
[v7u_N001846|1846] An international financial institution often experiences complex operating environments. One of the operational challenges is the implementation of its AML program in all its locations. In this context, the interplay between a global, group-wide AML program and the local AML regulations is vital.
ZH: 国际金融机构在各地实施反洗钱计划面临全球政策与当地法规协调的挑战。

[v7u_N001847|1847] For example, the Bank Secrecy Act, which is the primary AML law in the US, requires compliance from US branches of foreign financial institutions. This means foreign financial institutions must ensure that their group-wide policies meet the Bank Secrecy Act’s minimum standards.
ZH: 外国金融机构的美国分行须遵守《银行保密法》的最低标准。

[v7u_N001848|1848] This presents a challenge because AML standards vary across jurisdictions.
ZH: 不同司法管辖区的反洗钱标准存在差异，带来合规挑战。

[v7u_N001849|1849] To address potential differences in regulations, international financial institutions often attach jurisdiction-specific addenda to their group-wide AML policy.
ZH: 国际金融机构常为集团反洗钱政策附加特定司法管辖区的附录。

[v7u_N001850|1850] If a jurisdiction in which a financial institution operates has a higher AML standard than its home jurisdiction, the financial institution should document this in the addendum.
ZH: 若当地反洗钱标准高于母国，金融机构应在附录中记录更高标准。

[v7u_N001851|1851] For example, from 2012 to 2018, Hong Kong had a more stringent beneficial ownership identification rule of 10%, while the US’s rule was 25%. As a result, all international US banks operating in Hong Kong documented the higher standard in a Hong Kong-specific addendum.
ZH: 香港曾实行10%受益所有人识别规则，高于美国25%标准，国际银行需附加香港附录。

[v7u_N001852|1852] Information sharing within an international financial institution is another key to the success of its AML mandate.
ZH: 国际金融机构内部信息共享是反洗钱任务成功的关键。

[v7u_N001853|1853] Nevertheless, an international financial institution might encounter challenges pertaining to banking secrecy and data protection laws, such as FATF’s guidance document.
ZH: 银行保密和数据保护法律可能对信息共享构成挑战。

[v7u_N001854|1854] FATF’s Recommendation 18 stipulates that where local applicable laws and regulations permit, a financial institution should apply the principles in the Recommendations to its branches and subsidiaries abroad.
ZH: FATF建议18要求金融机构在允许的情况下对海外分支适用反洗钱原则。

[v7u_N001855|1855] The financial institution should have a balanced approach between its global, group-wide policy and its multiple local addenda.
ZH: 金融机构应在全球政策与当地附录之间采取平衡方法。

[v7u_N001856|1856] To ensure the financial institution achieves this balance, it should abide by its management oversight and governance obligations.
ZH: 金融机构应遵守管理监督和治理义务以实现全球政策与当地附录的平衡。
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N001847"
    ],
    "proposition": "外国金融机构的美国分行须遵守《银行保密法》的最低标准。",
    "source_quotes": [
      "the Bank Secrecy Act, which is the primary AML law in the US, requires compliance from US branches of foreign financial institutions. This means foreign financial institutions must ensure that their group-wide policies meet the Bank Secrecy Act’s minimum standards."
    ],
    "relation_cues": [
      "requires",
      "must ensure"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "外国金融机构在美国设有分行"
      ],
      "basis_or_condition": [
        "美国《银行保密法》的最低标准"
      ],
      "focal_handling_or_judgment": "外国金融机构确保其集团政策符合BSA最低标准",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001847",
        "quote": "the Bank Secrecy Act, which is the primary AML law in the US, requires compliance from US branches of foreign financial institutions. This means foreign financial institutions must ensure that their group-wide policies meet the Bank Secrecy Act’s minimum standards."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N001849",
      "v7u_N001850",
      "v7u_N001851"
    ],
    "proposition": "若当地AML标准高于母国，金融机构应在集团政策中附加司法管辖区特定附录并记录更高标准。",
    "source_quotes": [
      "To address potential differences in regulations, international financial institutions often attach jurisdiction-specific addenda to their group-wide AML policy.",
      "If a jurisdiction in which a financial institution operates has a higher AML standard than its home jurisdiction, the financial institution should document this in the addendum.",
      "For example, from 2012 to 2018, Hong Kong had a more stringent beneficial ownership identification rule of 10%, while the US’s rule was 25%. As a result, all international US banks operating in Hong Kong documented the higher standard in a Hong Kong-specific addendum."
    ],
    "relation_cues": [
      "if",
      "should",
      "higher",
      "document"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "当地AML标准高于母国标准"
      ],
      "basis_or_condition": [
        "存在跨境标准差异"
      ],
      "focal_handling_or_judgment": "附加司法管辖区特定附录并记录更高标准",
      "outcomes_or_paths": [
        "满足当地监管要求"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001849",
        "quote": "To address potential differences in regulations, international financial institutions often attach jurisdiction-specific addenda to their group-wide AML policy."
      },
      {
        "unit_id": "v7u_N001850",
        "quote": "If a jurisdiction in which a financial institution operates has a higher AML standard than its home jurisdiction, the financial institution should document this in the addendum."
      },
      {
        "unit_id": "v7u_N001851",
        "quote": "For example, from 2012 to 2018, Hong Kong had a more stringent beneficial ownership identification rule of 10%, while the US’s rule was 25%. As a result, all international US banks operating in Hong Kong documented the higher standard in a Hong Kong-specific addendum."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N001854"
    ],
    "proposition": "FATF建议18要求金融集团在允许的情况下对海外分支和子公司适用反洗钱原则。",
    "source_quotes": [
      "FATF’s Recommendation 18 stipulates that where local applicable laws and regulations permit, a financial institution should apply the principles in the Recommendations to its branches and subsidiaries abroad."
    ],
    "relation_cues": [
      "where",
      "permit",
      "should apply"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "集团在海外设有分支或子公司"
      ],
      "basis_or_condition": [
        "当地适用法律和法规允许"
      ],
      "focal_handling_or_judgment": "对海外分支和子公司适用FATF建议中的原则",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001854",
        "quote": "FATF’s Recommendation 18 stipulates that where local applicable laws and regulations permit, a financial institution should apply the principles in the Recommendations to its branches and subsidiaries abroad."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N001855",
      "v7u_N001856"
    ],
    "proposition": "金融机构应在全球政策与当地附录之间采取平衡方法，并遵守管理监督和治理义务。",
    "source_quotes": [
      "The financial institution should have a balanced approach between its global, group-wide policy and its multiple local addenda.",
      "To ensure the financial institution achieves this balance, it should abide by its management oversight and governance obligations."
    ],
    "relation_cues": [
      "should have",
      "to ensure",
      "should abide by"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "需要协调全球政策与当地附录"
      ],
      "basis_or_condition": [
        "管理监督和治理义务"
      ],
      "focal_handling_or_judgment": "采取平衡方法并遵守管理监督和治理义务",
      "outcomes_or_paths": [
        "实现全球政策与当地附录的平衡"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001855",
        "quote": "The financial institution should have a balanced approach between its global, group-wide policy and its multiple local addenda."
      },
      {
        "unit_id": "v7u_N001856",
        "quote": "To ensure the financial institution achieves this balance, it should abide by its management oversight and governance obligations."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
