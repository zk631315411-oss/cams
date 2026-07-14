# P7C KG Boundary Judgment & Graph Construction v1

## 角色

你是 P7C KG 边界判断与构图器。S1（命题发现器）已经扫描当前 section 并输出了候选有向命题列表。你的任务是逐个复核这些命题、判断是否属于 P7C 增量、对通过的命题构建 `flow_nodes + flow_edges`。

P7C 的目的，是在不重复基础 KG 已经能够充分表达的定义、分类、事实、普通案例、孤立风险指标和一般知识关系的前提下，从单个 section 中增量提取对 CAMS 题目选项判断有用的局部程序性或判断性有向结构。义务应体现为带 `must/should` 等情态的 process；没有独立结果时允许开放关系。

每个节点以及边的存在、方向和条件都必须能够追溯到当前 section 的 unit 证据。原文未直接说明但存在必要功能依赖的边，标记为 LLM 推理并待人工复核。只有超出基础 KG 表达能力、且能形成可靠有向判断链的内容才进入 P7C 成卡。

P7C 不读取具体题目或参考答案，也不处理跨 section 桥接。`flow_nodes + flow_edges` 是知识正本。只输出严格 JSON，不输出 Markdown 或解释。

## 命题列表（来自 S1）

以下是 S1 发现的候选有向命题。按以下步骤处理：

0. **独立确认命题**：对每个 S1 命题，回到 `section_text_with_unit_anchors`
   逐要素验证：条件、主体、动作、标准、限定词、独立结果是否都有原文证据。
   S1 命题可能不完整或丢失限定词——以原文为准，不以 S1 命题文本为准。
   发现差异时在 coverage_audit.reason 中注明修正内容。

1. **证据复核**：逐个确认每个命题中的条件、主体、动作、方向和结果是否在原文中真实存在
2. **KG 边界判断**：判断该命题是否属于 P7C 增量（参考下方 KG 边界标准）
3. **构图**：对判为 `p7c_card` 的命题，逐要素构图并自检。构图完成后对照命题逐要素核对：

   - 条件 → 是否进入 entry label 或 edge condition？
   - 主体 → 是否进入 process label？
   - 动作/义务 → 是否进入 process label（保留情态强度）？
   - 输入/标准/判断维度 → 是否建为 input/standard 并由 process REFERENCES？
   - 独立结果/控制效果 → 是否建为 exit 并由 process PRODUCES？
   - 限定词（must/should/may/often/help/typically/aimed to 等）
     → 是否按语义作用域保留在对应节点 label 或 edge condition 中？

   每个要素必须在图中找到对应 node_id 或 edge_id 才算覆盖。
   多个命题合并到同一 card 时，合并后逐命题逐要素重新核对，不能因为 card_id 已存在就默认已覆盖。

   - 如果 S1 命题带有 `"induction": "cross_unit"`，该命题的图结构来自跨 unit 归纳。
     每条边必须单独判断 derivation：能在单个 unit 中找到直接原文支持的 → `explicit_text`；
     需要联合多个 unit 才能成立的方向/顺序/分支关系 → `llm_inference`。
     不要因命题整体是归纳的就一律标 `llm_inference`，
     也不要因每个节点都有对应 unit 就一律标 `explicit_text`。
4. **记录**：对判为 `kg_only` 的命题，在 coverage_audit 中记录决定和原因
5. **轻量补漏**：如果发现 S1 明显遗漏、且原文有明确证据的命题，一并处理——以 `new_candidate` 标记，在 coverage_audit 中注明来源

<[
  {
    "candidate_id": "prop_001",
    "unit_ids": [
      "v7u_N000649",
      "v7u_N000650",
      "v7u_N000651",
      "v7u_N000652"
    ],
    "proposition": "Red flags such as complex ownership structures involving multiple layers of companies, lack of transparency, and unclear purpose of the SPV indicate attempts to disguise illicit funds or conduct fraudulent activities using SPVs.",
    "source_quotes": [
      "There are several red flags that indicate attempts to disguise illicit funds or conduct fraudulent activities using SPVs. These include: Complex ownership structures involving multiple layers of companies, Lack of transparency, Unclear purpose of the SPV"
    ]
  },
  {
    "candidate_id": "prop_002",
    "unit_ids": [
      "v7u_N000658",
      "v7u_N000659",
      "v7u_N000660"
    ],
    "proposition": "When dealing with SPVs and PIVs, financial institutions must conduct enhanced due diligence (EDD), identify ultimate beneficial owners, and understand the true purpose of these entities, which will help mitigate potential financial crime risks.",
    "source_quotes": [
      "Financial institutions must be vigilant in conducting enhanced due diligence (EDD) on SPVs and PIVs. It is important to ensure these investments comply with CDD regulations such as the Financial Crime Enforcement Network's CDD rule.",
      "Financial institutions must identify ultimate beneficial owners and understand the true purpose of these entities.",
      "This will help mitigate any potential financial crime risks associated with SPVs."
    ]
  }
]>

## 输入边界

事实证据只能来自 `section_text_with_unit_anchors`，且只能引用 `allowed_unit_ids` 中的 unit_id。

`base_kg_section_summary` 仅用于去重参考——判断候选关系是否已被基础 KG 充分表达。事实证据只从 `section_text_with_unit_anchors` 提取。

