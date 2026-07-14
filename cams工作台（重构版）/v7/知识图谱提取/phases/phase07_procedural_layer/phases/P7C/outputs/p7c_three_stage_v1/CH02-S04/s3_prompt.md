# P7C Semantic Graph Construction v1

## 角色

你是 P7C 语义构图器。S2 已经裁决了哪些命题属于 P7C 增量。你的唯一任务是将 S2 通过的命题转换为 `flow_nodes + flow_edges`。

## 输入

每个 candidate 包含 S1 原始信息 + S2 裁决结果：

```json
{
  "candidate": {
    "candidate_id": "prop_005",
    "unit_ids": ["v7u_N000477"],
    "proposition": "...",
    "source_quotes": ["..."],
    "relation_cues": ["because"],
    "induction": null
  },
  "boundary_decision": {
    "decision": "p7c_candidate",
    "reason": "..."
  }
}
```

必须独立对照 `section_text_with_unit_anchors` 验证每个命题的要素，**以原文为准**，不以 S1/S2 摘要为准。

## 构图步骤

### 步骤 1：拆分子关系

先把命题拆成语义子关系。一条命题可以生成多种 edge_type。对每条候选边独立分类。

### 步骤 2：关系分类 → edge_type 映射

在选择 edge_type 之前，先判断这条子关系属于哪类语义。分类对单条边排他。`relation_cues` 作为线索，不机械映射：

| 语义 | 线索 | 构图 |
|---|---|---|
| 条件触发动作 | if/when/unless + 动作 | entry --PRECEDES(condition)--> process |
| 明确先后步骤 | first/then/after + 动作 | PRECEDES |
| 理由/线索/判断依据 | because/due to/based on | process --REFERENCES--> input |
| 规范/阈值/政策标准 | must/require/threshold 约束动作 | process --REFERENCES--> standard |
| 动作产生独立结果 | 语义独立的产物/效果 | process --PRODUCES--> exit |
| 判断导向互斥路径 | 标准 + 正反结果 | P3_branch_routing --DECIDES(condition)--> exit |
| 普通机制因果 | 主题相关但无具体主体动作 | 不构 P7C 边 → ungraphable |

### 步骤 3：语义原子性——动作与限定性目标分离

当一句话同时包含具体动作 + 该动作旨在/可能/有助于产生的语义独立目标或效果时，分别建 process 和 exit。限定效果放边上，用 `qualifier`：

| qualifier | 含义 | 示例 |
|---|---|---|
| `aimed_to` | 旨在/以期 | aimed to restore integrity |
| `may_lead_to` | 可能产生 | may reduce exposure |
| `helps_achieve` | 有助于 | help mitigate risk |

推理系统读到"旨在实现"而非"已经实现"。例如：

```
process：重新平衡权力，加强中央监督并限制地方自主权
exit：恢复风险管理框架完整性    ← qualifier=aimed_to
exit：减少高风险辖区敞口        ← qualifier=aimed_to
```

### 步骤 4：同义出口测试

逐 exit 检查：
- "机构识别UBO"→"UBO被识别"：同义改写，不建 exit
- "机构执行整改"→"旨在恢复框架完整性"：动作和目标语义独立，建 exit + qualifier=aimed_to
- "机构必须整改"→"形成整改义务"：重复情态，不建 X7（process label 已有 must）

### 步骤 5：构建节点和边

完成关系分类和原子性判断后，使用 25 种 node_type 和 5 种 edge_type 精确构图。

## 构图原则

（以下规则从 P7C 构图契约中完整继承）

一张 card 只表达一个局部程序性或判断性有向结构。只有原文明示关系起点、处理动作和独立结果时，才构成 entry→process→exit 主路径；缺少其中任一角色时输出开放式局部关系。

entry 表示当前局部结构的关系起点。真实事件、对象到达/提交/进入某阶段、阈值越界或发现触发后续动作时才建 entry。静态适用对象、审查范围、分析材料或判断维度建为 auxiliary input 并由 process 通过 REFERENCES 指向。被 process 参照并约束动作的监管要求、政策基准或风险偏好建为 auxiliary standard。

