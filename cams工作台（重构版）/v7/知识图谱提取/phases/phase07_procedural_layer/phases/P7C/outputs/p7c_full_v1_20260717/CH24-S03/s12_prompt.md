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

section_id: `CH24-S03`

section_title: `US AML/CFT regulatory landscape > The Anti-Money Laundering Act of 2020`

section_text_with_unit_anchors:

```text
[v7u_N001710|1710] The main focus of the Anti-Money Laundering Act of 2020 (known as the AML Act in the US) was to modernize US banking laws and regulations for AML compliance.
ZH: 2020年《反洗钱法案》旨在现代化美国银行反洗钱合规法规

[v7u_N001711|1711] The act also broadens the use of AML practices to further national security and intelligence goals through greater transparency and enforcement measures.
ZH: 该法案通过提高透明度和执法措施，扩大反洗钱实践以促进国家安全和情报目标

[v7u_N001712|1712] This included the creation of a national Beneficial Ownership database, which will be updated with ownership information for entities required to register.
ZH: 创建国家受益所有人数据库，要求实体登记所有权信息

[v7u_N001713|1713] Additional rules, such as which financial institutions can access the database and how that information may be used, are anticipated in the future.
ZH: 预计未来将出台关于数据库访问权限和使用规则的补充规定

[v7u_N001714|1714] For example, the act expands AML compliance to include jurisdiction over activities in cryptocurrencies such as Bitcoin, as well as art and antique dealers.
ZH: 反洗钱合规范围扩大至加密货币及艺术品和古董经销商

[v7u_N001715|1715] The AML Act also includes new investigative powers regarding foreign financial institutions, while creating new criminal penalties for hiding transactions related to senior foreign political figures.
ZH: 新增针对外国金融机构的调查权，并对隐藏与外国高级政治人物相关交易的行为设定刑事处罚

[v7u_N001716|1716] The AML Act represents a strategic update to US banking law by including new financial technologies as well as national security priorities in AML compliance.
ZH: 《反洗钱法案》将新金融技术和国家安全优先事项纳入反洗钱合规，是美国银行法的战略更新

[v7u_N001717|1717] For example, the AML Act requires shell companies and other previously unregulated legal entities to disclose their beneficial owners and register ownership structures with FinCEN.
ZH: 要求壳公司等实体向FinCEN披露受益所有人并注册所有权结构

[v7u_N001718|1718] The act also extends protection for whistleblowers who alert authorities of AML regulatory violations.
ZH: 法案扩大对举报反洗钱违规行为的举报人保护

[v7u_N001719|1719] The goal is to broaden investigative powers to outline connections between entities like shell companies and their relationships with correspondent banks around the globe.
ZH: 目标是扩大调查权，以揭示壳公司等实体与全球代理行之间的关系

[v7u_N001720|1720] The AML Act also updates existing AML regulations to include cryptocurrency exchanges. They are considered to be money services businesses and have the same licensing and reporting requirements.
ZH: 法案将加密货币交易所视为货币服务企业，适用相同的许可和报告要求

[v7u_N001721|1721] Another goal of the AML Act is to transform SARs from a simple reporting requirement to a tool for intelligence gathering. SARs are now expected to provide a “high degree of usefulness” for law enforcement and national security agencies.
ZH: 《反洗钱法》将可疑交易报告转变为高价值情报工具

[v7u_N001722|1722] Additionally, there are provisions to facilitate cross-border sharing of SARs within financial institutions.
ZH: 《反洗钱法》允许金融机构内部跨境共享可疑交易报告

[v7u_N001723|1723] The AML Act also requires the development of further regulations to enhance strategic priorities regarding:
ZH: 《反洗钱法》要求制定进一步法规以强化战略优先事项

[v7u_N001724|1724] Corruption and fraud.
ZH: 战略优先事项包括腐败与欺诈

[v7u_N001725|1725] Cybercrime.
ZH: 战略优先事项包括网络犯罪

[v7u_N001726|1726] Terrorist financing.
ZH: 战略优先事项包括恐怖融资

[v7u_N001727|1727] Transnational criminal activity.
ZH: 战略优先事项包括跨国犯罪活动

[v7u_N001728|1728] Drug trafficking.
ZH: 战略优先事项包括毒品贩运

[v7u_N001729|1729] Human trafficking.
ZH: 战略优先事项包括人口贩运

[v7u_N001730|1730] Nuclear proliferation financing.
ZH: 战略优先事项包括核扩散融资

[v7u_N001731|1731] Pursuant to the AML Act, FinCEN has issued several notices of proposed rulemaking to further implement the AML Act. These include:
ZH: FinCEN 根据《反洗钱法》发布多项拟议规则制定通知

[v7u_N001732|1732] The requirement to maintain risk-based AML/CFT programs, such as mandatory risk assessment processes.
ZH: 要求维持基于风险的 反洗钱/反恐怖融资 计划，包括强制性风险评估流程

[v7u_N001733|1733] The incorporation of national priorities in institutions’ AML/CFT programs.
ZH: 要求将国家优先事项纳入机构的 反洗钱/反恐怖融资 计划

[v7u_N001734|1734] Additional rulemaking to further implement the AML Act and its legislative objectives will likely continue.
ZH: 《反洗钱法》的进一步规则制定可能会继续

[v7u_N001735|1735] The Financial Crimes Enforcement Network (FinCEN) is a bureau within the US Department of the Treasury. Its director reports to the Under Secretary for Terrorism and Financial Intelligence. FinCEN’s mission is to protect the financial system from illicit activities, combat financial crimes, and enhance national security.
ZH: FinCEN 是美国财政部下属机构，负责保护金融体系、打击金融犯罪并加强国家安全

[v7u_N001736|1736] The US Congress designates FinCEN as the central authority that collects, analyzes, and disseminates financial transaction data to support law enforcement, regulatory agencies, and policymakers.
ZH: 美国国会指定 FinCEN 为收集、分析和传播金融交易数据的中央权威机构

[v7u_N001737|1737] FinCEN’s analysis of data specifically plays a crucial role in combating AML and CFT as it assists in tracking fraud, tax evasion, narcotics trafficking, and terrorist financing.
ZH: FinCEN 的数据分析在打击洗钱和恐怖融资中发挥关键作用

[v7u_N001738|1738] FinCEN operates under the Bank Secrecy Act, which was amended by the USA PATRIOT Act.
ZH: FinCEN 依据《银行保密法》运作，该法经《爱国者法案》修订

[v7u_N001739|1739] The Bank Secrecy Act and its amendments grant FinCEN the authority to issue regulations, enforce compliance, and oversee AML programs in financial institutions.
ZH: 《银行保密法》授权 FinCEN 发布法规、执行合规并监督金融机构的反洗钱计划

[v7u_N001740|1740] For instance, FinCEN sets the standards for what constitutes suspicious activity and ensures that financial institutions properly file reports that could prove useful in criminal, tax, and counterterrorism investigations.
ZH: FinCEN 设定可疑活动标准并确保金融机构正确提交报告以支持调查

[v7u_N001741|1741] Additionally, FinCEN manages the collection, processing, storage, dissemination, and protection of Bank Secrecy Act data.
ZH: FinCEN 负责管理、保护《银行保密法》数据。

[v7u_N001742|1742] It partners with law enforcement in searching for information to investigate and prosecute entities involved in financial crime.
ZH: FinCEN 与执法部门合作，支持金融犯罪调查与起诉。

[v7u_N001743|1743] As the US FIU, FinCEN collaborates globally with over 100 FIUs within the Egmont Group, sharing financial intelligence to detect illicit financial flows. It also maintains a government-wide access service for financial crime data, helping federal, state, local, and international partners.
ZH: FinCEN 作为美国 FIU，与全球 100 多个 FIU 合作共享金融情报。

[v7u_N001744|1744] FinCEN’s key functions include:
ZH: FinCEN 的主要职能包括以下方面。

[v7u_N001745|1745] Issuing and enforcing AML/CFT regulations.
ZH: FinCEN 负责发布和执行 反洗钱/反恐怖融资 法规。

[v7u_N001746|1746] Supporting law enforcement in investigations and prosecutions.
ZH: FinCEN 支持执法部门的调查和起诉工作。

[v7u_N001747|1747] Managing and protecting Bank Secrecy Act data.
ZH: FinCEN 管理和保护《银行保密法》数据。

[v7u_N001748|1748] Coordinating with foreign FIUs on cross-border financial crime.
ZH: FinCEN 与外国 FIU 协调打击跨境金融犯罪。

[v7u_N001749|1749] Identifying financial crime risks and assisting with resource allocation.
ZH: FinCEN 识别金融犯罪风险并协助资源分配。

[v7u_N001750|1750] US financial regulators work collectively to ensure the financial system’s stability, integrity, and efficiency. The Office of the Comptroller of the Currency (OCC), Federal Reserve System (FRS), Federal Deposit Insurance Corporation (FDIC), and Securities and Exchange Commission (SEC) create a framework that safeguards financial institutions and consumers, mitigating risks that could threaten economic stability. They enforce compliance, promote transparency, and protect investors and depositors, while ensuring trust in financial markets.
ZH: 美国金融监管机构共同维护金融体系的稳定、完整和效率。

[v7u_N001751|1751] The OCC is an independent bureau within the US Department of the Treasury responsible for chartering, regulating, and supervising all national banks, federal savings associations, and US branches of foreign banks.
ZH: OCC 是财政部下属独立机构，负责全国性银行和联邦储蓄协会的监管。

[v7u_N001752|1752] It ensures that financial institutions operate safely and soundly, provide fair access to financial services, treat customers fairly, and comply with laws and regulations.
ZH: OCC 确保金融机构安全稳健运营、公平对待客户并遵守法律法规。

[v7u_N001753|1753] The FRS serves as the central bank of the US, working to ensure financial system stability by minimizing and containing systemic risks.
ZH: FRS 作为美国中央银行，致力于维护金融体系稳定。

[v7u_N001754|1754] It conducts several types of examinations to promote the safety and soundness of financial institutions while enhancing the efficiency and security of payment and settlement systems.
ZH: FRS 开展多种检查以促进金融机构安全稳健及支付结算系统效率。

[v7u_N001755|1755] Additionally, the FRS provides services to the banking industry and the US government, facilitating US dollar transactions and payments.
ZH: FRS 为银行业和美国政府提供美元交易和支付服务。

[v7u_N001756|1756] The FDIC is an independent agency established by Congress to uphold stability and public confidence in the US financial system. It fulfills this mission by insuring deposits, supervising financial institutions for safety, soundness, and consumer protection, and ensuring that financial institutions can be restructured or liquidated in an orderly manner if they fail.
ZH: FDIC 通过存款保险和监管维护金融体系稳定与公众信心。

[v7u_N001757|1757] The SEC oversees all aspects of the securities industry, ensuring investor protection, fair, orderly, and efficient markets, and capital formation.
ZH: SEC 监管证券行业，保护投资者并确保市场公平有序。

[v7u_N001758|1758] The president, with the Senate’s advice and consent, appoints up to five commissioners to lead the agency.
ZH: SEC 由总统任命并经参议院同意的最多五名委员领导。

[v7u_N001759|1759] By overseeing banking operations, managing systemic risks, insuring deposits, and regulating securities, these regulators collectively foster a resilient and well-functioning financial industry.
ZH: 各监管机构共同促进金融业的韧性和良好运作。

[v7u_N001760|1760] If a financial institution is found in violation of US laws and regulations related to financial crime, these regulators can impose civil monetary penalties, forfeiture of proceeds, limitations on future business activities, and criminal charges against the bank or its officers.
ZH: 金融机构违反金融犯罪法规时，监管机构可处以民事罚款、没收收益、限制业务或提起刑事指控。
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N001717"
    ],
    "proposition": "AML Act要求壳公司等实体向FinCEN披露受益所有人并注册所有权结构。",
    "source_quotes": [
      "For example, the AML Act requires shell companies and other previously unregulated legal entities to disclose their beneficial owners and register ownership structures with FinCEN."
    ],
    "relation_cues": [
      "requires",
      "disclose",
      "register"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "壳公司及其他未受监管的法律实体"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "向FinCEN披露受益所有人并注册所有权结构",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001717",
        "quote": "For example, the AML Act requires shell companies and other previously unregulated legal entities to disclose their beneficial owners and register ownership structures with FinCEN."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N001720"
    ],
    "proposition": "AML Act将加密货币交易所视为货币服务企业，适用相同的许可和报告要求。",
    "source_quotes": [
      "The AML Act also updates existing AML regulations to include cryptocurrency exchanges. They are considered to be money services businesses and have the same licensing and reporting requirements."
    ],
    "relation_cues": [
      "considered",
      "same"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "加密货币交易所"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "视为货币服务企业，适用相同许可和报告要求",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001720",
        "quote": "The AML Act also updates existing AML regulations to include cryptocurrency exchanges. They are considered to be money services businesses and have the same licensing and reporting requirements."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N001721"
    ],
    "proposition": "AML Act将可疑交易报告转变为情报工具，要求提供“高度有用性”。",
    "source_quotes": [
      "Another goal of the AML Act is to transform SARs from a simple reporting requirement to a tool for intelligence gathering. SARs are now expected to provide a “high degree of usefulness” for law enforcement and national security agencies."
    ],
    "relation_cues": [
      "transform",
      "expected"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "可疑交易报告（SARs）"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "转变为情报工具，要求提供高度有用性",
      "outcomes_or_paths": [
        "对执法和国家安全机构提供高度有用性"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001721",
        "quote": "Another goal of the AML Act is to transform SARs from a simple reporting requirement to a tool for intelligence gathering. SARs are now expected to provide a “high degree of usefulness” for law enforcement and national security agencies."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N001722"
    ],
    "proposition": "AML Act允许金融机构内部跨境共享可疑交易报告。",
    "source_quotes": [
      "Additionally, there are provisions to facilitate cross-border sharing of SARs within financial institutions."
    ],
    "relation_cues": [
      "facilitate",
      "cross-border sharing"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "金融机构内部"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "跨境共享可疑交易报告",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001722",
        "quote": "Additionally, there are provisions to facilitate cross-border sharing of SARs within financial institutions."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N001731",
      "v7u_N001732"
    ],
    "proposition": "FinCEN根据AML Act发布拟议规则通知，要求金融机构维持基于风险的AML/CFT计划，包括强制性风险评估流程。",
    "source_quotes": [
      "Pursuant to the AML Act, FinCEN has issued several notices of proposed rulemaking to further implement the AML Act. These include:",
      "The requirement to maintain risk-based AML/CFT programs, such as mandatory risk assessment processes."
    ],
    "relation_cues": [
      "pursuant to",
      "requirement"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "AML Act"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "FinCEN发布拟议规则通知，要求维持基于风险的AML/CFT计划及强制性风险评估",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001731",
        "quote": "Pursuant to the AML Act, FinCEN has issued several notices of proposed rulemaking to further implement the AML Act. These include:"
      },
      {
        "unit_id": "v7u_N001732",
        "quote": "The requirement to maintain risk-based AML/CFT programs, such as mandatory risk assessment processes."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N001740"
    ],
    "proposition": "FinCEN设定可疑活动标准并确保金融机构正确提交报告以支持调查。",
    "source_quotes": [
      "For instance, FinCEN sets the standards for what constitutes suspicious activity and ensures that financial institutions properly file reports that could prove useful in criminal, tax, and counterterrorism investigations."
    ],
    "relation_cues": [
      "sets",
      "ensures"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "FinCEN设定可疑活动标准并确保金融机构正确提交报告",
      "outcomes_or_paths": [
        "报告可用于刑事、税务和反恐调查"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001740",
        "quote": "For instance, FinCEN sets the standards for what constitutes suspicious activity and ensures that financial institutions properly file reports that could prove useful in criminal, tax, and counterterrorism investigations."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_007",
    "unit_ids": [
      "v7u_N001760"
    ],
    "proposition": "金融机构违反金融犯罪法规时，监管机构可处以民事罚款、没收收益、限制业务或提起刑事指控。",
    "source_quotes": [
      "If a financial institution is found in violation of US laws and regulations related to financial crime, these regulators can impose civil monetary penalties, forfeiture of proceeds, limitations on future business activities, and criminal charges against the bank or its officers."
    ],
    "relation_cues": [
      "if",
      "can impose"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "金融机构违反金融犯罪相关法律法规"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "监管机构施加处罚",
      "outcomes_or_paths": [
        "民事罚款",
        "没收收益",
        "限制未来业务活动",
        "对银行或高管提起刑事指控"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001760",
        "quote": "If a financial institution is found in violation of US laws and regulations related to financial crime, these regulators can impose civil monetary penalties, forfeiture of proceeds, limitations on future business activities, and criminal charges against the bank or its officers."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