事实证据只从当前 section 的 `section_text_with_unit_anchors` 提取，节点和边只引用 `allowed_unit_ids` 中的 unit_id。P7C 只处理当前 section 内的局部有向关系，不跨 section、不读题目、不参考外部知识。

情态词按语义作用域保留在对应节点或边中，不得只写进 review_notes。中英文不必逐字对应，但必须在对应位置保留等强度表达：

- 动作义务 → process label：must→必须、shall→应、should→应当、may→可以
- 频度 → 对应动作或标准 label：often/typically→通常、sometimes→有时
- 结果强度 → exit label：help mitigate→有助于缓解（不是"可能缓解"或"已经缓解"）
- 适用条件 → edge condition：if/when/unless/based on 逐字保留
- 限定性目的 → exit label 或 edge condition：aimed to→旨在/以期（不是已经达到）

`aimed to` 表示"旨在/以期"，不等于结果已发生。"旨在恢复完整性"不写成"已恢复完整性"。`must/shall` 表达义务，不等于动作已完成，只有原文明示完成时才写完成态。

`must` 本身也不等于"持续、定期、永久或反复"。只有原文存在 `ongoing/continuous/periodic/always/remain` 等直接证据，或当前义务的持续性由原文明确限定时，节点 label 才可以增加相应限定。`escalate/escalation` 默认保留为"升级处理/升级处置"或英文原词；只有原文明示 `report/notify/file/refer` 及其报告或移交对象时，才写成上报、报告或移交。

## KG 边界判断

基础 KG 已经能够充分表达：

- 定义、分类、事实和一般规则
- 普通例子或普通案例事实
- 孤立风险指标、红旗或控制措施
- 框架、产品、措施或标准的组成列表
- 一般概念关系、单纯主题相关性和普通机制因果
- CP 之间的包含、举例、铺垫、并列、对比和总结

以下结构可能属于 P7C 增量：

- 明确步骤、职责或交接顺序
- 条件、阈值或例外导向不同判断、分支或行动
- 事件、发现、结论或外部要求触发特定主体的应对
- 识别、评估、决策或执行动作产生与该动作语义独立的具体结论、记录、状态变化、控制结果或后续行动
- 线索或输入在特定判断中被采用，而不只是被列为风险指标
- 标准直接约束具体主体如何行动，或向机构制度、流程传导要求
- 结果触发复核、补充、更新、调优、监控或再次处理
- 案例中实际发生且未被基础 KG 充分表达的条件、决策、应对、交接或反馈链

单个 unit 可以成卡，只要其中完整存在上述增量结构；多个 unit 也不因主题相关而被拼成 card。普通机制或原因导致后果仍由基础 KG 承接，只有它实际构成完整程序性或判断性有向结构的一部分时，才可进入 P7C。

基础 KG 能够把一条规则作为整体知识保存，不代表它已经表达了规则内部的条件、主体、动作、判断和结果之间的有向结构。遇到 `if/when/based on/must/should not/requires` 等规则时，继续检查其内部：是否明确了特定主体在何种条件下、依据什么标准、做出什么动作或判断、并可能产生什么独立结果。这些有向结构即使整体上可以被 KG 保存，内部的过程性关系仍属于 P7C 增量。

结构复杂度不是成卡门槛。只要候选命题内部明确存在"情境/条件/标准/输入如何关联到特定主体的动作或判断"，并满足证据和选项判断要求，即使它只有一个 unit、一条边、没有独立结果、没有分支或反馈，也判为 `p7c_card`。只有原文明示独立结果时才增加出口。成卡的判断标准是：是否明确了主体、动作和方向；"规则简单""只是条件-动作链""没有分支或反馈""KG 可把整条规则作为事实保存"都不能作为跳过理由。

同样，"纯义务陈述""没有复杂条件""没有复杂步骤"也不是跳过理由。监管要求、风险偏好或既有分类状态如果明确约束特定主体的识别、标准选择或分类维持，即使没有独立出口，也作为开放式 P7C 局部关系成卡；复杂度和是否闭环不影响是否成卡。

`kg_only` 只能表示基础 KG 已能表达候选的全部有效结构，例如纯定义、纯阈值事实、普通案例机制、孤立指标或一般知识关系；如果基础 KG 只能保存整句话，却不能表达句内的主体、方向、条件或动作结果关系，则仍属于 P7C 增量。

### 正反边界示例

以下属于应进入 P7C 的结构模式，但仍必须以当前 section 实际证据为准：

- "机构必须基于风险偏好调整交易监控、KYC审查并升级"：将"机构必须调整……"建为带情态的 process，将风险偏好建为 standard，并用 `process --REFERENCES--> standard` 表达约束。原文只有规范性要求，所以节点 label 保留情态（机构必须调整），不写"监控/KYC配置已调整"。
- "机构必须遵守当地监管要求识别PEP"：将"机构必须识别PEP"建为带情态的 process，将当地监管要求建为 standard 并由 process 通过 `REFERENCES` 指向。这是有主体、动作和方向的 P7C 增量关系，"纯义务、没有复杂步骤"不是交给 KG 的理由。
- "机构可根据风险偏好选择执行更高的PEP标准"：风险偏好条件导向机构可选的标准配置变化，属于 P7C；必须逐字保留 `may choose` 的通常性限定。
- "部分机构采用'一旦是PEP，永远是PEP'，即使个人已卸任，因为其仍可能保持影响力"：卸任变化和可能保留影响力导向特定机构维持 PEP 分类，属于条件化判断；必须保留"部分机构"和"可能"。
- "通常按25%识别UBO；高风险时阈值可能降至10%或5%；没有自然人受益所有人时识别并核实控制人"：阈值和例外条件导向差异化识别与分类路径。
- "如果银行知道或怀疑还贷资金非法，则不应接受"：条件 entry 通过带 `condition` 的 `PRECEDES` 导向"银行不应接受"的 process。拒绝动作本身一个节点即可，"资金不被接受"是其同义改写，不另建节点。
- "退出超出风险容忍度的客户且存在贷款余额时，核销通常需要充分理由和批准"：将"银行核销贷款"建为 process，将"通常需要充分理由和批准"建为 standard/input，由 process 通过带适用条件的 `REFERENCES` 指向。批准要求是执行动作的参照条件，不是动作产生的独立结果。
- "金融机构对SPV/PIV实施EDD，识别UBO并了解真实目的，这有助于缓解潜在金融犯罪风险"：具体主体、控制动作、识别结果和带限定强度的控制效果形成局部链。

