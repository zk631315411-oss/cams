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

section_id: `CH56-S06`

section_title: `Technology for payment and batch screening > Transaction monitoring scenario development`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "covered_topics": [
    {
      "title_zh": "风险评估与场景设计",
      "title_en": "Risk Assessment and Scenario Design",
      "covered_units": [
        {
          "unit_id": "v7u_N004429",
          "unit_type": "process",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N004430",
          "unit_type": "case",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N004431",
          "unit_type": "risk_indicator",
          "kg_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N004432",
          "unit_type": "rule",
          "kg_role": "explains"
        }
      ]
    },
    {
      "title_zh": "监控中的客户细分",
      "title_en": "Customer Segmentation for Monitoring",
      "covered_units": [
        {
          "unit_id": "v7u_N004433",
          "unit_type": "process",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004434",
          "unit_type": "case",
          "kg_role": "illustrates"
        }
      ]
    },
    {
      "title_zh": "阈值设定与优化",
      "title_en": "Threshold Setting and Optimization",
      "covered_units": [
        {
          "unit_id": "v7u_N004435",
          "unit_type": "process",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004437",
          "unit_type": "process",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N004436",
          "unit_type": "risk_indicator",
          "kg_role": "states_consequence"
        }
      ]
    },
    {
      "title_zh": "严重性因素与警报优先级",
      "title_en": "Severity Factors and Alert Prioritization",
      "covered_units": [
        {
          "unit_id": "v7u_N004438",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N004439",
          "unit_type": "fact",
          "kg_role": "explains"
        }
      ]
    },
    {
      "title_zh": "增强监控的风险评级模型",
      "title_en": "Risk-Rating Models for Enhanced Monitoring",
      "covered_units": [
        {
          "unit_id": "v7u_N004440",
          "unit_type": "definition",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004441",
          "unit_type": "case",
          "kg_role": "illustrates"
        }
      ]
    },
    {
      "title_zh": "持续测试与校准",
      "title_en": "Ongoing Testing and Calibration",
      "covered_units": [
        {
          "unit_id": "v7u_N004442",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        }
      ]
    },
    {
      "title_zh": "克服系统局限性",
      "title_en": "Overcoming System Limitations",
      "covered_units": [
        {
          "unit_id": "v7u_N004443",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N004444",
          "unit_type": "process",
          "kg_role": "prescribes_measure"
        }
      ]
    }
  ],
  "covered_relations": [
    {
      "source_title": "风险评估与场景设计",
      "target_title": "监控中的客户细分",
      "relation_type": "prepares"
    },
    {
      "source_title": "风险评估与场景设计",
      "target_title": "阈值设定与优化",
      "relation_type": "prepares"
    },
    {
      "source_title": "监控中的客户细分",
      "target_title": "阈值设定与优化",
      "relation_type": "prepares"
    },
    {
      "source_title": "阈值设定与优化",
      "target_title": "严重性因素与警报优先级",
      "relation_type": "prepares"
    },
    {
      "source_title": "严重性因素与警报优先级",
      "target_title": "增强监控的风险评级模型",
      "relation_type": "prepares"
    },
    {
      "source_title": "增强监控的风险评级模型",
      "target_title": "持续测试与校准",
      "relation_type": "prepares"
    },
    {
      "source_title": "持续测试与校准",
      "target_title": "克服系统局限性",
      "relation_type": "prepares"
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N004429|4429] The first step in developing transaction monitoring scenarios is conducting a risk assessment to define the specific transaction patterns that require monitoring.
ZH: 开发交易监控场景的第一步是进行风险评估以定义需监控的交易模式。

[v7u_N004430|4430] Common scenario designs include frequent cross-border transactions with high-risk countries, structuring, sudden large cash deposits, and unexpected repayment of overdue credit amounts.
ZH: 常见场景包括频繁跨境交易、拆分交易、大额现金存款和逾期信贷的异常还款。

[v7u_N004431|4431] Transactions that do not align with a customer’s business profile, unexplained fund transfers, or sudden activity in dormant accounts might also indicate potential financial crime.
ZH: 与客户业务画像不符的交易、不明资金转移或休眠账户突然活动可能表明金融犯罪。

[v7u_N004432|4432] The financial institution should assess these scenarios against its risk profile to determine which are most relevant based on its business model, customer base, and regulatory obligations.
ZH: 金融机构应根据自身风险状况评估场景的相关性。

[v7u_N004433|4433] Financial institutions perform customer segmentation for effective monitoring, either before or after developing the scenarios. They categorize customers by business type, transaction behavior, geographic exposure, and risk level.
ZH: 金融机构按业务类型、交易行为、地理敞口和风险水平进行客户细分。

[v7u_N004434|4434] For example, high-cash businesses such as convenience stores or restaurants often have frequent cash deposits, while a salaried professional receiving cash payments might be unusual.
ZH: 高现金业务如便利店常有频繁现金存款，而受薪专业人士现金收款则异常。

[v7u_N004435|4435] By establishing optimal thresholds for each customer segment, financial institutions can fine-tune monitoring systems to balance accuracy and efficiency. Parameterization is key in this process, as it ensures that transaction limits, frequency checks, and behavioral patterns are set appropriately.
ZH: 为每个客户细分设定最优阈值，并通过参数化平衡准确性与效率。

[v7u_N004436|4436] Overly sensitive thresholds can overwhelm operational teams with false positives. Overly lenient settings might fail to detect legitimate financial crimes.
ZH: 阈值过于敏感会导致误报过多，过于宽松则可能漏报真实犯罪。

[v7u_N004437|4437] To mitigate these issues, financial institutions use historical transaction data, peer-group comparisons, and severity factors to refine monitoring rules.
ZH: 利用历史数据、同行比较和严重性因素来优化监控规则。

[v7u_N004438|4438] Severity factors are criteria for assessing the significance of suspicious transactions based on transaction size and frequency, customer risk profile, and potential regulatory impact.
ZH: 严重性因素是根据交易规模、频率、客户风险画像和监管影响评估可疑交易重要性的标准。

[v7u_N004439|4439] These factors help prioritize alerts for investigation.
ZH: 严重性因素有助于对警报进行优先级排序以便调查。

[v7u_N004440|4440] Risk-rating models enhance scenario effectiveness by assigning risk scores based on transaction behaviors, customer attributes, and exposure to highrisk jurisdictions.
ZH: 风险评级模型通过基于交易行为、客户属性和高风险司法管辖区敞口分配风险评分来增强场景有效性。

[v7u_N004441|4441] For example, products and services, such as offshore wire transfers and cryptocurrency transactions, also influence risk and require stricter thresholds than domestic payments.
ZH: 离岸电汇和加密货币交易等产品和服务影响风险，需要比国内支付更严格的阈值

[v7u_N004442|4442] To maintain efficiency, financial institutions should continuously test, calibrate, and conduct impact analysis to ensure scenarios remain effective.
ZH: 金融机构应持续测试、校准并进行影响分析以确保场景有效

[v7u_N004443|4443] Not all TM systems are equally capable. Some have rigid rule structures or limited integration with external risk intelligence sources.
ZH: 交易监控系统能力各异，有的规则结构僵化或与外部风险情报集成有限

[v7u_N004444|4444] To overcome these challenges, institutions may leverage machine learning, behavioral analytics, manual overrides, and expert-driven adjustments to ensure their monitoring frameworks remain adaptive to emerging threats.
ZH: 机构可利用机器学习、行为分析、人工覆盖和专家调整使监控框架适应新兴威胁
```

allowed_unit_ids:

```json
[
  "v7u_N004429",
  "v7u_N004430",
  "v7u_N004431",
  "v7u_N004432",
  "v7u_N004433",
  "v7u_N004434",
  "v7u_N004435",
  "v7u_N004436",
  "v7u_N004437",
  "v7u_N004438",
  "v7u_N004439",
  "v7u_N004440",
  "v7u_N004441",
  "v7u_N004442",
  "v7u_N004443",
  "v7u_N004444"
]
```

original_json:

```json
{
  "section_id": "CH56-S06",
  "section_title": "Technology for payment and batch screening > Transaction monitoring scenario development",
  "coverage_audit": [
    {
      "candidate_id": "cand_001",
      "unit_ids": [
        "v7u_N004429"
      ],
      "proposition": "开发交易监控场景的第一步是进行风险评估以定义需监控的交易模式",
      "decision": "kg_only",
      "card_id": null,
      "reason": "风险评估作为场景开发的第一步，其目的是定义监控模式，属于一般过程描述，基础KG已将风险评估作为process覆盖，定义模式是其应有之义，无法提取超出KG的有向结构。"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N004430"
      ],
      "proposition": "常见交易监控场景设计包括频繁跨境交易、拆分交易等",
      "decision": "kg_only",
      "card_id": null,
      "reason": "列举常见监控场景类型，属于基础事实，KG可保存。"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N004431"
      ],
      "proposition": "与客户画像不符的交易、不明资金转移或休眠账户活动可能表明金融犯罪",
      "decision": "kg_only",
      "card_id": null,
      "reason": "列出可能表明金融犯罪的交易特征，属于孤立风险指标，KG可承接。"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N004432"
      ],
      "proposition": "根据风险状况，金融机构应评估交易监控场景以确定最相关者",
      "decision": "p7c_card",
      "card_id": "p7card_CH56-S06_001",
      "reason": "明确了主体（金融机构）、义务情态（should）、动作（评估场景）以及约束标准（风险状况），构成标准约束评估动作的有向关系，基础KG无法表达这种约束关系。"
    },
    {
      "candidate_id": "cand_005",
      "unit_ids": [
        "v7u_N004433"
      ],
      "proposition": "金融机构进行客户细分，可在场景开发前或后，按业务类型、交易行为、地理敞口和风险水平分类",
      "decision": "kg_only",
      "card_id": null,
      "reason": "客户细分的时间和分类标准属于一般过程知识，KG已将其作为与阈值设定的准备关系覆盖，无增量有向结构。"
    },
    {
      "candidate_id": "cand_006",
      "unit_ids": [
        "v7u_N004434"
      ],
      "proposition": "高现金业务常有频繁现金存款，而受薪专业人士现金收款则异常",
      "decision": "kg_only",
      "card_id": null,
      "reason": "具体案例说明客户行为异常，属于普通案例，KG可承接。"
    },
    {
      "candidate_id": "cand_007",
      "unit_ids": [
        "v7u_N004435"
      ],
      "proposition": "机构为每个客户细分设定最优阈值以微调监控系统并平衡准确性与效率",
      "decision": "kg_only",
      "card_id": null,
      "reason": "设定阈值与客户细分的关系已在KG中体现（客户细分 prepares 阈值设定），且该单元主体描述一般过程，未超出KG表达能力。"
    },
    {
      "candidate_id": "cand_008",
      "unit_ids": [
        "v7u_N004436"
      ],
      "proposition": "阈值过于敏感导致误报过多，过于宽松则漏报",
      "decision": "kg_only",
      "card_id": null,
      "reason": "说明阈值敏感性对误报和漏报的影响，属于一般因果知识，KG可表达。"
    },
    {
      "candidate_id": "cand_009",
      "unit_ids": [
        "v7u_N004437"
      ],
      "proposition": "金融机构使用历史交易数据、同行比较和严重性因素来优化监控规则",
      "decision": "p7c_card",
      "card_id": "p7card_CH56-S06_002",
      "reason": "明确了特定输入（历史数据、同行比较、严重性因素）如何支持优化动作，构成输入-流程的有向关系，基础KG无法表达这种具体输入与动作的关联。"
    },
    {
      "candidate_id": "cand_010",
      "unit_ids": [
        "v7u_N004438"
      ],
      "proposition": "严重性因素是根据交易规模、频率、客户风险画像和监管影响评估可疑交易重要性的标准",
      "decision": "kg_only",
      "card_id": null,
      "reason": "定义严重性因素的构成标准，属于定义，KG可承接。"
    },
    {
      "candidate_id": "cand_011",
      "unit_ids": [
        "v7u_N004439"
      ],
      "proposition": "严重性因素帮助对警报进行优先级排序以便调查",
      "decision": "p7c_card",
      "card_id": "p7card_CH56-S06_003",
      "reason": "明确了标准（严重性因素）如何约束优先级排序动作，构成标准-流程的有向关系，基础KG无法表达该约束。"
    },
    {
      "candidate_id": "cand_012",
      "unit_ids": [
        "v7u_N004440"
      ],
      "proposition": "风险评级模型通过基于交易行为等分配风险评分来增强场景有效性",
      "decision": "kg_only",
      "card_id": null,
      "reason": "说明风险评分模型的功能和输入，属于一般机制解释，KG可表达。"
    },
    {
      "candidate_id": "cand_013",
      "unit_ids": [
        "v7u_N004441"
      ],
      "proposition": "离岸电汇和加密货币交易需要比国内支付更严格的阈值",
      "decision": "kg_only",
      "card_id": null,
      "reason": "具体产品或服务对阈值严格性的要求示例，KG可承接。"
    },
    {
      "candidate_id": "cand_014",
      "unit_ids": [
        "v7u_N004442"
      ],
      "proposition": "金融机构应持续测试、校准和进行影响分析以确保场景有效性",
      "decision": "kg_only",
      "card_id": null,
      "reason": "明确持续动作义务，但未构成有向关系（无标准或输入引用，无独立结果），无法形成边，因此不属于P7C增量。"
    },
    {
      "candidate_id": "cand_015",
      "unit_ids": [
        "v7u_N004443"
      ],
      "proposition": "并非所有TM系统能力相同，有些规则结构僵化或与外部风险情报集成有限",
      "decision": "kg_only",
      "card_id": null,
      "reason": "陈述TM系统能力差异，属于事实，KG可承接。"
    },
    {
      "candidate_id": "cand_016",
      "unit_ids": [
        "v7u_N004444"
      ],
      "proposition": "机构可利用机器学习、行为分析等使监控框架适应新兴威胁",
      "decision": "kg_only",
      "card_id": null,
      "reason": "说明克服局限性的技术手段，但未构成有向关系（输入到动作的边不明显），KG可表达。"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH56-S06_001",
      "section_id": "CH56-S06",
      "card_nature": "assessment",
      "title": "金融机构应基于风险状况评估交易监控场景",
      "flow_nodes": [
        {
          "node_id": "p7card_CH56-S06_001_P1",
          "node_category": "process",
          "node_type": "P1_assessment",
          "label": "金融机构应评估交易监控场景以确定最相关者",
          "evidence_unit_ids": [
            "v7u_N004432"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "p7card_CH56-S06_001_STD1",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "机构的风险状况",
          "evidence_unit_ids": [
            "v7u_N004432"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "p7card_CH56-S06_001_e1",
          "edge_type": "REFERENCES",
          "source": "p7card_CH56-S06_001_P1",
          "target": "p7card_CH56-S06_001_STD1",
          "evidence_unit_ids": [
            "v7u_N004432"
          ],
          "derivation": "explicit_text",
          "relation_type": "standard_constrains_action"
        }
      ],
      "source_unit_ids": [
        "v7u_N004432"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：金融机构应评估交易监控场景（process） --REFERENCES--> 机构的风险状况（standard）；KG不足：基础KG只能表达机构应进行风险评估的一般规则，无法表达该评估动作必须依据风险状况这一标准约束关系；选项判断：可帮助确认或排除关于评估依据的选项；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH56-S06_002",
      "section_id": "CH56-S06",
      "card_nature": "execution",
      "title": "金融机构使用历史数据等优化监控规则",
      "flow_nodes": [
        {
          "node_id": "p7card_CH56-S06_002_P1",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "金融机构优化监控规则",
          "evidence_unit_ids": [
            "v7u_N004437"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "p7card_CH56-S06_002_IN1",
          "node_category": "auxiliary",
          "node_type": "input",
          "label": "历史交易数据、同行比较和严重性因素",
          "evidence_unit_ids": [
            "v7u_N004437"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "p7card_CH56-S06_002_e1",
          "edge_type": "REFERENCES",
          "source": "p7card_CH56-S06_002_P1",
          "target": "p7card_CH56-S06_002_IN1",
          "evidence_unit_ids": [
            "v7u_N004437"
          ],
          "derivation": "explicit_text"
        }
      ],
      "source_unit_ids": [
        "v7u_N004437"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：金融机构优化监控规则（process） --REFERENCES--> 历史交易数据、同行比较和严重性因素（input）；KG不足：基础KG只表达优化规则是一般措施，无法表达这些具体输入如何支持优化动作；选项判断：可帮助确认优化规则所依据的数据类型；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH56-S06_003",
      "section_id": "CH56-S06",
      "card_nature": "execution",
      "title": "严重性因素帮助对警报进行优先级排序",
      "flow_nodes": [
        {
          "node_id": "p7card_CH56-S06_003_P1",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "对警报进行优先级排序以便调查",
          "evidence_unit_ids": [
            "v7u_N004439"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "p7card_CH56-S06_003_STD1",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "严重性因素",
          "evidence_unit_ids": [
            "v7u_N004439"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "p7card_CH56-S06_003_e1",
          "edge_type": "REFERENCES",
          "source": "p7card_CH56-S06_003_P1",
          "target": "p7card_CH56-S06_003_STD1",
          "evidence_unit_ids": [
            "v7u_N004439"
          ],
          "derivation": "explicit_text",
          "relation_type": "standard_constrains_action"
        }
      ],
      "source_unit_ids": [
        "v7u_N004439"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：对警报进行优先级排序（process） --REFERENCES--> 严重性因素（standard）；KG不足：基础KG只定义严重性因素并说明其用于评估交易重要性，未表达其直接约束警报优先级排序动作；选项判断：可帮助确认优先级排序的依据；LLM推理：无。"
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
  "cand_003",
  "cand_005",
  "cand_006",
  "cand_007",
  "cand_008",
  "cand_010",
  "cand_012",
  "cand_013",
  "cand_014",
  "cand_015",
  "cand_016"
]
```

