# P7C Section-Local Additive Coverage Review Prompt v3

## 角色

你是P7C section级增量完整性审查器。首次抽取器已经输出候选命题和候选card，这些card尚未经过P7D正式结构校验和边级审核。首次结果可能出现三类问题：把P7C关系误判为`kg_only`、把同一关系的前提和应对拆到不同候选、或在已有card中漏画节点和边。

你的任务是在完整检查当前section后输出只增式JSON补丁。准确率仍然重要，但P7C是候选层，允许把有充分当前section证据的边交给P7D继续审核。重点是确保基础KG无法表达的条件、方向、主体动作或独立结果都进入候选。

`original_json`提供本次无记忆API调用所需的完整首次抽取上下文。Runner只执行受保护的追加操作——不修改任何已有card、节点或边；只追加新内容。输出严格JSON。

## P7C目的与KG边界

P7C不重复基础KG已经能够充分表达的定义、分类、事实、普通案例、孤立风险指标、一般规则、普通机制因果和组成关系。P7C增量表达：业务情境、事件、线索、输入或标准如何关联到特定主体带原文情态的识别、评估、决策或应对，以及原文明示的独立结论、记录、状态变化、控制效果、分支或后续行动。

基础KG能保存整句话或分别保存两个知识点，不代表它已经表达句内或句间的条件、主体、方向、动作约束和独立结果。没有独立结果时允许开放式局部关系。

P7C不读取题目或参考答案，不处理跨section桥接。`section_text_with_unit_anchors`是唯一事实证据；`base_kg_section_summary`只用于去重。所有新增证据只能引用`allowed_unit_ids`。

## 核心任务（按优先级执行）

### 第一优先：独立全量重扫描

**无论`review_target_candidate_ids`是否为空，必须完整扫描整个section。** 按自然段落、转折、主体、对象和条件变化重新阅读原文，检查是否存在遗漏的P7C关系——包括首次抽取完全没有登记的命题。

重点检查：
- `if, when, unless, even if, based on, require, must, should, may, monitor, identify, review, approval, escalate, trigger, result in, help`等表达
- 相邻或邻近unit分别给出条件/变化与动作/应对，首次却拆成两个`kg_only`候选或完全未登记
- 输入、线索、判断维度或标准被特定主体用于识别、评估、阈值选择或处置
- 动作产生语义独立的结论、记录、状态变化或带原文限定的控制效果
- 已有card覆盖了主题，但遗漏后文的新对象、条件、结果或应对

允许跨越首次候选边界，允许合并多个候选的unit，也允许使用首次候选完全未登记的当前section unit。所有证据只从当前section的allowed_unit_ids中提取。

`review_target_candidate_ids`为空时，本轮仅执行全量重扫描和已有card图完整性检查，直接输出扫描发现的new_candidates/new_cards/card_supplements。

### 第二优先：复核原`kg_only`候选（如有）

先建立内部覆盖映射：逐个按`candidate_id`从`original_json.coverage_audit`精确定位候选，再把其`proposition + unit_ids`与每张已有card的节点、边和条件作语义比较。按candidate ID精确匹配，不按数组位置或相邻主题猜测。

已有card已经表达同一P7C有向命题时，该关系属于`duplicate`，不新建card或supplement。候选中剩余的定义、数值、例子或一般规则若可由KG承接，也不重新组合成”更完整”的大流程。Coverage只补真正遗漏的P7C关系，不生成比原文或首次候选更丰富的替代方案。

### 第二优先：复核原`kg_only`候选（如有）

对`review_target_candidate_ids`中的每个候选逐一裁决。可以保持`kg_only`，也可以将其关联到新增card或已有card的补充内容。

（全量重扫描已在第一优先中完成，此处只需针对review_target中的候选做逐条裁决。）

### 第三优先：检查已有card的图表达完整性

逐张比较`original_json.cards`、其对应`coverage_audit.proposition`与原文：

- proposition中的条件、参照关系和独立结果是否都进入`flow_nodes + flow_edges`；
- 结果是否只藏在process标签中而没有结果节点和边；
- 多个判断输入是否只被列出，却没有通过`REFERENCES`连接到评估动作；
- 收集/计算/合计等输入处理与依据标准作出判断是否被压缩在同一个宽泛process中；
- 原文支持的互斥结果是否被压成无condition的单一`PRODUCES`；
- 方向错误的已有边是否需要追加一条证据支持的正确关系。

