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

section_id: `CH02-S04`

section_title: `Types of financial crime > Case example: FullTechGlobal corruption scandal`

section_text_with_unit_anchors:

```text
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
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N000132",
      "v7u_N000133",
      "v7u_N000134",
      "v7u_N000136"
    ],
    "proposition": "客户FullTechGlobal Services因具有英国关联并面临海外贿赂指控，触发英国反贿赂法域外条款的适用。",
    "source_quotes": [
      "One day, she came across negative news concerning their customer FullTechGlobal Services, which is incorporated and headquartered in the US and is a subsidiary of a UK company.",
      "The company faced serious accusations of widespread bribery and corruption due to its overseas sales practices.",
      "This raised concerns under the extraterritorial provisions of the UK Bribery Act 2010.",
      "It applies to any company with a UK connection and also holds parent firms liable for corrupt activities by subsidiaries, regardless of location."
    ],
    "relation_cues": [
      "subsidiary",
      "accusations",
      "raised concerns",
      "applies to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "客户FullTechGlobal Services是美国公司且是英国公司的子公司，面临海外贿赂指控"
      ],
      "basis_or_condition": [
        "英国反贿赂法2010的域外条款适用于任何有英国关联的公司，母公司对子公司腐败负责"
      ],
      "focal_handling_or_judgment": "引发法律适用关切",
      "outcomes_or_paths": [
        "法律适用于该主体及其母公司"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000132",
        "quote": "One day, she came across negative news concerning their customer FullTechGlobal Services, which is incorporated and headquartered in the US and is a subsidiary of a UK company."
      },
      {
        "unit_id": "v7u_N000133",
        "quote": "The company faced serious accusations of widespread bribery and corruption due to its overseas sales practices."
      },
      {
        "unit_id": "v7u_N000134",
        "quote": "This raised concerns under the extraterritorial provisions of the UK Bribery Act 2010."
      },
      {
        "unit_id": "v7u_N000136",
        "quote": "It applies to any company with a UK connection and also holds parent firms liable for corrupt activities by subsidiaries, regardless of location."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N000138",
      "v7u_N000139",
      "v7u_N000140",
      "v7u_N000141",
      "v7u_N000142"
    ],
    "proposition": "Sophie展开调查和审计，发现客户通过中间人、虚增费用、贿赂等方式从事腐败，并识别出控防失败和洗钱路径。",
    "source_quotes": [
      "Sophie’s initial investigation revealed that FullTechGlobal had strategically employed intermediaries in high-risk jurisdictions to secure lucrative contracts.",
      "According to the allegations and further investigative efforts, it appeared the subsidiary was systematically obscuring illicit financial flows through inflated consultancy fees, fabricated invoicing practices, and opaque shell companies.",
      "Additionally, evidence suggested that FullTechGlobal provided sophisticated inducements, including lavish gifts and premium travel arrangements to public officials and high-ranking executives to unlawfully influence decision-making processes.",
      "She followed up on the investigation and conducted a review that identified failures within FullTechGlobal’s ABC framework and internal controls. Her audit uncovered deficiencies in internal control mechanisms and inadequate oversight, which facilitated prolonged and undetected corrupt activities.",
      "Bribery was identified as the predicate crime, leading to the laundering of illicit funds through complex financial networks designed to evade regulatory scrutiny and forensic tracing efforts."
    ],
    "relation_cues": [
      "revealed",
      "obscuring",
      "provided",
      "identified failures",
      "identified as"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "发现客户负面新闻（v7u_N000132）"
      ],
      "basis_or_condition": [
        "调查和审计工作"
      ],
      "focal_handling_or_judgment": "进行调查和审计以发现腐败行为及控防缺陷",
      "outcomes_or_paths": [
        "发现雇佣高风险中间人",
        "发现通过虚增费用和壳公司掩盖资金",
        "发现提供奢华礼品影响决策",
        "发现ABC框架和控制缺陷",
        "识别贿赂为上游犯罪并导致洗钱"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000138",
        "quote": "Sophie’s initial investigation revealed that FullTechGlobal had strategically employed intermediaries in high-risk jurisdictions to secure lucrative contracts."
      },
      {
        "unit_id": "v7u_N000139",
        "quote": "According to the allegations and further investigative efforts, it appeared the subsidiary was systematically obscuring illicit financial flows through inflated consultancy fees, fabricated invoicing practices, and opaque shell companies."
      },
      {
        "unit_id": "v7u_N000140",
        "quote": "Additionally, evidence suggested that FullTechGlobal provided sophisticated inducements, including lavish gifts and premium travel arrangements to public officials and high-ranking executives to unlawfully influence decision-making processes."
      },
      {
        "unit_id": "v7u_N000141",
        "quote": "She followed up on the investigation and conducted a review that identified failures within FullTechGlobal’s ABC framework and internal controls. Her audit uncovered deficiencies in internal control mechanisms and inadequate oversight, which facilitated prolonged and undetected corrupt activities."
      },
      {
        "unit_id": "v7u_N000142",
        "quote": "Bribery was identified as the predicate crime, leading to the laundering of illicit funds through complex financial networks designed to evade regulatory scrutiny and forensic tracing efforts."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N000143"
    ],
    "proposition": "基于调查发现，FullTechGlobal Services及其母公司面临英国反贿赂法下的严重后果：罚款、监管审查和刑事责任。",
    "source_quotes": [
      "Given these findings, the regulatory implications under the UK Bribery Act 2010 are profound. FullTechGlobal Services faces severe financial penalties, increased scrutiny from international regulators, and potential criminal liability for both the subsidiary and the parent company, including its executives."
    ],
    "relation_cues": [
      "Given",
      "faces"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "调查发现（s1c_002结果）"
      ],
      "basis_or_condition": [
        "英国反贿赂法2010"
      ],
      "focal_handling_or_judgment": "根据法律和发现确定监管后果",
      "outcomes_or_paths": [
        "严重经济处罚",
        "国际监管机构加强审查",
        "子公司和母公司及高管面临潜在刑事责任"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000143",
        "quote": "Given these findings, the regulatory implications under the UK Bribery Act 2010 are profound. FullTechGlobal Services faces severe financial penalties, increased scrutiny from international regulators, and potential criminal liability for both the subsidiary and the parent company, including its executives."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