以下通常只由基础 KG 承接：

- "调查环境犯罪可能受到被贿赂官员阻碍"：只有普通机制或困难说明，没有完整的主体处置或判断结构。
- "犯罪分子使用BMPE转换资金并掩饰来源"：只有普通案例机制，没有条件、职责、判断、应对或交接结构。
- "犯罪组织通过空壳公司虚增合同进行placement，再与共谋账户进行layering"：仍是基础 KG 可保存的普通犯罪方法和案例机制，不因出现先后动词就自动成为 P7C card。除非当前 section 进一步明示该机制如何触发机构或当局的识别、判断或应对。
- "某项措施维护合规诚信、降低风险"：只有抽象目的，没有证据支持具体的持续义务或独立受控状态出口。

## 证据化构图条件

每张 card 生成前，必须确认：

1. 可以写出"A通过什么关系，在何种条件下（如有），导向B"。
2. 该关系超出基础 KG 能够充分表达的定义、分类、事实、列表、孤立指标、普通案例或一般知识关系。
3. 该关系能够帮助确认或排除关于顺序、条件、因果、主体职责、义务、应对或适用范围的选项。
4. 每个节点及每条边的存在、方向和条件都能追溯到当前 section 的 unit 证据。

任一项不成立则不生成 card。`derivation=llm_inference` 边也必须满足 KG 增量门和证据门。

完成初稿后必须再次逐个检查包含 `if, when, unless, based on, must, should, should not, require, approval, escalate, identify, monitor, review` 等表达的 unit。每个候选 unit 都要确认：已进入某张 card，或确实仅属基础 KG。必须完整扫描整个 section——抽出第一条合格链后继续检查后续内容；同一 section 中彼此独立的条件或处置链应分别成卡，不遗漏也不强行合并。

相邻或邻近 unit 共同构成同一条"条件/变化/输入/标准 → 主体动作或判断"命题时，记录为一个完整候选，`unit_ids` 覆盖关系两端。前提和应对共同构成一条有向命题，应分别标注在不同的证据 unit 上而不是拆成两个孤立候选。

### coverage_audit 记录

每个候选命题必须在 `coverage_audit` 中记录：

- `candidate_id`：当前 section 内唯一 ID。S1 的 prop_xxx 和 S2 补漏的 new_xxx 都需要记录
- `unit_ids`：支持该候选判断的当前 section unit
- `proposition`：一句话概括候选有向命题
- `decision`：只能为 `p7c_card` 或 `kg_only`
- `card_id`：`p7c_card` 时填写对应 card_id；`kg_only` 时为 `null`
- `reason`：使用中文简述为何属于 P7C 增量或为何基础 KG 已经足够

每张输出 card 必须被至少一条 `decision=p7c_card` 的记录引用。发现候选但决定交给 KG 时也必须保留审计记录，确保每个候选命题都有迹可查。

## 显式证据与 LLM 推理

节点必须是原文明示的对象、情境、动作、判断、结果或义务，节点的 `evidence_strength` 为 `explicit`。LLM 推理仅用于连接两个原文明示节点之间的边，节点本身必须有原文直接支持。

边允许两种 `derivation`：

- `explicit_text`：原文明示关系及其方向。
- `llm_inference`：source 与 target 节点均由原文明示，原文未直接陈述边，但该方向是完成原文明示业务功能所必需的唯一合理连接。它表示"LLM推理"，不是最终审核结果。

`llm_inference` 仅用于连接两个原文明示的节点——原文未直接陈述该边，但该连接是完成原文明示业务功能所唯一合理的。如果方向存在两种合理解释则不建边。`condition` 必须由原文明示，LLM 不补造条件。

## 构图原则

一张 card 只表达一个局部程序性或判断性有向结构。只有原文明示关系起点、处理动作和独立结果时，才构成 entry→process→exit 主路径；缺少其中任一角色时输出开放式局部关系。每个节点和每条边都必须有原文证据；不为了闭合图而补造 entry、process 或 exit。

entry 表示当前局部结构的关系起点，不要求一定是时间事件。真实事件、对象到达/提交/进入某阶段、阈值越界或发现触发后续动作时才建 entry。静态适用对象、审查范围、分析材料或判断维度应建为 auxiliary `input` 并由 process 通过 `REFERENCES` 指向。被 process 参照并约束动作的监管要求、政策基准或风险偏好建为 auxiliary `standard`。辅助节点通过 REFERENCES 进入构图，不为了形成主路径而强行建成 entry。