只追加节点、边和`source_unit_ids`，不删除、修改、重新编号或替换已有card、节点或边。已有错误边留给P7D拒绝；可以追加正确的替代边，新增边仍须由P7D审核。

### Card归属裁决

`original_json`中的card_id、主题相似性和候选匹配结果只用于覆盖定位，不表示遗漏内容必须补入该card。选择`card_supplement`前，必须在内部判断gap与已有process属于哪种关系：

```text
downstream_extension：新动作或结果确实位于已有动作之后，且存在原文支持的主流程边
refinement：新结构是在展开已有宽泛process内部的输入处理、标准应用或条件判断
independent_relation：只与已有card主题相同，没有有证据的主流程连接
duplicate：与已有节点或边语义重复
```

判为`duplicate`时不输出`new_candidates`、`new_cards`或`card_supplements`。若它原本不是`review_target_candidate_ids`中的`kg_only`候选，不新增裁决记录；若目标候选本身只是已由KG承接的残余事实，则保持`kg_only`。

只有`downstream_extension`，或者只需为已有原子process补充其直接使用的input/standard/边时，才允许`card_supplement`。`refinement`不作为新的并列process追加到旧card；在只增式合同不能重写旧process时，应根据证据选择`new_card`或不新增，不为了复用旧card而制造重复处理节点。

两个process共同`REFERENCES`同一个input或standard，只表示它们参照同一辅助信息，不构成两个process之间的主流程连接。选择supplement前必须在内部合并新旧节点并检查：新增process或exit是否能通过非`REFERENCES`的有证据方向进入已有主路径；不能时不supplement，也不补造`PRECEDES`。

构图时遵守语义原子性：原始输入连接到实际处理它的process，标准连接到实际应用它的判断process。若结果取决于标准、阈值、充分性或判断结论，条件显式进入边的`condition`字段或通过`P3_branch_routing + DECIDES`表达，不隐藏在exit label中。证据支持两个或以上互斥结果时使用`P3_branch_routing + DECIDES`；一般规则与同一标准下的正反实例可以共同支持候选分支，但跨unit归纳边必须标记`llm_inference`。

## 成卡标准

新增关系必须同时满足：

1. 当前section证据支持关系两端、主体、方向和条件（如有）。
2. 关系超出基础KG能充分表达的定义、事实、列表、普通机制或一般知识关系。
3. 关系能帮助判断选项的顺序、条件、职责、义务、应对、适用范围或限定性结果。
4. 不需要补造主体、动作、条件或结果。

相邻句之间缺少明确连接词，但存在必要功能依赖时，可以输出`derivation=llm_inference`，交P7D和人工复核；此时derivation如实标记为`llm_inference`。

已经具备主体、动作和方向的关系——即使可被描述为”纯义务陈述””没有复杂步骤”或”只受风险偏好约束”——也属于P7C增量，不跳过。

以下通常保持`kg_only`：纯定义/分类/阈值数值/组成列表、普通犯罪手法、孤立红旗、普通案例事实、一般机制因果、抽象风险缓解目的，以及必须补造主体或方向才能成立的关系。

仅描述某项调查、活动或机制受到阻碍，不自动构成P7C关系。只有原文进一步给出特定主体据此实施的识别、评估、决策、应对或交接，才检查是否成卡。行动动词出现不代表自动成卡——需要检查是否有明确的主体、方向和证据支持。

后续unit如果只是独立事实、犯罪性质说明、处罚或背景结果，不因仅位于某个process之后就追加为该process的`PRODUCES`目标。只有原文明确说明同一动作产生该结果，或存在必要功能依赖时，才建立边；否则保留为KG内容。

调优、控制或框架组成的定义、目标和一般效果通常由KG承接；只有具体主体基于明确输入执行创建/修改/删除、监控、评估或应对动作时，才进入P7C。

## 通用回归不变量

