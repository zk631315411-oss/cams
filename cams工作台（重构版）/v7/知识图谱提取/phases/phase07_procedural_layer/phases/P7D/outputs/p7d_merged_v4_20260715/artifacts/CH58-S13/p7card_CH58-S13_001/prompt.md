# P7D Flow Edge Evidence Review Prompt v1

## 角色与边界

你是P7D独立边级证据审核器。P7C已经生成候选card；你的任务是逐条审核card中的现有`flow_edge`，不是重新抽取card。

不得新增、删除、改写、拆分或连接card、node或edge。不得修改P7C正本。不得读取或假设具体题目、选项、参考答案或其他section内容。只输出严格JSON，不输出Markdown或解释。

`section_text_with_unit_anchors`是唯一事实证据。只能引用`allowed_unit_ids`中的unit_id。P7C card中的节点、label、edge、condition和relation_type都只是待审核声明，不能反过来充当证据。

输入card已移除P7C声明的`derivation`、`source_quote`、`review_notes`、`candidate_status`和旧审核字段，避免影响独立判断。你必须仅根据当前section原文独立判断每条边的`derivation`（explicit_text/llm_inference/unsupported）和`llm_recommendation`（accepted/pending/rejected）。最终`review_status`由审核结果独立决定，不依赖P7C声明。

## 逐边审核问题

对每条现有edge分别检查：

1. `source_node_support`：source节点表达的主体、对象、动作、状态或结论是否有当前section依据。
2. `target_node_support`：target节点是否有当前section依据。
3. `direction_support`：原文是否支持source到target的方向；反向是否同样可能。
4. `condition_support`：edge的condition是否被原文明示支持。若原文关系本身是`if/when/unless`等条件关系而edge遗漏`condition`，填`unsupported`；只有关系确实无条件时，缺少condition才填`not_applicable`。
5. `qualifier_support`：must、should、may、might、could、often、only、not、unless、potentially等限定是否被保留，是否被强化或弱化；edge使用`aimed_to`、`may_lead_to`、`helps_achieve`时，分别核对原文是否明确表达“旨在/以期”“可能产生”“有助于”。没有相关限定时可以填`not_applicable`。
6. `parallel_or_correlation_check`：是否把并列来源、共同结果、相关关系、教材叙述顺序或一般主题关系错误写成`PRECEDES`、`PRODUCES`、`DECIDES`或`FEEDBACK`。

每项`status`只能是：`supported, pending, unsupported, not_applicable`。每项必须用中文填写`reason`。

`evidence_unit_ids`与`source_quotes`必须覆盖该边判断依赖的全部实质证据。若方向、condition或限定词需要把规则、标准与一个或多个实例联合起来才能成立，必须同时引用这些组成unit；只引用结果实例、却遗漏提供阈值或条件的unit，不构成完整审核记录。

## edge_type审核口径

- `PRECEDES`：只有原文明示顺序，或交换方向会违反唯一必要功能依赖时才成立。单一路径的`if/when/unless A，则B`中，A是B的逻辑前提，也属于必要功能先后，不要求钟表式时间顺序；应同时检查edge的`condition`是否保留原文条件。共同出现和教材顺序不成立。**原文用 because/due to/as a reason/for this reason 等表达理由或判断依据时，该关系不是流程先后，不得接受为 PRECEDES。** 应判断是否更适合 REFERENCES（判断依据→处理动作，按 REFERENCES 的正本方向即 process→auxiliary，人读反向为 auxiliary→process）。
- `REFERENCES`：只表达process对非时序输入、线索、标准或判断维度的参照，不表达先后、产出或条件分支。若带`condition`，它只能限定该参照关系的适用范围，并必须有原文证据。
- `PRODUCES`：process必须产生target结果；揭示既存状态不等于产生该状态。
- `DECIDES`：必须存在真实条件分流，condition有原文证据；单一条件应对不自动构成分支。
- `FEEDBACK`：结果或事件必须触发复核、补充、更新、调优、监控或再次处理。

## 语义压缩与隐藏条件检查

审核每条边时，不仅检查edge对象中的`condition`，还要检查source和target label是否把关系成立所需的条件、标准或判断结果藏在节点文字中。

如果target只有在某项标准、阈值、充分性、批准状态或判断结论成立时才会出现，而候选边使用无condition的`PRODUCES`直接连接到target，不能把`condition_support`标为`not_applicable`。应判断该关系是否遗漏条件；条件不可由现有边可靠表达时，相关检查为`unsupported`，不得因为target label中写了“达到、通过、满足、未达到、否则”等词就视为已经保留条件。

当同一判断标准下存在两个或以上互斥结果时，检查候选图是否错误地用单一泛化exit或无条件`PRODUCES`压扁分流。P7D不负责补画decision或分支，但应拒绝语义不成立的现有边。原文只支持单一路径时，也不得反向要求P7C补造另一分支。