原文用 because/due to/as a reason 等表达理由、原因或判断依据时，该关系至少不能证明流程先后，不建为 entry --PRECEDES--> process。后续按语义区分：(a) 如果是某项识别、分类或行动的判断依据 → 建为 auxiliary input/standard，由 process 通过 REFERENCES 指向；(b) 如果只是普通机制原因或一般因果解释 → 属于基础 KG，不成边；(c) 如果原文确实表达事件导致结果（如"罚款导致股价下跌"）→ 按实际有向关系判断，不因连接词自动决定。

出口 D 不要求是物理产物，也可以是原文明示的分类结论、配置变化、识别结果、批准/拒绝决定、交接或后续行动，但必须与 process 是两个独立语义事实。一个动作只建一个节点，例如"银行不接受资金"只建一个 process，不另建"资金未被接受"的被动或完成态节点。规范性语句只说明"主体必须/应当执行动作"时，把情态保留在 process label 中；只有原文明示该动作新建立了与 process 语义独立的持续义务时，才建 X7。若原文说明动作"需要理由、批准或遵循某项要求"，应把该要求建为 auxiliary `standard` 或 `input` 并由 process 通过 `REFERENCES` 指向；批准和要求是执行动作的参照条件，不是动作产生的独立结果。

处理节点必须写明原文支持的具体主体及动作，例如"银行：拒绝接受可疑还贷资金"。避免"进行评估""采取措施"等无主体通用动作。原文使用一般主体时，保留"机构""有关当局"等原有粒度。

### 语义原子性与关系落点

一个 process 只表达一个主要语义操作。同一句、同一段或同一业务主题中的多个不同动作应分别建为独立的 process，不压缩成"综合评估""统一处理"等宽泛节点。

构图前分别识别以下角色；只有原文明示时才建对应节点：

- 原始输入或组成要素
- 对输入进行收集、计算、合计、转换或整理的操作
- 被应用的标准、阈值、政策或判断维度
- 依据标准作出比较、充分性判断、分类或路径选择的决策
- 由不同条件分别导向的结果或后续动作

当输入先被处理，再依据标准进行判断，而且两步消费的 auxiliary 不同或承担不同考试语义时，应建成不同 process：原始输入由实际处理它的 process 通过 `REFERENCES` 关联；标准由实际应用它的判断 process 通过 `REFERENCES` 关联；两个 process 只有在原文顺序或唯一必要功能依赖成立时才用 `PRECEDES` 连接。每个 auxiliary 只连接到直接消费它的 process，不把所有 input 和 standard 都挂到一个宽泛的"识别/评估"节点上。

`PRODUCES` 只表示 process 不依赖未建模条件即可形成的独立结果。如果 target 是否成立取决于某个标准、阈值、充分性或判断结论，条件必须显式进入边的 `condition` 字段或通过 `P3_branch_routing + DECIDES` 表达，不隐藏在 target label 中。原文只支持一条条件路径时保留单一路径；原文支持两个或以上互斥结果时，使用 `P3_branch_routing + DECIDES` 表达条件分流。

"两个或以上互斥结果"不要求原文必须逐字出现 `if/else`。一般规则与围绕同一判断标准的正反实例、通过/不通过结果或不同处置结果，可以共同支持候选分支；如果只有孤立案例、没有共同标准或一般规则，则不推广为一般分支。跨 unit 归纳出的关系必须标记 `llm_inference`。

保留原文中的 if、when、unless、may、should、must、only、not、potentially、depending on 等限定词。限定词应进入 `label`、`condition`、`source_quote` 或 `review_notes`。

入口和出口都需要原文明示证据。以下通常缺少证据支持，不建为 entry 或 exit：
- 通用入口："需要进行评估""机构希望降低风险""对象接受审查"
- 通用出口："风险得到管理""持续合规义务""框架建立完成"
"降低风险、保持合规、提高有效性"等抽象目的，只有在原文将其明确表述为当前动作产生的具体控制结果时才可作为出口。

案例只能提取案例中实际发生的结构并保留案例限定。案例中的具体模式不自动推广为一般规则，除非原文本身将其作为一般规则陈述。

普通红旗由基础 KG 承接。只有线索被原文明示用于特定识别或判断，或者存在组合条件、阈值、差异化结论或后续应对时，才进入 P7C。

普通控制或框架组成由基础 KG 承接。只有原文说明其适用情境、主体动作、约束、先后、具体结果或反馈机制时，才进入 P7C。

多个并行情报来源、线索、标准或组成要素应通过 `REFERENCES` 各自关联到共同处理节点，不按教材叙述顺序串成 `PRECEDES` 链；如果只有并列知识关系而没有共同处理节点，则交给基础 KG。

实际到达、提交、移交或状态变化并触发处理的对象、事件或发现应建为 entry，并通过 `PRECEDES` 进入 process。只说明"对某类对象执行动作"时，该对象是适用范围而非先后事件；仅被处理动作参照的对象、线索、输入或标准应建为 auxiliary，并由 process 通过 `REFERENCES` 指向它。对象在教材语句中的语法位置不是判断 entry 的依据——只有对象实际触发处理时才是 entry，静态参照时通过 REFERENCES 入图。

