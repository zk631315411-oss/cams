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

section_id: `CH06-S07`

section_title: `Money Laundering Risks in Financial Services > Shell and shelf companies risks`

section_text_with_unit_anchors:

```text
[v7u_N000426|426] A shell company or corporation is a company that, at the time of incorporation, has no significant assets or operations.
ZH: 壳公司（shell company）指成立时无重大资产或运营的公司

[v7u_N000427|427] A similarly named "shelf" company is a corporation that has had no activity. It has been created and put "on the shelf" so that it can be sold later to someone who prefers a previously registered corporation over a new one.
ZH: 现成公司（shelf company）是已注册但无活动的公司，可后续出售

[v7u_N000428|428] Both shell and shelf companies are generally kept dormant and used later to appear legitimate while usually masking the beneficial owner.
ZH: 壳公司和现成公司通常保持休眠，用于掩盖受益所有人

[v7u_N000429|429] A front company is an entity that conducts some legitimate business while also shielding another company from liability or scrutiny.
ZH: 幌子公司（front company）从事合法业务同时掩护另一公司

[v7u_N000430|430] Financial criminals might use a front company to conceal illicit activity. For example, they might operate a car wash to launder the profits of drug trafficking.
ZH: 幌子公司可用于洗钱，例如以洗车行掩盖毒品交易利润

[v7u_N000431|431] While there are legitimate uses for shell, shelf, and front companies, within the context of researching and accepting customers, they are considered high risk.
ZH: 壳公司、现成公司和幌公司在客户准入中视为高风险

[v7u_N000432|432] Shell companies can be established with the primary objective of claiming the proceeds of crime as legitimate revenue or commingling criminal proceeds with legitimate revenue. According to the Financial Action Task Force (FATF), the use of shell companies to facilitate financial crime is a well-documented typology.
ZH: 壳公司可用于将犯罪收益混入合法收入，FATF已记录此类型

[v7u_N000433|433] Shell companies can be set up in onshore and offshore locations.
ZH: 壳公司可在在岸和离岸地点设立

[v7u_N000434|434] Their ownership structures can take several forms:
ZH: 壳公司的所有权结构有多种形式

[v7u_N000435|435] Shares can be issued to a natural or legal person in registered or bearer form.
ZH: 股份可以记名或不记名形式发行给自然人或法人

[v7u_N000436|436] Some shell companies can be created for a single purpose or to hold a single asset.
ZH: 部分壳公司可为单一目的或持有单一资产而设立

[v7u_N000437|437] Some shell companies can be established as multipurpose entities.
ZH: 部分壳公司可设立为多用途实体

[v7u_N000438|438] Shell companies are often legally incorporated and registered by the criminal organization but have no legitimate business purpose. Often purchased from lawyers, accountants, or corporate service providers, they are convenient vehicles for bribery and corruption, money laundering, and sanctions evasion.
ZH: 壳公司常由犯罪组织合法注册但无正当商业目的，用于贿赂、洗钱和逃避制裁

[v7u_N000439|439] Sometimes, the stock of these shell corporations is issued in bearer shares, which means that whoever carries them is the purported owner.
ZH: 不记名股票（bearer shares）的持有者即为名义所有人

[v7u_N000440|440] Tax haven countries and their strict secrecy laws can further conceal the true ownership of shell corporations. In addition, the information may be held by professionals who claim secrecy.
ZH: 避税天堂的保密法及专业人士的保密义务可进一步隐藏壳公司真实所有权

[v7u_N000441|441] When FATF reviewed the rules and practices that impair the effectiveness of financial crime prevention and detection systems, it found in particular that shell corporations and nominees are widely used mechanisms to launder the proceeds from crime. As a result, shell companies are considered to represent a higher risk of financial crime.
ZH: FATF发现壳公司和名义人是洗钱高风险机制

[v7u_N000442|442] Danske Bank, Denmark's largest financial institution, became embroiled in a significant money laundering case centered around its Estonian branch. According to Reuters, between 2007 and 2015, approximately €200 billion of suspicious funds were funneled through the bank, primarily originating from Russia as well as Estonia, Latvia, Cyprus, and Great Britain. The scandal became known in 2018, unveiling the intricate use of shell and shelf companies to facilitate the laundering process.
ZH: 丹麦银行爱沙尼亚分行洗钱案涉及壳公司和现成公司

[v7u_N000443|443] One prominent example was the use of United Kingdom limited liability partnerships (LLP) and Scottish limited partnerships (SLP). These entities allowed for minimal disclosure requirements, enabling criminals to hide behind complex ownership structures. The shell companies conducted fictitious transactions and created false invoices to justify the movement of funds, making it difficult for authorities to trace the origins of the illicit money.
ZH: 英国LLP和SLP被用于洗钱，利用低披露要求隐藏所有权

[v7u_N000444|444] The laundering process in the Danske Bank scandal involved multiple steps to layer and integrate the illicit funds.
ZH: 丹麦银行洗钱过程包括多层放置、离析和融合

[v7u_N000445|445] Initially, money was deposited into accounts held by shell and shelf companies in Danske Bank's Estonian branch.
ZH: 资金最初存入丹麦银行爱沙尼亚分行的壳公司和现成公司账户

[v7u_N000446|446] These funds were then transferred through a complex web of transactions involving other shell companies, often spanning multiple jurisdictions.
ZH: 资金通过涉及其他壳公司的复杂交易网络跨境转移

[v7u_N000447|447] By moving the money through various entities and accounts, the criminals created a convoluted trail that was challenging to untangle.
ZH: 犯罪分子通过多个实体和账户转移资金制造混乱的追踪线索

[v7u_N000448|448] The use of false documentation, including fake contracts and invoices, provided legitimacy to the transactions.
ZH: 使用虚假合同和发票等伪造文件为交易提供合法性

[v7u_N000449|449] An additional finding of the scandal revealed that Danske Bank’s head office was unaware of the AML compliance failings, including the lack of an MLRO appointment for over a year, as they did not have adequate oversight and supervision of the Estonian branch and of the transactions that were being processed.
ZH: 丹麦银行总部对爱沙尼亚分行的反洗钱合规失败不知情

[v7u_N000450|450] The Danske Bank scandal had far-reaching consequences for the institution and the broader financial landscape. According to a press release by the US Department of Justice, Danske Bank faced significant regulatory scrutiny, leading to the resignation of several top executives. Danske Bank pleaded guilty to bank fraud conspiracy and paid substantial fines of more than US$2 billion.
ZH: 丹麦银行因洗钱丑闻认罪银行欺诈并支付超20亿美元罚款

[v7u_N000451|451] The scandal also reiterated the importance of robust AML controls and the need for enhanced transparency in financial transactions and adequate supervision of subsidiary businesses and operations if they are remote or overseas in higher-risk jurisdictions.
ZH: 丑闻重申了健全反洗钱控制和海外子公司监管的重要性
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N000431"
    ],
    "proposition": "壳公司、现成公司和幌公司在客户准入中视为高风险。",
    "source_quotes": [
      "While there are legitimate uses for shell, shelf, and front companies, within the context of researching and accepting customers, they are considered high risk."
    ],
    "relation_cues": [
      "considered"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "客户准入（researching and accepting customers）"
      ],
      "basis_or_condition": [
        "存在合法用途"
      ],
      "focal_handling_or_judgment": "壳公司、现成公司和幌公司被视为高风险",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000431",
        "quote": "While there are legitimate uses for shell, shelf, and front companies, within the context of researching and accepting customers, they are considered high risk."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N000441"
    ],
    "proposition": "FATF发现壳公司和名义人被广泛用于洗钱，因此壳公司被认为代表更高洗钱风险。",
    "source_quotes": [
      "When FATF reviewed the rules and practices that impair the effectiveness of financial crime prevention and detection systems, it found in particular that shell corporations and nominees are widely used mechanisms to launder the proceeds from crime. As a result, shell companies are considered to represent a higher risk of financial crime."
    ],
    "relation_cues": [
      "found",
      "As a result",
      "considered"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "FATF审查妨碍金融犯罪预防和检测有效性的规则和实践"
      ],
      "basis_or_condition": [
        "壳公司和名义人被广泛用于洗钱"
      ],
      "focal_handling_or_judgment": "壳公司被认为代表更高洗钱风险",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000441",
        "quote": "When FATF reviewed the rules and practices that impair the effectiveness of financial crime prevention and detection systems, it found in particular that shell corporations and nominees are widely used mechanisms to launder the proceeds from crime. As a result, shell companies are considered to represent a higher risk of financial crime."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N000449"
    ],
    "proposition": "丹麦银行总部对爱沙尼亚分行的反洗钱合规失败不知情，原因是缺乏充分的监督和监督。",
    "source_quotes": [
      "An additional finding of the scandal revealed that Danske Bank’s head office was unaware of the AML compliance failings, including the lack of an MLRO appointment for over a year, as they did not have adequate oversight and supervision of the Estonian branch and of the transactions that were being processed."
    ],
    "relation_cues": [
      "revealed",
      "unaware",
      "as",
      "did not have"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "丹麦银行洗钱丑闻调查"
      ],
      "basis_or_condition": [
        "总部缺乏对爱沙尼亚分支机构的充分监督和监督"
      ],
      "focal_handling_or_judgment": "总部对反洗钱合规失败不知情",
      "outcomes_or_paths": [
        "反洗钱合规失败，包括一年多未任命MLRO"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000449",
        "quote": "An additional finding of the scandal revealed that Danske Bank’s head office was unaware of the AML compliance failings, including the lack of an MLRO appointment for over a year, as they did not have adequate oversight and supervision of the Estonian branch and of the transactions that were being processed."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N000450"
    ],
    "proposition": "丹麦银行因洗钱丑闻认罪银行欺诈共谋并支付超过20亿美元罚款。",
    "source_quotes": [
      "According to a press release by the US Department of Justice, Danske Bank faced significant regulatory scrutiny, leading to the resignation of several top executives. Danske Bank pleaded guilty to bank fraud conspiracy and paid substantial fines of more than US$2 billion."
    ],
    "relation_cues": [
      "pleaded guilty",
      "paid fines"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "丹麦银行洗钱丑闻及监管审查"
      ],
      "basis_or_condition": [
        "银行欺诈共谋"
      ],
      "focal_handling_or_judgment": "丹麦银行认罪银行欺诈共谋",
      "outcomes_or_paths": [
        "支付超过20亿美元罚款",
        "多名高管辞职"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000450",
        "quote": "According to a press release by the US Department of Justice, Danske Bank faced significant regulatory scrutiny, leading to the resignation of several top executives. Danske Bank pleaded guilty to bank fraud conspiracy and paid substantial fines of more than US$2 billion."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