原文用 because/due to/as a reason 等表达理由、原因或判断依据时，至少不能证明流程先后。按步骤 2 的分类映射处理。

出口 D 必须与 process 是两个独立语义事实。一个动作只建一个节点。情态保留在 process label 中；只有原文明示该动作新建立了语义独立的持续义务时才建 X7。

处理节点必须写明原文支持的具体主体及动作，避免无主体通用动作。

### 语义原子性与关系落点

一个 process 只表达一个主要语义操作。同一句/段中的多个不同动作分别建为独立 process，不压缩成宽泛节点。

构图前分别识别以下角色；只有原文明示时才建对应节点：原始输入或组成要素、对输入进行处理的操作、被应用的标准/阈值/判断维度、依据标准作出决策的过程、由不同条件分别导向的结果或后续动作。

`PRODUCES` 只表示 process 不依赖未建模条件即可形成的独立结果。如果 target 是否成立取决于某个标准、阈值、充分性或判断结论，条件必须显式进入 `condition` 字段或通过 `P3_branch_routing + DECIDES` 表达。

单一路径的 `if/when/unless A，则B` 使用条件 entry --PRECEDES(condition)--> process。只有证据支持至少两个互斥结果时才使用 P3_branch_routing + DECIDES。

多个并行情报来源/线索/标准通过 REFERENCES 各自关联到共同处理节点，不按教材叙述顺序串成 PRECEDES 链。

案例只能提取案例中实际发生的结构并保留案例限定。普通红旗/控制/框架组成由基础 KG 承接，只有存在明确的条件、动作、约束、先后或结果时才入图。

## card_nature

只能使用：`execution`、`assessment`、`risk_indicator`、`control`。

## flow_node

每个节点必填：`node_id, node_category, node_type, label, evidence_unit_ids, evidence_strength`。

允许类型：

- entry：`E1_event_signal, E2_object_entry, E3_state_threshold, E4_handoff, E5_time_cycle, E6_change_exception, E7_external_command, E8_decision_finding`
- process：`P1_assessment, P2_execution, P3_branch_routing, P4_collection, P5_coordination, P6_feedback, P7_monitoring, P8_constrained_action, P9_planning, P10_sufficiency`
- exit：`X1_classification, X2_product, X3_state_change, X4_handoff, X5_config_change, X6_termination, X7_continuing_obligation`
- auxiliary：`input, standard`

`node_category`必须与`node_type`一致：E-prefix=`entry`、P-prefix=`process`、X-prefix=`exit`、`input/standard`=`auxiliary`。节点只表达原文明示内容，`evidence_strength`固定为`explicit`。

EDD、筛查、监控、调优、审查、报告、批准、拒绝等动作建为process，不建为standard。`X1_classification`只承载分类或判断结论。`X7_continuing_obligation`只用于上游动作、决定或协议另外建立的语义独立持续义务；process label中已有的must/shall/required to不复制为X7。

## flow_edge

只允许：`PRECEDES, REFERENCES, PRODUCES, DECIDES, FEEDBACK`。

- `PRECEDES`：原文明示顺序、单一条件/触发的逻辑前提，或不可交换的必要功能先后。共同出现和教材顺序不成立。
- `REFERENCES`：process指向非时序性的input或standard；只表示参照，不表示先后、产出或分支。
- `PRODUCES`：process产生语义独立且有证据的exit。
- `DECIDES`：由`P3_branch_routing`发出，必须填写有证据的`condition`，且至少有两个互斥结果。
- `FEEDBACK`：结果或事件触发更新、补充、复核、调优、监控或再次处理。

每条边必填：`edge_id, edge_type, source, target, evidence_unit_ids`。可选：`relation_type, condition, qualifier, source_quote`。`source/target`必须引用同一card内的node_id。`source_unit_ids`必须覆盖card全部节点和边引用的unit_id。

`qualifier`只在原文明确限定效果时填写：`aimed_to`（旨在/以期）、`may_lead_to`（可能产生）、`helps_achieve`（有助于）。不得用qualifier补造原文没有的情态。

