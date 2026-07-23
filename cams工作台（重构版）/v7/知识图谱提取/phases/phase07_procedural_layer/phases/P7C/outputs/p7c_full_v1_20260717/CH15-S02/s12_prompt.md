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

section_id: `CH15-S02`

section_title: `Money laundering risks associated with DNFBPs > Gaming sector risks`

section_text_with_unit_anchors:

```text
[v7u_N001071|1071] The gaming sector includes physical and virtual casinos, internet gaming, and betting or gambling.
ZH: 博彩业包括实体赌场、虚拟赌场、互联网游戏及投注或赌博

[v7u_N001072|1072] Gaming operators offer various products and services based on their local regulations.
ZH: 博彩运营商根据当地法规提供不同的产品和服务

[v7u_N001073|1073] This means that the financial crime risk associated with each gaming segment is unique.
ZH: 每个博彩细分领域具有独特的金融犯罪风险

[v7u_N001074|1074] For example, both casinos and online operators are vulnerable to many forms of money laundering, such as customers converting illicit funds into chips, engaging in minimal play, and using falsified documents to open multiple accounts.
ZH: 赌场和在线运营商均易遭受多种洗钱方式，如筹码转换和伪造文件开户

[v7u_N001075|1075] The gaming sector has unique characteristics that carry inherently high financial crime risks.
ZH: 博彩业具有固有高金融犯罪风险的独特特征

[v7u_N001076|1076] These include risks associated with a fragmented regulatory environment, the cross-border nature of activities, and the offering of quasi-financial services.
ZH: 博彩业风险因素包括监管环境碎片化、跨境活动和准金融服务

[v7u_N001077|1077] Another inherent risk arises from the variety, frequency, and volume of transactions.
ZH: 交易种类、频率和数量带来的固有风险

[v7u_N001078|1078] This situation is further complicated by the rapid growth of online gaming, which involves non-face-to-face customer interactions and onboarding, along with emerging technologies that often introduce vulnerabilities alongside opportunity.
ZH: 在线游戏增长带来非面对面交互和新兴技术漏洞

[v7u_N001079|1079] Since online gaming operators onboard customers remotely, they might face exposure to high-risk jurisdictions.
ZH: 远程开户使在线博彩运营商面临高风险司法管辖区敞口

[v7u_N001080|1080] The quick onboarding process appeals to criminals, and the risk of identity fraud escalates when necessary controls are lacking.
ZH: 快速开户流程吸引犯罪分子，缺乏控制时身份欺诈风险上升

[v7u_N001081|1081] Additionally, online gaming operators might inadvertently permit customers outside the jurisdiction to participate in gaming if IP spoofing occurs or geolocation safeguards fail, usually facilitated by users accessing the website or mobile application through a VPN.
ZH: 在线博彩运营商可能因IP欺骗或地理定位失败而允许辖区外客户参与

[v7u_N001082|1082] Physical casinos encounter certain financial crime risks as well.
ZH: 实体赌场面临金融犯罪风险

[v7u_N001083|1083] While they are not classified as financial institutions, they do provide quasi-financial services.
ZH: 赌场虽非金融机构但提供准金融服务

[v7u_N001084|1084] For example, they accept funds on account, perform money and foreign currency exchanges, facilitate money transfers, provide stored-value services, cash checks, and offer safe deposit boxes.
ZH: 赌场提供的准金融服务包括资金托管、货币兑换、转账、储值、支票兑现和保险箱

[v7u_N001085|1085] These services potentially expose them to many of the same risks faced by financial institutions.
ZH: 赌场因提供准金融服务而面临与金融机构类似的风险

[v7u_N001086|1086] Junkets, a form of tourism, including sponsored or incentive-based trips, are also inherently high-risk due to the cross-border movement of funds and people, particularly involving high-net-worth individuals.
ZH: 赌团因跨境资金和人员流动及涉及高净值人士而具有高风险

[v7u_N001087|1087] Junket operators refer clients to casinos and seldom collect KYC details from the customers and share them with casinos. This practice introduces risks regarding transparency of customer identification and source of funds.
ZH: 赌团运营商不收集了解你的客户信息导致客户身份和资金来源透明度风险

[v7u_N001088|1088] Both physical and online gaming are susceptible to certain financial crime risks.
ZH: 实体和在线博彩均易受金融犯罪风险影响

[v7u_N001089|1089] They encounter criminal threats such as organized crime, loan sharking, prostitution, drug dealing, and human trafficking, all of which are predicate offenses.
ZH: 博彩业面临有组织犯罪、高利贷、卖淫、毒品和人口贩卖等上游犯罪威胁

[v7u_N001090|1090] They are also at risk of transaction structuring to evade reporting thresholds, including the use of third parties and multiple transactions to arrange deposits.
ZH: 博彩业存在通过第三方和多笔交易规避报告门槛的结构化交易风险

[v7u_N001091|1091] In peer-to-peer or collusion gaming, such as poker, participants might intentionally lose to another player to transfer value and potentially criminal proceeds.
ZH: 在P2P或串通博彩中参与者可能故意输牌以转移价值
```

## S1.1 候选列表

```json
[]
```
