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

section_id: `CH02-S01`

section_title: `Types of financial crime > Predicate crimes and money laundering`

section_text_with_unit_anchors:

```text
[v7u_N000060|60] Predicate crimes are specified unlawful activities whose proceeds can give rise to prosecution for money laundering.
ZH: 上游犯罪是指其收益可导致洗钱起诉的特定非法活动

[v7u_N000061|61] Individuals or organizations who engage in predicate crimes often want to "clean," or launder the proceeds from these crimes so they can use them legitimately without drawing attention from law enforcement.
ZH: 实施上游犯罪的个人或组织清洗犯罪收益以合法使用

[v7u_N000062|62] FATF has identified 21 categories of predicate offenses that financial institutions must acknowledge and monitor under AML compliance programs.
ZH: FATF 确定了金融机构必须关注的 21 类上游犯罪

[v7u_N000063|63] However, different jurisdictions might classify these offenses differently.
ZH: 不同司法管辖区对上游犯罪的分类存在差异

[v7u_N000064|64] For example, while some countries have strong laws against human trafficking, others do not recognize certain forms of exploitation as criminal offenses.
ZH: 举例：各国对人口贩卖的法律认定不同导致分类差异

[v7u_N000065|65] This variation can complicate AML efforts, with compliance professionals operating in cross-border contexts needing to align risk controls with the laws and regulations of more than one jurisdiction.
ZH: 跨境反洗钱合规需协调多个司法管辖区的法律差异

[v7u_N000066|66] The list of 21 FATF-designated predicate crimes includes:
ZH: FATF 指定的 21 类上游犯罪清单引述

[v7u_N000067|67] 1. Participation in an organized criminal group and racketeering: Engaging in systemic financial crimes
ZH: 参与有组织犯罪集团和敲诈勒索属于上游犯罪

[v7u_N000068|68] 2. Terrorism, including terrorist financing: Providing financial support to these operations
ZH: 恐怖主义及恐怖融资属于上游犯罪

[v7u_N000069|69] 3. Trafficking in human beings and migrant smuggling: Generating illicit profits through human exploitation
ZH: 人口贩卖和偷运移民属于上游犯罪

[v7u_N000070|70] 4. Sexual exploitation, including that of children: Crimes linked to forced prostitution and human trafficking
ZH: 性剥削（包括儿童性剥削）属于上游犯罪

[v7u_N000071|71] 5. Illicit trafficking in narcotic drugs and psychotropic substances: Production, transportation, and sale of illegal substances
ZH: 非法贩运麻醉药品和精神药物属于上游犯罪

[v7u_N000072|72] 6. Illicit arms trafficking: Illegal trade and smuggling of firearms and explosives
ZH: 非法武器贩运属于上游犯罪

[v7u_N000073|73] 7. Illicit trafficking of stolen and other goods: Black market trade of stolen and counterfeit items
ZH: 非法贩运被盗物品及其他货物属于上游犯罪

[v7u_N000074|74] 8. Corruption and bribery: Abuse of power in public or private sectors for financial gain
ZH: 腐败和贿赂属于上游犯罪

[v7u_N000075|75] 9. Fraud: Financial deception, scams, and identity theft schemes
ZH: 欺诈属于上游犯罪

[v7u_N000076|76] 10. Counterfeiting currency: Illegal manufacturing of banknotes
ZH: 伪造货币属于上游犯罪

[v7u_N000077|77] 11. Counterfeiting and piracy of products: Violations of intellectual property, including counterfeit goods
ZH: 假冒和盗版产品属于上游犯罪

[v7u_N000078|78] 12. Environmental crime: Logging, poaching, and waste disposal
ZH: 环境犯罪属于上游犯罪

[v7u_N000079|79] 13. Murder and grievous bodily injury: Violent crimes motivated by financial gain
ZH: 谋杀和严重身体伤害属于上游犯罪

[v7u_N000080|80] 14. Kidnapping, illegal restraint, and hostage-taking: Crimes involving ransom demands
ZH: 绑架、非法拘禁和劫持人质属于上游犯罪

[v7u_N000081|81] 15. Robbery or theft: Large-scale property crimes driven by financial motives
ZH: 抢劫或盗窃：出于财务动机的大规模财产犯罪

[v7u_N000082|82] 16. Smuggling (including in relation to customs and excise duties and taxes): Illegal movement of goods to evade duties
ZH: 走私（包括关税和消费税相关）：为逃避关税而非法移动货物

[v7u_N000083|83] 17. Tax crimes (related to direct and indirect taxes): Tax fraud and false reporting schemes
ZH: 税收犯罪（直接税和间接税）：税务欺诈和虚假申报计划

[v7u_N000084|84] 18. Extortion: Coercing for financial gain through threats or intimidation
ZH: 敲诈勒索：通过威胁或恐吓强迫获取经济利益

[v7u_N000085|85] 19. Forgery: Falsifying documents, financial records, or identities
ZH: 伪造：伪造文件、财务记录或身份信息

[v7u_N000086|86] 20.Piracy: Maritime or cyber-based hijacking for financial gain
ZH: 海盗行为：为获取经济利益而进行的海上或网络劫持

[v7u_N000087|87] 21. Insider trading and market manipulation: Illegal use of nonpublic information to achieve profits
ZH: 内幕交易和市场操纵：利用非公开信息非法获利

[v7u_N000088|88] Economic sanctions, whether asset freezes or sector-specific restrictions, impose high financial, reputational, and operational costs on individuals and entities targeted by them.
ZH: 制裁对目标个人和实体施加高额财务、声誉和运营成本

[v7u_N000089|89] For this reason, sanctions targets often attempt to evade or circumvent sanctions in order to secretly engage in a prohibited activity, such as continuing to use an asset or receive economic benefits.
ZH: 制裁目标常试图规避制裁以秘密从事被禁止的活动

[v7u_N000090|90] For example, a designated individual might evade personal sanctions and continue using his luxury yacht by obscuring its ownership.
ZH: 示例：被制裁个人通过隐藏豪华游艇所有权规避个人制裁

[v7u_N000091|91] Sanctions evasion can be internal, with the help of personnel at an organization, or external, when evaders try to bypass internal controls without assistance from the inside.
ZH: 制裁规避可分为内部规避（借助内部人员）和外部规避

[v7u_N000092|92] Methods of sanctions evasion include payments, trade, and ownership.
ZH: 制裁规避方法包括支付、贸易和所有权相关手段

[v7u_N000093|93] Payment-related evasion occurs when, for example, Bank A attempts to have Bank B process prohibited transactions, with or without help from Bank B insiders.
ZH: 支付相关规避：银行A试图让银行B处理被禁止交易

[v7u_N000094|94] Identifying information is removed, or stripped, from payment instructions to avoid detection.
ZH: 从支付指令中移除识别信息以逃避检测

[v7u_N000095|95] Nested and payable accounts are particularly vulnerable to this evasion typology.
ZH: 嵌套账户和应付账户特别容易受到支付信息剥离的规避手法影响

[v7u_N000096|96] Trade-related evasion involves illegally importing or exporting goods without proper licensing or despite trade bans.
ZH: 贸易相关规避：未经适当许可或违反贸易禁令非法进出口货物

[v7u_N000097|97] Common techniques include the use of shell companies, switching cargo on the open sea (also known as transshipment), and using neutral or opaque jurisdictions for transit.
ZH: 贸易规避常见手法：使用壳公司、公海换货（转运）、利用中立或保密司法管辖区

[v7u_N000098|98] Ownership-related evasion involves obscuring the ownership of an asset by a designated person. This can be achieved by using complex corporate structures, proxies, and bearer shares and by diluting ownership.
ZH: 所有权相关规避：通过复杂公司结构、代理人、不记名股票和稀释所有权隐藏资产所有权

[v7u_N000099|99] Regulated entities must have strong AML and sanctions compliance programs with robust policies, procedures, and internal controls for detecting and preventing sanctions evasion. The penalties for noncompliance and failing to prevent sanctions evasion could include:
ZH: 受监管实体必须建立强大的反洗钱和制裁合规计划，违规处罚包括：

[v7u_N000100|100] Civil monetary penalties against organizations
ZH: 对组织的民事罚款

[v7u_N000101|101] Civil and criminal prosecution of individuals
ZH: 个人可能面临洗钱相关民事和刑事起诉

[v7u_N000102|102] Designations as a sanctions target
ZH: 个人可能被列为制裁目标

[v7u_N000103|103] Businessman Alexei Komarov amassed his fortune through Volkof Industries, a high-tech distribution company with clients worldwide. Though some of his customers were from a wide range of industries (from consumer electronics and automotive to healthcare and industrial manufacturing), most sales went to a foreign government engaged in nuclear weapons development. After UN sanctions targeted this proliferation activity, Volkof Industries faced restrictions, losing its access to global markets.
ZH: Alexei Komarov通过Volkof Industries从事扩散融资的案例

[v7u_N000104|104] Facing financial collapse, Komarov was determined to find a way to continue trading.
ZH: Komarov面临财务崩溃，决心继续交易

[v7u_N000105|105] To evade the sanctions, he created a shell company, RedStar Solutions.
ZH: Komarov创建壳公司RedStar Solutions以规避制裁

[v7u_N000106|106] He incorporated it in a jurisdiction with limited regulatory expectations toward AML and sanctions compliance and masked it as a technical support and maintenance service provider.
ZH: 在监管宽松的司法管辖区注册壳公司并伪装成技术服务商

[v7u_N000107|107] Through RedStar, he resumed exports to the foreign government developing its nuclear weapons program, using transshipment points in permissive jurisdictions and falsified invoices that labeled export-controlled items, such as semiconductors, as “industrial machinery and spare parts.”
ZH: 通过转运点和伪造发票恢复出口受控物品

[v7u_N000108|108] RedStar also employed local distributors in those jurisdictions to further distance Komarov and Volkof Industries from the transactions and paid them to ensure the shipments were received without question.
ZH: 利用当地分销商进一步掩盖交易关联

[v7u_N000109|109] To launder the proceeds back to Volkof Industries, Komarov routed payments through offshore accounts and shell companies. He was thus able to credit Volkof Industries’ accounts using laundered funds from the illegal activities of RedStar.
ZH: 通过离岸账户和壳公司清洗非法收益的示例

[v7u_N000110|110] Komarov’s goal was not just to hide the profits of RedStar, but to keep Volkof Industries trading, as its name still carried weight in industry circles. Despite UN sanctions against Volkof Industries, this strategy helped the company meet loan obligations, retain employees, and strengthen business ties to the foreign government, its main client.
ZH: Komarov的双重目标：隐藏利润并维持Volkof Industries运营

[v7u_N000111|111] The scheme unraveled when a bank’s compliance officer flagged irregular payment flows linked to RedStar. Further investigation exposed the illicit network, revealing Komarov and Volkof Industries’ role in sanctions evasion, proliferation financing, laundering criminal proceeds, and foreign bribery and corruption offences.
ZH: 合规官发现异常支付，揭露制裁规避、扩散融资、洗钱等犯罪
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N000062"
    ],
    "proposition": "金融机构必须承认并监控FATF确定的21类上游犯罪。",
    "source_quotes": [
      "FATF has identified 21 categories of predicate offenses that financial institutions must acknowledge and monitor under AML compliance programs."
    ],
    "relation_cues": [
      "must",
      "acknowledge and monitor"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "金融机构的AML合规项目"
      ],
      "basis_or_condition": [
        "FATF确定的21类上游犯罪"
      ],
      "focal_handling_or_judgment": "承认并监控这些犯罪类别",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000062",
        "quote": "FATF has identified 21 categories of predicate offenses that financial institutions must acknowledge and monitor under AML compliance programs."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N000099",
      "v7u_N000100",
      "v7u_N000101",
      "v7u_N000102"
    ],
    "proposition": "受监管实体必须建立强大的反洗钱和制裁合规计划，否则可能面临民事罚款、个人刑事起诉以及被列为制裁目标等处罚。",
    "source_quotes": [
      "Regulated entities must have strong AML and sanctions compliance programs with robust policies, procedures, and internal controls for detecting and preventing sanctions evasion. The penalties for noncompliance and failing to prevent sanctions evasion could include:",
      "Civil monetary penalties against organizations",
      "Civil and criminal prosecution of individuals",
      "Designations as a sanctions target"
    ],
    "relation_cues": [
      "must",
      "penalties",
      "noncompliance"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "存在制裁规避风险或需要检测和预防制裁规避"
      ],
      "basis_or_condition": [
        "未能遵守规定或未能预防制裁规避"
      ],
      "focal_handling_or_judgment": "建立强大的反洗钱和制裁合规计划",
      "outcomes_or_paths": [
        "民事罚款",
        "个人民事和刑事起诉",
        "被列为制裁目标"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000099",
        "quote": "Regulated entities must have strong AML and sanctions compliance programs with robust policies, procedures, and internal controls for detecting and preventing sanctions evasion. The penalties for noncompliance and failing to prevent sanctions evasion could include:"
      },
      {
        "unit_id": "v7u_N000100",
        "quote": "Civil monetary penalties against organizations"
      },
      {
        "unit_id": "v7u_N000101",
        "quote": "Civil and criminal prosecution of individuals"
      },
      {
        "unit_id": "v7u_N000102",
        "quote": "Designations as a sanctions target"
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N000103",
      "v7u_N000104",
      "v7u_N000105",
      "v7u_N000106",
      "v7u_N000107",
      "v7u_N000108",
      "v7u_N000109",
      "v7u_N000110",
      "v7u_N000111"
    ],
    "proposition": "银行的合规官通过标记异常支付流并进一步调查，揭露了Komarov和Volkof Industries在制裁规避、扩散融资、洗钱及贿赂等犯罪中的角色。",
    "source_quotes": [
      "After UN sanctions targeted this proliferation activity, Volkof Industries faced restrictions, losing its access to global markets.",
      "Facing financial collapse, Komarov was determined to find a way to continue trading.",
      "To evade the sanctions, he created a shell company, RedStar Solutions.",
      "He incorporated it in a jurisdiction with limited regulatory expectations toward AML and sanctions compliance and masked it as a technical support and maintenance service provider.",
      "Through RedStar, he resumed exports to the foreign government developing its nuclear weapons program, using transshipment points in permissive jurisdictions and falsified invoices that labeled export-controlled items, such as semiconductors, as “industrial machinery and spare parts.”",
      "RedStar also employed local distributors in those jurisdictions to further distance Komarov and Volkof Industries from the transactions and paid them to ensure the shipments were received without question.",
      "To launder the proceeds back to Volkof Industries, Komarov routed payments through offshore accounts and shell companies. He was thus able to credit Volkof Industries’ accounts using laundered funds from the illegal activities of RedStar.",
      "Komarov’s goal was not just to hide the profits of RedStar, but to keep Volkof Industries trading, as its name still carried weight in industry circles. Despite UN sanctions against Volkof Industries, this strategy helped the company meet loan obligations, retain employees, and strengthen business ties to the foreign government, its main client.",
      "The scheme unraveled when a bank’s compliance officer flagged irregular payment flows linked to RedStar. Further investigation exposed the illicit network, revealing Komarov and Volkof Industries’ role in sanctions evasion, proliferation financing, laundering criminal proceeds, and foreign bribery and corruption offences."
    ],
    "relation_cues": [
      "flagged",
      "further investigation",
      "exposed",
      "unraveled"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "联合国制裁针对扩散活动，Volkof Industries面临限制",
        "Komarov创建壳公司并采取各种手段规避制裁并洗钱"
      ],
      "basis_or_condition": [
        "合规官标记了与RedStar相关的异常支付流"
      ],
      "focal_handling_or_judgment": "银行合规官进行调查揭露了非法网络",
      "outcomes_or_paths": [
        "揭露了Komarov和Volkof Industries在制裁规避、扩散融资、洗钱和贿赂中的角色"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000103",
        "quote": "After UN sanctions targeted this proliferation activity, Volkof Industries faced restrictions, losing its access to global markets."
      },
      {
        "unit_id": "v7u_N000104",
        "quote": "Facing financial collapse, Komarov was determined to find a way to continue trading."
      },
      {
        "unit_id": "v7u_N000105",
        "quote": "To evade the sanctions, he created a shell company, RedStar Solutions."
      },
      {
        "unit_id": "v7u_N000106",
        "quote": "He incorporated it in a jurisdiction with limited regulatory expectations toward AML and sanctions compliance and masked it as a technical support and maintenance service provider."
      },
      {
        "unit_id": "v7u_N000107",
        "quote": "Through RedStar, he resumed exports to the foreign government developing its nuclear weapons program, using transshipment points in permissive jurisdictions and falsified invoices that labeled export-controlled items, such as semiconductors, as “industrial machinery and spare parts.”"
      },
      {
        "unit_id": "v7u_N000108",
        "quote": "RedStar also employed local distributors in those jurisdictions to further distance Komarov and Volkof Industries from the transactions and paid them to ensure the shipments were received without question."
      },
      {
        "unit_id": "v7u_N000109",
        "quote": "To launder the proceeds back to Volkof Industries, Komarov routed payments through offshore accounts and shell companies. He was thus able to credit Volkof Industries’ accounts using laundered funds from the illegal activities of RedStar."
      },
      {
        "unit_id": "v7u_N000110",
        "quote": "Komarov’s goal was not just to hide the profits of RedStar, but to keep Volkof Industries trading, as its name still carried weight in industry circles. Despite UN sanctions against Volkof Industries, this strategy helped the company meet loan obligations, retain employees, and strengthen business ties to the foreign government, its main client."
      },
      {
        "unit_id": "v7u_N000111",
        "quote": "The scheme unraveled when a bank’s compliance officer flagged irregular payment flows linked to RedStar. Further investigation exposed the illicit network, revealing Komarov and Volkof Industries’ role in sanctions evasion, proliferation financing, laundering criminal proceeds, and foreign bribery and corruption offences."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