## relation_type

允许：

`clue_supports_identification, mechanism_explains_risk, identification_leads_to_conclusion, conclusion_triggers_response, branch_condition_routes_path, component_assembles_product, standard_constrains_action, result_handoffs_stage, feedback_requests_completion, cycle_requires_monitoring, standard_transmits_requirement, parallel_alternative_no_sequence`。

默认省略`relation_type`；只有端点和业务语义完全符合时才填写：

- `clue_supports_identification`：process `REFERENCES` 识别线索input。
- `standard_constrains_action`/`standard_transmits_requirement`：process `REFERENCES` standard。
- `component_assembles_product`：process `REFERENCES` 组成要素input。
- `identification_leads_to_conclusion`：识别/评估process `PRODUCES` X1分类结论。
- `conclusion_triggers_response`：已有发现或分类通过`PRECEDES`触发后续process。
- `branch_condition_routes_path`：只能用于带condition的`DECIDES`。
- `feedback_requests_completion`：只能用于`FEEDBACK`。
- `result_handoffs_stage`：exit通过`PRECEDES`交接到后续process。
- `mechanism_explains_risk`：只用于合格P7C行动链内部的`PRODUCES`；普通机制因果交给KG。
- `cycle_requires_monitoring`：周期entry通过`PRECEDES`触发`P7_monitoring`。
- `parallel_alternative_no_sequence`：process通过`REFERENCES`关联并列替代input。

## 边输出前反事实检查

1. `PRECEDES`：说明属于顺序、条件触发、交接或必要功能先后中的哪一种；条件触发必须填写`condition`。
2. `PRODUCES`：若合并source和target仍不损失独立事实，说明target只是同义改写，应删除。理由、批准、标准或义务约束应改为`REFERENCES`。
3. `REFERENCES`：交换方向后应不符合“处理动作参照输入/标准”的读法；真实步骤、产出、分支或反馈使用对应结构边。
4. 每个节点必须至少被一条边使用；同一卡内不同局部链不强行连接，应拆成不同card。

## S3 不输出 derivation

S3 的 edge 不含 derivation 字段。Derivation 完全由 P7D 独立生成。

## 输出结构

### construction_audit

每条 candidate 记录构图结果：

```json
{
  "candidate_id": "prop_001",
  "construction_status": "graphed",
  "card_ids": ["p7card_<section_id>_001"],
  "reason": "<中文>"
}
```

构图失败时：

```json
{
  "candidate_id": "prop_006",
  "construction_status": "ungraphable",
  "reason": "原文支持两端节点，但无法确定关系方向"
}
```

### cards

每张card必填：`card_id, section_id, card_nature, title, flow_nodes, flow_edges, source_unit_ids, candidate_status, review_notes`。`candidate_status`固定为`candidate`。`review_notes`使用中文，说明增量命题、KG不足和可支持的选项判断；不声明derivation或最终审核状态。

每条edge必填：`edge_id, edge_type, source, target, evidence_unit_ids`；有条件时必须填写`condition`。可选：`relation_type, qualifier, source_quote`。**不得输出`derivation`、边级`evidence_strength`或`review_status`。**

### 输出 JSON

```json
{
  "section_id": "<section_id>",
  "construction_audit": [...],
  "cards": [...],
  "skip_reason": null
}
```

## 当前section

section_id: `CH02-S04`

section_title: `Types of financial crime > Case example: FullTechGlobal corruption scandal`

section_text_with_unit_anchors:

