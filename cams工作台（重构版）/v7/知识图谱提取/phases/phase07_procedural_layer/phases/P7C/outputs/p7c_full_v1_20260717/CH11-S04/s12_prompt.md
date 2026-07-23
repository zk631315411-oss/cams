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

section_id: `CH11-S04`

section_title: `Money laundering risks associated with MSBs, payment service providers, and ecommerce > E-commerce risks`

section_text_with_unit_anchors:

```text
[v7u_N000846|846] Participants in e-commerce include merchants, customers, and financial institutions (FI).
ZH: 电子商务参与者包括商户、客户和金融机构。

[v7u_N000847|847] E-commerce businesses greatly facilitate legitimate global commerce between buyers and sellers. However, they also offer criminals a venue for conducting illegal activities and concealing the movement of illicit funds.
ZH: 电子商务促进合法全球贸易，但也为犯罪活动提供渠道。

[v7u_N000848|848] Key financial crime risks associated with e-commerce include:
ZH: 列举与电子商务相关的关键金融犯罪风险。

[v7u_N000849|849] Consumer fraud, in which a seller does not deliver a good or service after receiving payment from the buyer
ZH: 消费者欺诈：卖家收款后不交付商品或服务。

[v7u_N000850|850] Use of a stolen credit or debit card or other data to purchase goods or services
ZH: 使用被盗信用卡或借记卡购买商品或服务。

[v7u_N000851|851] Use of an e-commerce business:
ZH: 利用电子商务企业进行非法活动。

[v7u_N000852|852] As a front for illicit transactions
ZH: 利用电子商务企业作为非法交易的幌子。

[v7u_N000853|853] To launder illicit funds
ZH: 利用电子商务企业清洗非法资金。

[v7u_N000854|854] Criminals can use e-commerce businesses to both illegally generate funds and launder them. Ultimately, these funds will be deposited with an FI.
ZH: 犯罪分子利用电子商务企业非法产生资金并洗钱，最终存入金融机构。

[v7u_N000855|855] Therefore, FIs must strive to prevent and detect financial crime through their roles as payment processors, card issuers for customers, and account openers for merchants.
ZH: 金融机构有义务在支付处理、发卡和商户开户等角色中预防和发现金融犯罪。

[v7u_N000856|856] Two examples of financial crime threats that financial institutions should be aware of include the use of e-commerce businesses as front companies for dark market activities and for trade-based money laundering.
ZH: 金融犯罪威胁示例：电子商务企业作为暗网市场和贸易洗钱的前台公司。

[v7u_N000857|857] In a recent case, an online business that posed as a clothing store covertly sold illegal drugs to customers. The business used codewords such as “T-shirt size” to allow customers to indicate the type and quantity of drugs they wanted.
ZH: 案例：伪装成服装店的在线商家使用暗语销售非法药物。

[v7u_N000858|858] In another example, members of a terrorist organization were able to transfer funds through a PSP to a collaborator in another jurisdiction under the guise of purchasing printers on a well-known marketplace.
ZH: 案例：恐怖组织通过PSP以购买打印机为名向另一辖区转移资金。

[v7u_N000859|859] Red flags for financial crime related to the use of e-commerce include the following:
ZH: 列举与电子商务相关的金融犯罪红旗信号信号。

[v7u_N000860|860] Prices inconsistent with the fair market value of goods or services being sold
ZH: 价格与商品或服务的公平市场价值不一致。

[v7u_N000861|861] Sales of goods or services that are difficult to value
ZH: 难以估值的商品或服务销售是电子商务洗钱风险之一

[v7u_N000862|862] Attempts by customers to hide their identity or location, such as by using a virtual private network
ZH: 客户使用VPN等工具隐藏身份或位置是洗钱风险信号

[v7u_N000863|863] Unusual counterparty pairs
ZH: 不寻常的交易对手配对是电子商务洗钱风险指标

[v7u_N000864|864] Involvement of potential shell companies
ZH: 涉及潜在壳公司是电子商务洗钱风险之一
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N000854",
      "v7u_N000855"
    ],
    "proposition": "由于犯罪分子通过电子商务产生的资金最终存入金融机构，金融机构必须通过其作为支付处理方、客户发卡行和商户开户行的角色，努力预防和发现金融犯罪。",
    "source_quotes": [
      "Ultimately, these funds will be deposited with an FI.",
      "Therefore, FIs must strive to prevent and detect financial crime through their roles as payment processors, card issuers for customers, and account openers for merchants."
    ],
    "relation_cues": [
      "Therefore",
      "must",
      "through"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "犯罪分子通过电子商务产生的资金最终存入金融机构"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "金融机构必须通过其角色预防和发现金融犯罪",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000854",
        "quote": "Ultimately, these funds will be deposited with an FI."
      },
      {
        "unit_id": "v7u_N000855",
        "quote": "Therefore, FIs must strive to prevent and detect financial crime through their roles as payment processors, card issuers for customers, and account openers for merchants."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
