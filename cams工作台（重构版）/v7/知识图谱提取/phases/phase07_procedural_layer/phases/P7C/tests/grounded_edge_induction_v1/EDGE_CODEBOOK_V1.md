# Grounded Flow Edge Codebook v1

> **状态**：本 CODEBOOK 归纳的 12 种关系类型已纳入 P7A schema，作为 `flow_edge.relation_type` 的正式取值。`edge_type`（PRECEDES/REFERENCES/PRODUCES/DECIDES/FEEDBACK）保留作为渲染类型。两者的映射关系见第 33-46 行。

## 核心判断

`edge_type` 主要表达通用流程图结构；本轮归纳出的关系类型主要表达考试推理图中的“为什么相连”。二者可以共存：

```text
edge_type      = 图结构/运行关系
relation_type  = 考试推理/业务语义关系
```

本文件先给出候选 `relation_type`。是否纳入 P7A schema，后续再决定。

## 候选关系类型

| 代码 | relation_type | 中文名 | 定义 | 典型来源 |
|---|---|---|---|---|
| R1 | clue_supports_identification | 线索支持识别 | 异常、红旗、事实线索支持考生识别风险、可疑性或高风险模式 | CH11-S05, CH03-S06, CH17-S02 |
| R2 | mechanism_explains_risk | 机制解释风险 | 作案机制、结构安排或产品特征解释为什么存在洗钱/恐融风险 | CH14-S02, CH08-S03, CH13-S01 |
| R3 | identification_leads_to_conclusion | 识别导向结论 | 识别或评估结果导向风险分类、可疑性、充分性或适宜性结论 | CH47-S08, CH01-S02 |
| R4 | conclusion_triggers_response | 结论触发应对 | 风险、可疑、缺陷或合规结论触发加强监控、升级、报告、补救或拒绝等要求 | CH11-S05, CH47-S16, CH49-S12 |
| R5 | branch_condition_routes_path | 分支条件路由 | 判断条件决定进入不同分支、期限、升级或处置路径 | CH47-S16, CH49-S12 |
| R6 | component_assembles_product | 组件装配产物 | 信息字段、证据、叙述组件或记录要素共同构成正式产物 | CH49-S04 |
| R7 | standard_constrains_action | 标准约束行动 | 法律、保密、相称性、准确性、监管期限等标准限定动作如何执行 | CH49-S12, CH47-S16, CH20-S05 |
| R8 | result_handoffs_stage | 结果交接下游 | 当前处理结果成为下一角色、层级、系统或外部机构继续处理的输入 | CH47-S08, CH01-S02, CH03-S07 |
| R9 | feedback_requests_completion | 反馈要求补充 | 复核问题、缺失信息或叙述不足要求补充研究、修订或重新处理 | CH47-S16 |
| R10 | cycle_requires_monitoring | 周期/持续监控 | 周期、持续义务、后评估或 ongoing monitoring 关系要求复核或继续观察 | CH19-S07, CH49-S16 |
| R11 | standard_transmits_requirement | 标准传导要求 | 国际标准、监管原则、指南或评估结果传导为辖区或机构控制要求 | CH19-S01, CH20-S05, CH20-S06, CH19-S07 |
| R12 | parallel_alternative_no_sequence | 并列替代非时序 | 多个 typology、标准、组件或案例点互为并列，不应强制串成时间先后边 | CH03-S06, CH20-S05, CH13-S01 |

## 与 edge_type 的建议映射

| relation_type | 常见 edge_type 映射 | 说明 |
|---|---|---|
| R1 clue_supports_identification | REFERENCES 或 PRECEDES | 若线索作为判断依据，偏 REFERENCES；若图需要主链，可用 PRECEDES |
| R2 mechanism_explains_risk | PRECEDES | 表示机制说明导向风险理解，不是严格时间先后 |
| R3 identification_leads_to_conclusion | PRODUCES 或 PRECEDES | 评估/识别产生结论时偏 PRODUCES |
| R4 conclusion_triggers_response | PRECEDES | 结论触发后续处置 |
| R5 branch_condition_routes_path | DECIDES | 必须有 condition |
| R6 component_assembles_product | REFERENCES 或 PRODUCES | 处理节点参照组件，或装配动作产生产物 |
| R7 standard_constrains_action | REFERENCES | 处理节点参照标准、法律或约束，且行动受到其限制 |
| R8 result_handoffs_stage | PRECEDES | 结果进入下一阶段 |
| R9 feedback_requests_completion | FEEDBACK 或 PRECEDES | 若更新材料/产物，用 FEEDBACK；若回到补充动作，用 PRECEDES |
| R10 cycle_requires_monitoring | FEEDBACK 或 PRECEDES | 持续/周期关系视图结构决定 |
| R11 standard_transmits_requirement | PRECEDES 或 REFERENCES | 标准作为外部依据时偏 REFERENCES，作为传导链时偏 PRECEDES |
| R12 parallel_alternative_no_sequence | no_edge 或 REFERENCES | 主要作用是禁止误用 PRECEDES |

## 初步建议

工程方案是区分结构边与业务语义：

```json
{
  "edge_type": "PRECEDES",
  "relation_type": "clue_supports_identification"
}
```

其中 `edge_type` 保证现有渲染和校验可运行，`relation_type` 承载考试推理语义。