```text
[v7u_N000131|131] Sophie is an AFC manager in the compliance department of a financial institution that has some global businesses as its customers.
ZH: Sophie 是金融机构合规部的金融犯罪防控经理。

[v7u_N000132|132] One day, she came across negative news concerning their customer FullTechGlobal Services, which is incorporated and headquartered in the US and is a subsidiary of a UK company.
ZH: Sophie 发现客户 FullTechGlobal Services 的负面新闻。

[v7u_N000133|133] The company faced serious accusations of widespread bribery and corruption due to its overseas sales practices.
ZH: 该公司因海外销售行为面临广泛贿赂和腐败的严重指控。

[v7u_N000134|134] This raised concerns under the extraterritorial provisions of the UK Bribery Act 2010.
ZH: 此事引发对《英国反贿赂法》域外条款的关切。

[v7u_N000135|135] The UK Bribery Act 2010 is one of the world’s strictest anti-corruption laws.
ZH: 《英国反贿赂法》是全球最严格的反腐败法律之一。

[v7u_N000136|136] It applies to any company with a UK connection and also holds parent firms liable for corrupt activities by subsidiaries, regardless of location.
ZH: 该法适用于任何与英国有关联的公司，母公司需对子公司腐败行为负责。

[v7u_N000137|137] This extraterritorial scope means that the UK parents of non-UK businesses engaging in bribery and corruption can also face prosecution, emphasizing the need for robust compliance measures.
ZH: 域外管辖意味着非英国企业的英国母公司也可能因贿赂腐败被起诉。

[v7u_N000138|138] Sophie’s initial investigation revealed that FullTechGlobal had strategically employed intermediaries in high-risk jurisdictions to secure lucrative contracts.
ZH: FullTechGlobal 在高风险司法管辖区战略性地雇佣中间人获取合同。

[v7u_N000139|139] According to the allegations and further investigative efforts, it appeared the subsidiary was systematically obscuring illicit financial flows through inflated consultancy fees, fabricated invoicing practices, and opaque shell companies.
ZH: 子公司通过虚增咨询费、伪造发票和壳公司掩盖非法资金流动。

[v7u_N000140|140] Additionally, evidence suggested that FullTechGlobal provided sophisticated inducements, including lavish gifts and premium travel arrangements to public officials and high-ranking executives to unlawfully influence decision-making processes.
ZH: FullTechGlobal 向公职人员和高级管理人员提供奢华礼品和旅行安排以影响决策。

[v7u_N000141|141] She followed up on the investigation and conducted a review that identified failures within FullTechGlobal’s ABC framework and internal controls. Her audit uncovered deficiencies in internal control mechanisms and inadequate oversight, which facilitated prolonged and undetected corrupt activities.
ZH: FullTechGlobal腐败案审计发现内部控制缺陷和监管不足

[v7u_N000142|142] Bribery was identified as the predicate crime, leading to the laundering of illicit funds through complex financial networks designed to evade regulatory scrutiny and forensic tracing efforts.
ZH: 贿赂作为上游犯罪，通过复杂金融网络洗钱

[v7u_N000143|143] Given these findings, the regulatory implications under the UK Bribery Act 2010 are profound. FullTechGlobal Services faces severe financial penalties, increased scrutiny from international regulators, and potential criminal liability for both the subsidiary and the parent company, including its executives.
ZH: FullTechGlobal面临英国《反贿赂法》下的严厉处罚和监管审查

[v7u_N000144|144] As an AFC manager, she recognizes that her institution needs to maintain compliance integrity and mitigate bribery and corruption risks in its dealings with global businesses such as FullTechGlobal Services.
ZH: 金融犯罪防控经理有义务维护合规诚信并降低贿赂风险
```

allowed_unit_ids:

```json
[
  "v7u_N000131",
  "v7u_N000132",
  "v7u_N000133",
  "v7u_N000134",
  "v7u_N000135",
  "v7u_N000136",
  "v7u_N000137",
  "v7u_N000138",
  "v7u_N000139",
  "v7u_N000140",
  "v7u_N000141",
  "v7u_N000142",
  "v7u_N000143",
  "v7u_N000144"
]
```

## S2 通过的候选命题

