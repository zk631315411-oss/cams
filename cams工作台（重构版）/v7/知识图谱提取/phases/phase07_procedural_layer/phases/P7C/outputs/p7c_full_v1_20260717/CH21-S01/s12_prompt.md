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

section_id: `CH21-S01`

section_title: `AFC guidance from other organizations > G-20 Anti-Corruption Working Group AFC guidance`

section_text_with_unit_anchors:

```text
[v7u_N001587|1587] The G-20 was founded in 1999 as an informal forum for finance ministers and central bank governors of the most industrialized and developing economies.
ZH: G20成立于1999年，最初为财长和央行行长论坛

[v7u_N001588|1588] The G-20’s membership includes 19 countries, plus the EU and the African Union.
ZH: G20成员包括19个国家、欧盟和非洲联盟

[v7u_N001589|1589] Its original focus was economic and financial stability-related issues, but it has since expanded to include other issues, such as anti-corruption.
ZH: G20最初关注经济金融稳定，后扩展至反腐败等领域

[v7u_N001590|1590] After the 2007 global financial crisis, G-20 participation was upgraded to include heads of state or government, and leaders now meet regularly.
ZH: 2007年金融危机后G20升级为国家元首级定期会议

[v7u_N001591|1591] The G-20 Anti-Corruption Working Group (ACWG) was set up in 2010. Its primary goal is to recommend ways the G-20 can contribute to international anti-corruption efforts.
ZH: G20反腐败工作组（ACWG）成立于2010年，旨在推动国际反腐败

[v7u_N001592|1592] ACWG actively works with the World Bank, the OECD, UNODC, IMF, and FATF.
ZH: ACWG与世界银行、OECD、UNODC、IMF和FATF合作

[v7u_N001593|1593] The World Bank and UNODC are also involved in the ACWG through the Stolen Assets Recovery Initiative (StAR). StAR plays an advisory role on asset recovery, AML/CFT, transparency and beneficial ownership, and income and asset disclosures.
ZH: 世界银行和UNODC通过追回被盗资产倡议（StAR）参与ACWG

[v7u_N001594|1594] As of 2025, the G-20 ACWG Action Plan was focused on:
ZH: 截至2025年G20 ACWG行动计划重点领域列表

[v7u_N001595|1595] Strengthening the public sector by promoting transparency, integrity, and accountability.
ZH: 加强公共部门透明度、诚信和问责制

[v7u_N001596|1596] Increasing efficiency of asset recovery measures.
ZH: 提高资产追回措施的效率

[v7u_N001597|1597] Enhancing and mobilizing the inclusive participation of the public sector, private sector, civil society, and academia to prevent and combat corruption.
ZH: 动员公共、私营、民间社会和学术界参与预防和打击腐败

[v7u_N001598|1598] Enhancing whistle-blower protection mechanisms.
ZH: 加强举报人保护机制

[v7u_N001599|1599] cooperation. They outline strategies for combating illicit financial activities, recovering stolen assets, and enhancing regulatory frameworks across jurisdictions to strengthen governance and promote integrity in both public and private sectors. These include:
ZH: 合作策略包括打击非法金融活动、追回被盗资产和加强监管框架

[v7u_N001600|1600] Country-specific beneficial ownership guides.
ZH: 国别受益所有人指南

[v7u_N001601|1601] International cooperation.
ZH: G20反腐败工作组倡导金融犯罪防控领域的国际合作。

[v7u_N001602|1602] Recovery of the proceeds of corruption.
ZH: G20反腐败工作组关注腐败所得追回。

[v7u_N001603|1603] Combating money laundering.
ZH: G20反腐败工作组指导打击洗钱活动。

[v7u_N001604|1604] Enhancing asset disclosure.
ZH: G20反腐败工作组建议加强资产披露。

[v7u_N001605|1605] Tackling foreign bribery.
ZH: G20反腐败工作组要求打击海外贿赂。

[v7u_N001606|1606] Prevention of corruption in the public sector.
ZH: G20反腐败工作组建议预防公共部门腐败

[v7u_N001607|1607] Strengthening anti-corruption.
ZH: G20反腐败工作组建议加强反腐败工作

[v7u_N001608|1608] Promoting business/government collaboration.
ZH: G20反腐败工作组促进企业与政府合作
```

## S1.1 候选列表

```json
[]
```