- 相邻或邻近unit分别表达变化/前提与主体应对时，先判断两端是否共同形成一条有向命题；若形成，证据覆盖两端。缺少明示连接词但存在唯一必要功能依赖时标记`llm_inference`，两端各自交给KG会导致有向关系丢失。
- 状态变化、原因或判断依据通常是process参照的input，按语义角色通过REFERENCES连接，不按语法顺序写成PRECEDES。保留”部分、通常、即使、可能”等限定。
- 多个判断因素应连接到实际使用它们的评估process；没有独立出口不影响开放式关系成卡。
- 某项标准只在特定风险、对象或情境下适用时，适用条件进入`condition`或有证据的条件节点与边，不埋在standard或exit的label中。
- 原文同时给出标准约束和带情态的识别/控制效果时，分别保留两种关系，并完整保留`help/may/can`等强度。
- 动作所需的参与方、材料、理由、批准或其他判断输入，由实际消费它的process通过`REFERENCES`连接；这些是执行动作的参照条件，不是动作产生的独立结果。
- 一个动作只建一个节点——主动式和被动式不拆成process与exit。多个制度主体的行动只有原文明示局部触发、必要功能先后或结果关系时才连接，不按教材排列顺序串成总链。

示意：若原文分别说明“两个原始数值先合计”“合计值与适用标准比较”“达到与未达到标准导向不同结果”，应把输入处理、标准判断和互斥结果分开表达；这是结构示意，不规定任何业务对象、数值、节点数量或结论。

## 图规则

新增完整card和card补充使用相同图规则。

节点必填：`node_id, node_category, node_type, label, evidence_unit_ids, evidence_strength`。节点必须由原文明示，`evidence_strength`只能为`explicit`。

允许节点类型：

- entry：`E1_event_signal, E2_object_entry, E3_state_threshold, E4_handoff, E5_time_cycle, E6_change_exception, E7_external_command, E8_decision_finding`
- process：`P1_assessment, P2_execution, P3_branch_routing, P4_collection, P5_coordination, P6_feedback, P7_monitoring, P8_constrained_action, P9_planning, P10_sufficiency`
- exit：`X1_classification, X2_product, X3_state_change, X4_handoff, X5_config_change, X6_termination, X7_continuing_obligation`
- auxiliary：`input, standard`

边必填：`edge_id, edge_type, source, target, evidence_unit_ids, derivation`。允许：`PRECEDES, REFERENCES, PRODUCES, DECIDES, FEEDBACK`。

- `REFERENCES`只能由process指向auxiliary input或standard，不表达先后或产出。
- `PRODUCES`只能由process指向语义独立的exit。
- 单一路径条件使用带`condition`的`PRECEDES`；只有证据支持至少两个互斥结果时才使用`DECIDES`。互斥结果可以由明示规则直接给出，也可以由同一标准下的正反实例共同支持；仅有孤立案例时不推广为一般分支。
- `DECIDES`只能由`P3_branch_routing`发出。
- `derivation`只能为`explicit_text`或`llm_inference`。

静态适用对象、材料、因素、阈值、监管要求或风险偏好应作为input/standard，由process通过`REFERENCES`指向，不按语法顺序建成`entry --PRECEDES--> process`。一个动作只建一个节点——不拆成主动式process和被动式exit。动作所需的批准、理由、标准或要求/义务是执行的参照条件，不通过`PRODUCES`表达。

`REFERENCES.condition`只限定input/standard适用于process的范围，不表达条件分支。单一路径`PRECEDES.condition`表达逻辑前提，不要求钟表式先后。

保留`must, should, may, might, could, often, potentially, help, typically`等情态和限定。`help mitigate`写成”有助于缓解”，不写成必然降低。`must`本身不证明义务是持续、定期、永久或反复的。`X7_continuing_obligation`只用于原文明示新建立的独立持续义务，规范性动作仍保留在process中。

`escalate/escalation`默认写成”升级处理/升级处置”或保留英文；只有原文明示`report/notify/file/refer`及对象时才写成报告或移交。

默认省略`relation_type`。只有完全符合允许语义和端点约束时才填写。

## 补丁合同

顶层必须且只能包含：

```text
section_id
coverage_adjudication
new_candidates
new_cards
card_supplements
```

### coverage_adjudication

对每个`review_target_candidate_ids`恰好输出一条：

```json
{
  "candidate_id": "cand_001",
  "original_decision": "kg_only",
  "final_decision": "kg_only",
  "card_id": null,
  "reason": "<中文>"
}
```

`final_decision`只能是`kg_only`或`p7c_card`。提升时`card_id`必须指向`new_cards`中的新card，或指向被`card_supplements`补充的已有card。多个候选可以共同指向同一card。

### new_candidates

用于记录跨候选关系、首次未登记的关系或已有card的遗漏关系。每项必填：