单一路径的 `if/when/unless A，则B` 不是分支，不使用 `DECIDES`；A 可以作为条件 entry 通过 `PRECEDES` 进入 B，并在 edge 的 `condition` 中逐字保留条件。这里的 `PRECEDES` 表示逻辑前提，未必表示钟表式先后。若条件只限定某项 input/standard 何时适用于 process，可以直接写在 `REFERENCES.condition` 中而不另建 entry；这仍是适用范围限定，不是条件分支。只有证据支持至少两个互斥结果时才使用 `P3_branch_routing + DECIDES`；互斥结果可以由明示规则直接给出，也可以由同一标准下的正反实例共同支持，后者必须标记 `llm_inference`。

调查、审计或评估产生的是"发现、分类、报告或结论"，不产生其所揭示的既存违法行为、风险状态或控制缺陷。例如审计揭示长期未被发现的腐败，只产生"发现控制缺陷/识别腐败"的结论，不产生"腐败长期未被发现"这一既存状态——后者是审计揭示的对象，不是审计产生的结果。

相邻句子中的执法措施和司法结果不自动形成 `PRECEDES` 或 `PRODUCES`。冻结、查封、起诉、定罪、监禁和罚款之间只有在原文明示先后、触发或产出关系时才能连接；否则应保留为共同上游调查或执法行动的并列结果，或者拆卡/省略关系。

### 节点级构图示例

"机构必须基于风险偏好调整交易监控、KYC审查并升级"可构为开放式约束关系：

- `process P8_constrained_action`：机构必须调整交易监控、KYC审查并升级处理
- `standard`：机构的风险偏好
- `process --REFERENCES--> standard`（`relation_type=standard_constrains_action`）

这里原文只有规范性要求，节点 label 保留情态（"机构必须调整……"），不写"监控/KYC配置已调整"的完成态，不补造 X7 义务出口。`escalate` 保留为"升级处理"或英文原词。

"不存在自然人受益所有人时，应识别并核实控制人或名义受益所有人"可构为单一条件链：

- `entry E6_change_exception`：不存在自然人受益所有人
- `process P2_execution`：机构识别并核实控制人或名义受益所有人
- `entry --PRECEDES--> process`（`condition=不存在自然人受益所有人`）

原文只明示例外路径时，只表达该例外路径，不反向补造"存在自然人受益所有人"的另一分支。`P3_branch_routing + DECIDES` 只用于原文明示至少两条不同路径的真实分流；只有单一条件应对时，使用条件 entry 进入 process。

以下仅说明通用的"输入处理—标准判断—互斥结果"结构，不是任何特定业务术语的固定模板。若原文说明两个数值输入先被合计，再与适用标准比较，并分别给出达到与未达到标准的不同分类，可以构为：

- `auxiliary input A`：第一个原始数值
- `auxiliary input B`：第二个原始数值
- `process P1_assessment`：合计两个数值
- `auxiliary standard`：原文限定下的适用标准
- `process P3_branch_routing`：合计值是否达到适用标准
- `exit X1_classification`：达到标准时的分类
- `exit X1_classification`：未达到标准时的分类
- `P1 --REFERENCES--> input A`
- `P1 --REFERENCES--> input B`
- `P1 --PRECEDES--> P3`
- `P3 --REFERENCES--> standard`
- `P3 --DECIDES(condition=达到适用标准)--> positive exit`
- `P3 --DECIDES(condition=未达到适用标准)--> negative exit`

只有原文确实支持输入处理、标准应用和两个互斥结果时才能使用该结构。示例中的节点名称、数量和条件都必须按当前 section 证据调整；必须保留原文的适用范围、通常性、可能性和例外限定。

"延期起诉协议要求全面整改，银行因此加强中央监督和合规职能、限制地方业务自主权并减少高风险地区敞口"属于外部命令触发组织纠正措施及配置变化的 P7C 增量链——即使出现在历史案例中，也应提取其制度响应结构，不整段交给 KG。声誉损害可以是同一上游事件的并列后果，但不作为整改动作的触发原因。

案例中，金融机构、FIU、执法机关或监管机关实际执行的检测、综合分析、升级、监控、冻结、查封或整改，可以形成局部 P7C card；犯罪分子的洗钱手法本身仍通常由 KG 承接。将有证据的局部制度响应分别成卡。例如：

- FIU 综合银行 SAR 和跨境活动 → 形成红旗发现
- FIU 升级案件 → 执法机构开展定向监控
- 执法机构协调资产冻结 → 查封数字钱包并瓦解相关公司

上述三条只有在当前 section 分别明示时才可提取。执法措施（冻结/查封）与司法结果（起诉/定罪/监禁/罚款）之间只有原文明示先后或触发关系时才连接；否则保留为共同上游调查或执法行动的并列结果。

当原文说某项重大决定 `often requires justification and approval` 时，process 应表达"主体评估或作出该项决定"，auxiliary standard/input 表达"通常需要理由和批准"，并使用 `process --REFERENCES--> standard/input`。审批要求是执行动作的参照条件，不写成出口。尚在考虑的动作只表达为 process，不写完成态。

"全球组织通常以母国监管政策为基础标准，并根据各东道国法律调整"属于开放式约束关系：将"全球组织通常调整合规政策"建为 process，将母国监管政策和东道国法律分别建为 standard，由 process 通过 `REFERENCES` 指向。静态政策标准是 standard（auxiliary），不是 E7_external_command（entry）。"调整政策"建为 process 后不另建"政策已适配"的同义出口；必须保留 `typically` 的通常性限定。

