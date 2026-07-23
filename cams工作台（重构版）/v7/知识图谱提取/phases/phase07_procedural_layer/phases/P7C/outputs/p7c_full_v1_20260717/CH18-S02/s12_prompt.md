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

section_id: `CH18-S02`

section_title: `Global AFC Frameworks, Governance, and Regulations > Case example: Implementing AFC standards at FinTrust`

section_text_with_unit_anchors:

```text
[v7u_N001281|1281] Amina is a manager at FinTrust, a financial institution in the US. She is going to deliver a training session to a new graduate trainee, Drew.
ZH: 案例场景：FinTrust经理Amina向新员工Drew提供培训

[v7u_N001282|1282] Drew tells Amina about a situation in which a high-net-worth customer from Russia applied for an account and the bank rejected the application. He asks what FinTrust’s protocols are for such situations.
ZH: Drew询问FinTrust对受制裁地区客户申请账户的处理规程

[v7u_N001283|1283] Amina tells Drew that when a customer from a sanctioned jurisdiction applies for an account, compliance personnel at FinTrust must act immediately. They perform enhanced due diligence, screen for PEPs, and enhance monitoring for unusual transactions. These controls lower the risk of unknowingly facilitating money laundering or violating sanctions.
ZH: FinTrust对受制裁地区申请人执行强化尽职调查、政治敏感人物筛查和异常交易监控

[v7u_N001284|1284] Amina explains that some international bodies establish standards or recommendations that help ensure coordinated and strong controls against financial crime.
ZH: 国际机构制定标准以协调金融犯罪防控措施

[v7u_N001285|1285] Generally, most jurisdictions will then tailor and implement these standards into their respective laws and regulations before FinTrust incorporates them into its program.
ZH: 各司法管辖区将国际标准转化为国内法律并实施

[v7u_N001286|1286] Amina explains to Drew that financial crime has been a growing concern for decades, and the global fight against transnational crime took a major step forward with the Palermo Convention in 2000. This UN treaty addressed organized crime, money laundering, and corruption, encouraging governments to adopt stricter financial crime controls.
ZH: 2000年《巴勒莫公约》推动各国采取更严格的金融犯罪控制措施

[v7u_N001287|1287] She also mentions that the terrorist attacks of September 11, 2001, exposed new vulnerabilities. They revealed how terrorist organizations exploited the financial system to move illicit funds undetected.
ZH: 9/11恐怖袭击暴露了金融体系被恐怖组织利用的漏洞

[v7u_N001288|1288] In response, FATF expanded its mission to include terrorism financing.
ZH: FATF将使命扩展至打击恐怖融资

[v7u_N001289|1289] Additionally, the US enacted the USA PATRIOT Act, introducing stricter KYC rules, enhanced transaction monitoring, and increased information sharing between banks and regulators.
ZH: 美国《爱国者法案》引入更严格的了解你的客户规则和交易监控

[v7u_N001290|1290] The EU and the UN Security Council followed suit with similar measures, strengthening law enforcement cooperation and intelligence sharing.
ZH: 欧盟和联合国安理会随后采取类似措施加强执法合作

[v7u_N001291|1291] Today, multiple international organizations, such as FATF, Basel Committee on Banking Supervision, and Wolfsberg Group, continue to shape financial crime compliance standards.
ZH: FATF、巴塞尔银行监管委员会和沃尔夫斯堡集团等国际组织持续塑造金融犯罪合规标准

[v7u_N001292|1292] They issue recommendations that influence banking operations worldwide, from CDD to transaction screening for sanctions violations.
ZH: 这些组织发布影响全球银行业务的建议，涵盖客户尽职调查和制裁交易筛查

[v7u_N001293|1293] Amina emphasizes that ignoring these standards can lead to severe consequences for FinTrust, including regulatory fines, reputational damage, or even loss of access to the global banking system.
ZH: 忽视金融犯罪防控标准可能导致监管罚款、声誉损害或失去全球银行系统准入

[v7u_N001294|1294] Regulatory bodies such as the OFAC, SEC, and OCC can impose multi-million-dollar penalties, ceaseand-desist orders, and operational restrictions.
ZH: OFAC、SEC和OCC等监管机构可处以数百万美元罚款及运营限制

[v7u_N001295|1295] In more serious cases, senior executives and compliance officers might face criminal prosecution, asset forfeitures, and even imprisonment for willful violations.
ZH: 严重违规时高管和合规官可能面临刑事起诉和监禁
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N001283"
    ],
    "proposition": "当客户来自受制裁司法管辖区并申请账户时，FinTrust合规人员必须立即执行强化尽职调查、政治敏感人物筛查和异常交易监控，以降低风险。",
    "source_quotes": [
      "Amina tells Drew that when a customer from a sanctioned jurisdiction applies for an account, compliance personnel at FinTrust must act immediately. They perform enhanced due diligence, screen for PEPs, and enhance monitoring for unusual transactions. These controls lower the risk of unknowingly facilitating money laundering or violating sanctions."
    ],
    "relation_cues": [
      "when",
      "must",
      "perform",
      "lower"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "客户来自受制裁司法管辖区并申请账户"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "FinTrust合规人员必须立即执行强化尽职调查、政治敏感人物筛查和异常交易监控",
      "outcomes_or_paths": [
        "降低无意中协助洗钱或违反制裁的风险"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001283",
        "quote": "Amina tells Drew that when a customer from a sanctioned jurisdiction applies for an account, compliance personnel at FinTrust must act immediately. They perform enhanced due diligence, screen for PEPs, and enhance monitoring for unusual transactions. These controls lower the risk of unknowingly facilitating money laundering or violating sanctions."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
