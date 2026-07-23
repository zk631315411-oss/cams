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

section_id: `CH37-S01`

section_title: `Enterprise-wide risk assessment > Enterprise-wide risk assessment`

section_text_with_unit_anchors:

```text
[v7u_N002721|2721] EWRAs, sometimes called bank-wide risk assessments, institutional risk assessments, or financial crime risk assessments, help organizations evaluate their overall risk exposure to financial crime, including money laundering (ML), terrorist financing (TF), proliferation financing, sanctions evasion, tax evasion, bribery, corruption, and fraud.
ZH: 企业级风险评估（EWRA）的定义与范围，涵盖洗钱、恐怖融资、制裁规避、欺诈等多种金融犯罪。

[v7u_N002722|2722] The EWRA provides a standardized way to measure and track risks, ensuring they are mitigated across all operations, products, and services.
ZH: EWRA 提供标准化的风险衡量与追踪方法，确保风险在所有运营、产品和服务中得到缓解。

[v7u_N002723|2723] Organizations conduct EWRAs periodically and whenever there is material change in the organization’s business structure, its regulatory environment, or if a money laundering or wider financial crime trend is identified.
ZH: 组织应定期或在业务结构、监管环境发生重大变化时，或发现洗钱等金融犯罪趋势时开展 EWRA。

[v7u_N002724|2724] The organization's AFC risk assessment team typically leads the EWRA, although in smaller organizations it might be the governance or advisory team.
ZH: EWRA 通常由金融犯罪防控（金融犯罪防控）风险评估团队主导，小型组织可能由治理或咨询团队负责。

[v7u_N002725|2725] The results of an EWRA are reported to the MLRO, or equivalent, and the relevant stakeholders, such as senior managers and department heads.
ZH: EWRA 结果需报告给洗钱报告官（MLRO）及高级管理层、部门负责人等相关利益方。

[v7u_N002726|2726] The MLRO uses these results in the ongoing evaluation and determination of the organization’s financial crime risk appetite.
ZH: MLRO 利用 EWRA 结果持续评估并确定组织的金融犯罪风险偏好。

[v7u_N002727|2727] The EWRA should use a broad range of public and private information sources to assess risk comprehensively.
ZH: EWRA 应利用广泛的公共和私人信息来源，以全面评估风险。

[v7u_N002728|2728] It should review all customer types, jurisdictions, products, delivery channels, transactions, and the operating environment, including staff education and training on the financial crime risk the organization needs to manage.
ZH: EWRA 应审查所有客户类型、司法管辖区、产品、交付渠道、交易及运营环境，包括员工培训。

[v7u_N002729|2729] Additionally, it should review prior risk alerts as identified by the alert management systems, particularly those that result in a true match, which should be further analyzed for residual risk.
ZH: EWRA 还应审查预警管理系统中的历史风险警报，特别是真实匹配项，以分析剩余风险。

[v7u_N002730|2730] A risk assessment should place particular focus where:
ZH: 风险评估应特别关注以下情形：

[v7u_N002731|2731] The probability of the risk occurring and its impact are greatest.
ZH: 风险发生概率及其影响最大时，应重点关注。

[v7u_N002732|2732] The risk exceeds the organization’s appetite.
ZH: 风险超出组织风险偏好时，应重点关注。

[v7u_N002733|2733] Controls are ineffective.
ZH: 控制措施无效时，应重点关注。

[v7u_N002734|2734] Systems or controls have changed.
ZH: 系统或控制措施发生变化时，应重点关注。

[v7u_N002735|2735] In global organizations, the EWRA should be conducted in a flexible, coordinated manner and based on a common methodology. Subsidiaries or branches should be allowed to include the specific risk dynamics and relevant local elements of their own operations. The parent organization should incorporate input from all subsidiaries and branches in the group-wide risk assessment.
ZH: 全球性组织的 EWRA 应基于统一方法论灵活协调开展，允许子公司纳入本地风险要素，母公司应整合所有子公司的意见。
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002723"
    ],
    "proposition": "组织应定期或在业务结构、监管环境发生重大变化时，或发现洗钱等金融犯罪趋势时开展企业级风险评估。",
    "source_quotes": [
      "Organizations conduct EWRAs periodically and whenever there is material change in the organization’s business structure, its regulatory environment, or if a money laundering or wider financial crime trend is identified."
    ],
    "relation_cues": [
      "whenever",
      "if",
      "periodically"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "定期",
        "业务结构重大变化",
        "监管环境重大变化",
        "发现洗钱或金融犯罪趋势"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "组织开展企业级风险评估（EWRA）",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002723",
        "quote": "Organizations conduct EWRAs periodically and whenever there is material change in the organization’s business structure, its regulatory environment, or if a money laundering or wider financial crime trend is identified."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002730",
      "v7u_N002731",
      "v7u_N002732",
      "v7u_N002733",
      "v7u_N002734"
    ],
    "proposition": "风险评估应特别关注：风险发生概率和影响最大、风险超出组织风险偏好、控制措施无效、系统或控制措施发生变化的情形。",
    "source_quotes": [
      "A risk assessment should place particular focus where:",
      "The probability of the risk occurring and its impact are greatest.",
      "The risk exceeds the organization’s appetite.",
      "Controls are ineffective.",
      "Systems or controls have changed."
    ],
    "relation_cues": [
      "where",
      "should",
      "exceeds",
      "ineffective",
      "changed"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "风险发生概率和影响最大",
        "风险超出组织风险偏好",
        "控制措施无效",
        "系统或控制措施发生变化"
      ],
      "focal_handling_or_judgment": "风险评估应重点关注",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002730",
        "quote": "A risk assessment should place particular focus where:"
      },
      {
        "unit_id": "v7u_N002731",
        "quote": "The probability of the risk occurring and its impact are greatest."
      },
      {
        "unit_id": "v7u_N002732",
        "quote": "The risk exceeds the organization’s appetite."
      },
      {
        "unit_id": "v7u_N002733",
        "quote": "Controls are ineffective."
      },
      {
        "unit_id": "v7u_N002734",
        "quote": "Systems or controls have changed."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002735"
    ],
    "proposition": "全球性组织的企业级风险评估应基于统一方法论灵活协调开展，允许子公司纳入本地风险要素，母公司应整合所有子公司的意见。",
    "source_quotes": [
      "In global organizations, the EWRA should be conducted in a flexible, coordinated manner and based on a common methodology. Subsidiaries or branches should be allowed to include the specific risk dynamics and relevant local elements of their own operations. The parent organization should incorporate input from all subsidiaries and branches in the group-wide risk assessment."
    ],
    "relation_cues": [
      "should",
      "flexible",
      "coordinated",
      "based on",
      "allowed to",
      "incorporate"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "全球组织"
      ],
      "basis_or_condition": [
        "统一方法论"
      ],
      "focal_handling_or_judgment": "以灵活协调方式开展EWRA，允许子公司纳入本地要素，母公司整合输入",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002735",
        "quote": "In global organizations, the EWRA should be conducted in a flexible, coordinated manner and based on a common methodology. Subsidiaries or branches should be allowed to include the specific risk dynamics and relevant local elements of their own operations. The parent organization should incorporate input from all subsidiaries and branches in the group-wide risk assessment."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N002725"
    ],
    "proposition": "企业级风险评估的结果需报告给洗钱报告官及高级管理层、部门负责人等相关利益方。",
    "source_quotes": [
      "The results of an EWRA are reported to the MLRO, or equivalent, and the relevant stakeholders, such as senior managers and department heads."
    ],
    "relation_cues": [
      "reported to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "EWRA结果"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "报告给MLRO及利益相关方",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002725",
        "quote": "The results of an EWRA are reported to the MLRO, or equivalent, and the relevant stakeholders, such as senior managers and department heads."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N002726"
    ],
    "proposition": "洗钱报告官利用企业级风险评估结果持续评估并确定组织的金融犯罪风险偏好。",
    "source_quotes": [
      "The MLRO uses these results in the ongoing evaluation and determination of the organization’s financial crime risk appetite."
    ],
    "relation_cues": [
      "uses",
      "ongoing",
      "evaluation",
      "determination"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "EWRA结果"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "MLRO持续评估并确定金融犯罪风险偏好",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002726",
        "quote": "The MLRO uses these results in the ongoing evaluation and determination of the organization’s financial crime risk appetite."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