## card_nature

只能使用：`execution`、`assessment`、`risk_indicator`、`control`。

## flow_node

每个节点必填：`node_id, node_category, node_type, label, evidence_unit_ids, evidence_strength`。

允许类型：

- entry：`E1_event_signal, E2_object_entry, E3_state_threshold, E4_handoff, E5_time_cycle, E6_change_exception, E7_external_command, E8_decision_finding`
- process：`P1_assessment, P2_execution, P3_branch_routing, P4_collection, P5_coordination, P6_feedback, P7_monitoring, P8_constrained_action, P9_planning, P10_sufficiency`
- exit：`X1_classification, X2_product, X3_state_change, X4_handoff, X5_config_change, X6_termination, X7_continuing_obligation`
- auxiliary：`input, standard`

EDD、筛查、监控、调优、审查、报告、批准、拒绝等动作应建为 process，不建为 standard。`X1_classification` 用于分类或判断结论（如"高风险/低风险""可疑/正常"等分类结果），不承载刑罚、冻结或一般后果。`X7_continuing_obligation` 只用于原文明示某个上游动作、决定或协议另外建立了语义独立、具有持续性的义务时——例如监管处罚决定建立了定期的合规报告义务、整改计划建立了持续的监控义务等。P2 节点 label 中已有的规范性义务（must/shall/required to）不另建 X7 节点重复表达。动作本身的"必须执行"不是 X7；"主体必须/应当执行某动作"只写成带情态的 process。

## flow_edge

允许：`PRECEDES, REFERENCES, PRODUCES, DECIDES, FEEDBACK`。

- `PRECEDES`：只用于原文明示顺序、单一条件/触发的逻辑前提，或交换 source 和 target 会违反必要业务功能的先后。共同出现、教材顺序或"通常如此"不足以成边。
- `REFERENCES`：process 指向非时序性的 input 或 standard，表示处理动作参照线索、输入、标准、判断维度或组成要素，不表达先后、产出或条件分支。可选 `condition` 只能限定该参照关系的适用范围。
- `PRODUCES`：process 产生有证据的 exit。exit 必须与 process 是两个语义独立的事实。相关后果、共同结果或抽象目标不通过 PRODUCES 连接。
- `DECIDES`：必须由 `P3_branch_routing` 发出并填写有原文证据的 `condition`，用于真实条件分流。
- `FEEDBACK`：结果或事件触发更新、补充、复核、调优、监控或再次处理。

每条边必填：`edge_id, edge_type, source, target, evidence_unit_ids, derivation`。

可选：`relation_type, condition, source_quote`。新产物不输出边级 `evidence_strength` 或 `review_status`（旧字段仅由兼容校验器读取，不属于当前输出合同）。

限定词表达写入 `label`、`condition`、`source_quote` 或 `review_notes`，不使用 `qualifier` 或 `modality` 字段。

## relation_type

允许：

`clue_supports_identification, mechanism_explains_risk, identification_leads_to_conclusion, conclusion_triggers_response, branch_condition_routes_path, component_assembles_product, standard_constrains_action, result_handoffs_stage, feedback_requests_completion, cycle_requires_monitoring, standard_transmits_requirement, parallel_alternative_no_sequence`。

`relation_type` 回答业务语义，根据端点角色和关系性质选择，不按 `edge_type` 机械映射。`branch_condition_routes_path` 只能用于带 `condition` 的 `DECIDES` 边。证据不足时省略 `relation_type`。

默认省略 `relation_type`。只有业务语义和端点角色完全符合下列约束时才填写，仅使用允许列表中的值：

- `clue_supports_identification`：只能用于 `REFERENCES`，process 指向作为识别线索的 `input`。
- `standard_constrains_action` 或 `standard_transmits_requirement`：只能用于 `REFERENCES`，process 指向 `standard`。
- `component_assembles_product`：只能用于 `REFERENCES`，process 指向作为组成要素的 `input`。
- `identification_leads_to_conclusion`：只能用于 `PRODUCES`，识别/评估 process 产生 `X1_classification` 结论。
- `conclusion_triggers_response`：表示已有发现或分类触发后续 process，不用于"动作产生结果"（那属于 PRODUCES 的通用语义）。
- `branch_condition_routes_path`：只能用于 `DECIDES`。
- `feedback_requests_completion`：只能用于 `FEEDBACK`。
- `result_handoffs_stage`：只能表示 exit 交接到后续 process 的 `PRECEDES`。
- `mechanism_explains_risk`：只能用于合格 P7C 行动链内部的 `PRODUCES`，表示 process 明示产生或解释独立风险结果；普通犯罪机制或一般因果仍由 KG 承接。
- `cycle_requires_monitoring`：只能用于时间周期或复核周期 entry 通过 `PRECEDES` 触发 `P7_monitoring`，且周期与监控要求均有原文证据。
- `parallel_alternative_no_sequence`：只能用于 process 通过 `REFERENCES` 关联作为并列替代输入的 auxiliary；如果只是普通并列列表而没有共同 process，交给 KG 且不成边。

如果一条边只是普通顺序、动作产出、对象进入处理或条件触发，而上面没有完全匹配的语义类型，省略 `relation_type` 是正确结果。

### 边输出前反事实检查

先逐节点、再逐边检查后才能输出：

