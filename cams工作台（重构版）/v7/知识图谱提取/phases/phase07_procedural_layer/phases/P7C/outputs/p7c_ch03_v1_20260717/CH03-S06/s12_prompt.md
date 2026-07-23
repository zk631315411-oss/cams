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

section_id: `CH03-S06`

section_title: `Examples of predicate crimes > How terrorists move and store funds`

section_text_with_unit_anchors:

```text
[v7u_N000257|257] Terrorists and terrorist organizations have many options when choosing to move and store funds between jurisdictions. The choice depends on numerous variables. These variables include the size of the transaction, how quickly the transaction needs to be performed, and the risks of detection for the organization and its financial facilitators.
ZH: 恐怖分子选择资金转移和存储方式时考虑交易规模、速度和检测风险

[v7u_N000258|258] Whether it is through trade, commerce, or outside of the financial system, terrorists will seek to abuse any channel and method available to them.
ZH: 恐怖分子会滥用任何可用的渠道和方法转移和存储资金

[v7u_N000259|259] Because of the exploitative nature of terrorism financing, banks should have a comprehensive understanding of their customers and the nature of their transactions.
ZH: 银行应全面了解客户及其交易性质以应对恐怖融资风险

[v7u_N000260|260] Terrorist organizations could use the traditional banking system, along with legitimate money service businesses, and cash to move and store funds.
ZH: 恐怖组织可能利用传统银行系统、合法货币服务企业和现金转移和存储资金

[v7u_N000261|261] For example, correspondent banking is a business model that makes financial transactions possible between unrelated banks in different jurisdictions.
ZH: 代理行是不同司法管辖区银行间实现金融交易的业务模式

[v7u_N000262|262] It also makes possible a red flag for terrorism financing, through nested transactions in which funds could be paid to unrelated third parties or in lines of business different than the customer of record.
ZH: 通过嵌套交易识别恐怖融资红旗信号信号

[v7u_N000263|263] Prepaid cards are typically sold with few KYC requirements.
ZH: 预付卡通常只需很少的了解你的客户要求即可购买

[v7u_N000264|264] Terrorists might use false identities to purchase multiple prepaid cards. They could use illicit cash or stolen credit cards as a funding mechanism to load onto prepaid cards.
ZH: 恐怖分子可能使用虚假身份购买多张预付卡，并用非法现金或盗刷信用卡充值

[v7u_N000265|265] Many terrorist organizations also use cryptocurrencies and stablecoins in their financing operations.
ZH: 许多恐怖组织也使用加密货币和稳定币进行融资

[v7u_N000266|266] A potential red flag could be numerous, seemingly unrelated deposits of cryptocurrency. Afterward, the deposits are quickly converted to stablecoins, or into fiat currency and withdrawn through a virtual asset service provider and/or in a jurisdiction with poor AFC controls.
ZH: 大量看似无关的小额加密货币存款随后快速兑换并提取是潜在红旗信号信号

[v7u_N000267|267] Terrorist organizations may also use alternative remittance systems (ARS).
ZH: 恐怖组织也可能使用替代性汇款系统

[v7u_N000268|268] ARS transactions are legal in some jurisdictions and represent an exchange of value between two parties but without moving physical cash from one location to another.
ZH: 替代性汇款系统交易是双方之间的价值交换，不涉及实体现金转移

[v7u_N000269|269] Red flags for illegal use of ARS include repeated deposits made in one jurisdiction followed by immediate ATM withdrawals in another jurisdiction.
ZH: 替代性汇款系统非法使用的红旗信号信号包括在一个司法管辖区重复存款后在另一司法管辖区立即ATM取款
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N000259"
    ],
    "proposition": "由于恐怖融资的剥削性质，银行应全面了解客户及其交易性质。",
    "source_quotes": [
      "Because of the exploitative nature of terrorism financing, banks should have a comprehensive understanding of their customers and the nature of their transactions."
    ],
    "relation_cues": [
      "because of",
      "should"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "恐怖融资的剥削性质"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "银行应全面了解客户及其交易性质",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000259",
        "quote": "Because of the exploitative nature of terrorism financing, banks should have a comprehensive understanding of their customers and the nature of their transactions."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N000262"
    ],
    "proposition": "代理行通过嵌套交易使恐怖融资红旗信号成为可能。",
    "source_quotes": [
      "It also makes possible a red flag for terrorism financing, through nested transactions in which funds could be paid to unrelated third parties or in lines of business different than the customer of record."
    ],
    "relation_cues": [
      "makes possible",
      "through"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "代理行业务中的嵌套交易"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "识别恐怖融资红旗信号",
      "outcomes_or_paths": [
        "资金可能支付给无关第三方或与记录客户不同的业务线"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000262",
        "quote": "It also makes possible a red flag for terrorism financing, through nested transactions in which funds could be paid to unrelated third parties or in lines of business different than the customer of record."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N000266"
    ],
    "proposition": "大量看似无关的小额加密货币存款随后快速兑换并提取是潜在红旗信号。",
    "source_quotes": [
      "A potential red flag could be numerous, seemingly unrelated deposits of cryptocurrency. Afterward, the deposits are quickly converted to stablecoins, or into fiat currency and withdrawn through a virtual asset service provider and/or in a jurisdiction with poor AFC controls."
    ],
    "relation_cues": [
      "could be",
      "afterward"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "大量看似无关的小额加密货币存款"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "判定为潜在红旗信号",
      "outcomes_or_paths": [
        "存款快速兑换并提取"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000266",
        "quote": "A potential red flag could be numerous, seemingly unrelated deposits of cryptocurrency. Afterward, the deposits are quickly converted to stablecoins, or into fiat currency and withdrawn through a virtual asset service provider and/or in a jurisdiction with poor AFC controls."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N000269"
    ],
    "proposition": "替代性汇款系统非法使用的红旗信号包括在一个司法管辖区重复存款后在另一司法管辖区立即ATM取款。",
    "source_quotes": [
      "Red flags for illegal use of ARS include repeated deposits made in one jurisdiction followed by immediate ATM withdrawals in another jurisdiction."
    ],
    "relation_cues": [
      "include"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "替代性汇款系统的使用"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "识别替代性汇款系统非法使用的红旗信号",
      "outcomes_or_paths": [
        "一个司法管辖区重复存款，另一司法管辖区立即ATM取款"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000269",
        "quote": "Red flags for illegal use of ARS include repeated deposits made in one jurisdiction followed by immediate ATM withdrawals in another jurisdiction."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
