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

section_id: `CH24-S07`

section_title: `US AML/CFT regulatory landscape > History of AML regime in Europe`

section_text_with_unit_anchors:

```text
[v7u_N001781|1781] The EU is a political and economic union of jurisdictions.
ZH: 欧盟是一个由多个司法管辖区组成的政治经济联盟。

[v7u_N001782|1782] Note that Norway, Iceland, and Liechtenstein are not part of the EU but are members of the European Economic Area (EEA).
ZH: 挪威、冰岛和列支敦士登不是欧盟成员，但属于欧洲经济区。

[v7u_N001783|1783] Although members of the EEA do not take part in the EU’s legislative process, they are required to comply with the EU’s AML/CFT legislation, which can be issued as a regulation or a directive.
ZH: 欧洲经济区成员必须遵守欧盟反洗钱/反恐怖融资法规。

[v7u_N001784|1784] A regulation is a legal act that is immediately applicable in each member state.
ZH: 法规是一种在成员国直接适用的法律行为。

[v7u_N001785|1785] A directive is a legal act that sets principles and goals.
ZH: 指令是一种设定原则和目标的立法行为。

[v7u_N001786|1786] National legislators must transpose, or incorporate into their legislation, EU directives by a certain deadline to make them binding.
ZH: 国家立法者必须在截止日期前将欧盟指令转化为国内法。

[v7u_N001787|1787] Since 1991, the EU has used directives to establish its AML/CFT regime.
ZH: 自1991年起，欧盟通过指令建立反洗钱/反恐怖融资制度。

[v7u_N001788|1788] The first AML directive (1AMLD) primarily applied to banks and required member states to criminalize money laundering.
ZH: 第一项反洗钱指令主要适用于银行，并要求成员国将洗钱定为刑事犯罪。

[v7u_N001789|1789] Since then, the EU has amended the AMLDs, with the 2AMLD in 2001, 3AMLD in 2005, 4AMLD in 2015, and 5AMLD in 2018.
ZH: 欧盟后续修订了反洗钱指令，包括2001年、2005年、2015年和2018年的版本。

[v7u_N001790|1790] Many of the EU’s provisions to the AMLDs were to address previous challenges.
ZH: 欧盟反洗钱指令的许多条款旨在解决先前挑战。

[v7u_N001791|1791] For example, some member states did not transpose the AMLDs in their national legislation in a timely manner or in full compliance.
ZH: 一些成员国未能及时或完全将反洗钱指令转化为国内法。

[v7u_N001792|1792] These factors resulted in lapses, such as banks failing to comply with core requirements and deficiencies in consolidated supervision for cross-border entities.
ZH: 转化不力导致银行未能遵守核心要求以及跨境实体合并监管缺陷。

[v7u_N001793|1793] This fragmentation between entities reduced the effectiveness of supervision and cooperation among authorities and resulted in AML breaches.
ZH: 实体间的碎片化降低了监管和合作的有效性，导致反洗钱违规。

[v7u_N001794|1794] Therefore, the EU passed the 5AMLD to strengthen the obligation for cooperation between AML and banking supervisors. The AMLD amendments also aimed to strengthen existing regulations and expand regulatory scope to include entities such as NBFIs, DNFBPs, and cryptoasset service providers.
ZH: 欧盟通过第五项反洗钱指令加强反洗钱与银行监管合作，并扩大监管范围至非银行金融机构、指定非金融行业和加密资产服务商。

[v7u_N001795|1795] Until 2018, member states differed on the predicate offenses for money laundering.
ZH: 2018年前，成员国对洗钱上游犯罪的定义存在差异。

[v7u_N001796|1796] This led the EU to pass Directive 2018/1673, or the “AML Criminal Law Directive,” which establishes minimum rules concerning the definition of criminal offenses and penalties for money laundering.
ZH: 欧盟通过2018/1673号指令（反洗钱刑法指令）统一洗钱犯罪定义和处罚最低标准。

[v7u_N001797|1797] In 2024, the EU amended Directive 2018/1673 to ensure that violations of EU restrictive measures constitute a criminal offense.
ZH: 2024年，欧盟修订2018/1673号指令，将违反限制性措施定为刑事犯罪。

[v7u_N001798|1798] The EU also introduced the EU AML Single Rulebook, also known as the EU AML package, which includes the 6AMLD.
ZH: 欧盟推出反洗钱单一规则手册（含第六项反洗钱指令）。

[v7u_N001799|1799] For the first time, this framework combined a regulation with a directive to increase its level of harmonization and effectiveness within member states.
ZH: 该框架首次结合法规与指令，提高成员国间的协调性和有效性。
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N001783"
    ],
    "proposition": "欧洲经济区成员虽不参与欧盟立法，但必须遵守欧盟反洗钱/反恐怖融资法规。",
    "source_quotes": [
      "Although members of the EEA do not take part in the EU’s legislative process, they are required to comply with the EU’s AML/CFT legislation, which can be issued as a regulation or a directive."
    ],
    "relation_cues": [
      "although",
      "required to comply"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "欧洲经济区成员不参与欧盟立法过程"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "必须遵守欧盟 AML/CFT 法规",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001783",
        "quote": "Although members of the EEA do not take part in the EU’s legislative process, they are required to comply with the EU’s AML/CFT legislation, which can be issued as a regulation or a directive."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N001786"
    ],
    "proposition": "国家立法者必须在截止日期前将欧盟指令转化为国内法，使其具有约束力。",
    "source_quotes": [
      "National legislators must transpose, or incorporate into their legislation, EU directives by a certain deadline to make them binding."
    ],
    "relation_cues": [
      "must",
      "by a certain deadline"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "欧盟指令需要转化为国内法"
      ],
      "basis_or_condition": [
        "在截止日期前"
      ],
      "focal_handling_or_judgment": "国家立法者将指令转化为国内法",
      "outcomes_or_paths": [
        "使指令具有约束力"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001786",
        "quote": "National legislators must transpose, or incorporate into their legislation, EU directives by a certain deadline to make them binding."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N001788"
    ],
    "proposition": "第一项反洗钱指令主要适用于银行，并要求成员国将洗钱定为刑事犯罪。",
    "source_quotes": [
      "The first AML directive (1AMLD) primarily applied to banks and required member states to criminalize money laundering."
    ],
    "relation_cues": [
      "applied to",
      "required"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "欧盟通过第一项反洗钱指令"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "指令主要适用于银行并要求成员国将洗钱定为刑事犯罪",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001788",
        "quote": "The first AML directive (1AMLD) primarily applied to banks and required member states to criminalize money laundering."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