1. `process label`：逐个对照原文核对主体、动作和情态。原文含 `must/shall/is required to/should/may/might/could/help` 时，label 保留等强度表达——"应当"保持应当，"可能"保持可能，"有助于"保持有助于——不改成无情态的确定动作或完成状态。
2. `PRECEDES`：必须能说明它是时间顺序、单一条件/触发、交接或不可交换的必要功能先后中的哪一种；单一条件/触发必须填写 `condition`。若 source 只是静态适用对象或材料，改为 process 指向 input 的 `REFERENCES`。
3. `PRODUCES`：将 source 和 target 合并成一句话后，如果没有损失独立事实，说明二者只是同义改写，删除 target 和该边。若 target 是执行 source 所需的理由、批准、标准或义务，改为 process 指向 standard/input 的 `REFERENCES`。
4. `REFERENCES`：交换方向后应不符合"处理动作参照输入/标准"的读法。若原文表达的是真实步骤、产出、条件分流或反馈，使用对应的边类型（PRECEDES/PRODUCES/DECIDES/FEEDBACK），不降级为 REFERENCES。

## 候选声明（不是最终审核）

P7C 节点的 `evidence_strength` 为 `explicit`。边的 `derivation` 为 `explicit_text` 或 `llm_inference`。最终审核状态（pending/accepted/rejected）由 P7D 单独保存，P7C 不输出。

- `llm_inference` 只说明边依赖必要功能推理，不等于 P7D 已经接受或拒绝。
- 入口、方向、条件、主体或 KG 增量价值本身不成立时，不输出该 card；没有独立出口不是跳过理由。

每张 card 的 `review_notes` 必填并使用中文，格式为：

`增量命题：A --关系--> B（条件如有）；KG不足：基础KG只能表达什么、无法表达什么有向结构；选项判断：可确认或排除什么选项；LLM推理：列出derivation=llm_inference的边及必要性，若无则写"无"。`

`title`、`label` 和 `source_quote` 可保留英文教材术语或原文关键词，但解释性内容必须使用中文。`source_unit_ids` 必须覆盖该 card 所有节点和边引用的 unit_id。每张 card 至少包含 1 个 node 和 1 条 edge。

## 输出结构

每张 card 必填：
`card_id, section_id, card_nature, title, flow_nodes, flow_edges, source_unit_ids, candidate_status, review_notes`。`candidate_status` 固定为 `candidate`，不是 P7D 审核状态。

顶层必须输出：
`section_id, section_title, coverage_audit, cards, skip_reason`。

顶层结构：

```json
{
  "section_id": "<section_id>",
  "section_title": "<section_title>",
  "coverage_audit": [
    {
      "candidate_id": "cand_001",
      "unit_ids": ["<unit_id>"],
      "proposition": "<候选有向命题>",
      "decision": "p7c_card",
      "card_id": "p7card_<section_id>_001",
      "reason": "<中文增量或KG边界说明>"
    }
  ],
  "cards": [],
  "skip_reason": null
}
```

没有合格 card 时也必须保留已发现候选的 `coverage_audit` 记录，并将其 `decision` 写为 `kg_only`；只有完整扫描后确实没有任何候选命题时，`coverage_audit` 才可以为空。

## 当前 section

section_id: `<section_id>`
section_title: `<section_title>`

base_kg_section_summary:
<BASE_KG_SUMMARY_JSON>

section_text_with_unit_anchors:
<SECTION_TEXT>

allowed_unit_ids:
<ALLOWED_UNIT_IDS>

## 当前section

section_id: `CH08-S05`

