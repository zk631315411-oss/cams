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

section_id: `CH24-S10`

section_title: `US AML/CFT regulatory landscape > Markets in Cryptoassets Regulation`

section_text_with_unit_anchors:

```text
[v7u_N001831|1831] The Markets in Cryptoassets Regulation (MiCA), also known as MiCAR, has instituted the EU’s legislative framework governing the transparency, disclosure, authorization, and supervision of issuers and virtual asset service providers (VASP) since December 2024.
ZH: MiCA是欧盟加密资产立法框架，涵盖透明度、披露、授权与监管

[v7u_N001832|1832] The European Commission created MiCA to address the risks that unregulated cryptoassets pose to investors and financial markets.
ZH: 欧盟委员会制定MiCA以应对未监管加密资产对投资者和金融市场的风险

[v7u_N001833|1833] Key provisions focus on cryptoassets that existing financial services legislation did not previously regulate.
ZH: MiCA关键条款聚焦于现有金融立法未监管的加密资产

[v7u_N001834|1834] For instance, MiCA covers the issuance and trading of cryptoassets other than electronic money tokens (EMT) and asset-referenced tokens (ART).
ZH: MiCA涵盖除电子货币代币和资产参考代币外的加密资产发行与交易

[v7u_N001835|1835] MiCA provisions set forth how VASPs should handle the custody, administration, operation, and exchange of cryptoassets.
ZH: MiCA规定VASP应如何处理加密资产的托管、管理、运营与兑换

[v7u_N001836|1836] For example, MiCA regulates how VASPs receive and execute transactions on behalf of clients and conduct advice or portfolio management.
ZH: MiCA监管VASP代表客户接收和执行交易以及提供咨询或投资组合管理

[v7u_N001837|1837] MiCA restricts the issuance of EMTs to licensed entities such as banks and electronic money institutions that are already subject to the EU’s AFC regime.
ZH: MiCA限制EMT仅由已受欧盟金融犯罪防控制度监管的持牌实体发行

[v7u_N001838|1838] To issue ARTs, MiCA requires the party to obtain a license.
ZH: MiCA要求发行ART须获得许可证

[v7u_N001839|1839] Generally, the EU only grants licenses to firms established in the EU because the regulation makes few exceptions.
ZH: 欧盟通常仅向在欧盟设立的实体授予许可证，例外极少

[v7u_N001840|1840] The firm should have qualified shareholders and directors that are of good repute and do not have convictions of financial crime offenses. The firm should also have an effective AFC program.
ZH: 实体须具备声誉良好的股东和董事且无金融犯罪定罪，并拥有有效的金融犯罪防控计划

[v7u_N001841|1841] If the firm’s business model exposes the firm or the sector to serious financial crime risks or demonstrates deficiencies in the AFC program, the relevant regulatory body should reject the license.
ZH: 监管机构应拒绝存在严重金融犯罪风险或金融犯罪防控缺陷的牌照申请。

[v7u_N001842|1842] When receiving a request for admission to trading, VASPs must assess the reliability of the technical solutions, the reputation of the issuer and its development team, and the potential risks linked to the cryptoasset.
ZH: VASP在受理加密资产上市交易前须评估技术方案、发行人声誉及风险。

[v7u_N001843|1843] VASPs should reject admission to trading cryptoassets with inbuilt anonymization functions unless they can identify the token holders and their transaction history.
ZH: VASP应拒绝上市具有内置匿名功能的加密资产，除非能识别持有人及交易历史。

[v7u_N001844|1844] MiCA establishes rules against market abuse, thus prohibiting insider trading and market manipulation.
ZH: MiCA制定禁止内幕交易和市场操纵的市场滥用规则。

[v7u_N001845|1845] VASPs must have controls to prevent and detect market abuse and immediately report reasonable suspicions about an order or transaction to the relevant regulatory authority.
ZH: VASP须建立市场滥用防控机制并向监管机构报告可疑订单或交易。
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N001835",
      "v7u_N001836"
    ],
    "proposition": "MiCA要求VASP处理加密资产的托管、管理、运营、兑换，并监管其代表客户执行交易和提供咨询。",
    "source_quotes": [
      "MiCA provisions set forth how VASPs should handle the custody, administration, operation, and exchange of cryptoassets.",
      "MiCA regulates how VASPs receive and execute transactions on behalf of clients and conduct advice or portfolio management."
    ],
    "relation_cues": [
      "should",
      "regulates"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "VASP提供加密资产相关服务"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "VASP应遵守MiCA关于托管、管理、运营、兑换、客户交易和咨询的规定",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001835",
        "quote": "MiCA provisions set forth how VASPs should handle the custody, administration, operation, and exchange of cryptoassets."
      },
      {
        "unit_id": "v7u_N001836",
        "quote": "MiCA regulates how VASPs receive and execute transactions on behalf of clients and conduct advice or portfolio management."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N001837"
    ],
    "proposition": "MiCA限制EMT仅由已受欧盟金融犯罪防控制度监管的持牌实体发行。",
    "source_quotes": [
      "MiCA restricts the issuance of EMTs to licensed entities such as banks and electronic money institutions that are already subject to the EU’s AFC regime."
    ],
    "relation_cues": [
      "restricts",
      "subject to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "发行EMT"
      ],
      "basis_or_condition": [
        "发行方须为已受欧盟AFC监管的持牌实体（银行或电子货币机构）"
      ],
      "focal_handling_or_judgment": "限制EMT的发行主体",
      "outcomes_or_paths": [
        "仅允许符合条件的实体发行EMT"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001837",
        "quote": "MiCA restricts the issuance of EMTs to licensed entities such as banks and electronic money institutions that are already subject to the EU’s AFC regime."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N001838",
      "v7u_N001839",
      "v7u_N001840",
      "v7u_N001841"
    ],
    "proposition": "发行ART须获得欧盟许可证，仅授予欧盟设立且具有良好声誉股东/董事及有效AFC计划的实体；若商业模式有严重风险或AFC缺陷，监管机构应拒绝许可。",
    "source_quotes": [
      "To issue ARTs, MiCA requires the party to obtain a license.",
      "Generally, the EU only grants licenses to firms established in the EU because the regulation makes few exceptions.",
      "The firm should have qualified shareholders and directors that are of good repute and do not have convictions of financial crime offenses. The firm should also have an effective AFC program.",
      "If the firm’s business model exposes the firm or the sector to serious financial crime risks or demonstrates deficiencies in the AFC program, the relevant regulatory body should reject the license."
    ],
    "relation_cues": [
      "requires",
      "grants",
      "should have",
      "should reject"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "发行ART"
      ],
      "basis_or_condition": [
        "实体须在欧盟设立",
        "股东和董事声誉良好且无金融犯罪定罪",
        "拥有有效AFC计划"
      ],
      "focal_handling_or_judgment": "监管机构授予或拒绝ART发行许可证",
      "outcomes_or_paths": [
        "满足正面条件且无严重风险/缺陷时授予许可证",
        "存在严重金融犯罪风险或AFC缺陷时拒绝许可证"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001838",
        "quote": "To issue ARTs, MiCA requires the party to obtain a license."
      },
      {
        "unit_id": "v7u_N001839",
        "quote": "Generally, the EU only grants licenses to firms established in the EU because the regulation makes few exceptions."
      },
      {
        "unit_id": "v7u_N001840",
        "quote": "The firm should have qualified shareholders and directors that are of good repute and do not have convictions of financial crime offenses. The firm should also have an effective AFC program."
      },
      {
        "unit_id": "v7u_N001841",
        "quote": "If the firm’s business model exposes the firm or the sector to serious financial crime risks or demonstrates deficiencies in the AFC program, the relevant regulatory body should reject the license."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N001842",
      "v7u_N001843"
    ],
    "proposition": "VASP在受理加密资产上市请求时须评估技术方案、发行人声誉及风险；应拒绝具有内置匿名功能的加密资产，除非能识别持有人及交易历史。",
    "source_quotes": [
      "When receiving a request for admission to trading, VASPs must assess the reliability of the technical solutions, the reputation of the issuer and its development team, and the potential risks linked to the cryptoasset.",
      "VASPs should reject admission to trading cryptoassets with inbuilt anonymization functions unless they can identify the token holders and their transaction history."
    ],
    "relation_cues": [
      "must assess",
      "should reject unless"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "收到加密资产上市交易请求"
      ],
      "basis_or_condition": [
        "加密资产具有内置匿名功能且无法识别持有人及交易历史"
      ],
      "focal_handling_or_judgment": "VASP对上市请求进行评估并决定是否接受",
      "outcomes_or_paths": [
        "评估后符合要求可接受上市",
        "匿名功能无法识别持有人及交易历史时拒绝上市"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001842",
        "quote": "When receiving a request for admission to trading, VASPs must assess the reliability of the technical solutions, the reputation of the issuer and its development team, and the potential risks linked to the cryptoasset."
      },
      {
        "unit_id": "v7u_N001843",
        "quote": "VASPs should reject admission to trading cryptoassets with inbuilt anonymization functions unless they can identify the token holders and their transaction history."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N001844",
      "v7u_N001845"
    ],
    "proposition": "MiCA禁止内幕交易和市场操纵，VASP须建立市场滥用防控机制并立即向监管机构报告可疑订单或交易。",
    "source_quotes": [
      "MiCA establishes rules against market abuse, thus prohibiting insider trading and market manipulation.",
      "VASPs must have controls to prevent and detect market abuse and immediately report reasonable suspicions about an order or transaction to the relevant regulatory authority."
    ],
    "relation_cues": [
      "prohibiting",
      "must have",
      "report"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "市场活动涉及加密资产"
      ],
      "basis_or_condition": [
        "MiCA反市场滥用规则"
      ],
      "focal_handling_or_judgment": "VASP建立市场滥用防控并报告可疑",
      "outcomes_or_paths": [
        "发现可疑订单或交易时立即向监管机构报告"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001844",
        "quote": "MiCA establishes rules against market abuse, thus prohibiting insider trading and market manipulation."
      },
      {
        "unit_id": "v7u_N001845",
        "quote": "VASPs must have controls to prevent and detect market abuse and immediately report reasonable suspicions about an order or transaction to the relevant regulatory authority."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
