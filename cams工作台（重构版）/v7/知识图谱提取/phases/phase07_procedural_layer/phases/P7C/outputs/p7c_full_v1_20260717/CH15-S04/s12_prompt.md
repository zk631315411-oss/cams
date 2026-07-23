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

section_id: `CH15-S04`

section_title: `Money laundering risks associated with DNFBPs > Trust and company service provider and company secretary sector risks`

section_text_with_unit_anchors:

```text
[v7u_N001120|1120] Trust and company service providers (TCSP) offer a range of business services, including nominee services, the establishment of shell companies, and the incorporation of onshore and offshore companies.
ZH: 信托与公司服务提供商（TCSP）提供代名服务、设立壳公司等业务

[v7u_N001121|1121] Company secretaries ensure compliance with corporate governance standards and relevant laws and regulations. Their responsibilities include maintaining company records, filing annual reports, and organizing board meetings.
ZH: 公司秘书负责确保公司治理合规、维护记录、提交年报及组织董事会会议。

[v7u_N001122|1122] The nature of their work can present money laundering risks.
ZH: 指定非金融行业与职业的工作性质可能带来洗钱风险。

[v7u_N001123|1123] Criminals might exploit TCSPs to obfuscate true ownership of assets or structure transactions that disguise the origin of illicit funds.
ZH: 犯罪分子可能利用信托与公司服务提供商掩盖资产真实所有权或交易资金来源。

[v7u_N001124|1124] For secretaries, heightened money laundering risks arise if they fail to vet key stakeholders or identify red flags in corporate structures and transactions.
ZH: 公司秘书若未能审查关键利益相关者或识别公司结构与交易中的红旗信号信号，则洗钱风险升高。

[v7u_N001125|1125] A lack of due diligence in maintaining company records or supporting corporate governance processes could enable criminals to obscure UBO identities, unwittingly facilitating illicit activities.
ZH: 缺乏尽职调查维护公司记录或支持公司治理流程，可能使犯罪分子掩盖最终受益所有人身份。

[v7u_N001126|1126] TCSPs often offer nominee services, where they provide third parties to act on behalf of customers in ownership and management roles, such as directors, officers, or shareholders.
ZH: 信托与公司服务提供商常提供名义服务，由第三方代表客户担任董事、高管或股东。

[v7u_N001127|1127] These nominee directors or shareholders can be used to conceal the identity of the UBO or operator of the business, creating a layer of anonymity that heightens money laundering risks through obfuscation.
ZH: 名义董事或股东可被用于隐藏最终受益所有人身份，增加洗钱风险。

[v7u_N001128|1128] Criminals might use this nominee structure to distance themselves from illicit activities and treat it as a cover to move funds across jurisdictions with weak regulations.
ZH: 犯罪分子可能利用名义结构远离非法活动，并作为在监管薄弱地区转移资金的掩护。

[v7u_N001129|1129] Shelf companies are often sold to customers looking to bypass procedural requirements or expedite company formation.
ZH: 现成公司常出售给希望绕过程序要求或加快公司成立的客户。

[v7u_N001130|1130] Shelf companies present an increased money laundering risk.
ZH: 现成公司带来更高的洗钱风险。

[v7u_N001131|1131] Since they are pre-registered, they typically have clean histories and can be established with fake ownership structures. This can complicate the ability of financial institutions and regulatory authorities to identify the actual UBOs.
ZH: 现成公司预注册、历史清白且可建立虚假所有权结构，使识别最终受益所有人复杂化。

[v7u_N001132|1132] Offshore company formation involves establishing a company outside the customer’s home country, usually in low-tax and/or high-secrecy jurisdictions.
ZH: 离岸公司注册是指在客户母国之外、通常在低税或高保密司法管辖区设立公司。

[v7u_N001133|1133] The services include handling administrative tasks such as maintaining the company's registration, filing documents, and ensuring compliance with local regulations.
ZH: 离岸公司注册服务包括维护公司登记、提交文件及确保当地合规等行政事务。

[v7u_N001134|1134] However, weak AML regulations in some offshore locations allow criminals to obfuscate true ownership.
ZH: 部分离岸地区反洗钱法规薄弱，使犯罪分子得以掩盖真实所有权。

[v7u_N001135|1135] The limited availability of public records and complex international transaction flows increase the money laundering risks associated with offshore companies, making TCSP an important gatekeeper.
ZH: 有限的公开记录和复杂的国际交易流增加了离岸公司的洗钱风险，使信托与公司服务提供商成为重要守门人。
```

## S1.1 候选列表

```json
[]
```
