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

section_id: `CH16-S04`

section_title: `High-risk business sectors > Free-trade zones risks`

section_text_with_unit_anchors:

```text
[v7u_N001175|1175] A free-trade zone (FTZ) is a designated area within a country treated as outside its customs territory, allowing businesses to import, store, handle, manufacture, and distribute goods without incurring customs duties until those goods enter the domestic market.
ZH: 自由贸易区（FTZ）是境内关外的指定区域，货物入区免关税。

[v7u_N001176|1176] FTZs were originally set up to attract foreign direct investments and create jobs, and they are often located in developing countries.
ZH: 自由贸易区最初旨在吸引外资和创造就业，多位于发展中国家。

[v7u_N001177|1177] According to the think tank Global Financial Integrity, approximately 4,500 FTZs exist in more than 130 countries as of 2025.
ZH: 截至2025年，全球约130个国家拥有约4500个自由贸易区。

[v7u_N001178|1178] FTZs benefit companies by offering cost savings, enhancing cash flow, and boosting their competitiveness in international trade.
ZH: 自由贸易区为企业节省成本、改善现金流并提升国际竞争力。

[v7u_N001179|1179] FTZs can lower or remove taxes, customs duties, and business registration regulations.
ZH: 自由贸易区可降低或取消税收、关税及商业注册监管要求。

[v7u_N001180|1180] Many zones globally offer special exemptions from standard immigration procedures and foreign investment restrictions, among other benefits.
ZH: 许多自由贸易区提供标准移民程序和外资限制的特别豁免。

[v7u_N001181|1181] These zones aim to promote economic activity and employment that might otherwise take place elsewhere.
ZH: 自由贸易区旨在促进经济活动和就业

[v7u_N001182|1182] However, their business-friendly features attract criminals to exploit them.
ZH: 自由贸易区的商业友好特征吸引犯罪分子利用

[v7u_N001183|1183] The EU has commented that FTZs have a high incidence of corruption, tax evasion, and other criminal activities, such as fraud and sanctions evasion.
ZH: 欧盟指出自由贸易区腐败、逃税、欺诈和制裁规避高发

[v7u_N001184|1184] The European Commission has also pointed out that since FTZs are popular for storing artwork, antiquities, precious metals, and wine, and that they pose emerging threats to the integrity of the trade system.
ZH: 欧盟委员会指出自由贸易区对贸易体系构成新兴威胁

[v7u_N001185|1185] According to FATF, systemic weaknesses for FTZs include:
ZH: FATF指出的自由贸易区系统性弱点列表

[v7u_N001186|1186] Inadequate AML/CFT safeguards.
ZH: 自由贸易区反洗钱/反恐怖融资保障措施不足

[v7u_N001187|1187] Minimal oversight by local authorities.
ZH: 地方当局对自由贸易区监管极少

[v7u_N001188|1188] Weak procedures to inspect goods and legal entities, including inadequate recordkeeping and information technology systems.
ZH: 自由贸易区货物和法人检查程序薄弱，记录保存和IT系统不足

[v7u_N001189|1189] Lack of cooperation between FTZs and local customs authorities.
ZH: 自由贸易区与当地海关当局缺乏合作

[v7u_N001190|1190] FTZs might enable TBML by importing consignments with counterfeit or tampered paperwork and then re-exporting the goods to other countries while disguising their actual origin and nature.
ZH: 自由贸易区通过伪造文件进口再出口货物，便利贸易洗钱

[v7u_N001191|1191] This environment also provides a platform for illegal trades, such as drug trafficking, ivory trade, stolen artwork, and people smuggling.
ZH: 自由贸易区为毒品、象牙、艺术品走私和人口贩运提供平台

[v7u_N001192|1192] Additionally, FTZ regulations with inadequate enforcement might facilitate tax evasion and VAT fraud by allowing criminals to obscure the actual beneficial owners of assets derived from crimes.
ZH: 自由贸易区执法不力便利逃税和增值税欺诈

[v7u_N001193|1193] This can hinder authorities and law enforcement agencies from tracing and recovering proceeds of crime due to relaxed oversight.
ZH: 监管宽松阻碍当局追踪和追回犯罪所得
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N001190"
    ],
    "proposition": "自由贸易区可能通过伪造文件进口再出口货物来便利贸易洗钱。",
    "source_quotes": [
      "FTZs might enable TBML by importing consignments with counterfeit or tampered paperwork and then re-exporting the goods to other countries while disguising their actual origin and nature."
    ],
    "relation_cues": [
      "might",
      "by"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "importing consignments with counterfeit or tampered paperwork and then re-exporting the goods to other countries while disguising their actual origin and nature"
      ],
      "focal_handling_or_judgment": "FTZs might enable TBML",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001190",
        "quote": "FTZs might enable TBML by importing consignments with counterfeit or tampered paperwork and then re-exporting the goods to other countries while disguising their actual origin and nature."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N001192"
    ],
    "proposition": "自由贸易区执法不力可能便利逃税和增值税欺诈。",
    "source_quotes": [
      "Additionally, FTZ regulations with inadequate enforcement might facilitate tax evasion and VAT fraud by allowing criminals to obscure the actual beneficial owners of assets derived from crimes."
    ],
    "relation_cues": [
      "might",
      "by"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "FTZ regulations with inadequate enforcement"
      ],
      "basis_or_condition": [
        "allowing criminals to obscure the actual beneficial owners of assets derived from crimes"
      ],
      "focal_handling_or_judgment": "might facilitate tax evasion and VAT fraud",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001192",
        "quote": "Additionally, FTZ regulations with inadequate enforcement might facilitate tax evasion and VAT fraud by allowing criminals to obscure the actual beneficial owners of assets derived from crimes."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N001193"
    ],
    "proposition": "监管宽松阻碍当局追踪和追回犯罪所得。",
    "source_quotes": [
      "This can hinder authorities and law enforcement agencies from tracing and recovering proceeds of crime due to relaxed oversight."
    ],
    "relation_cues": [
      "can",
      "due to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "relaxed oversight"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "hinder authorities and law enforcement agencies from tracing and recovering proceeds of crime",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001193",
        "quote": "This can hinder authorities and law enforcement agencies from tracing and recovering proceeds of crime due to relaxed oversight."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
