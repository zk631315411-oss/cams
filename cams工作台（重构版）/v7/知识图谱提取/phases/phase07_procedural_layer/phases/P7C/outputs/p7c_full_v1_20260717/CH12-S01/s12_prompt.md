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

section_id: `CH12-S01`

section_title: `Money laundering risks associated with insurance, securities, brokerage, and custodian services > Insurance products risks`

section_text_with_unit_anchors:

```text
[v7u_N000877|877] The insurance sector contributes to the financial services industry by providing essential risk management solutions and enhancing financial stability.
ZH: 保险业通过提供风险管理解决方案增强金融稳定性

[v7u_N000878|878] It offers a diverse range of products, such as life, property, casualty, medical, travel, and liability insurance.
ZH: 保险产品涵盖寿险、财产险、医疗险、旅行险和责任险等

[v7u_N000879|879] In the context of money laundering, the insurance sector is primarily involved in the integration stage of the laundering process.
ZH: 保险业主要涉及洗钱的融合阶段

[v7u_N000880|880] The sector’s inherent AML risk is generally lower than that of banking due to less liquid transactions, less complex product nature, and structured payout schedules.
ZH: 保险业固有洗钱风险低于银行业

[v7u_N000881|881] However, industry supervisory authorities usually remind entities that certain high-risk accounts and products still require attention.
ZH: 行业监管机构提醒关注高风险账户和产品

[v7u_N000882|882] Specifically, insurance products with high cash values or flexible payment options can be misused to obscure the source of funds, facilitating both money laundering and terrorist financing.
ZH: 高现金价值或灵活缴费的保险产品可能被滥用以掩盖资金来源

[v7u_N000883|883] Certain products can be high-risk, such as high-value life insurance and investment-linked policies, and can present AML concerns.
ZH: 高额人寿保险和投资连结保单属于高风险产品

[v7u_N000884|884] Criminals might exploit these products by making large, irregular premium payments, cashing out policies prematurely, or having an unrelated third party make the payments for the policy itself.
ZH: 犯罪分子可能通过大额不规则缴费、提前退保或第三方代缴保费来利用保险产品

[v7u_N000885|885] Red flags include early termination of policies after the cooling-off period, premium overpayments from third parties, claims filed shortly after the policy becomes effective, and early cash surrenders.
ZH: 保险洗钱红旗信号信号包括冷静期后退保、第三方超额缴费、保单生效后立即理赔和早期现金退保

[v7u_N000886|886] These actions can indicate attempts to convert illicit funds into legitimate assets.
ZH: 这些行为可能表明试图将非法资金转化为合法资产

[v7u_N000887|887] For instance, a criminal might purchase a high-value life insurance policy with illicit funds and then surrender it shortly after for a higher cash value, effectively laundering illegal money into legitimate assets.
ZH: 犯罪分子用非法资金购买高额人寿保单后立即退保套现，实现洗钱

[v7u_N000888|888] Maritime insurance is often linked to trade-based money laundering.
ZH: 海事保险常与贸易洗钱相关联

[v7u_N000889|889] Criminals might misclassify goods or submit fraudulent declarations to trigger insurance payouts, enabling illicit transfers of value that involve both money laundering and insurance fraud.
ZH: 犯罪分子可能通过错误分类货物或提交虚假申报来触发保险赔付，涉及洗钱和保险欺诈

[v7u_N000890|890] For example, goods such as electronic components might be falsely declared as “used clothing” to reduce scrutiny.
ZH: 例如，电子元件被虚假申报为“旧衣服”以减少审查

[v7u_N000891|891] Phantom shipping can occur when criminals report shipments that never existed. Undershipment happens when fewer goods are shipped than declared. Both allow criminals to file claims for lost or damaged shipments that never existed.
ZH: 虚假运输和少装货物是两种欺诈类型，犯罪分子可对不存在的货物损失提出索赔

[v7u_N000892|892] The combination of money laundering and insurance fraud enables illicit transfers of value while obscuring the true nature of the activities involved.
ZH: 洗钱与保险欺诈相结合，掩盖了活动的真实性质并实现非法价值转移
```

## S1.1 候选列表

```json
[]
```
