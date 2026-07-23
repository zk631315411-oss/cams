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

section_id: `CH35-S02`

section_title: `Second LOD's AFC role and its interaction with the front office > Second LOD's interaction with other functions`

section_text_with_unit_anchors:

```text
[v7u_N002584|2584] The second line of defense AFC team interacts with various risk management and non-risk management functions to ensure effective risk oversight and regulatory compliance. These interactions maintain the organization's integrity and align functions with risk management strategies. Key functions include:
ZH: 第二道防线金融犯罪防控团队与多个风险管理及非风险管理职能互动，以确保有效的风险监督和合规。

[v7u_N002585|2585] Legal: Assists with interpreting regulations, handling compliance issues, and managing potential legal liabilities, such as reporting requirements and client offboarding in suspected money laundering cases.
ZH: 法律部门协助解释法规、处理合规问题及管理潜在法律责任，如可疑洗钱案件中的报告要求和客户退出。

[v7u_N002586|2586] Training and human resources (HR): Develops and implements materials on staff compliance, AML regulations, and internal policies to embed a culture of compliance, especially in the front office.
ZH: 培训与人力资源部门制定并实施员工合规、反洗钱法规及内部政策的材料，以嵌入合规文化。

[v7u_N002587|2587] In larger organizations, the learning and development team within HR might be responsible for training employees on compliance and risk management policies.
ZH: 在大型组织中，人力资源部门内的学习与发展团队可能负责员工合规与风险管理政策培训。

[v7u_N002588|2588] They ensure staff understand their roles in mitigating risks, including those related to AML/CFT.
ZH: 确保员工理解其在缓解风险（包括反洗钱/反恐怖融资相关风险）中的角色。

[v7u_N002589|2589] HR ensures employees are trained in compliance and risk management policies, and understand their roles in mitigating risks, including those related to AML/CFT.
ZH: 人力资源确保员工接受合规与风险管理政策培训，并理解其在缓解风险（包括反洗钱/反恐怖融资相关风险）中的角色。

[v7u_N002590|2590] HR may address employee accountability and disciplinary measures after a compliance breach.
ZH: 人力资源部门可在合规违规后处理员工问责和纪律措施。

[v7u_N002591|2591] Vendor management: Conduct due diligence and risk assessments, ensuring third-party vendors comply with AFC policies and do not pose additional risks.
ZH: 供应商管理部门对第三方供应商进行尽职调查和风险评估，确保其遵守金融犯罪防控政策且不带来额外风险。

[v7u_N002592|2592] Data integrity and privacy: The privacy team may help the second-line AFC team in drafting data protection impact assessments and advise on personal data handling and retention periods during suspicious activity investigations.
ZH: 隐私团队可协助第二道防线金融犯罪防控团队起草数据保护影响评估，并就可疑活动调查中的个人数据处理和保留期限提供建议。

[v7u_N002593|2593] For new procedures involving personal data for AML/CFT checks, the AFC team may need legal endorsement to navigate compliance.
ZH: 涉及个人数据的反洗钱/反恐怖融资新程序可能需要法律认可以确保合规。

[v7u_N002594|2594] If an organization processes customer identification data for AML/CFT compliance while also following the EU’s General Data Protection Regulation (GDPR), it must balance both requirements.
ZH: 组织在处理客户身份数据以符合反洗钱/反恐怖融资要求的同时，还需遵守欧盟《通用数据保护条例》，必须平衡两者。

[v7u_N002595|2595] The organization should work closely with its legal team to ensure lawful processing, data minimization, and proper handling of customer consent during CDD.
ZH: 组织应与法律团队密切合作，确保客户尽职调查过程中的合法处理、数据最小化及客户同意管理。

[v7u_N002596|2596] General compliance: Aligns broader compliance activities with financial crime risk assessments and mitigations, ensuring consistency in risk thresholds, compliance requirements, and monitoring efforts.
ZH: 一般合规职能将更广泛的合规活动与金融犯罪风险评估和缓解措施对齐，确保风险阈值、合规要求和监控工作的一致性。

[v7u_N002597|2597] Credit risk: Assesses credit requests and gathers data about a client's creditworthiness. Offboarding clients might require considering loan recovery.
ZH: 信用风险部门评估信贷请求并收集客户信用状况数据，客户退出时可能需要考虑贷款回收。

[v7u_N002598|2598] Reputational risks: Evaluates a client’s reputational concerns and the potential impacts to mitigate risks. If reputational risk does not directly involve AFC, decisions may be jointly made with, or escalated to, the second-line risk teams to determine the best course of action.
ZH: 声誉风险部门评估客户声誉问题及潜在影响以缓解风险；若不直接涉及金融犯罪防控，决策可能由第二道防线风险团队共同做出或上报。

[v7u_N002599|2599] Operational risk: Evaluates risks that organizations might encounter in dayto-day operations. Some organizations also manage fraud risk assessments as part of their operational risk management.
ZH: 操作风险部门评估组织在日常运营中可能遇到的风险，部分组织还将欺诈风险评估纳入操作风险管理。
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002585"
    ],
    "proposition": "在可疑洗钱案件中，法律部门协助处理报告要求和客户退出。",
    "source_quotes": [
      "Legal: Assists with interpreting regulations, handling compliance issues, and managing potential legal liabilities, such as reporting requirements and client offboarding in suspected money laundering cases."
    ],
    "relation_cues": [
      "such as",
      "in"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "可疑洗钱案件"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "法律部门协助处理报告要求和客户退出",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002585",
        "quote": "Legal: Assists with interpreting regulations, handling compliance issues, and managing potential legal liabilities, such as reporting requirements and client offboarding in suspected money laundering cases."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002590"
    ],
    "proposition": "合规违规后，人力资源部门可处理员工问责和纪律措施。",
    "source_quotes": [
      "HR may address employee accountability and disciplinary measures after a compliance breach."
    ],
    "relation_cues": [
      "may",
      "after"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "合规违规后"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "人力资源部门处理员工问责和纪律措施",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002590",
        "quote": "HR may address employee accountability and disciplinary measures after a compliance breach."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002593"
    ],
    "proposition": "涉及个人数据的反洗钱/反恐融资新程序可能需要法律认可。",
    "source_quotes": [
      "For new procedures involving personal data for AML/CFT checks, the AFC team may need legal endorsement to navigate compliance."
    ],
    "relation_cues": [
      "may",
      "involving"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "涉及个人数据的反洗钱/反恐融资新程序"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "金融犯罪防控团队可能需要法律认可",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002593",
        "quote": "For new procedures involving personal data for AML/CFT checks, the AFC team may need legal endorsement to navigate compliance."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N002594"
    ],
    "proposition": "组织在反洗钱/反恐融资合规中处理客户身份数据并同时遵守GDPR时，必须平衡两者要求。",
    "source_quotes": [
      "If an organization processes customer identification data for AML/CFT compliance while also following the EU’s General Data Protection Regulation (GDPR), it must balance both requirements."
    ],
    "relation_cues": [
      "if",
      "while",
      "must"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "组织处理客户身份数据以符合反洗钱/反恐融资要求并同时遵守GDPR"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "必须平衡两者要求",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002594",
        "quote": "If an organization processes customer identification data for AML/CFT compliance while also following the EU’s General Data Protection Regulation (GDPR), it must balance both requirements."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N002598"
    ],
    "proposition": "若声誉风险不直接涉及金融犯罪防控，决策可由第二道防线风险团队共同做出或上报。",
    "source_quotes": [
      "If reputational risk does not directly involve AFC, decisions may be jointly made with, or escalated to, the second-line risk teams to determine the best course of action."
    ],
    "relation_cues": [
      "if",
      "does not directly involve",
      "may",
      "or"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "声誉风险不直接涉及金融犯罪防控"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "决策由第二道防线风险团队共同做出或上报",
      "outcomes_or_paths": [
        "确定最佳行动方案"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002598",
        "quote": "If reputational risk does not directly involve AFC, decisions may be jointly made with, or escalated to, the second-line risk teams to determine the best course of action."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
