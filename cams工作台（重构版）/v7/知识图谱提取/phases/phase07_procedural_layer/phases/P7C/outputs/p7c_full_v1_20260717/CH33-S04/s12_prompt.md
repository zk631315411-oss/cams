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

section_id: `CH33-S04`

section_title: `Introduction > AFC program components`

section_text_with_unit_anchors:

```text
[v7u_N002375|2375] An AFC program systematically identifies, assesses, measures, manages, monitors, and mitigates risks that could impact an organization's objectives. This program is critical in maintaining stability, compliance, and operational effectiveness. Large organizations, such as financial institutions, manage several risks, such as:
ZH: 金融犯罪防控项目系统识别、评估、管理风险，大型机构面临多种风险类型

[v7u_N002376|2376] Operational risk arises from inadequate internal processes, people, systems, or external events. A subset of this is model risk, caused by decision-making errors due to inadequate model validation.
ZH: 操作风险源于内部流程、人员、系统或外部事件，模型风险是其子集

[v7u_N002377|2377] Credit risk arises from potential losses from borrower default.
ZH: 信用风险源于借款人违约导致的潜在损失

[v7u_N002378|2378] Market risk is caused by market fluctuations that affect investments.
ZH: 市场风险由影响投资的市场波动引起

[v7u_N002379|2379] Legal and compliance risk arises when there is a failure to comply with laws and regulations, leading to legal action or penalties.
ZH: 法律合规风险源于未遵守法律法规导致诉讼或处罚

[v7u_N002380|2380] Treasury and capital risk involves risks in managing an organization's cash, investments, and funding. Liquidity risk refers to the organization’s ability to meet financial obligations.
ZH: 财资与资本风险涉及现金、投资和资金管理，流动性风险指偿债能力

[v7u_N002381|2381] Reputational risk results from negative publicity or public perception.
ZH: 声誉风险源于负面宣传或公众看法。

[v7u_N002382|2382] Conduct risk arises when the actions of an organization or personnel harm consumers, stakeholders, or communities.
ZH: 行为风险产生于组织或人员行为损害消费者、利益相关者或社区时。

[v7u_N002383|2383] Financial crime includes money laundering, terrorist financing, sanctions violations, proceeds from fraud, tax evasion, and other predicate crimes.
ZH: 金融犯罪包括洗钱、恐怖融资、制裁违规、欺诈收益、逃税及其他上游犯罪。

[v7u_N002384|2384] Financial crime risk spans multiple categories.
ZH: 金融犯罪风险涵盖多个类别。

[v7u_N002385|2385] For example, when financial crime controls fail, the organization might face legal and compliance issues, reputational damage, poor conduct, and operational risk.
ZH: 金融犯罪控制失效时，组织可能面临法律合规问题、声誉损害、行为风险和操作风险。

[v7u_N002386|2386] Key elements of the AFC program include the risk appetite statement, risk tolerance, policies and procedures, controls, and independent testing.
ZH: 金融犯罪防控项目的关键要素包括风险偏好声明、风险容忍度、政策与程序、控制措施及独立测试。

[v7u_N002387|2387] The risk appetite statement defines the risk level the organization is willing to operate within to achieve its objectives.
ZH: 风险偏好声明定义了组织为实现目标愿意承担的风险水平。

[v7u_N002388|2388] It guides behaviors, decision-making, and risk management practices.
ZH: 风险偏好声明指导行为、决策和风险管理实践。

[v7u_N002389|2389] The board approves the risk appetite statement in alignment with the strategic business objectives.
ZH: 董事会批准与战略业务目标一致的风险偏好声明。

[v7u_N002390|2390] Risk tolerance specifies the risk levels within the overall risk appetite. It represents the quantitative and qualitative limits for specific risk categories, establishing boundaries for business activities, including financial crime risk.
ZH: 风险容忍度规定了整体风险偏好内的风险水平，为特定风险类别设定定量和定性界限。

[v7u_N002391|2391] Policies and procedures are guidelines on managing risks.
ZH: 政策与程序是管理风险的指南。

[v7u_N002392|2392] Policies interpret laws and regulations, and provide the framework while procedures are the step-by-step instructions on how to implement the policies.
ZH: 政策解释法律法规并提供框架，程序是实施政策的逐步说明。

[v7u_N002393|2393] Controls are the actions to mitigate risks and ensure adherence to policies and procedures.
ZH: 控制措施是为降低风险并确保遵守政策和程序而采取的行动。

[v7u_N002394|2394] Effective internal controls help detect and prevent financial crime activities.
ZH: 有效的内部控制有助于检测和预防金融犯罪活动。

[v7u_N002395|2395] Independent testing involves an internal audit function or a specialist third party that assesses the effectiveness of the AFC program and ensures that the policies and procedures are followed.
ZH: 独立测试由内部审计或第三方专家评估金融犯罪防控项目的有效性及政策程序的遵循情况。
```

## S1.1 候选列表

```json
[]
```
