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

section_id: `CH24-S16`

section_title: `US AML/CFT regulatory landscape > Japan AML regulations`

section_text_with_unit_anchors:

```text
[v7u_N001927|1927] Japan’s AML/CFT framework aligns with FATF’s Recommendations and evolving financial crime risks.
ZH: 日本的反洗钱/反恐怖融资框架与FATF建议及不断变化的金融犯罪风险保持一致。

[v7u_N001928|1928] The framework includes the Act on Prevention of Transfer of Criminal Proceeds, the Act on Punishment of Organized Crimes and Control of Crime Proceeds, and the Foreign Exchange and Foreign Trade Act.
ZH: 日本反洗钱/反恐怖融资框架包括《犯罪收益转移防止法》等法律。

[v7u_N001929|1929] According to Japan’s AML/CFT legislation, financial institutions and DNFBPs must adhere to CDD requirements, report suspicious transactions, and implement internal risk-based AML programs.
ZH: 金融机构和DNFBP必须遵守客户尽职调查要求、报告可疑交易并实施基于风险的反洗钱计划。

[v7u_N001930|1930] Additionally, the legislation requires enhanced due diligence for high-risk customers, including PEPs.
ZH: 法律要求对高风险客户（包括政治敏感人物）进行强化尽职调查。

[v7u_N001931|1931] Compliance failures can result in administrative penalties or criminal sanctions.
ZH: 合规失败可能导致行政处罚或刑事制裁。

[v7u_N001932|1932] In addition to these requirements, financial institutions must conduct ongoing monitoring of customer transactions to detect unusual patterns and regularly update risk assessments to reflect emerging threats.
ZH: 金融机构必须持续监控客户交易并定期更新风险评估。

[v7u_N001933|1933] Obliged entities are also encouraged to invest in technological solutions such as artificial intelligence and machine learning to improve transaction monitoring and fraud detection.
ZH: 鼓励义务实体投资人工智能和机器学习等技术解决方案以改进交易监控和欺诈检测。

[v7u_N001934|1934] Recent updates to these legislations include strengthening digital asset regulations, increasing oversight of money transfer service providers, and enhancing transparency in beneficial ownership reporting.
ZH: 日本近期立法更新包括加强数字资产监管、增加对汇款服务提供商的监管以及提高受益所有人透明度。

[v7u_N001935|1935] Japan is also focusing on international cooperation, working closely with FATF and other global regulators to improve its AML/CFT measures.
ZH: 日本注重国际合作，与FATF及其他全球监管机构密切合作以改进其反洗钱/反恐怖融资措施。

[v7u_N001936|1936] Additionally, the Japanese government established an Inter-Ministerial Council for AML/CFT/CPF Policy to coordinate and advance the government’s AML/CFT and weapons proliferation efforts. In April 2024, the Council formulated a National AML/CFT/CPF Action Plan and monitors progress on the Action Plan as part of its work.
ZH: 日本政府设立了反洗钱/反恐怖融资/防扩散融资部际委员会，并于2024年4月制定了国家行动计划。
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N001930"
    ],
    "proposition": "法律要求对高风险客户（包括政治敏感人物）进行强化尽职调查。",
    "source_quotes": [
      "Additionally, the legislation requires enhanced due diligence for high-risk customers, including PEPs."
    ],
    "relation_cues": [
      "requires",
      "for",
      "including"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "高风险客户（包括政治敏感人物）"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "进行强化尽职调查",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001930",
        "quote": "Additionally, the legislation requires enhanced due diligence for high-risk customers, including PEPs."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N001931"
    ],
    "proposition": "合规失败可能导致行政处罚或刑事制裁。",
    "source_quotes": [
      "Compliance failures can result in administrative penalties or criminal sanctions."
    ],
    "relation_cues": [
      "can result in"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "合规失败"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "可能引发处罚",
      "outcomes_or_paths": [
        "行政处罚或刑事制裁"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001931",
        "quote": "Compliance failures can result in administrative penalties or criminal sanctions."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
