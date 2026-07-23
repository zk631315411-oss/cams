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

section_id: `CH12-S05`

section_title: `Money laundering risks associated with insurance, securities, brokerage, and custodian services > Custodial services risks`

section_text_with_unit_anchors:

```text
[v7u_N000938|938] A custodian bank is a financial institution that safeguards its customers' assets, including stocks and bonds.
ZH: 托管银行是保管客户资产（如股票和债券）的金融机构

[v7u_N000939|939] Custodian banks typically serve banks and other financial institutions, including securities intermediaries.
ZH: 托管银行通常服务于银行和其他金融机构

[v7u_N000940|940] They provide a range of services, including securities safekeeping, processing and execution of settlement instructions, transition management, and funds distribution.
ZH: 托管银行提供证券保管、结算指令处理、过渡管理和基金分销等服务

[v7u_N000941|941] They might also provide reporting and tax compliance services.
ZH: 托管银行可能提供报告和税务合规等附加服务。

[v7u_N000942|942] These services can be for a customer’s account and/or for its underlying clients, representing various beneficial owners.
ZH: 托管服务可针对客户账户或其底层客户，代表多个受益所有人。

[v7u_N000943|943] This complexity emphasizes the need for custodian banks to know their customers and underlying clients, including their:
ZH: 复杂性要求托管银行了解客户和底层客户的多项信息。

[v7u_N000944|944] AML policies.
ZH: 需要了解客户的反洗钱政策。

[v7u_N000945|945] Geographical footprint of business operations.
ZH: 需要了解客户的业务运营地理足迹。

[v7u_N000946|946] Country of incorporation.
ZH: 需要了解客户的注册国家。

[v7u_N000947|947] Transparency in information exchange.
ZH: 需要了解客户的信息交换透明度。

[v7u_N000948|948] Money laundering risks are inherent in custodial services, particularly with shell companies or nominee accounts.
ZH: 托管服务固有洗钱风险，尤其涉及壳公司或名义账户。

[v7u_N000949|949] They can conceal true ownership of assets, making it difficult to identify beneficial owners.
ZH: 空壳公司或名义账户可隐藏资产真实所有权，难以识别受益所有人。

[v7u_N000950|950] Additionally, custodian banks might be used to layer transactions, complicating the tracking of fund origins and identification of suspicious activity.
ZH: 托管银行可能被用于离析阶段交易，增加追踪资金起源和识别可疑活动的难度。

[v7u_N000951|951] Financial crime risks in custodial services stem from relying on other banks to perform KYC checks. This reliance creates a false sense of security, as the custodian bank might not have complete information on client identities. If the other bank fails to perform adequate checks, the custodian could inadvertently facilitate transactions involving illicit funds, exposing itself to regulatory scrutiny.
ZH: 依赖其他银行进行了解你的客户检查会带来金融犯罪风险，可能无意中为非法资金提供便利。

[v7u_N000952|952] Multiple customers in a chain present additional risks as complex ownership structures obscure beneficial ownership and complicate transaction tracing. Each additional client in the chain adds a layer of complexity, which can complicate due diligence processes.
ZH: 链条中的多个客户因复杂所有权结构而增加风险，模糊受益所有人并复杂化交易追踪。

[v7u_N000953|953] Regulators have begun examining the custodial services sector more closely for financial crime risk.
ZH: 监管机构开始更密切地审查托管服务部门的金融犯罪风险。

[v7u_N000954|954] For example, in 2024, the UK’s FCA admonished custodian banks for their AML shortcomings and emphasized the need for rigorous AML controls. They cited a variety of common failings, including discrepancies between registered and actual activities, inadequate AML resources, and failure to assess customer activity risks.
ZH: 2024年英国FCA批评托管银行反洗钱缺陷，强调需要严格的反洗钱控制。
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N000954"
    ],
    "proposition": "2024年英国FCA因反洗钱缺陷批评托管银行，并强调需要严格的反洗钱控制，指出常见失败包括注册与实际活动不符、反洗钱资源不足、未评估客户活动风险。",
    "source_quotes": [
      "For example, in 2024, the UK’s FCA admonished custodian banks for their AML shortcomings and emphasized the need for rigorous AML controls. They cited a variety of common failings, including discrepancies between registered and actual activities, inadequate AML resources, and failure to assess customer activity risks."
    ],
    "relation_cues": [
      "admonished",
      "emphasized",
      "need",
      "failings"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "2024年英国FCA对托管服务部门的审查"
      ],
      "basis_or_condition": [
        "托管银行存在反洗钱缺陷"
      ],
      "focal_handling_or_judgment": "FCA批评托管银行并强调需要严格的反洗钱控制",
      "outcomes_or_paths": [
        "发现常见失败包括注册与实际活动不符、反洗钱资源不足、未评估客户活动风险"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000954",
        "quote": "For example, in 2024, the UK’s FCA admonished custodian banks for their AML shortcomings and emphasized the need for rigorous AML controls. They cited a variety of common failings, including discrepancies between registered and actual activities, inadequate AML resources, and failure to assess customer activity risks."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
