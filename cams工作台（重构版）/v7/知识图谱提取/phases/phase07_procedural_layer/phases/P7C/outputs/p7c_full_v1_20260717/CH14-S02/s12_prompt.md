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

section_id: `CH14-S02`

section_title: `Money Laundering Risks in DNFBPs and Other High-Risk Sectors > Case example: DNFBP risks in the Hendricks case`

section_text_with_unit_anchors:

```text
[v7u_N001045|1045] Josh is a US-based lawyer and AFC professional with experience in regulated entities. He has been invited to participate in his jurisdiction’s Financial Risk Review Task Force to examine whether additional regulations are needed for DNFBPs and other high-risk sectors. The task force aims to classify the various types of DNFBPs, the customers they serve, and the associated risks to establish the regulatory needs.
ZH: 案例：Josh参与司法管辖区金融风险审查工作组，审查DNFBP及高风险行业监管需求。

[v7u_N001046|1046] A notable case discussed involved Kurt Hendricks, a Russian customer charged with bank fraud and money laundering related to two condominiums in California.
ZH: Hendricks案：俄罗斯客户被控银行欺诈和洗钱，涉及加州两套公寓。

[v7u_N001047|1047] Hendricks used a corporate nominee and a multi-tiered structure of shell companies to conceal his identity from US financial institutions.
ZH: Hendricks使用公司名义代理人和多层壳公司结构向美国金融机构隐瞒身份。

[v7u_N001048|1048] He wired nearly US$4 million from overseas accounts in Latvia and Switzerland, where there are lower regulatory expectations with response to AML/CFT, to fund a US$3 million real estate transaction through a corporate entity set up by the nominee in the British Virgin Islands.
ZH: Hendricks从拉脱维亚和瑞士的低监管账户电汇近400万美元，通过英属维尔京群岛公司实体完成房地产交易。

[v7u_N001049|1049] The remaining funds were invested in a brokerage account maintained by the nominee and used to pay expenses for the condominiums.
ZH: 剩余资金投资于名义代理人维护的经纪账户，并用于支付公寓费用。

[v7u_N001050|1050] The Hendricks case demonstrated how money laundering cases can involve multiple DNFBPs, each presenting unique risks, including:
ZH: Hendricks案展示了洗钱案如何涉及多个DNFBP，各自呈现独特风险。

[v7u_N001051|1051] Real estate agents who facilitate high-value transactions involving ultimate beneficial owners that are not clearly identified.
ZH: 房地产经纪人促成高价值交易，最终受益所有人身份不明。

[v7u_N001052|1052] Lawyers and trust or company service providers (TCSP) who create complex corporate structures to obscure the sources of funds.
ZH: 律师和信托或公司服务提供商（TCSP）创建复杂公司结构以掩盖资金来源。

[v7u_N001053|1053] Accountants who enable illicit transactions to appear legitimate.
ZH: 会计师使非法交易看似合法。

[v7u_N001054|1054] The task force noted that attorneys in the US are self-regulated by state bar associations, which provide recommended rules but lack mandatory reporting requirements.
ZH: 美国律师由州律师协会自律，提供推荐规则但缺乏强制报告要求。

[v7u_N001055|1055] Similarly, real estate agencies and TCSPs do not have to adhere to AML/CFT regulations or conduct audits for compliance.
ZH: 房地产中介和TCSP无需遵守反洗钱/反恐怖融资法规或进行合规审计。

[v7u_N001056|1056] Given the complexities and risks associated with DNFBPs, the task force recommended comprehensive AML/CFT regulations to bridge existing gaps.
ZH: 工作组建议制定全面的反洗钱/反恐怖融资法规以弥补现有差距。

[v7u_N001057|1057] Requiring DNFBPs to set up an AML/CFT framework and find the right balance between customer privacy and AML reporting requirements could deter the financial benefits of enabling such activities and reduce the occurrence of money laundering.
ZH: 要求DNFBP建立反洗钱/反恐怖融资框架并在客户隐私与报告要求间取得平衡。

[v7u_N001058|1058] This tailored regulatory approach enhances the financial system's integrity and protects it from exploitation by criminal actors.
ZH: 量身定制的监管方法增强金融体系完整性，防止被犯罪分子利用。
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N001056"
    ],
    "proposition": "工作组基于DNFBP的复杂性和风险，建议制定全面的反洗钱/反恐怖融资法规以弥补现有差距。",
    "source_quotes": [
      "Given the complexities and risks associated with DNFBPs, the task force recommended comprehensive AML/CFT regulations to bridge existing gaps."
    ],
    "relation_cues": [
      "Given",
      "recommended"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "DNFBP的复杂性和风险"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "工作组建议制定全面的反洗钱/反恐怖融资法规",
      "outcomes_or_paths": [
        "弥补现有差距"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001056",
        "quote": "Given the complexities and risks associated with DNFBPs, the task force recommended comprehensive AML/CFT regulations to bridge existing gaps."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N001057"
    ],
    "proposition": "要求DNFBP建立反洗钱/反恐怖融资框架并在客户隐私与报告要求间取得平衡，能够阻止相关活动的经济利益并减少洗钱发生。",
    "source_quotes": [
      "Requiring DNFBPs to set up an AML/CFT framework and find the right balance between customer privacy and AML reporting requirements could deter the financial benefits of enabling such activities and reduce the occurrence of money laundering."
    ],
    "relation_cues": [
      "Requiring",
      "could"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "要求DNFBP建立框架并平衡隐私与报告要求"
      ],
      "focal_handling_or_judgment": "要求DNFBP建立反洗钱/反恐怖融资框架并平衡隐私与报告要求",
      "outcomes_or_paths": [
        "阻止相关活动的经济利益",
        "减少洗钱发生"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001057",
        "quote": "Requiring DNFBPs to set up an AML/CFT framework and find the right balance between customer privacy and AML reporting requirements could deter the financial benefits of enabling such activities and reduce the occurrence of money laundering."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