输入处理与标准判断是不同语义操作：原始数据、材料或组成要素应被实际处理它们的process参照；标准、阈值、政策或判断维度应被实际应用它们的判断process参照。如果一个宽泛process label同时声称收集/计算输入并完成条件分类，必须分别检查每条边能否由原文支持，不能用宽泛节点文字替代边的方向与条件证据。

一般规则与同一标准下的正反实例可以共同支持候选分支，但从多个unit或实例归纳出一般关系时，`derivation`通常应为`llm_inference`。孤立实例不得自动推广成一般分流规则。

相邻句中的冻结、查封、调查、起诉、定罪、监禁和罚款不自动形成单链。多个线索、标准、情报来源或共同结果不因排列顺序形成先后边。

`REFERENCES`不要求原文必须出现字面上的“参照/使用”。当相邻句围绕同一对象，原文明示process正在设定、应用或比较某项参数，而target恰好给出该参数的基准或风险调整值，且不存在其他合理连接时，可以审核为`llm_inference`而不是直接判为`unsupported`。若只是同主题并列或存在多种合理连接，仍应拒绝或待审。

`PRODUCES`可以表达原文明示的限定性控制效果，例如`help mitigate/may reduce/can improve`，前提是target label完整保留“有助于/可能/可以”等情态，且`qualifier_support`通过。`PRODUCES`这个结构类型本身不把限定性效果强化为必然完成状态；若target删掉限定词或写成“已经降低/已经消除”，应判为`unsupported`。

当edge填写`qualifier=aimed_to/may_lead_to/helps_achieve`时，必须审核该限定是否作用于当前source→target关系，而不是只在附近出现。限定有原文依据且作用域正确时可通过；缺失、错配或把目的/可能性强化为已实现结果时应判为`unsupported`。

如果process与target只是同一谓词的主动式/被动式或完成态改写，例如“机构识别UBO”与“UBO被识别”，二者不是独立事实，`PRODUCES`应判为`unsupported`。如果target是执行source所需的理由、批准、标准或义务，它约束source而不是由source产生，`PRODUCES`也应判为`unsupported`。

当target为`X7_continuing_obligation`时，必须确认原文明示source动作、决定或协议新建立了一个语义独立的持续义务。若target只是把source中的“必须/应当执行某动作”复制成义务出口，`PRODUCES`应判为`unsupported`。

## derivation与建议

`derivation`只描述这条边如何由证据得到，不能用来代替审核结论：

- `explicit_text`：原文明示关系及方向。
- `llm_inference`：两端均有证据，但关系或方向依赖必要功能推理。
- `unsupported`：至少一端、关系、方向或条件缺少依据。

`llm_recommendation`只能是：

- `accepted`：所有必要检查均有充分支持。
- `pending`：存在歧义，或关系依赖必要功能推理，需要人工判断。
- `rejected`：至少一个关键检查明确不成立。

不要为了保留card而接受边。也不要因为边来自P7C或标为`explicit`就默认接受。

## 输出合同

必须覆盖输入card中的每一条edge，edge_id不得遗漏、增加或重复。顺序与输入保持一致。

```json
{
  "section_id": "CH58-S13",
  "card_id": "<card_id>",
  "edge_reviews": [
    {
      "edge_id": "<existing edge_id>",
      "derivation": "explicit_text",
      "llm_recommendation": "accepted",
      "checks": {
        "source_node_support": {"status": "supported", "reason": "<中文>"},
        "target_node_support": {"status": "supported", "reason": "<中文>"},
        "direction_support": {"status": "supported", "reason": "<中文>"},
        "condition_support": {"status": "not_applicable", "reason": "该边没有condition。"},
        "qualifier_support": {"status": "supported", "reason": "<中文>"},
        "parallel_or_correlation_check": {"status": "supported", "reason": "<中文>"}
      },
      "evidence_unit_ids": ["<allowed unit id>"],
      "source_quotes": ["<当前section原文短引>"],
      "reason": "<中文总判断>"
    }
  ]
}
```

## 当前section与card

section_id: `CH58-S13`
section_title: `Data as an input for solutions > Data preparation`

section_text_with_unit_anchors:
[v7u_N004786|4786] Data preparation is a process that includes collecting, cleaning, transforming, and preparing data for analysis.
ZH: 数据准备包括收集、清洗、转换和准备数据以供分析

[v7u_N004787|4787] Clean, well-structured data enhances system robustness by reducing errors, speeding up processing, and optimizing system performance.
ZH: 干净、结构良好的数据通过减少错误、加快处理速度来增强系统稳健性

[v7u_N004788|4788] When done correctly, data preparation can have a direct impact on the business, as data quality ensures accuracy, consistency, reliability, and compliance with regulatory requirements. Thorough data preparation builds a strong foundation for detecting financial crime and making informed decisions.
ZH: 正确的数据准备直接影响业务，确保准确性、一致性、可靠性和合规性

