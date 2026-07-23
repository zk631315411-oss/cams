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

section_id: `CH16-S07`

section_title: `High-risk business sectors > Military organization and goods risks`

section_text_with_unit_anchors:

```text
[v7u_N001226|1226] Military organizations as parties to a transaction and military goods and services pose specific financial crime risks to organizations.
ZH: 军事组织交易和军事商品服务带来特定金融犯罪风险

[v7u_N001227|1227] Military organizations include:
ZH: 军事组织包括以下类型

[v7u_N001228|1228] Armed forces
ZH: 军事组织包括武装部队

[v7u_N001229|1229] Government-owned or -controlled:
ZH: 政府所有或控制的军事组织

[v7u_N001230|1230] Military research facilities
ZH: 军事研究设施属于高风险实体

[v7u_N001231|1231] Defense manufacturers
ZH: 国防制造商属于高风险实体

[v7u_N001232|1232] Private-sector defense suppliers
ZH: 私营部门国防供应商属于高风险实体

[v7u_N001233|1233] Military goods and services are articles, services, and technology that jurisdictions use for national defense.
ZH: 军事商品和服务是用于国防的物品、服务和技术

[v7u_N001234|1234] Because of their potential threat to international security and human rights, these items, along with dual-use goods, are routinely subject to embargoes and export controls.
ZH: 军事和两用商品因安全和人权威胁常受禁运和出口管制

[v7u_N001235|1235] Dual-use goods are those with both military and civilian uses.
ZH: 两用商品是兼具军事和民用用途的物品

[v7u_N001236|1236] Military goods and services include:
ZH: 军事商品和服务包括以下类别

[v7u_N001237|1237] Firearms and ammunition
ZH: 军事商品包括枪支弹药

[v7u_N001238|1238] Missiles
ZH: 导弹属于军事商品

[v7u_N001239|1239] Tanks
ZH: 坦克属于军事商品

[v7u_N001240|1240] Aircraft
ZH: 飞机属于军事商品

[v7u_N001241|1241] Biological and chemical agents
ZH: 生物和化学制剂属于高风险商品

[v7u_N001242|1242] Nuclear weapons
ZH: 核武器属于高风险商品

[v7u_N001243|1243] Defense services, data, and technology
ZH: 国防服务、数据和技术属于高风险商品

[v7u_N001244|1244] Military-related financial crime risks include bribery and corruption, arms embargo and export control evasion, and financing of terrorism and weapons of mass destruction (WMD).
ZH: 军事相关金融犯罪风险包括贿赂腐败、武器禁运与出口管制规避、恐怖融资及大规模杀伤性武器扩散融资

[v7u_N001245|1245] Governments own or control many military organizations. Government officials, who are politically exposed persons (PEP) by definition, often oversee or manage these organizations. Therefore, military organizations pose a higher risk for bribery and corruption.
ZH: 军事组织因政府控制和政治敏感人物参与而具有更高的贿赂与腐败风险

[v7u_N001246|1246] An arms embargo is a type of international sanction that bans a targeted jurisdiction from importing or exporting military or dual-use goods and services.
ZH: 武器禁运是一种禁止目标管辖区进出口军事或军民两用物品的国际制裁

[v7u_N001247|1247] Export controls are laws and guidelines that regulate the trade of critical items for reasons of foreign policy and international security. They apply to specific items, including military goods and services, and require exporters to obtain a license to sell these items.
ZH: 出口管制是出于外交政策和国际安全原因管制关键物品贸易的法律和指南

[v7u_N001248|1248] Evading arms embargoes and export controls can be profitable to individuals and favorable to the national interests of sanctioned jurisdictions. Therefore, military goods and services pose high risk for evasion of these controls.
ZH: 军事物品和服务因利润丰厚及受制裁管辖区国家利益而面临较高的规避武器禁运和出口管制风险

[v7u_N001249|1249] Trade involving military goods and services also poses the risk of supplying terrorist organizations with weapons and state-based actors with materials that promote the development and proliferation of WMDs.
ZH: 军事物品贸易存在向恐怖组织提供武器及向国家行为体提供大规模杀伤性武器扩散材料的风险
```

## S1.1 候选列表

```json
[]
```