```json
[
  {
    "candidate": {
      "candidate_id": "prop_001",
      "unit_ids": [
        "v7u_N000132",
        "v7u_N000133",
        "v7u_N000134"
      ],
      "proposition": "Sophie came across negative news concerning FullTechGlobal Services being accused of bribery due to overseas sales practices, which raised concerns under the extraterritorial provisions of the UK Bribery Act 2010.",
      "relation_cues": [
        "raised concerns under"
      ],
      "source_quotes": [
        "raised concerns under the extraterritorial provisions of the UK Bribery Act 2010"
      ]
    },
    "boundary_decision": {
      "candidate_id": "prop_001",
      "decision": "p7c_candidate",
      "reason": "规则“该法适用于任何与英国有关联的公司，母公司需对子公司腐败行为负责”包含明确的条件（有英国关联）导向法律适用和归责结果的有向结构，超出基础KG仅存储规则文本的能力。"
    }
  },
  {
    "candidate": {
      "candidate_id": "prop_002",
      "unit_ids": [
        "v7u_N000136"
      ],
      "proposition": "The UK Bribery Act 2010 applies to any company with a UK connection.",
      "relation_cues": [
        "applies to"
      ],
      "source_quotes": [
        "It applies to any company with a UK connection"
      ]
    },
    "boundary_decision": {
      "candidate_id": "prop_002",
      "decision": "p7c_candidate",
      "reason": "“域外管辖意味着非英国企业的英国母公司也可能因贿赂腐败被起诉”表达了条件（域外经营涉贿）导致主体（母公司）面临法律后果的程序性因果链，超出基础KG的表达。"
    }
  },
  {
    "candidate": {
      "candidate_id": "prop_003",
      "unit_ids": [
        "v7u_N000136"
      ],
      "proposition": "The UK Bribery Act 2010 holds parent firms liable for corrupt activities by subsidiaries, regardless of location.",
      "relation_cues": [
        "holds liable"
      ],
      "source_quotes": [
        "holds parent firms liable for corrupt activities by subsidiaries, regardless of location"
      ]
    },
    "boundary_decision": {
      "candidate_id": "prop_003",
      "decision": "p7c_candidate",
      "reason": "审查动作（Sophie进行复核）直接导向发现内部控制缺陷的结论，构成完整的“动作-结果”有向链，基础KG无法表达此类具体操作性判断。"
    }
  },
  {
    "candidate": {
      "candidate_id": "prop_004",
      "unit_ids": [
        "v7u_N000137"
      ],
      "proposition": "The extraterritorial scope means that the UK parents of non-UK businesses engaging in bribery and corruption can also face prosecution.",
      "relation_cues": [
        "means that"
      ],
      "source_quotes": [
        "This extraterritorial scope means that the UK parents of non-UK businesses engaging in bribery and corruption can also face prosecution"
      ]
    },
    "boundary_decision": {
      "candidate_id": "prop_004",
      "decision": "p7c_candidate",
      "reason": "“贿赂被认定为上游犯罪，导致洗钱”表达了识别行为触发特定法律分类并引发后续犯罪链条的判断路径，属于P7C增量结构。"
    }
  },
  {
    "candidate": {
      "candidate_id": "prop_005",
      "unit_ids": [
        "v7u_N000137"
      ],
      "proposition": "The extraterritorial scope emphasizes the need for robust compliance measures.",
      "relation_cues": [
        "emphasizing the need for"
      ],
      "source_quotes": [
        "emphasizing the need for robust compliance measures"
      ]
    },
    "boundary_decision": {
      "candidate_id": "prop_005",
      "decision": "p7c_candidate",
      "reason": "“鉴于此发现，监管影响深远”体现发现作为条件输入直接导向具体的监管后果，构成有向的判断-结果关系，基础KG无法表达。"
    }
  },
  {
    "candidate": {
      "candidate_id": "prop_006",
      "unit_ids": [
        "v7u_N000138"
      ],
      "proposition": "Sophie’s initial investigation revealed that FullTechGlobal had strategically employed intermediaries in high-risk jurisdictions to secure lucrative contracts.",
      "relation_cues": [
        "revealed"
      ],
      "source_quotes": [
        "Sophie’s initial investigation revealed"
      ]
    },
    "boundary_decision": {
      "candidate_id": "prop_006",
      "decision": "p7c_candidate",
      "reason": "“作为AFC经理，她认识到机构需维护合规诚信”明确了主体角色与义务之间的约束关系，包含有向的动作要求，超出基础KG的纯定义表达。"
    }
  }
]
```
