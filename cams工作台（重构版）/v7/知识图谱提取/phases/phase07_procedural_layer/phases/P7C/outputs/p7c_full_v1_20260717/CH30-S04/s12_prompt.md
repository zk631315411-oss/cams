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

section_id: `CH30-S04`

section_title: `Using reports, guidance notes, and policy papers in your AML/CFT controls > National, sectoral, and thematic risk assessments`

section_text_with_unit_anchors:

```text
[v7u_N002183|2183] A national risk assessment (NRA) is a document that a jurisdiction produces to identify and evaluate money laundering threats and vulnerabilities, determine risk levels, and develop strategies to respond to risks.
ZH: 国家风险评估（NRA）是司法管辖区识别和评估洗钱威胁与脆弱性的文件。

[v7u_N002184|2184] NRAs should be comprehensive documents, drawing on a wide range of data.
ZH: NRA应全面并基于广泛数据。

[v7u_N002185|2185] FATF Recommendation 1 requires jurisdictions to identify, assess, understand, and mitigate the money laundering, terrorist financing, and proliferation financing risks they face.
ZH: FATF建议1要求司法管辖区识别、评估、理解并减轻洗钱、恐怖融资和扩散融资风险。

[v7u_N002186|2186] Jurisdictions can consolidate and articulate their knowledge of these risks using an NRA.
ZH: NRA是司法管辖区整合和表达风险知识的工具。

[v7u_N002187|2187] FATF encourages all jurisdictions to produce an NRA, and EU jurisdictions are legally obliged to produce a risk assessment via the fourth EU AML directive.
ZH: FATF鼓励所有司法管辖区开展NRA，欧盟司法管辖区根据第四反洗钱指令有法律义务。

[v7u_N002188|2188] FATF has produced guidance for conducting NRAs. In addition, international organizations such as the World Bank and the Council of Europe have produced detailed methodologies that jurisdictions can use and adapt to produce an NRA. Alternatively, jurisdictions might decide to develop their own methodology.
ZH: FATF、世界银行和欧洲委员会等提供NRA指南和方法论。

[v7u_N002189|2189] NRAs analyze risk in a number of ways, including focusing on emerging sectors or areas of increasing risk.
ZH: NRA以多种方式分析风险，包括关注新兴领域或风险上升领域。

[v7u_N002190|2190] Jurisdictions can produce sectoral risk assessments (SRAs) or thematic risk assessments to supplement the NRA and to highlight these issues.
ZH: 司法管辖区可开展行业风险评估（SRA）或专题风险评估以补充NRA。

[v7u_N002191|2191] Whereas SRAs focus on specific sectors, such as the gaming industry, thematic assessments look at issues such as the risk that emerging technologies pose.
ZH: SRA聚焦特定行业，专题评估关注新兴技术等议题。

[v7u_N002192|2192] A jurisdiction might conduct a separate SRA or thematic risk assessment if new risks arise or in response to new regulations for a sector.
ZH: 当新风险出现或新法规出台时，司法管辖区可能开展单独的SRA或专题评估。

[v7u_N002193|2193] As with NRAs, international organizations provide methodologies to help jurisdictions create SRAs and thematic risk assessments.
ZH: 国际组织为SRA和专题风险评估提供方法论。

[v7u_N002194|2194] FATF Recommendation 2 requires jurisdictions to implement policies that align with the identified risk.
ZH: FATF建议2要求司法管辖区实施与已识别风险一致的政策。

[v7u_N002195|2195] Jurisdictions should also produce action plans to mitigate the risks identified in the NRA, SRA, or thematic risk assessment, which can be public or confidential documents.
ZH: 司法管辖区应制定行动计划以减轻NRA、SRA或专题评估中识别的风险。

[v7u_N002196|2196] Public risk assessments and action plans provide organizations with information about risk levels the government applies to their sector and other sectors, along with other highlevel information about risk and the government’s priorities for addressing it.
ZH: 公开的风险评估和行动计划为组织提供政府对其行业及其他行业风险水平的信息。
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002185"
    ],
    "proposition": "FATF建议1要求司法管辖区识别、评估、理解并减轻洗钱、恐怖融资和扩散融资风险。",
    "source_quotes": [
      "FATF Recommendation 1 requires jurisdictions to identify, assess, understand, and mitigate the money laundering, terrorist financing, and proliferation financing risks they face."
    ],
    "relation_cues": [
      "requires"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "司法管辖区面临风险"
      ],
      "basis_or_condition": [
        "FATF建议1"
      ],
      "focal_handling_or_judgment": "识别、评估、理解并减轻风险",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002185",
        "quote": "FATF Recommendation 1 requires jurisdictions to identify, assess, understand, and mitigate the money laundering, terrorist financing, and proliferation financing risks they face."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002187"
    ],
    "proposition": "FATF鼓励所有司法管辖区开展NRA，欧盟司法管辖区有法律义务根据第四反洗钱指令制作风险评估。",
    "source_quotes": [
      "FATF encourages all jurisdictions to produce an NRA, and EU jurisdictions are legally obliged to produce a risk assessment via the fourth EU AML directive."
    ],
    "relation_cues": [
      "encourages",
      "legally obliged"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "所有司法管辖区",
        "欧盟司法管辖区"
      ],
      "basis_or_condition": [
        "FATF鼓励",
        "第四反洗钱指令"
      ],
      "focal_handling_or_judgment": "制作国家风险评估（NRA）",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002187",
        "quote": "FATF encourages all jurisdictions to produce an NRA, and EU jurisdictions are legally obliged to produce a risk assessment via the fourth EU AML directive."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002192"
    ],
    "proposition": "当新风险出现或新法规出台时，司法管辖区可能开展单独的行业或专题评估。",
    "source_quotes": [
      "A jurisdiction might conduct a separate SRA or thematic risk assessment if new risks arise or in response to new regulations for a sector."
    ],
    "relation_cues": [
      "if",
      "might"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "新风险出现",
        "新法规出台"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "开展单独的行业或专题风险评估",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002192",
        "quote": "A jurisdiction might conduct a separate SRA or thematic risk assessment if new risks arise or in response to new regulations for a sector."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N002194"
    ],
    "proposition": "FATF建议2要求司法管辖区实施与所识别风险一致的政策。",
    "source_quotes": [
      "FATF Recommendation 2 requires jurisdictions to implement policies that align with the identified risk."
    ],
    "relation_cues": [
      "requires"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "已识别风险"
      ],
      "basis_or_condition": [
        "FATF建议2"
      ],
      "focal_handling_or_judgment": "实施与风险一致的政策",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002194",
        "quote": "FATF Recommendation 2 requires jurisdictions to implement policies that align with the identified risk."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N002195"
    ],
    "proposition": "司法管辖区应制定行动计划以减轻NRA、SRA或专题评估中识别的风险。",
    "source_quotes": [
      "Jurisdictions should also produce action plans to mitigate the risks identified in the NRA, SRA, or thematic risk assessment, which can be public or confidential documents."
    ],
    "relation_cues": [
      "should"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "NRA、SRA或专题评估中识别的风险"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "制定行动计划以减轻风险",
      "outcomes_or_paths": [
        "行动计划可以是公开或保密文件"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002195",
        "quote": "Jurisdictions should also produce action plans to mitigate the risks identified in the NRA, SRA, or thematic risk assessment, which can be public or confidential documents."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
