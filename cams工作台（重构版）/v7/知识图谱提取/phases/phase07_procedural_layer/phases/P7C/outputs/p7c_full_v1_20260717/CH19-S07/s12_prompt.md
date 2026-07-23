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

section_id: `CH19-S07`

section_title: `Financial Action Task Force > Impact of FATF mutual evaluation reports on jurisdictions`

section_text_with_unit_anchors:

```text
[v7u_N001430|1430] After the plenary discussion and final quality review are complete, FATF publishes the mutual evaluation report.
ZH: FATF在全体会议讨论和最终质量审查后发布互评估报告

[v7u_N001431|1431] Jurisdictions that perform poorly on evaluations risk placement on FATF’s grey list or black list.
ZH: 评估表现不佳的司法管辖区可能被列入FATF灰名单或黑名单

[v7u_N001432|1432] A poor evaluation can lead to increased scrutiny from international banks, reputational damage, and economic consequences such as higher transaction costs and reduced foreign investment.
ZH: 评估不佳会导致国际银行审查加强、声誉受损及经济后果

[v7u_N001433|1433] After jurisdictions receive the ratings on Recommendations, they should address the shortcomings FATF identified in the mutual evaluation report.
ZH: 司法管辖区应根据互评估报告中的评级解决FATF指出的缺陷

[v7u_N001434|1434] FATF encourages these jurisdictions to enact new—or amend existing— regulations or laws to strengthen their AML/CFT regime.
ZH: FATF鼓励司法管辖区制定或修订法规以加强反洗钱/反恐怖融资体系

[v7u_N001435|1435] FATF also encourages financial institutions, law enforcement agencies, and regulatory bodies to enhance their compliance frameworks to meet FATF standards.
ZH: FATF鼓励金融机构、执法和监管机构加强合规框架以符合标准

[v7u_N001436|1436] These enhancements lead to greater investment in technology, training, and personnel for detecting and preventing financial crimes.
ZH: 合规增强促使在技术、培训和人员方面加大投资以防范金融犯罪

[v7u_N001437|1437] Additionally, jurisdictions often strengthen national FIUs and cross-border cooperation mechanisms.
ZH: 司法管辖区通常加强国家金融情报机构和跨境合作机制

[v7u_N001438|1438] According to FATF’s website, all jurisdictions are subject to post-assessment monitoring.
ZH: 所有司法管辖区均须接受FATF评估后监测

[v7u_N001439|1439] This monitoring can include regular reports of improvements for jurisdictions that are already largely compliant and actively addressing the remaining few shortcomings.
ZH: 监测包括对基本合规且积极整改的司法管辖区定期提交改进报告

[v7u_N001440|1440] Additionally, FATF can issue public warnings against a jurisdiction that makes insufficient progress to address key deficiencies.
ZH: FATF可对关键缺陷整改不力的司法管辖区发布公开警告

[v7u_N001441|1441] The United Arab Emirates (UAE) offers an example of the strength of the mutual evaluation report process. FATF placed the UAE on the grey list in 2022 and removed it from the list in 2024. The removal was due to the UAE successfully amending its legislation to close loopholes, criminalize money laundering, and improve financial transparency. Specifically, the UAE achieved its removal from the grey list by:
ZH: FATF 互评估报告对司法管辖区的影响示例：阿联酋从灰名单移除

[v7u_N001442|1442] Updating its guidelines for financial institutions and DNFBPs.
ZH: 更新金融机构和 DNFBP 的指引

[v7u_N001443|1443] Engaging in an ongoing legal and regulatory communications campaign, highlighting new and updated requirements.
ZH: 开展持续的法律和监管沟通活动，强调新要求

[v7u_N001444|1444] Increasing the frequency of its assessments.
ZH: 增加评估频率

[v7u_N001445|1445] Increasing the frequency and size of sanctions to penalize AML/CFT failures.
ZH: 增加制裁频率和规模以惩罚 反洗钱/反恐怖融资 失败

[v7u_N001446|1446] Strengthening beneficial ownership regulations.
ZH: 加强受益所有人法规

[v7u_N001447|1447] Creating a dedicated court to hear cases involving financial crime.
ZH: 设立专门法院审理金融犯罪案件

[v7u_N001448|1448] Adopting a new penal code.
ZH: 通过新刑法典

[v7u_N001449|1449] Creating a new platform to streamline the reporting of suspicious activities.
ZH: 创建新平台以简化可疑活动报告

[v7u_N001450|1450] Note that the impacts from a mutual evaluation are not limited to the national level. Changes in laws and regulations would also have an impact on regulated organizations that operate in relevant jurisdictions.
ZH: 互评估的影响不仅限于国家层面，也影响受监管机构

[v7u_N001451|1451] Therefore, regulated organizations should implement control frameworks and resources.
ZH: 受监管机构必须实施控制框架和资源

[v7u_N001452|1452] Recommendation 1 of FATF standards requires jurisdictions to identify, assess, and understand their money laundering and terrorist financing risks and implement measures to ensure effective risk mitigation.
ZH: FATF 建议 1 要求司法管辖区识别、评估并减轻洗钱和恐怖融资风险

[v7u_N001453|1453] To achieve this, FATF promotes a risk-based approach, enabling jurisdictions to enhance efficiency by prioritizing high-risk threats, optimizing resource allocation, improving compliance flexibility, strengthening AML/CFT measures, and adapting to evolving financial crimes.
ZH: FATF 推广风险为本方法以提升效率

[v7u_N001454|1454] There is no universal approach to assessing risks.
ZH: 不存在通用的风险评估方法

[v7u_N001455|1455] FATF states that risk assessments may be undertaken at various levels beyond the national level, and with differing purposes and scope, though the basic obligation of assessing and understanding money laundering and terrorist financing risks rests on the jurisdiction itself.
ZH: FATF 允许在国家层面之外进行风险评估，但基本义务在司法管辖区自身

[v7u_N001456|1456] Therefore, jurisdictions should tailor the national risk assessment process based on their capacity, risk exposure, and context.
ZH: 司法管辖区应根据自身能力、风险敞口和背景定制国家风险评估

[v7u_N001457|1457] To better assist jurisdictions, FATF provides a six-step best-practice framework in which jurisdictions should conduct:
ZH: FATF 提供六步最佳实践框架以协助司法管辖区

[v7u_N001458|1458] 1. An environmental scan to evaluate economic, political, and legal factors.
ZH: 第一步：环境扫描，评估经济、政治和法律因素

[v7u_N001459|1459] 2. An analytical scan to collect and analyze money laundering and terrorist financing data.
ZH: 第二步：分析扫描，收集和分析洗钱和恐怖融资数据

[v7u_N001460|1460] 3. An analysis of threats to identify key money laundering and terrorist financing actors and methods.
ZH: 第三步：威胁分析，识别关键洗钱和恐怖融资行为者及方法

[v7u_N001461|1461] 4. An analysis of vulnerabilities to assess weaknesses in financial systems.
ZH: 分析金融体系漏洞以评估弱点

[v7u_N001462|1462] 5. A risk assessment to assign risk levels and develop mitigation plans.
ZH: 进行风险评估以分配风险等级并制定缓解计划

[v7u_N001463|1463] 6. Horizon scanning to monitor emerging trends and future threats.
ZH: 进行地平线扫描以监测新兴趋势和未来威胁

[v7u_N001464|1464] According to FATF’s 2024 guidance on national risk assessments, sectoral and thematic risk assessments help authorities develop typologies to understand how bad actors could exploit specific sectors for money laundering and terrorist financing.
ZH: 行业和专题风险评估帮助当局制定类型学以了解洗钱和恐怖融资风险

[v7u_N001465|1465] The results of sectoral and thematic risk assessments complement those of the national risk assessment.
ZH: 行业和专题风险评估结果补充国家风险评估

[v7u_N001466|1466] Enterprise-wide risk assessments ensure that organizations systematically identify and assess money laundering and terrorist financing risks across all operations. These assessments strengthen compliance, internal controls, and regulatory alignment while optimizing risk management.
ZH: 全企业风险评估确保组织系统识别和评估洗钱和恐怖融资风险
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N001430"
    ],
    "proposition": "FATF在全体会议讨论和最终质量审查完成后发布互评估报告。",
    "source_quotes": [
      "After the plenary discussion and final quality review are complete, FATF publishes the mutual evaluation report."
    ],
    "relation_cues": [
      "After"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "全体会议讨论和最终质量审查完成"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "FATF发布互评估报告",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001430",
        "quote": "After the plenary discussion and final quality review are complete, FATF publishes the mutual evaluation report."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N001431"
    ],
    "proposition": "评估表现不佳的司法管辖区可能被列入FATF灰名单或黑名单。",
    "source_quotes": [
      "Jurisdictions that perform poorly on evaluations risk placement on FATF’s grey list or black list."
    ],
    "relation_cues": [
      "risk"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "评估表现不佳"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "可能被列入FATF灰名单或黑名单",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001431",
        "quote": "Jurisdictions that perform poorly on evaluations risk placement on FATF’s grey list or black list."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N001433"
    ],
    "proposition": "司法管辖区在收到互评估报告评级后应解决FATF指出的缺陷。",
    "source_quotes": [
      "After jurisdictions receive the ratings on Recommendations, they should address the shortcomings FATF identified in the mutual evaluation report."
    ],
    "relation_cues": [
      "After",
      "should"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "收到互评估报告评级"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "解决FATF指出的缺陷",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001433",
        "quote": "After jurisdictions receive the ratings on Recommendations, they should address the shortcomings FATF identified in the mutual evaluation report."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N001434"
    ],
    "proposition": "FATF鼓励司法管辖区制定或修订法规以加强反洗钱/反恐怖融资体系。",
    "source_quotes": [
      "FATF encourages these jurisdictions to enact new—or amend existing— regulations or laws to strengthen their AML/CFT regime."
    ],
    "relation_cues": [
      "encourages"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "FATF鼓励司法管辖区制定或修订法规",
      "outcomes_or_paths": [
        "加强反洗钱/反恐怖融资体系"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001434",
        "quote": "FATF encourages these jurisdictions to enact new—or amend existing— regulations or laws to strengthen their AML/CFT regime."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N001435"
    ],
    "proposition": "FATF鼓励金融机构、执法和监管机构加强合规框架以符合标准。",
    "source_quotes": [
      "FATF also encourages financial institutions, law enforcement agencies, and regulatory bodies to enhance their compliance frameworks to meet FATF standards."
    ],
    "relation_cues": [
      "encourages"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "FATF鼓励金融机构、执法和监管机构加强合规框架",
      "outcomes_or_paths": [
        "符合FATF标准"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001435",
        "quote": "FATF also encourages financial institutions, law enforcement agencies, and regulatory bodies to enhance their compliance frameworks to meet FATF standards."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N001436"
    ],
    "proposition": "合规增强促使在技术、培训和人员方面加大投资以防范金融犯罪。",
    "source_quotes": [
      "These enhancements lead to greater investment in technology, training, and personnel for detecting and preventing financial crimes."
    ],
    "relation_cues": [
      "lead to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "合规增强"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "加大投资",
      "outcomes_or_paths": [
        "防范金融犯罪"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001436",
        "quote": "These enhancements lead to greater investment in technology, training, and personnel for detecting and preventing financial crimes."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_007",
    "unit_ids": [
      "v7u_N001438",
      "v7u_N001439"
    ],
    "proposition": "所有司法管辖区须接受评估后监测，包括对基本合规且积极整改的司法管辖区定期提交改进报告。",
    "source_quotes": [
      "all jurisdictions are subject to post-assessment monitoring.",
      "This monitoring can include regular reports of improvements for jurisdictions that are already largely compliant and actively addressing the remaining few shortcomings."
    ],
    "relation_cues": [
      "subject to",
      "include"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "基本合规且积极整改"
      ],
      "focal_handling_or_judgment": "接受评估后监测",
      "outcomes_or_paths": [
        "定期提交改进报告"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001438",
        "quote": "all jurisdictions are subject to post-assessment monitoring."
      },
      {
        "unit_id": "v7u_N001439",
        "quote": "This monitoring can include regular reports of improvements for jurisdictions that are already largely compliant and actively addressing the remaining few shortcomings."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_008",
    "unit_ids": [
      "v7u_N001440"
    ],
    "proposition": "FATF可对关键缺陷整改不力的司法管辖区发布公开警告。",
    "source_quotes": [
      "FATF can issue public warnings against a jurisdiction that makes insufficient progress to address key deficiencies."
    ],
    "relation_cues": [
      "can",
      "insufficient"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "关键缺陷整改不力"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "发布公开警告",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001440",
        "quote": "FATF can issue public warnings against a jurisdiction that makes insufficient progress to address key deficiencies."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_009",
    "unit_ids": [
      "v7u_N001441",
      "v7u_N001442",
      "v7u_N001443",
      "v7u_N001444",
      "v7u_N001445",
      "v7u_N001446",
      "v7u_N001447",
      "v7u_N001448",
      "v7u_N001449"
    ],
    "proposition": "阿联酋因成功修订立法等整改措施，于2024年被FATF从灰名单移除（2022年列入）。",
    "source_quotes": [
      "FATF placed the UAE on the grey list in 2022 and removed it from the list in 2024. The removal was due to the UAE successfully amending its legislation to close loopholes, criminalize money laundering, and improve financial transparency.",
      "Updating its guidelines for financial institutions and DNFBPs.",
      "Engaging in an ongoing legal and regulatory communications campaign, highlighting new and updated requirements.",
      "Increasing the frequency of its assessments.",
      "Increasing the frequency and size of sanctions to penalize AML/CFT failures.",
      "Strengthening beneficial ownership regulations.",
      "Creating a dedicated court to hear cases involving financial crime.",
      "Adopting a new penal code.",
      "Creating a new platform to streamline the reporting of suspicious activities."
    ],
    "relation_cues": [
      "placed",
      "removed",
      "due to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "FATF将阿联酋列入灰名单（2022年）"
      ],
      "basis_or_condition": [
        "阿联酋成功修订立法、更新指引、加强受益所有人法规、设立专门法院等系列整改措施"
      ],
      "focal_handling_or_judgment": "FATF将阿联酋从灰名单移除（2024年）",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001441",
        "quote": "FATF placed the UAE on the grey list in 2022 and removed it from the list in 2024. The removal was due to the UAE successfully amending its legislation to close loopholes, criminalize money laundering, and improve financial transparency."
      },
      {
        "unit_id": "v7u_N001442",
        "quote": "Updating its guidelines for financial institutions and DNFBPs."
      },
      {
        "unit_id": "v7u_N001443",
        "quote": "Engaging in an ongoing legal and regulatory communications campaign, highlighting new and updated requirements."
      },
      {
        "unit_id": "v7u_N001444",
        "quote": "Increasing the frequency of its assessments."
      },
      {
        "unit_id": "v7u_N001445",
        "quote": "Increasing the frequency and size of sanctions to penalize AML/CFT failures."
      },
      {
        "unit_id": "v7u_N001446",
        "quote": "Strengthening beneficial ownership regulations."
      },
      {
        "unit_id": "v7u_N001447",
        "quote": "Creating a dedicated court to hear cases involving financial crime."
      },
      {
        "unit_id": "v7u_N001448",
        "quote": "Adopting a new penal code."
      },
      {
        "unit_id": "v7u_N001449",
        "quote": "Creating a new platform to streamline the reporting of suspicious activities."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_010",
    "unit_ids": [
      "v7u_N001450",
      "v7u_N001451"
    ],
    "proposition": "互评估的影响不仅限于国家层面，受监管机构应实施控制框架和资源。",
    "source_quotes": [
      "the impacts from a mutual evaluation are not limited to the national level. Changes in laws and regulations would also have an impact on regulated organizations that operate in relevant jurisdictions.",
      "Therefore, regulated organizations should implement control frameworks and resources."
    ],
    "relation_cues": [
      "Therefore"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "互评估影响不仅限于国家层面，也影响受监管机构"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "受监管机构应实施控制框架和资源",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001450",
        "quote": "the impacts from a mutual evaluation are not limited to the national level. Changes in laws and regulations would also have an impact on regulated organizations that operate in relevant jurisdictions."
      },
      {
        "unit_id": "v7u_N001451",
        "quote": "Therefore, regulated organizations should implement control frameworks and resources."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_011",
    "unit_ids": [
      "v7u_N001452"
    ],
    "proposition": "FATF建议1要求司法管辖区识别、评估和理解洗钱和恐怖融资风险，并实施措施确保有效风险缓解。",
    "source_quotes": [
      "Recommendation 1 of FATF standards requires jurisdictions to identify, assess, and understand their money laundering and terrorist financing risks and implement measures to ensure effective risk mitigation."
    ],
    "relation_cues": [
      "requires"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "识别、评估和理解洗钱和恐怖融资风险并实施措施",
      "outcomes_or_paths": [
        "有效风险缓解"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001452",
        "quote": "Recommendation 1 of FATF standards requires jurisdictions to identify, assess, and understand their money laundering and terrorist financing risks and implement measures to ensure effective risk mitigation."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_012",
    "unit_ids": [
      "v7u_N001453"
    ],
    "proposition": "FATF推广风险为本方法，使司法管辖区通过优先高风险威胁等提升效率。",
    "source_quotes": [
      "FATF promotes a risk-based approach, enabling jurisdictions to enhance efficiency by prioritizing high-risk threats, optimizing resource allocation, improving compliance flexibility, strengthening AML/CFT measures, and adapting to evolving financial crimes."
    ],
    "relation_cues": [
      "promotes",
      "enabling"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "推广风险为本方法",
      "outcomes_or_paths": [
        "提升效率"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001453",
        "quote": "FATF promotes a risk-based approach, enabling jurisdictions to enhance efficiency by prioritizing high-risk threats, optimizing resource allocation, improving compliance flexibility, strengthening AML/CFT measures, and adapting to evolving financial crimes."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_013",
    "unit_ids": [
      "v7u_N001455"
    ],
    "proposition": "FATF允许在国家层面之外进行风险评估，但基本义务在司法管辖区自身。",
    "source_quotes": [
      "FATF states that risk assessments may be undertaken at various levels beyond the national level, and with differing purposes and scope, though the basic obligation of assessing and understanding money laundering and terrorist financing risks rests on the jurisdiction itself."
    ],
    "relation_cues": [
      "may",
      "though"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "基本义务在司法管辖区自身"
      ],
      "focal_handling_or_judgment": "可在国家层面之外进行风险评估",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001455",
        "quote": "FATF states that risk assessments may be undertaken at various levels beyond the national level, and with differing purposes and scope, though the basic obligation of assessing and understanding money laundering and terrorist financing risks rests on the jurisdiction itself."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_014",
    "unit_ids": [
      "v7u_N001456"
    ],
    "proposition": "司法管辖区应根据自身能力、风险敞口和背景定制国家风险评估过程。",
    "source_quotes": [
      "jurisdictions should tailor the national risk assessment process based on their capacity, risk exposure, and context."
    ],
    "relation_cues": [
      "should",
      "based on"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "自身能力、风险敞口和背景"
      ],
      "focal_handling_or_judgment": "定制国家风险评估过程",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001456",
        "quote": "jurisdictions should tailor the national risk assessment process based on their capacity, risk exposure, and context."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_015",
    "unit_ids": [
      "v7u_N001457",
      "v7u_N001458",
      "v7u_N001459",
      "v7u_N001460",
      "v7u_N001461",
      "v7u_N001462",
      "v7u_N001463"
    ],
    "proposition": "FATF提供六步最佳实践框架指导司法管辖区进行国家风险评估。",
    "source_quotes": [
      "FATF provides a six-step best-practice framework in which jurisdictions should conduct:",
      "1. An environmental scan to evaluate economic, political, and legal factors.",
      "2. An analytical scan to collect and analyze money laundering and terrorist financing data.",
      "3. An analysis of threats to identify key money laundering and terrorist financing actors and methods.",
      "4. An analysis of vulnerabilities to assess weaknesses in financial systems.",
      "5. A risk assessment to assign risk levels and develop mitigation plans.",
      "6. Horizon scanning to monitor emerging trends and future threats."
    ],
    "relation_cues": [
      "six-step"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "按照六步最佳实践框架进行国家风险评估",
      "outcomes_or_paths": [
        "环境扫描评估经济、政治和法律因素",
        "分析扫描收集和分析洗钱和恐怖融资数据",
        "威胁分析识别关键行为者及方法",
        "漏洞分析评估金融体系弱点",
        "风险评估分配风险等级并制定缓解计划",
        "地平线扫描监测新兴趋势和未来威胁"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001457",
        "quote": "FATF provides a six-step best-practice framework in which jurisdictions should conduct:"
      },
      {
        "unit_id": "v7u_N001458",
        "quote": "1. An environmental scan to evaluate economic, political, and legal factors."
      },
      {
        "unit_id": "v7u_N001459",
        "quote": "2. An analytical scan to collect and analyze money laundering and terrorist financing data."
      },
      {
        "unit_id": "v7u_N001460",
        "quote": "3. An analysis of threats to identify key money laundering and terrorist financing actors and methods."
      },
      {
        "unit_id": "v7u_N001461",
        "quote": "4. An analysis of vulnerabilities to assess weaknesses in financial systems."
      },
      {
        "unit_id": "v7u_N001462",
        "quote": "5. A risk assessment to assign risk levels and develop mitigation plans."
      },
      {
        "unit_id": "v7u_N001463",
        "quote": "6. Horizon scanning to monitor emerging trends and future threats."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_016",
    "unit_ids": [
      "v7u_N001464"
    ],
    "proposition": "行业和专题风险评估帮助当局制定类型学，以了解行为人如何利用特定部门进行洗钱和恐怖融资。",
    "source_quotes": [
      "sectoral and thematic risk assessments help authorities develop typologies to understand how bad actors could exploit specific sectors for money laundering and terrorist financing."
    ],
    "relation_cues": [
      "help"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "行业和专题风险评估"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "制定类型学",
      "outcomes_or_paths": [
        "了解行为人如何利用特定部门"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001464",
        "quote": "sectoral and thematic risk assessments help authorities develop typologies to understand how bad actors could exploit specific sectors for money laundering and terrorist financing."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_017",
    "unit_ids": [
      "v7u_N001466"
    ],
    "proposition": "全企业风险评估确保组织系统性识别和评估所有运营中的洗钱和恐怖融资风险，强化合规、内控和监管对齐。",
    "source_quotes": [
      "Enterprise-wide risk assessments ensure that organizations systematically identify and assess money laundering and terrorist financing risks across all operations. These assessments strengthen compliance, internal controls, and regulatory alignment while optimizing risk management."
    ],
    "relation_cues": [
      "ensure"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "进行全企业风险评估",
      "outcomes_or_paths": [
        "系统性识别和评估风险",
        "强化合规、内控和监管对齐"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001466",
        "quote": "Enterprise-wide risk assessments ensure that organizations systematically identify and assess money laundering and terrorist financing risks across all operations. These assessments strengthen compliance, internal controls, and regulatory alignment while optimizing risk management."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
