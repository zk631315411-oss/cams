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

section_id: `CH26-S02`

section_title: `Other laws and regulations that impact organizations > Digital Operational Resilience Act`

section_text_with_unit_anchors:

```text
[v7u_N002028|2028] Digitalization has deepened interconnections and dependencies within the financial sector and with third-party service providers. In this context, information and communications technology (ICT) risk has increased as illicit actors frequently exploit ICT infrastructures to attack financial institutions.
ZH: 数字化加深了金融业与第三方的互联和依赖，增加了ICT风险。

[v7u_N002029|2029] Considering the relevance of digital resilience, the EU passed the Digital Operational Resilience Act (DORA). The goal of this regulation is to strengthen the cybersecurity of EU’s financial services sector.
ZH: 欧盟通过《数字运营韧性法案》（DORA）以加强金融服务业网络安全。

[v7u_N002030|2030] It applies to all financial institutions as of January 2025.
ZH: DORA自2025年1月起适用于所有金融机构。

[v7u_N002031|2031] DORA sets requirements in the following areas:
ZH: DORA在以下领域设定要求（列表引导）。

[v7u_N002032|2032] ICT risk management: Financial institutions should implement a robust control system coordinated by an independent ICT risk control function. This body is responsible for setting the data operational resilience strategy, which includes determining the appropriate risk tolerance level. A management body then approves this tolerance level. These bodies should make the necessary arrangements to ensure continuity of critical AFC functions and include a secondary processing site.
ZH: ICT风险管理：金融机构应建立由独立ICT风险控制职能协调的稳健控制体系。

[v7u_N002033|2033] Incident reporting: Financial institutions should promptly report significant ICT incidents to the designated competent authorities.
ZH: 事件报告：金融机构应及时向指定主管当局报告重大ICT事件。

[v7u_N002034|2034] Resilience testing: Financial institutions should conduct yearly vulnerability assessments, while the designated competent authorities are responsible for conducting threat-led penetration tests every three years.
ZH: 金融机构每年进行漏洞评估，主管当局每三年进行威胁主导的渗透测试。

[v7u_N002035|2035] The financial institution utilizing a third-party service is primarily responsible for remediating vulnerabilities it identifies during end-to-end testing.
ZH: 使用第三方服务的金融机构主要负责修复端到端测试中发现的漏洞。

[v7u_N002036|2036] Third-party risk management: Financial institutions should conduct ex-ante due diligence - meaning a preventative review before taking action - and ongoing monitoring of vendors.
ZH: 金融机构应对供应商进行事前尽职调查和持续监控。

[v7u_N002037|2037] They should prohibit dealing with vendors that have insufficient security standards.
ZH: 应禁止与安全标准不足的供应商交易。

[v7u_N002038|2038] To mitigate concentration risk, financial institutions should establish an exit strategy from vendor services related to critical AFC functions, such as sanction screening and transaction monitoring.
ZH: 为缓解集中风险，金融机构应为关键金融犯罪防控功能的供应商服务制定退出策略。

[v7u_N002039|2039] Additionally, critical ICT third-party service providers are subject to EU-level supervision and obliged to establish a subsidiary in the EU.
ZH: 关键ICT第三方服务提供商受欧盟层面监管，并须在欧盟设立子公司。

[v7u_N002040|2040] Information sharing: Financial institutions can regularly share information regarding threats and vulnerability intelligence to prevent the materialization of incidents. Information sharing enables other financial institutions to effectively contain impacts of financial crimes and recover faster.
ZH: 信息共享：金融机构可定期共享威胁和漏洞情报，以预防事件发生。

[v7u_N002041|2041] By meeting DORA’s enhanced cybersecurity and risk management requirements, financial institutions reduce the risk that criminals and terrorists will exploit digital vulnerabilities to launder money through their accounts.
ZH: 遵守DORA的网络安全和风险管理要求可降低洗钱风险
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002030"
    ],
    "proposition": "DORA自2025年1月起适用于所有金融机构。",
    "source_quotes": [
      "It applies to all financial institutions as of January 2025."
    ],
    "relation_cues": [
      "applies to",
      "as of"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "金融机构"
      ],
      "basis_or_condition": [
        "自2025年1月起"
      ],
      "focal_handling_or_judgment": "DORA适用",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002030",
        "quote": "It applies to all financial institutions as of January 2025."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002032"
    ],
    "proposition": "金融机构应实施由独立ICT风险控制职能协调的稳健ICT风险管理体系，包括制定数字运营韧性战略、确定风险容忍度、确保关键AFC功能连续性及设置二级处理站点。",
    "source_quotes": [
      "Financial institutions should implement a robust control system coordinated by an independent ICT risk control function. This body is responsible for setting the data operational resilience strategy, which includes determining the appropriate risk tolerance level. A management body then approves this tolerance level. These bodies should make the necessary arrangements to ensure continuity of critical AFC functions and include a secondary processing site."
    ],
    "relation_cues": [
      "should",
      "responsible for",
      "then"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "由独立ICT风险控制职能协调"
      ],
      "focal_handling_or_judgment": "金融机构实施ICT风险管理，包括制定战略、确定容忍度、确保连续性、设置二级站点",
      "outcomes_or_paths": [
        "管理体批准容忍度"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002032",
        "quote": "Financial institutions should implement a robust control system coordinated by an independent ICT risk control function. This body is responsible for setting the data operational resilience strategy, which includes determining the appropriate risk tolerance level. A management body then approves this tolerance level. These bodies should make the necessary arrangements to ensure continuity of critical AFC functions and include a secondary processing site."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002033"
    ],
    "proposition": "金融机构应及时向指定主管当局报告重大ICT事件。",
    "source_quotes": [
      "Financial institutions should promptly report significant ICT incidents to the designated competent authorities."
    ],
    "relation_cues": [
      "should",
      "promptly",
      "to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "发生重大ICT事件"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "金融机构向主管当局报告",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002033",
        "quote": "Financial institutions should promptly report significant ICT incidents to the designated competent authorities."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N002034",
      "v7u_N002035"
    ],
    "proposition": "金融机构每年进行漏洞评估，主管当局每三年进行威胁主导的渗透测试；使用第三方服务的金融机构负责修复端到端测试中发现的漏洞。",
    "source_quotes": [
      "Financial institutions should conduct yearly vulnerability assessments, while the designated competent authorities are responsible for conducting threat-led penetration tests every three years.",
      "The financial institution utilizing a third-party service is primarily responsible for remediating vulnerabilities it identifies during end-to-end testing."
    ],
    "relation_cues": [
      "should",
      "while",
      "responsible for",
      "during"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "韧性测试：金融机构进行漏洞评估，主管当局进行渗透测试，并修复发现漏洞",
      "outcomes_or_paths": [
        "漏洞修复"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002034",
        "quote": "Financial institutions should conduct yearly vulnerability assessments, while the designated competent authorities are responsible for conducting threat-led penetration tests every three years."
      },
      {
        "unit_id": "v7u_N002035",
        "quote": "The financial institution utilizing a third-party service is primarily responsible for remediating vulnerabilities it identifies during end-to-end testing."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N002036",
      "v7u_N002037",
      "v7u_N002038"
    ],
    "proposition": "金融机构应对供应商进行事前尽职调查和持续监控，禁止与安全标准不足的供应商交易，并为关键AFC功能建立退出策略。",
    "source_quotes": [
      "Financial institutions should conduct ex-ante due diligence - meaning a preventative review before taking action - and ongoing monitoring of vendors.",
      "They should prohibit dealing with vendors that have insufficient security standards.",
      "To mitigate concentration risk, financial institutions should establish an exit strategy from vendor services related to critical AFC functions, such as sanction screening and transaction monitoring."
    ],
    "relation_cues": [
      "should",
      "prohibit",
      "to mitigate",
      "establish"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "为缓解集中风险"
      ],
      "focal_handling_or_judgment": "第三方风险管理：进行尽职调查和监控，禁止不合格交易，建立退出策略",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002036",
        "quote": "Financial institutions should conduct ex-ante due diligence - meaning a preventative review before taking action - and ongoing monitoring of vendors."
      },
      {
        "unit_id": "v7u_N002037",
        "quote": "They should prohibit dealing with vendors that have insufficient security standards."
      },
      {
        "unit_id": "v7u_N002038",
        "quote": "To mitigate concentration risk, financial institutions should establish an exit strategy from vendor services related to critical AFC functions, such as sanction screening and transaction monitoring."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N002039"
    ],
    "proposition": "关键ICT第三方服务提供商须接受欧盟层面监管，并须在欧盟设立子公司。",
    "source_quotes": [
      "Additionally, critical ICT third-party service providers are subject to EU-level supervision and obliged to establish a subsidiary in the EU."
    ],
    "relation_cues": [
      "subject to",
      "obliged to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "关键ICT第三方服务提供商"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "接受欧盟监管并设立欧盟子公司",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002039",
        "quote": "Additionally, critical ICT third-party service providers are subject to EU-level supervision and obliged to establish a subsidiary in the EU."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_007",
    "unit_ids": [
      "v7u_N002040"
    ],
    "proposition": "金融机构可定期共享威胁和漏洞情报，以预防安全事件发生；信息共享有助于其他金融机构有效控制影响并更快恢复。",
    "source_quotes": [
      "Financial institutions can regularly share information regarding threats and vulnerability intelligence to prevent the materialization of incidents. Information sharing enables other financial institutions to effectively contain impacts of financial crimes and recover faster."
    ],
    "relation_cues": [
      "can",
      "to prevent",
      "enables"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "金融机构共享威胁和漏洞情报",
      "outcomes_or_paths": [
        "预防事件发生",
        "帮助其他机构控制影响并恢复"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002040",
        "quote": "Financial institutions can regularly share information regarding threats and vulnerability intelligence to prevent the materialization of incidents. Information sharing enables other financial institutions to effectively contain impacts of financial crimes and recover faster."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_008",
    "unit_ids": [
      "v7u_N002041"
    ],
    "proposition": "满足DORA的网络安全和风险管理要求可降低犯罪分子利用数字漏洞进行洗钱的风险。",
    "source_quotes": [
      "By meeting DORA’s enhanced cybersecurity and risk management requirements, financial institutions reduce the risk that criminals and terrorists will exploit digital vulnerabilities to launder money through their accounts."
    ],
    "relation_cues": [
      "by meeting",
      "reduce"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "金融机构满足DORA要求"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "降低洗钱风险",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002041",
        "quote": "By meeting DORA’s enhanced cybersecurity and risk management requirements, financial institutions reduce the risk that criminals and terrorists will exploit digital vulnerabilities to launder money through their accounts."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