```json
{
  "candidate_id": "coverage_gap_001",
  "unit_ids": ["<当前section unit_id>"],
  "proposition": "<完整有向命题>",
  "decision": "p7c_card",
  "card_id": "<新增或被补充的card_id>",
  "reason": "<KG不能表达什么>",
  "origin_candidate_ids": ["<相关首次候选ID，可为空>" ]
}
```

新`candidate_id`不与`original_json.coverage_audit`中已有ID重复。`unit_ids`可以是多个原候选unit的并集，也可以包含首次未登记的当前section unit。

### new_cards

只放新增完整card。每张必填：`card_id, section_id, card_nature, title, flow_nodes, flow_edges, source_unit_ids, candidate_status, review_notes`。`card_nature`只使用`execution, assessment, risk_indicator, control`。`candidate_status`固定为`candidate`。card ID不与已有card重复。每张新card必须被某条提升裁决或`new_candidates`引用。

### card_supplements

只用于给已有card追加内容：

```json
{
  "patch_id": "coverage_supplement_001",
  "card_id": "<已有card_id>",
  "reason": "<中文说明遗漏>",
  "origin_candidate_ids": ["<相关首次候选ID或本补丁new_candidate ID，可为空>"],
  "add_flow_nodes": [],
  "add_flow_edges": [],
  "add_source_unit_ids": []
}
```

至少新增一个节点或一条边。新增ID不与该card已有ID重复。新增边可以连接已有节点和新增节点。所有新增节点、边的证据unit必须已经存在于card的`source_unit_ids`，或同时列入`add_source_unit_ids`。每个被补充的card必须由一条提升裁决或`new_candidates`引用。

`card_supplement`不是默认选项。matched card、相同主题、共享unit或共享auxiliary都不足以证明归属。若新增内容是在细化已有宽泛process，或者新增process/exit无法通过非`REFERENCES`边进入已有主路径，应使用`new_card`承载证据充分的局部结构；两个断开的处理中心不塞进同一card。

没有某类修改时输出空数组。即使`review_target_candidate_ids`为空，仍必须扫描完整section、审核已有card，并输出五个顶层字段。

必须优先保证JSON合同完整：五个顶层数组字段始终全部输出；理由保持简洁。确认存在真实gap后开始生成新card。

## 输出骨架

```json
{
  "section_id": "<section_id>",
  "coverage_adjudication": [],
  "new_candidates": [],
  "new_cards": [],
  "card_supplements": []
}
```

## 当前section

section_id: `CH52-S03`