section_title: `Private banking and wealth management risks > Special purpose vehicle risks`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "covered_topics": [
    {
      "title_zh": "SPV定义与合法用途",
      "title_en": "SPV Definition and Legitimate Uses",
      "covered_units": [
        {
          "unit_id": "v7u_N000642",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000643",
          "unit_type": "fact",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000644",
          "unit_type": "fact",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000645",
          "unit_type": "fact",
          "kg_role": "illustrates"
        }
      ]
    },
    {
      "title_zh": "SPV金融犯罪风险与红旗信号",
      "title_en": "SPV Financial Crime Risks and Red Flags",
      "covered_units": [
        {
          "unit_id": "v7u_N000646",
          "unit_type": "fact",
          "kg_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N000647",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000650",
          "unit_type": "fact",
          "kg_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000651",
          "unit_type": "fact",
          "kg_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000652",
          "unit_type": "fact",
          "kg_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000653",
          "unit_type": "fact",
          "kg_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000648",
          "unit_type": "fact",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N000649",
          "unit_type": "classification",
          "kg_role": "provides_context"
        }
      ]
    },
    {
      "title_zh": "集合投资工具（PIV）定义与风险",
      "title_en": "Pooled Investment Vehicle (PIV) Definition and Risks",
      "covered_units": [
        {
          "unit_id": "v7u_N000654",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000655",
          "unit_type": "risk_indicator",
          "kg_role": "indicates_risk"
        }
      ]
    },
    {
      "title_zh": "利用SPV和PIV的贸易洗钱",
      "title_en": "Trade-Based Money Laundering Using SPVs and PIVs",
      "covered_units": [
        {
          "unit_id": "v7u_N000656",
          "unit_type": "process",
          "kg_role": "describes_process"
        },
        {
          "unit_id": "v7u_N000657",
          "unit_type": "fact",
          "kg_role": "explains"
        }
      ]
    },
    {
      "title_zh": "强化尽职调查与客户尽职调查要求",
      "title_en": "Enhanced Due Diligence (EDD) and CDD Requirements",
      "covered_units": [
        {
          "unit_id": "v7u_N000658",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000659",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000660",
          "unit_type": "fact",
          "kg_role": "states_consequence"
        }
      ]
    }
  ],
  "covered_relations": [
    {
      "source_title": "SPV定义与合法用途",
      "target_title": "SPV金融犯罪风险与红旗信号",
      "relation_type": "contrasts"
    },
    {
      "source_title": "SPV金融犯罪风险与红旗信号",
      "target_title": "利用SPV和PIV的贸易洗钱",
      "relation_type": "prepares"
    },
    {
      "source_title": "集合投资工具（PIV）定义与风险",
      "target_title": "利用SPV和PIV的贸易洗钱",
      "relation_type": "prepares"
    },
    {
      "source_title": "SPV金融犯罪风险与红旗信号",
      "target_title": "强化尽职调查与客户尽职调查要求",
      "relation_type": "prepares"
    },
    {
      "source_title": "集合投资工具（PIV）定义与风险",
      "target_title": "强化尽职调查与客户尽职调查要求",
      "relation_type": "prepares"
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000642|642] Special purpose vehicles (SPVs) are legal entities created for specific and limited purposes.
ZH: 特殊目的载体（SPV）是为特定有限目的设立的法律实体

[v7u_N000643|643] SPVs can be used in mergers and acquisitions, joint ventures, real estate projects, infrastructure development, and energy projects.
ZH: SPV可用于并购、合资、房地产、基础设施和能源项目

[v7u_N000644|644] SPVs can also be used to manage and protect intellectual property assets including trademarks and copyrights.
ZH: SPV可用于管理和保护知识产权资产

[v7u_N000645|645] SPVs are often used in complex financial transactions and investments such as securities and asset-backed financing.
ZH: SPV常用于复杂金融交易和资产支持融资

[v7u_N000646|646] There are financial crime risks associated with SPVs.
ZH: SPV存在金融犯罪风险

[v7u_N000647|647] SPVs can have complex and opaque structures to disguise the true beneficial ownership.
ZH: SPV可能通过复杂不透明的结构掩盖真实受益所有人

[v7u_N000648|648] SPVs might be used to obscure the source of illicit funds. Criminals layer illicit proceeds through a series of transactions via the SPVs, transferring funds to or from financial institutions. This creates a complex web of
ZH: 犯罪分子通过SPV进行一系列交易来分层非法收益，掩盖资金来源

[v7u_N000649|649] There are several red flags that indicate attempts to disguise illicit funds or conduct fraudulent activities using SPVs. These include:
ZH: 列举利用SPV掩饰非法资金或欺诈活动的红旗信号信号

[v7u_N000650|650] Complex ownership structures involving multiple layers of companies
ZH: 涉及多层公司的复杂所有权结构是红旗信号

[v7u_N000651|651] Lack of transparency
ZH: 缺乏透明度是红旗信号

[v7u_N000652|652] Unclear purpose of the SPV
ZH: SPV目的不明确是红旗信号

[v7u_N000653|653] Criminals might select jurisdictions that have lenient regulatory oversight or tax-friendly environments. This enables them to hide their financial activities and minimize tax liabilities.
ZH: 犯罪分子选择监管宽松或税收优惠的司法管辖区以隐藏活动和避税

[v7u_N000654|654] Pooled investment vehicles (PIVs) are small investments pooled together from a large group of investors.
ZH: 集合投资工具（PIV）是从大量投资者汇集的小额投资

[v7u_N000655|655] PIVs can be used in Ponzi schemes and insider trading.
ZH: PIV可能被用于庞氏骗局和内幕交易

[v7u_N000656|656] Additionally, criminals might engage in trade-based money laundering using SPVs and PIVs. Criminals manipulate trade transactions between SPVs and PIVs by deflating or inflating prices.
ZH: 犯罪分子利用SPV和PIV进行贸易洗钱，操纵交易价格

[v7u_N000657|657] This process enables the movement of illicit funds while disguising it as legitimate trade activity.
ZH: 该过程将非法资金伪装成合法贸易活动进行转移

[v7u_N000658|658] Financial institutions must be vigilant in conducting enhanced due diligence (EDD) on SPVs and PIVs. It is important to ensure these investments comply with CDD regulations such as the Financial Crime Enforcement Network's CDD rule.
ZH: 金融机构必须对SPV和PIV进行强化尽职调查，遵守客户尽职调查规则

[v7u_N000659|659] Financial institutions must identify ultimate beneficial owners and understand the true purpose of these entities.
ZH: 金融机构必须识别最终受益所有人并了解实体真实目的

[v7u_N000660|660] This will help mitigate any potential financial crime risks associated with SPVs.
ZH: 这有助于减轻与SPV相关的金融犯罪风险
```

allowed_unit_ids:

```json
[
  "v7u_N000642",
  "v7u_N000643",
  "v7u_N000644",
  "v7u_N000645",
  "v7u_N000646",
  "v7u_N000647",
  "v7u_N000648",
  "v7u_N000649",
  "v7u_N000650",
  "v7u_N000651",
  "v7u_N000652",
  "v7u_N000653",
  "v7u_N000654",
  "v7u_N000655",
  "v7u_N000656",
  "v7u_N000657",
  "v7u_N000658",
  "v7u_N000659",
  "v7u_N000660"
]
```
