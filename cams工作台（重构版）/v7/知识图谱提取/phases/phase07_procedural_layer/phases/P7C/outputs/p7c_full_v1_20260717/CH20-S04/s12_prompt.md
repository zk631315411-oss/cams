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

section_id: `CH20-S04`

section_title: `AFC guidance from leading international organizations > Organisation for Economic Co-operation and Development AFC guidance`

section_text_with_unit_anchors:

```text
[v7u_N001503|1503] The Organisation for Economic Co-operation and Development (OECD) is an intergovernmental organization founded in 1961. It works closely with policymakers, stakeholders, and citizens to establish evidence-based international standards for a variety of policy issues.
ZH: OECD是1961年成立的政府间组织，与政策制定者、利益相关者和公民合作制定基于证据的国际标准。

[v7u_N001504|1504] The OECD consists of three sections:
ZH: OECD由三个部分组成。

[v7u_N001505|1505] The Council is its decision-making body. It is composed of one representative from each member country plus the EU and is chaired by the Secretary-General.
ZH: OECD理事会是决策机构，由各成员国代表和欧盟代表组成，由秘书长主持。

[v7u_N001506|1506] The Substantive Committees propose solutions, develop standards, assess data, and review policy actions. There are more than 300 such committees.
ZH: OECD专业委员会提出解决方案、制定标准、评估数据并审查政策行动，共有300多个委员会。

[v7u_N001507|1507] The Secretariat is made up of more than 3,500 employees who carry out the work of the OECD. They include economists, lawyers, scientists, political analysts, digital experts, statisticians, and other specialists.
ZH: OECD秘书处由3500多名员工组成，包括经济学家、律师、科学家等专家。

[v7u_N001508|1508] In November 1997, the OECD adopted the Convention on Combating Bribery of Foreign Public Officials in International Business Transactions.
ZH: 1997年11月，OECD通过了《打击在国际商业交易中贿赂外国公职人员公约》。

[v7u_N001509|1509] The Convention requires signatory countries to establish legislation that criminalizes the bribery of foreign public officials in international business transactions.
ZH: 该公约要求签署国立法将贿赂外国公职人员定为刑事犯罪。

[v7u_N001510|1510] It also establishes an open-ended, peer-driven monitoring mechanism to ensure the thorough implementation of international obligations.
ZH: 公约建立了开放、同行驱动的监督机制以确保国际义务的全面实施。

[v7u_N001511|1511] It is the first and only international anti-corruption instrument focused on the “supply side” of the bribery transaction: the person or entity offering, promising, or giving a bribe.
ZH: 该公约是首个也是唯一一个聚焦贿赂交易“供应方”的国际反腐败文书。

[v7u_N001512|1512] The OECD Working Group on Bribery in International Business Transactions evaluates and makes recommendations on a jurisdiction’s implementation and enforcement of the Convention and related instruments. The Working Group issues reports that detail a jurisdiction’s achievements and challenges, including enforcement of foreign bribery offenses. The reports also document the jurisdiction’s progress since its last evaluation.
ZH: OECD贿赂工作组评估并建议各司法管辖区实施和执行公约的情况，发布详细报告。

[v7u_N001513|1513] Many organizations utilize the OECD's guidance and resources as a reference to identify risks from various areas. The OECD discusses a range of topics, including:
ZH: 许多组织利用OECD的指导和资源识别风险，OECD讨论一系列主题。

[v7u_N001514|1514] Digital currencies, such as cryptocurrencies.
ZH: 数字货币（如加密货币）是OECD讨论的主题之一。

[v7u_N001515|1515] Beneficial ownership.
ZH: 受益所有人是OECD讨论的主题之一。

[v7u_N001516|1516] Transnational organized crime.
ZH: 跨国有组织犯罪是OECD讨论的主题之一。

[v7u_N001517|1517] Tax crime.
ZH: 税务犯罪是OECD讨论的主题之一。

[v7u_N001518|1518] Risks of corruption, conflict financing, and money laundering linked to gold flows.
ZH: 与黄金流动相关的腐败、冲突融资和洗钱风险是OECD讨论的主题之一。

[v7u_N001519|1519] Main areas of weakness and potential areas for action to combat money laundering, tax evasion, and foreign bribery.
ZH: 打击洗钱、逃税和外国贿赂的主要薄弱环节和潜在行动领域是OECD讨论的主题之一。

[v7u_N001520|1520] Identifying, freezing, and returning stolen assets.
ZH: 识别、冻结和返还被盗资产是OECD讨论的主题之一。
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N001508",
      "v7u_N001509",
      "v7u_N001510"
    ],
    "proposition": "OECD反贿赂公约要求签署国将贿赂外国公职人员定为刑事犯罪，并建立开放、同行驱动的监督机制。",
    "source_quotes": [
      "In November 1997, the OECD adopted the Convention on Combating Bribery of Foreign Public Officials in International Business Transactions.",
      "The Convention requires signatory countries to establish legislation that criminalizes the bribery of foreign public officials in international business transactions.",
      "It also establishes an open-ended, peer-driven monitoring mechanism to ensure the thorough implementation of international obligations."
    ],
    "relation_cues": [
      "requires",
      "establishes"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "国家是公约签署国"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "公约要求签署国将贿赂外国公职人员定为刑事犯罪，并建立开放、同行驱动的监督机制",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001508",
        "quote": "In November 1997, the OECD adopted the Convention on Combating Bribery of Foreign Public Officials in International Business Transactions."
      },
      {
        "unit_id": "v7u_N001509",
        "quote": "The Convention requires signatory countries to establish legislation that criminalizes the bribery of foreign public officials in international business transactions."
      },
      {
        "unit_id": "v7u_N001510",
        "quote": "It also establishes an open-ended, peer-driven monitoring mechanism to ensure the thorough implementation of international obligations."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N001512"
    ],
    "proposition": "OECD贿赂工作组评估并建议司法管辖区实施和执行公约的情况，并发布详细报告。",
    "source_quotes": [
      "The OECD Working Group on Bribery in International Business Transactions evaluates and makes recommendations on a jurisdiction’s implementation and enforcement of the Convention and related instruments. The Working Group issues reports that detail a jurisdiction’s achievements and challenges, including enforcement of foreign bribery offenses. The reports also document the jurisdiction’s progress since its last evaluation."
    ],
    "relation_cues": [
      "evaluates",
      "makes recommendations",
      "issues reports"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "OECD贿赂工作组评估并建议司法管辖区实施和执行公约的情况",
      "outcomes_or_paths": [
        "发布详细报告，记录成就和挑战，包括外国贿赂执法情况以及自上次评估以来的进展"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001512",
        "quote": "The OECD Working Group on Bribery in International Business Transactions evaluates and makes recommendations on a jurisdiction’s implementation and enforcement of the Convention and related instruments. The Working Group issues reports that detail a jurisdiction’s achievements and challenges, including enforcement of foreign bribery offenses. The reports also document the jurisdiction’s progress since its last evaluation."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