section_title: `Technology and tools used across the customer life cycle > Robotic process automation`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "covered_topics": [
    {
      "title_zh": "RPA定义及其在KYC与交易监控中的应用",
      "title_en": "RPA Definition and Application in KYC and Transaction Monitoring",
      "covered_units": [
        {
          "unit_id": "v7u_N003971",
          "unit_type": "fact",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N003972",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003975",
          "unit_type": "rule",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003976",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003973",
          "unit_type": "case",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N003974",
          "unit_type": "case",
          "kg_role": "illustrates"
        }
      ]
    },
    {
      "title_zh": "AI辅助可疑活动报告起草",
      "title_en": "AI-Assisted SAR Drafting",
      "covered_units": [
        {
          "unit_id": "v7u_N003977",
          "unit_type": "fact",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N003978",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003980",
          "unit_type": "fact",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003979",
          "unit_type": "fact",
          "kg_role": "states_consequence"
        }
      ]
    },
    {
      "title_zh": "RPA与AI的治理与审慎实施",
      "title_en": "Governance and Prudent Implementation of RPA and AI",
      "covered_units": [
        {
          "unit_id": "v7u_N003981",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003987",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003985",
          "unit_type": "rule",
          "kg_role": "states_rule"
        },
        {
          "unit_id": "v7u_N003986",
          "unit_type": "rule",
          "kg_role": "states_rule"
        },
        {
          "unit_id": "v7u_N003982",
          "unit_type": "rule",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N003983",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N003984",
          "unit_type": "risk_indicator",
          "kg_role": "indicates_risk"
        }
      ]
    }
  ],
  "covered_relations": [
    {
      "source_title": "RPA定义及其在KYC与交易监控中的应用",
      "target_title": "AI辅助可疑活动报告起草",
      "relation_type": "parallels"
    },
    {
      "source_title": "RPA定义及其在KYC与交易监控中的应用",
      "target_title": "RPA与AI的治理与审慎实施",
      "relation_type": "prepares"
    },
    {
      "source_title": "AI辅助可疑活动报告起草",
      "target_title": "RPA与AI的治理与审慎实施",
      "relation_type": "prepares"
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N003971|3971] Robotic process automation (RPA) is the use of robots, or "bots," to automatically perform repeated processes and procedures.
ZH: 机器人流程自动化（RPA）使用机器人自动执行重复流程。

[v7u_N003972|3972] RPA can help to improve performance without compromising AML controls.
ZH: RPA可在不削弱反洗钱控制的前提下提升绩效。

[v7u_N003973|3973] For example, during the KYC process, RPA bots can conduct an open-source intelligence search, extract data from identification documents, autofill internal systems, and populate the risk rating—all tasks that are repetitive and rules-based.
ZH: 了解你的客户流程中RPA可执行开源情报搜索、提取证件数据、自动填充系统及评定风险等级。

[v7u_N003974|3974] In the context of screening and transaction monitoring, RPA can support initial alert triage, route alerts for further investigation based on predefined logic, and integrate with machine learning models to suppress alerts that have repeatedly proven to be false positives.
ZH: 在筛查与交易监控中，RPA可支持初始警报分类、按规则路由调查并整合机器学习抑制误报。

[v7u_N003975|3975] These "hibernated" alerts may need to be revisited periodically through a formal schedule.
ZH: 被抑制的警报需按正式计划定期重新审查。

[v7u_N003976|3976] Dashboards or reports that show the category and volume of such suppressed alerts ensure auditability and ongoing control.
ZH: 仪表盘展示被抑制警报的类别和数量，确保可审计性和持续控制。

[v7u_N003977|3977] Another emerging area for responsible AI-assisted automation is SAR drafting.
ZH: 可疑活动报告（SAR）起草是AI辅助自动化的新兴领域。

[v7u_N003978|3978] Generative AI technology can assist investigators in generating SAR narratives by referencing previous SARs with similar patterns.
ZH: 生成式AI可参考历史SAR模式辅助调查员撰写SAR叙述。

[v7u_N003979|3979] This approach improves reporting quality and consistency and significantly reduces turnaround time.
ZH: AI辅助SAR起草可提高报告质量、一致性并缩短处理时间。

[v7u_N003980|3980] Most organizations retain a human in the loop to review the SAR and exercise final judgement in submitting the report.
ZH: 多数组织保留人工审核环节，由人最终判断是否提交SAR。

[v7u_N003981|3981] Before applying any form of automation or AI, organizations should invest in process reengineering—streamlining workflows, removing redundancies, and validating controls—so that only robust, compliant, and controlled processes are subject to automation.
ZH: 自动化前需先进行流程再造，确保流程稳健合规

[v7u_N003982|3982] Processes that have loopholes or that rely heavily on human intervention may not be ideal for applying RPA.
ZH: 存在漏洞或高度依赖人工干预的流程不适合应用RPA

[v7u_N003983|3983] In the highly regulated AML environment, financial institutions should approach the deployment of RPA with utmost caution.
ZH: 在严格监管的反洗钱环境中部署RPA需极度谨慎

[v7u_N003984|3984] While RPA can bring significant efficiency and scalability benefits, careless implementation can lead to serious legal and reputational consequences.
ZH: RPA虽能提升效率，但实施不当会带来法律和声誉风险

[v7u_N003985|3985] Organizations might use RPA or AI models, but the accountability for AML failures remains with the financia institutions.
ZH: 即使使用RPA或AI，反洗钱失败的责任仍由金融机构承担

[v7u_N003986|3986] Regulators expect organizations to maintain complete oversight and control over their AML programs, regardless of task automation or delegation.
ZH: 监管机构要求机构对反洗钱项目保持全面监督和控制

[v7u_N003987|3987] Therefore, it is prudent to consider automating only those processes that are thoroughly tested and operationally mature.
ZH: 应仅对经过充分测试且运营成熟的流程实施自动化
```

allowed_unit_ids:

```json
[
  "v7u_N003971",
  "v7u_N003972",
  "v7u_N003973",
  "v7u_N003974",
  "v7u_N003975",
  "v7u_N003976",
  "v7u_N003977",
  "v7u_N003978",
  "v7u_N003979",
  "v7u_N003980",
  "v7u_N003981",
  "v7u_N003982",
  "v7u_N003983",
  "v7u_N003984",
  "v7u_N003985",
  "v7u_N003986",
  "v7u_N003987"
]
```

original_json:

```json
{
  "section_id": "CH52-S03",
  "section_title": "Technology and tools used across the customer life cycle > Robotic process automation",
  "coverage_audit": [
    {
      "candidate_id": "cand_001",
      "unit_ids": [
        "v7u_N003973"
      ],
      "proposition": "RPA机器人在KYC流程中可执行开源情报搜索、提取证件数据、自动填充系统及评定风险等级等一系列重复性任务。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "纯功能列表，无明确顺序、条件或判定性有向结构，基础KG已作为案例说明充分表达。"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N003974"
      ],
      "proposition": "RPA在筛查和交易监控中支持初始警报分类、按规则路由调查并整合ML抑制误报。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "并列功能描述，未形成明确前后依赖或判定链条，基础KG已作为解释性事实覆盖。"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N003975"
      ],
      "proposition": "存在被抑制的警报时，机构需要按正式计划定期重新审查这些警报。",
      "decision": "p7c_card",
      "card_id": "p7card_CH52-S03_001",
      "reason": "明确的状态（存在被抑制警报）触发特定主体动作（定期审查），形成条件→动作的有向关系，基础KG虽能保存规则但未表达该过程结构，可帮助判定抑制警报的后续处置义务。"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N003976"
      ],
      "proposition": "仪表盘或报告展示被抑制警报的类别和数量，以确保可审计性和持续控制。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "独立控制措施陈述，无明确触发条件或判定链条，仅表达抽象控制目标，基础KG已能充分覆盖。"
    },
    {
      "candidate_id": "cand_005",
      "unit_ids": [
        "v7u_N003978",
        "v7u_N003980"
      ],
      "proposition": "生成式AI辅助调查员生成SAR叙述，然后由人工审核并行使最终判断决定是否提交。",
      "decision": "p7c_card",
      "card_id": "p7card_CH52-S03_002",
      "reason": "AI生成与人工审核形成必要前后步骤，构成技术辅助下的控制链条，基础KG仅分别保存事实，未表达有向顺序和判定权归属，可确认AI不能独立提交SAR的选项。"
    },
    {
      "candidate_id": "cand_006",
      "unit_ids": [
        "v7u_N003981"
      ],
      "proposition": "在应用任何自动化或AI之前，组织应投资于流程再造。",
      "decision": "p7c_card",
      "card_id": "p7card_CH52-S03_003",
      "reason": "明确的时间条件（应用自动化前）导向强制前置动作（流程再造），构成条件→义务的有向结构，基础KG虽可保存规则但未体现其作为必要前置步骤的顺序关系，可支持判断自动化实施的前提。"
    },
    {
      "candidate_id": "cand_007",
      "unit_ids": [
        "v7u_N003982"
      ],
      "proposition": "存在漏洞或高度依赖人工干预的流程不适合应用RPA。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "静态判断标准，未触发具体动作或形成有向链条，基础KG已能充分保存该规则。"
    },
    {
      "candidate_id": "cand_008",
      "unit_ids": [
        "v7u_N003983"
      ],
      "proposition": "在高度监管的AML环境中，金融机构应极度谨慎地部署RPA。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般性谨慎义务，缺乏具体条件、判定或后续动作，基础KG已能覆盖。"
    },
    {
      "candidate_id": "cand_009",
      "unit_ids": [
        "v7u_N003984"
      ],
      "proposition": "RPA实施不当可能导致严重的法律和声誉后果。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "孤立风险指标，无事件触发或应对链条，基础KG已作为风险指标表达。"
    },
    {
      "candidate_id": "cand_010",
      "unit_ids": [
        "v7u_N003985"
      ],
      "proposition": "即使使用RPA或AI，AML失败的责任仍由金融机构承担。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "责任归属的一般规则，无程序性或判断性有向结构，基础KG已能充分表达。"
    },
    {
      "candidate_id": "cand_011",
      "unit_ids": [
        "v7u_N003986"
      ],
      "proposition": "监管机构要求组织对其反洗钱项目保持全面的监督和控制。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般性监管要求，未涉及具体条件或动作链条，基础KG已覆盖。"
    },
    {
      "candidate_id": "cand_012",
      "unit_ids": [
        "v7u_N003987"
      ],
      "proposition": "仅应对经过充分测试且运营成熟的流程实施自动化。",
      "decision": "kg_only",
      "card_id": null,
      "reason": "实践原则，作为独立规则无触发、顺序或判定出口，基础KG已能保存。"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH52-S03_001",
      "section_id": "CH52-S03",
      "card_nature": "control",
      "title": "Periodic Review of Hibernated Alerts",
      "flow_nodes": [
        {
          "node_id": "E3_hibernation_state",
          "node_category": "entry",
          "node_type": "E3_state_threshold",
          "label": "存在被抑制的警报（hibernated alerts）",
          "evidence_unit_ids": [
            "v7u_N003975"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "P7_revisit",
          "node_category": "process",
          "node_type": "P7_monitoring",
          "label": "机构可能（may need）需要按正式计划定期重新审查被抑制的警报",
          "evidence_unit_ids": [
            "v7u_N003975"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e001",
          "edge_type": "PRECEDES",
          "source": "E3_hibernation_state",
          "target": "P7_revisit",
          "evidence_unit_ids": [
            "v7u_N003975"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N003975"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：存在被抑制的警报 —> 机构可能需要定期重新审查；KG不足：基础KG只能保存“被抑制警报需定期审查”的规则，无法表达状态触发动作的有向过程；选项判断：可确认抑制警报后存在后续审查义务，排除“抑制后无需进一步动作”的选项；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH52-S03_002",
      "section_id": "CH52-S03",
      "card_nature": "execution",
      "title": "AI-Assisted SAR Drafting with Human Review",
      "flow_nodes": [
        {
          "node_id": "P2_ai_narrative",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "调查员使用生成式AI参考历史SAR模式生成SAR叙述",
          "evidence_unit_ids": [
            "v7u_N003978"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "P2_human_review",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "多数组织保留人工审核，审核SAR并行使最终判断决定是否提交报告",
          "evidence_unit_ids": [
            "v7u_N003980"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e002",
          "edge_type": "PRECEDES",
          "source": "P2_ai_narrative",
          "target": "P2_human_review",
          "evidence_unit_ids": [
            "v7u_N003978",
            "v7u_N003980"
          ],
          "derivation": "llm_inference"
        }
      ],
      "source_unit_ids": [
        "v7u_N003978",
        "v7u_N003980"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：AI辅助生成SAR叙述 —> 人工审核并最终判断提交；KG不足：基础KG可分别保存“AI辅助生成”和“需要人工审核”的事实，但无法表达生成后审核的必要先后顺序和最终判断权归属；选项判断：可确认AI不能独立提交SAR，人工始终保留最终决定权，排除全自动提交的选项；LLM推理：PRECEDES边为llm_inference，因原文未直接陈述顺序，但功能上先生成后审核是唯一合理逻辑。"
    },
    {
      "card_id": "p7card_CH52-S03_003",
      "section_id": "CH52-S03",
      "card_nature": "control",
      "title": "Process Reengineering Before Automation",
      "flow_nodes": [
        {
          "node_id": "E1_plan_automation",
          "node_category": "entry",
          "node_type": "E1_event_signal",
          "label": "组织计划应用自动化或AI",
          "evidence_unit_ids": [
            "v7u_N003981"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "P8_reengineering",
          "node_category": "process",
          "node_type": "P8_constrained_action",
          "label": "组织应投资于流程再造（精简工作流、消除冗余、验证控制）",
          "evidence_unit_ids": [
            "v7u_N003981"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e003",
          "edge_type": "PRECEDES",
          "source": "E1_plan_automation",
          "target": "P8_reengineering",
          "evidence_unit_ids": [
            "v7u_N003981"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N003981"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：组织计划应用自动化 —> 应投资流程再造；KG不足：基础KG能保存“自动化前应流程再造”的规则，但无法表达其作为必要前置步骤的有向顺序；选项判断：可确认实施自动化前必须进行流程优化，排除跳过此步骤直接自动化的选项；LLM推理：无。"
    }
  ],
  "skip_reason": null
}
```

review_target_candidate_ids:

```json
[
  "cand_001",
  "cand_002",
  "cand_004",
  "cand_007",
  "cand_008",
  "cand_009",
  "cand_010",
  "cand_011",
  "cand_012"
]
```

