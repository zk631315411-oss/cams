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

section_id: `CH37-S05`

section_title: `Enterprise-wide risk assessment > Third-party tools to conduct risk assessment`

section_text_with_unit_anchors:

```text
[v7u_N002797|2797] Organizations need to conduct a risk assessment to understand the types of risk and their potential impacts.
ZH: 组织需进行风险评估以了解风险类型及潜在影响

[v7u_N002798|2798] The risk assessment process involves collating qualitative and quantitative data about risks, such as the number of wire transfers sent internationally or to high-risk jurisdictions.
ZH: 风险评估过程涉及收集定性和定量数据，如国际电汇数量

[v7u_N002799|2799] This data helps determine inherent risk, control strength, and the remaining residual risk.
ZH: 数据用于确定固有风险、控制强度和剩余风险

[v7u_N002800|2800] The company can then determine what steps it needs to take to mitigate risk and align to its risk appetite.
ZH: 公司可据此确定缓解风险的措施并与风险偏好对齐

[v7u_N002801|2801] Many organizations develop or purchase risk assessment tools. Sometimes organizations combine multiple internal and third-party tools. These tools can be used to quickly upload data, verify accuracy, look for gaps, and calculate risk scoring.
ZH: 机构可开发或购买风险评估工具，结合内外部工具快速上传数据、验证准确性、查找缺口并计算风险评分。

[v7u_N002802|2802] Risk calculation involves assigning a scoring methodology, such as relative weighting, to the risks and controls of an organization.
ZH: 风险计算涉及为机构的风险和控制分配评分方法，如相对权重。

[v7u_N002803|2803] A company using an internal or third-party risk assessment tool must input inherent risk and control strength correctly to ensure that residual risk is correctly calculated.
ZH: 使用内部或第三方风险评估工具时，必须正确输入固有风险和控制强度，以确保剩余风险计算准确。

[v7u_N002804|2804] For example, if a particular control is assessed as working correctly, it could inflate the overall control strength, which would incorrectly decrease the residual risk.
ZH: 举例：若某项控制被评估为有效，可能夸大整体控制强度，导致剩余风险被错误降低。

[v7u_N002805|2805] An internal or third-party risk assessment tool might be leveraged for data collation prior to those calculations, to weight and validate the calculations formulas, look for data gaps, and complete the overall calculation.
ZH: 风险评估工具可用于计算前的数据整理、加权和验证计算公式、查找数据缺口并完成整体计算。

[v7u_N002806|2806] Whether automated or manual, the tool must be tailored to the institution so that it not only includes the correct calculations but can be refined to include risks unique to that organization.
ZH: 无论自动化还是手动，工具必须根据机构量身定制，包含正确计算并纳入该机构特有的风险。

[v7u_N002807|2807] Some companies take a hybrid approach and manage higher-risk products or client assessments themselves while relying on third-party tools to automate their lower-risk products.
ZH: 部分公司采用混合方法：自行管理高风险产品或客户评估，同时依赖第三方工具自动化低风险产品。
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002803",
      "v7u_N002804"
    ],
    "proposition": "使用内部或第三方风险评估工具时，必须正确输入固有风险和控制强度，以确保剩余风险计算准确；若控制评估有误，可能错误降低剩余风险。",
    "source_quotes": [
      "A company using an internal or third-party risk assessment tool must input inherent risk and control strength correctly to ensure that residual risk is correctly calculated.",
      "For example, if a particular control is assessed as working correctly, it could inflate the overall control strength, which would incorrectly decrease the residual risk."
    ],
    "relation_cues": [
      "must",
      "if",
      "could",
      "would"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "使用内部或第三方风险评估工具"
      ],
      "basis_or_condition": [
        "正确输入固有风险和控制强度"
      ],
      "focal_handling_or_judgment": "确保剩余风险计算准确",
      "outcomes_or_paths": [
        "正确输入时剩余风险计算准确",
        "若控制评估有误，可能错误降低剩余风险"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002803",
        "quote": "A company using an internal or third-party risk assessment tool must input inherent risk and control strength correctly to ensure that residual risk is correctly calculated."
      },
      {
        "unit_id": "v7u_N002804",
        "quote": "For example, if a particular control is assessed as working correctly, it could inflate the overall control strength, which would incorrectly decrease the residual risk."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002806"
    ],
    "proposition": "无论自动化还是手动，风险评估工具必须根据机构量身定制，以包含正确计算并纳入该机构特有风险。",
    "source_quotes": [
      "Whether automated or manual, the tool must be tailored to the institution so that it not only includes the correct calculations but can be refined to include risks unique to that organization."
    ],
    "relation_cues": [
      "must",
      "so that"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "制定或使用风险评估工具"
      ],
      "basis_or_condition": [
        "工具需包含正确计算并纳入特有风险"
      ],
      "focal_handling_or_judgment": "工具必须量身定制",
      "outcomes_or_paths": [
        "包含正确计算",
        "可纳入机构特有风险"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002806",
        "quote": "Whether automated or manual, the tool must be tailored to the institution so that it not only includes the correct calculations but can be refined to include risks unique to that organization."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002807"
    ],
    "proposition": "部分公司采用混合方法：自行管理高风险产品或客户评估，依赖第三方工具自动化低风险产品。",
    "source_quotes": [
      "Some companies take a hybrid approach and manage higher-risk products or client assessments themselves while relying on third-party tools to automate their lower-risk products."
    ],
    "relation_cues": [
      "while",
      "hybrid"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "公司需要管理不同风险等级的产品或客户"
      ],
      "basis_or_condition": [
        "风险高低不同"
      ],
      "focal_handling_or_judgment": "采取混合方法管理",
      "outcomes_or_paths": [
        "高风险：自行管理",
        "低风险：依赖第三方工具自动化"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002807",
        "quote": "Some companies take a hybrid approach and manage higher-risk products or client assessments themselves while relying on third-party tools to automate their lower-risk products."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