[v7u_N004789|4789] Although data engineers typically perform data preparation, it is important that members of the AFC team understand each step in the process.
ZH: 金融犯罪防控团队成员应理解数据准备的每个步骤

[v7u_N004790|4790] Data extraction is the process of gathering data from various sources such as customer databases and third-party providers.
ZH: 数据提取是从客户数据库和第三方提供商等来源收集数据的过程

[v7u_N004791|4791] The methods used to collect data include application programming interface calls, extract, transform, load processes, and network traffic analysis.
ZH: 数据收集方法包括API调用、ETL流程和网络流量分析

[v7u_N004792|4792] The more comprehensive the data, the better the chance of identifying suspicious patterns.
ZH: 数据越全面，识别可疑模式的机会越大

[v7u_N004793|4793] Data transformation involves cleaning and converting raw data to improve its quality and usability.
ZH: 数据转换涉及清洗和转换原始数据以提高其质量和可用性

[v7u_N004794|4794] This step removes duplicates, corrects errors, handles missing values, and ensures consistency across the dataset.
ZH: 数据转换步骤包括去重、纠错、处理缺失值和确保一致性

[v7u_N004795|4795] For example, inconsistencies in date formats or currency types could lead to incorrect analyses.
ZH: 日期格式或货币类型不一致可能导致错误分析

[v7u_N004796|4796] Data transformation also converts data into a format suitable for analysis.
ZH: 数据转换还将数据转换为适合分析的格式

[v7u_N004797|4797] This includes normalizing and encoding data, and creating features, such as aggregated data, frequencies, sums, averages, and standard deviations.
ZH: 数据转换包括归一化、编码和创建特征（如聚合数据、频率、总和、平均值和标准差）

[v7u_N004798|4798] Data loading stores the processed data in a database or data warehouse.
ZH: 数据加载将处理后的数据存储到数据库或数据仓库中

[v7u_N004799|4799] Data mining and data matching take the data that has been extracted, prepared, and loaded and apply various algorithms and analytical techniques to it. The purpose is to detect anomalies and recognize patterns and correlations indicative of suspicious behavior.
ZH: 数据挖掘和数据匹配对提取、准备和加载的数据应用算法和分析技术，以检测异常和识别可疑行为模式

[v7u_N004800|4800] Accurate and consistent data makes AFC systems more robust, impactful, and effective, leading to reliable patterns and model classifications.
ZH: 准确一致的数据使金融犯罪防控系统更稳健、有效，产生可靠的模式和模型分类

allowed_unit_ids:
[
  "v7u_N004786",
  "v7u_N004787",
  "v7u_N004788",
  "v7u_N004789",
  "v7u_N004790",
  "v7u_N004791",
  "v7u_N004792",
  "v7u_N004793",
  "v7u_N004794",
  "v7u_N004795",
  "v7u_N004796",
  "v7u_N004797",
  "v7u_N004798",
  "v7u_N004799",
  "v7u_N004800"
]

p7c_card_under_review:
{
  "card_id": "p7card_CH58-S13_001",
  "section_id": "CH58-S13",
  "title": "对已准备数据应用算法以检测异常和识别可疑模式",
  "card_nature": "execution",
  "source_unit_ids": [
    "v7u_N004799"
  ],
  "flow_nodes": [
    {
      "node_id": "e001",
      "node_category": "auxiliary",
      "node_type": "input",
      "label": "已提取、准备和加载的数据",
      "evidence_unit_ids": [
        "v7u_N004799"
      ]
    },
    {
      "node_id": "e002",
      "node_category": "process",
      "node_type": "P2_execution",
      "label": "应用各种算法和分析技术",
      "evidence_unit_ids": [
        "v7u_N004799"
      ]
    },
    {
      "node_id": "e003",
      "node_category": "exit",
      "node_type": "X1_classification",
      "label": "检测异常",
      "evidence_unit_ids": [
        "v7u_N004799"
      ]
    },
    {
      "node_id": "e004",
      "node_category": "exit",
      "node_type": "X1_classification",
      "label": "识别指示可疑行为的模式和相关性",
      "evidence_unit_ids": [
        "v7u_N004799"
      ]
    }
  ],
  "flow_edges": [
    {
      "edge_id": "r001",
      "edge_type": "REFERENCES",
      "source": "e002",
      "target": "e001",
      "evidence_unit_ids": [
        "v7u_N004799"
      ]
    },
    {
      "edge_id": "r002",
      "edge_type": "PRODUCES",
      "source": "e002",
      "target": "e003",
      "qualifier": "aimed_to",
      "evidence_unit_ids": [
        "v7u_N004799"
      ]
    },
    {
      "edge_id": "r003",
      "edge_type": "PRODUCES",
      "source": "e002",
      "target": "e004",
      "qualifier": "aimed_to",
      "evidence_unit_ids": [
        "v7u_N004799"
      ]
    }
  ]
}
