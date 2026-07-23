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

section_id: `CH24-S13`

section_title: `US AML/CFT regulatory landscape > Australia AML regulations`

section_text_with_unit_anchors:

```text
[v7u_N001868|1868] Legislation includes AML/CTF Act 2006 and AML/CTF Amendment Act 2024.
ZH: 澳大利亚反洗钱/反恐怖融资立法包括2006年反洗钱/反恐怖融资法案及2024年修正案

[v7u_N001869|1869] The amendments introduce several provisions, including:
ZH: 修正案引入了若干条款

[v7u_N001870|1870] Extending AML/CFT obligations to DNFBPs.
ZH: 将反洗钱/反恐怖融资义务扩展至指定非金融行业和职业（DNFBPs）

[v7u_N001871|1871] Granting AUSTRAC enhanced enforcement powers.
ZH: 授予AUSTRAC更强的执法权力

[v7u_N001872|1872] Amending tipping off provisions.
ZH: 修改泄密（tipping off）条款

[v7u_N001873|1873] Emphasizing the risk-based approach.
ZH: 强调基于风险的方法（RBA）

[v7u_N001874|1874] Legislation requires entities to comply with the new obligations by 2026.
ZH: 立法要求实体在2026年前遵守新义务

[v7u_N001875|1875] The primary legislation governing AML/CFT in Australia is the Anti-Money Laundering and Counter-Terrorism Financing Act 2006 (AML/CTF Act 2006).
ZH: 澳大利亚反洗钱/反恐怖融资主要立法是2006年反洗钱/反恐怖融资法案

[v7u_N001876|1876] This act requires reporting entities to implement and maintain an AML/CFT compliance program. This program includes risk assessment, internal controls for CDD and regulatory reporting, employee training, and independent reviews.
ZH: 该法案要求报告实体实施并维护反洗钱/反恐怖融资合规计划

[v7u_N001877|1877] Australia recently passed the AML/CTF Amendment Act 2024, which is a significant enhancement of its AML/CFT framework.
ZH: 澳大利亚近期通过了2024年反洗钱/反恐怖融资修正案，显著增强反洗钱/反恐怖融资框架

[v7u_N001878|1878] The purpose of the amendments is to ensure Australia’s laws align with FATF’s international standards and continue to effectively deter, detect, and disrupt money laundering as well as terrorism financing and proliferation financing.
ZH: 修正案旨在使澳大利亚法律符合FATF国际标准

[v7u_N001879|1879] The AML/CTF Amendment Act 2024 introduces several key provisions, including:
ZH: 2024年反洗钱/反恐怖融资修正案引入多项关键条款

[v7u_N001880|1880] Extending AML/CFT obligations to DNFBPs, such as real estate agents, legal professionals, accountants, and dealers in precious metals and stones. This includes the obligations to identify and verify customers, conduct ongoing monitoring, and report suspicious activities to AUSTRAC.
ZH: 反洗钱/反恐怖融资义务扩展至DNFBPs，包括房地产中介、律师、会计师等

[v7u_N001881|1881] Granting AUSTRAC enhanced enforcement powers, including the ability to impose higher penalties for noncompliance, issue remedial directions, and pursue civil and criminal actions against entities that breach AML/CFT obligations.
ZH: AUSTRAC获得增强执法权，可对违反反洗钱/反恐怖融资义务的实体处以更高罚款、发出补救指示并提起民事或刑事诉讼。

[v7u_N001882|1882] Amending tipping off provisions to facilitate greater information sharing between regulatory bodies, law enforcement agencies, and international counterparts.
ZH: 修改举报规定，促进监管机构、执法机构与国际同行之间的信息共享。

[v7u_N001883|1883] Emphasizing the risk-based approach, allowing entities to tailor their AML/CFT measures based on the level of risk identified. This approach ensures that resources are allocated effectively to mitigate higher-risk areas.
ZH: 强调风险为本方法，允许实体根据识别出的风险水平调整反洗钱/反恐怖融资措施，确保资源有效配置以缓解高风险领域。

[v7u_N001884|1884] Reporting entities will be required to comply with many of the new obligations by March 2026.
ZH: 报告实体须在2026年3月前遵守多项新义务。

[v7u_N001885|1885] AUSTRAC is the principal regulatory authority responsible for overseeing the AML/CFT regime in Australia. It acts as both a national FIU and a regulatory agency, collecting and analyzing financial transaction reports, monitoring compliance with AML/CFT obligations, and enforcing regulatory actions against noncompliant entities.
ZH: AUSTRAC是澳大利亚负责监督反洗钱/反恐怖融资制度的主要监管机构，兼具国家FIU和监管机构职能。

[v7u_N001886|1886] The Australian Sanctions Office (ASO) within the Department of Foreign Affairs and Trade (DFAT) administers Australia's sanctions regime, implementing and enforcing UNSC sanctions and Australian autonomous sanctions.
ZH: 澳大利亚制裁办公室（ASO）隶属于外交贸易部，负责管理澳大利亚制裁制度，执行联合国安理会制裁和澳大利亚自主制裁。

[v7u_N001887|1887] DFAT coordinates with AUSTRAC and other regulatory bodies to ensure that entities comply with sanctions obligations.
ZH: 外交贸易部与AUSTRAC及其他监管机构协调，确保实体遵守制裁义务。

[v7u_N001888|1888] Singapore's National AML Strategy was updated in October 2024 and outlines its approach to combat money laundering risks, emphasizing a three-pillar framework of prevention, detection, and enforcement.
ZH: 新加坡于2024年10月更新国家反洗钱战略，强调预防、检测和执法三大支柱框架。

[v7u_N001889|1889] Singapore follows a risk-based approach to AML/CFT compliance. This approach requires financial institutions and DNFBPs to implement CDD, enhanced due diligence for high-risk clients, ongoing transaction monitoring, and suspicious transaction reporting.
ZH: 新加坡要求金融机构和DNFBP实施风险为本的反洗钱/反恐怖融资合规措施，包括客户尽职调查、强化尽职调查、持续交易监控和可疑交易报告。

[v7u_N001890|1890] The key legislation governing AML/CFT in Singapore includes:
ZH: 列举新加坡反洗钱/反恐怖融资关键立法。

[v7u_N001891|1891] The Corruption, Drug Trafficking and Other Serious Crimes (Confiscation of Benefits) Act 1992: Criminalizes money laundering and mandates reporting of suspicious transactions.
ZH: 《腐败、贩毒和其他严重犯罪（没收利益）法》将洗钱定为犯罪并规定可疑交易报告义务。

[v7u_N001892|1892] The Terrorism (Suppression of Financing) Act 2002: Addresses the criminalization and prevention of terrorism financing.
ZH: 《恐怖主义（制止资助）法》将恐怖融资定为犯罪并加以预防。

[v7u_N001893|1893] Singapore's major regulators include:
ZH: 列举新加坡主要监管机构。

[v7u_N001894|1894] Monetary Authority of Singapore: Regulates financial institutions, DNFBPs, and non-profit organizations, and issues AML/CFT guidelines, and supervises compliance.
ZH: 新加坡金融管理局监管金融机构、DNFBP和非营利组织，发布反洗钱/反恐怖融资指引并监督合规。

[v7u_N001895|1895] Commercial Affairs Department of the Singapore Police Force: Investigates financial crimes, including money laundering and fraud.
ZH: 新加坡警察部队商业事务局调查包括洗钱和欺诈在内的金融犯罪。

[v7u_N001896|1896] Accounting and Corporate Regulatory Authority: Oversees corporate entities and enforces AML/CFT obligations on corporate service providers.
ZH: 会计与企业管理局监管企业实体并对企业服务提供商执行反洗钱/反恐怖融资义务。

[v7u_N001897|1897] Casino Regulatory Authority and Gambling Regulatory Authority: Monitor AML/CFT compliance in the gaming sector.
ZH: 赌场监管局和赌博监管局监督博彩业的反洗钱/反恐怖融资合规。

[v7u_N001898|1898] Additionally, DNFBP sectors are regulated for AML/CFT by their licensing authority, registration authority, or self-regulatory body.
ZH: DNFBP行业由其发牌机构、注册机构或自律机构进行反洗钱/反恐怖融资监管。

[v7u_N001899|1899] Precious stones and metal dealers other than pawnbrokers are not considered part of these DNFBP sectors.
ZH: 除当铺外的宝石和贵金属经销商不属于DNFBP行业。

[v7u_N001900|1900] The Suspicious Transaction Reporting Office (STRO) is the FIU of the jurisdiction. STRO is part of the Singapore Police Force and responsible for receiving and analyzing financial intelligence.
ZH: 可疑交易报告办公室（STRO）是新加坡的金融情报机构，隶属于新加坡警察部队，负责接收和分析金融情报。

[v7u_N001901|1901] In addition to the legislation, the following are also useful resources for AFC professionals:
ZH: 除立法外，金融犯罪防控专业人员可参考的其他有用资源

[v7u_N001902|1902] Monetary Authority of Singapore notices and guidelines: Set compliance obligations for obligated entities
ZH: 新加坡金融管理局的通知和指南为义务实体设定合规义务

[v7u_N001903|1903] AML/CFT Industry Partnership guidelines and best practice papers: Enable the financial sector, regulators, law enforcement agencies, and other government entities to collaboratively identify, assess, and mitigate emerging risks. This self-regulatory approach is effective in delivering benefits to customers and strengthening the commercial and investment banking industry.
ZH: 反洗钱/反恐怖融资行业伙伴关系指南和最佳实践文件促进金融业、监管机构、执法机构等协作识别、评估和缓解新兴风险
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N001875",
      "v7u_N001876"
    ],
    "proposition": "AML/CTF法案要求报告实体实施并维护反洗钱/反恐怖融资合规计划，包括风险评估、内控、员工培训和独立审查。",
    "source_quotes": [
      "The primary legislation governing AML/CFT in Australia is the Anti-Money Laundering and Counter-Terrorism Financing Act 2006 (AML/CTF Act 2006).",
      "This act requires reporting entities to implement and maintain an AML/CFT compliance program. This program includes risk assessment, internal controls for CDD and regulatory reporting, employee training, and independent reviews."
    ],
    "relation_cues": [
      "requires",
      "implement and maintain"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "报告实体"
      ],
      "basis_or_condition": [
        "AML/CTF Act 2006"
      ],
      "focal_handling_or_judgment": "实施并维护AML/CFT合规计划",
      "outcomes_or_paths": [
        "包括风险评估、内控、员工培训和独立审查"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001875",
        "quote": "The primary legislation governing AML/CFT in Australia is the Anti-Money Laundering and Counter-Terrorism Financing Act 2006 (AML/CTF Act 2006)."
      },
      {
        "unit_id": "v7u_N001876",
        "quote": "This act requires reporting entities to implement and maintain an AML/CFT compliance program. This program includes risk assessment, internal controls for CDD and regulatory reporting, employee training, and independent reviews."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N001880"
    ],
    "proposition": "修正案将反洗钱/反恐怖融资义务扩展至DNFBPs，包括识别验证客户、持续监控和报告可疑活动。",
    "source_quotes": [
      "Extending AML/CFT obligations to DNFBPs, such as real estate agents, legal professionals, accountants, and dealers in precious metals and stones. This includes the obligations to identify and verify customers, conduct ongoing monitoring, and report suspicious activities to AUSTRAC."
    ],
    "relation_cues": [
      "Extending",
      "includes"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "DNFBPs"
      ],
      "basis_or_condition": [
        "AML/CTF Amendment Act 2024"
      ],
      "focal_handling_or_judgment": "承担AML/CFT义务",
      "outcomes_or_paths": [
        "识别验证客户、持续监控、向AUSTRAC报告可疑活动"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001880",
        "quote": "Extending AML/CFT obligations to DNFBPs, such as real estate agents, legal professionals, accountants, and dealers in precious metals and stones. This includes the obligations to identify and verify customers, conduct ongoing monitoring, and report suspicious activities to AUSTRAC."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N001881"
    ],
    "proposition": "修正案授予AUSTRAC增强执法权，包括对违规实体处以更高罚款、发出补救指示以及提起民事或刑事诉讼。",
    "source_quotes": [
      "Granting AUSTRAC enhanced enforcement powers, including the ability to impose higher penalties for noncompliance, issue remedial directions, and pursue civil and criminal actions against entities that breach AML/CFT obligations."
    ],
    "relation_cues": [
      "Granting",
      "including"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "实体违反AML/CFT义务"
      ],
      "basis_or_condition": [
        "AML/CTF Amendment Act 2024"
      ],
      "focal_handling_or_judgment": "AUSTRAC行使增强执法权",
      "outcomes_or_paths": [
        "处以更高罚款、发出补救指示、提起民事或刑事诉讼"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001881",
        "quote": "Granting AUSTRAC enhanced enforcement powers, including the ability to impose higher penalties for noncompliance, issue remedial directions, and pursue civil and criminal actions against entities that breach AML/CFT obligations."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N001883"
    ],
    "proposition": "修正案强调风险为本方法，允许实体根据识别的风险水平定制反洗钱/反恐怖融资措施，以确保资源有效配置。",
    "source_quotes": [
      "Emphasizing the risk-based approach, allowing entities to tailor their AML/CFT measures based on the level of risk identified. This approach ensures that resources are allocated effectively to mitigate higher-risk areas."
    ],
    "relation_cues": [
      "Emphasizing",
      "allowing",
      "based on"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "实体识别出风险水平"
      ],
      "basis_or_condition": [
        "风险为本方法"
      ],
      "focal_handling_or_judgment": "定制AML/CFT措施",
      "outcomes_or_paths": [
        "确保资源有效配置以缓解高风险领域"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001883",
        "quote": "Emphasizing the risk-based approach, allowing entities to tailor their AML/CFT measures based on the level of risk identified. This approach ensures that resources are allocated effectively to mitigate higher-risk areas."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N001889"
    ],
    "proposition": "新加坡采用风险为本反洗钱/反恐怖融资合规方法，要求金融机构和DNFBPs实施客户尽职调查、强化尽职调查、持续交易监控和可疑交易报告。",
    "source_quotes": [
      "Singapore follows a risk-based approach to AML/CFT compliance. This approach requires financial institutions and DNFBPs to implement CDD, enhanced due diligence for high-risk clients, ongoing transaction monitoring, and suspicious transaction reporting."
    ],
    "relation_cues": [
      "follows",
      "requires",
      "risk-based"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "金融机构和DNFBPs"
      ],
      "basis_or_condition": [
        "风险为本方法"
      ],
      "focal_handling_or_judgment": "实施AML/CFT合规措施",
      "outcomes_or_paths": [
        "客户尽职调查、强化尽职调查、持续监控、可疑交易报告"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001889",
        "quote": "Singapore follows a risk-based approach to AML/CFT compliance. This approach requires financial institutions and DNFBPs to implement CDD, enhanced due diligence for high-risk clients, ongoing transaction monitoring, and suspicious transaction reporting."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N001891"
    ],
    "proposition": "《腐败、贩毒和其他严重犯罪（没收利益）法》将洗钱定为犯罪并规定可疑交易报告义务。",
    "source_quotes": [
      "The Corruption, Drug Trafficking and Other Serious Crimes (Confiscation of Benefits) Act 1992: Criminalizes money laundering and mandates reporting of suspicious transactions."
    ],
    "relation_cues": [
      "Criminalizes",
      "mandates"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "洗钱行为"
      ],
      "basis_or_condition": [
        "CDSA 1992"
      ],
      "focal_handling_or_judgment": "将洗钱定为犯罪",
      "outcomes_or_paths": [
        "规定可疑交易报告义务"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001891",
        "quote": "The Corruption, Drug Trafficking and Other Serious Crimes (Confiscation of Benefits) Act 1992: Criminalizes money laundering and mandates reporting of suspicious transactions."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_007",
    "unit_ids": [
      "v7u_N001892"
    ],
    "proposition": "《恐怖主义（制止资助）法》将恐怖融资定为犯罪并加以预防。",
    "source_quotes": [
      "The Terrorism (Suppression of Financing) Act 2002: Addresses the criminalization and prevention of terrorism financing."
    ],
    "relation_cues": [
      "criminalization",
      "prevention"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "恐怖融资行为"
      ],
      "basis_or_condition": [
        "TSOF Act 2002"
      ],
      "focal_handling_or_judgment": "将恐怖融资定为犯罪并预防",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001892",
        "quote": "The Terrorism (Suppression of Financing) Act 2002: Addresses the criminalization and prevention of terrorism financing."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
