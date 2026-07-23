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

section_id: `CH36-S05`

section_title: `Types of risk assessment > Preparing a risk appetite statement`

section_text_with_unit_anchors:

```text
[v7u_N002704|2704] According to the Financial Stability Board in the US, the RAS is a formal document, developed by an organization’s senior management and approved by the board of directors. It establishes risk limits while supporting the organization’s business objectives. This prospective document defines what types of risks the organization is willing to accept, mitigate, or avoid based on its strategic targets, regulatory environment, and expectations.
ZH: 风险偏好声明（RAS）是由高级管理层制定、董事会批准的形式文件

[v7u_N002705|2705] To prepare an effective RAS, an organization should have a structured approach to:
ZH: 准备有效RAS的结构化方法列表引导

[v7u_N002706|2706] Drive the decision-making process with top-down board leadership and bottom-up feedback from all levels of management.
ZH: 通过自上而下的董事会领导和自下而上的管理层反馈推动决策

[v7u_N002707|2707] Identify unique risks to the organization and assess the effects, actively consulting with risk management teams.
ZH: 识别机构特有风险并评估影响，积极咨询风险管理团队

[v7u_N002708|2708] Decide the extent to which these risks can be accepted.
ZH: 决定这些风险可接受的程度

[v7u_N002709|2709] Define clear thresholds or limits.
ZH: 定义明确的阈值或限额

[v7u_N002710|2710] Draft the RAS with senior management and seek approval from the board.
ZH: 与高级管理层共同起草RAS并寻求董事会批准

[v7u_N002711|2711] Regularly monitor and update the RAS.
ZH: 定期监控和更新RAS

[v7u_N002712|2712] Ensure that all business units are aware of the RAS, including updates.
ZH: 确保所有业务单元了解RAS及其更新

[v7u_N002713|2713] An effective RAS allows informed decision-making and helps the organization reach its strategic objectives while mitigating and managing risks effectively.
ZH: 有效的RAS有助于明智决策并实现战略目标

[v7u_N002714|2714] Regulatory expectations and legal obligations help determine the acceptable level of risks in the RAS.
ZH: 监管期望和法律义务帮助确定RAS中的可接受风险水平

[v7u_N002715|2715] Financial institutions should not accept risks that violate applicable AML/CFT laws or sanctions regimes.
ZH: 金融机构不得接受违反反洗钱/反恐怖融资法律或制裁制度的风险

[v7u_N002716|2716] For example, if a potential customer resides in a Category I jurisdiction, that jurisdiction might have strategic AML/CFT deficiencies, and countermeasures might apply.
ZH: 示例：一类辖区可能具有战略性反洗钱/反恐怖融资缺陷并适用反制措施

[v7u_N002717|2717] If the applicable laws require financial institutions to seek permission from the regulator before entering any business relationships, the RAS must carefully address customer acceptance or business relationships with those jurisdictions.
ZH: 若法律要求获得监管许可才能建立业务关系，RAS必须审慎处理客户接纳

[v7u_N002718|2718] A financial institution’s RAS might include zero appetite statements. Zero appetite means the financial institution refuses to take on certain risks related to specific customer types, products, services, or sectors.
ZH: 零容忍偏好指金融机构拒绝承担特定客户、产品或行业相关风险

[v7u_N002719|2719] For example, a financial institution might declare it will not accept customers from countries under strict EU, UN, or OFAC sanctions.
ZH: 示例：金融机构声明不接受受欧盟、联合国或OFAC严格制裁国家的客户

[v7u_N002720|2720] By avoiding certain risks, the organization minimizes exposure to high-risk areas.
ZH: 规避特定风险可最小化机构对高风险领域的敞口
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002705",
      "v7u_N002706",
      "v7u_N002707",
      "v7u_N002708",
      "v7u_N002709",
      "v7u_N002710",
      "v7u_N002711",
      "v7u_N002712"
    ],
    "proposition": "准备有效RAS需采取结构化方法，包括推动决策、识别风险、决定可接受程度、定义阈值、起草并审批、监控更新、确保知晓等步骤。",
    "source_quotes": [
      "To prepare an effective RAS, an organization should have a structured approach to:",
      "Drive the decision-making process with top-down board leadership and bottom-up feedback from all levels of management.",
      "Identify unique risks to the organization and assess the effects, actively consulting with risk management teams.",
      "Decide the extent to which these risks can be accepted.",
      "Define clear thresholds or limits.",
      "Draft the RAS with senior management and seek approval from the board.",
      "Regularly monitor and update the RAS.",
      "Ensure that all business units are aware of the RAS, including updates."
    ],
    "relation_cues": [
      "should",
      "drive",
      "identify",
      "assess",
      "decide",
      "define",
      "draft",
      "approve",
      "monitor",
      "update",
      "ensure"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "准备有效的风险偏好声明(RAS)"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "采取结构化方法，包括推动决策、识别风险、决定可接受程度、定义阈值、起草审批、监控更新、确保知晓",
      "outcomes_or_paths": [
        "完成RAS的制定与传达"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002705",
        "quote": "To prepare an effective RAS, an organization should have a structured approach to:"
      },
      {
        "unit_id": "v7u_N002706",
        "quote": "Drive the decision-making process with top-down board leadership and bottom-up feedback from all levels of management."
      },
      {
        "unit_id": "v7u_N002707",
        "quote": "Identify unique risks to the organization and assess the effects, actively consulting with risk management teams."
      },
      {
        "unit_id": "v7u_N002708",
        "quote": "Decide the extent to which these risks can be accepted."
      },
      {
        "unit_id": "v7u_N002709",
        "quote": "Define clear thresholds or limits."
      },
      {
        "unit_id": "v7u_N002710",
        "quote": "Draft the RAS with senior management and seek approval from the board."
      },
      {
        "unit_id": "v7u_N002711",
        "quote": "Regularly monitor and update the RAS."
      },
      {
        "unit_id": "v7u_N002712",
        "quote": "Ensure that all business units are aware of the RAS, including updates."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002714",
      "v7u_N002715",
      "v7u_N002716",
      "v7u_N002717",
      "v7u_N002718",
      "v7u_N002719"
    ],
    "proposition": "确定RAS中的可接受风险水平需考虑监管期望和法律义务；不得接受违反AML/CFT法律或制裁的风险；对于一类辖区可能适用反制措施；对于要求监管许可的辖区需审慎处理；可采取零容忍策略，不接受受制裁国家客户。",
    "source_quotes": [
      "Regulatory expectations and legal obligations help determine the acceptable level of risks in the RAS.",
      "Financial institutions should not accept risks that violate applicable AML/CFT laws or sanctions regimes.",
      "For example, if a potential customer resides in a Category I jurisdiction, that jurisdiction might have strategic AML/CFT deficiencies, and countermeasures might apply.",
      "If the applicable laws require financial institutions to seek permission from the regulator before entering any business relationships, the RAS must carefully address customer acceptance or business relationships with those jurisdictions.",
      "A financial institution’s RAS might include zero appetite statements. Zero appetite means the financial institution refuses to take on certain risks related to specific customer types, products, services, or sectors.",
      "For example, a financial institution might declare it will not accept customers from countries under strict EU, UN, or OFAC sanctions."
    ],
    "relation_cues": [
      "help determine",
      "should not accept",
      "violate",
      "for example",
      "if",
      "might",
      "must",
      "zero appetite",
      "refuses",
      "declare",
      "will not accept"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "准备RAS时确定可接受风险水平"
      ],
      "basis_or_condition": [
        "监管期望和法律义务",
        "违反AML/CFT法律或制裁",
        "客户位于一类辖区",
        "法律要求获得监管许可"
      ],
      "focal_handling_or_judgment": "确定可接受风险水平并设定相应限制",
      "outcomes_or_paths": [
        "不得接受违反AML/CFT法律或制裁的风险",
        "对一类辖区可能适用反制措施",
        "对要求监管许可的辖区审慎处理客户接纳",
        "采取零容忍，不接受受制裁国家客户"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002714",
        "quote": "Regulatory expectations and legal obligations help determine the acceptable level of risks in the RAS."
      },
      {
        "unit_id": "v7u_N002715",
        "quote": "Financial institutions should not accept risks that violate applicable AML/CFT laws or sanctions regimes."
      },
      {
        "unit_id": "v7u_N002716",
        "quote": "For example, if a potential customer resides in a Category I jurisdiction, that jurisdiction might have strategic AML/CFT deficiencies, and countermeasures might apply."
      },
      {
        "unit_id": "v7u_N002717",
        "quote": "If the applicable laws require financial institutions to seek permission from the regulator before entering any business relationships, the RAS must carefully address customer acceptance or business relationships with those jurisdictions."
      },
      {
        "unit_id": "v7u_N002718",
        "quote": "A financial institution’s RAS might include zero appetite statements. Zero appetite means the financial institution refuses to take on certain risks related to specific customer types, products, services, or sectors."
      },
      {
        "unit_id": "v7u_N002719",
        "quote": "For example, a financial institution might declare it will not accept customers from countries under strict EU, UN, or OFAC sanctions."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
