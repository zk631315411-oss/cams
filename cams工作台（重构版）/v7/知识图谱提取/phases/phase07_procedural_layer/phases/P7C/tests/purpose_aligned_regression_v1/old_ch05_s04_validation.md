# P7 Validation Report

card_count: 1
edge_count: 0
bridge_count: 0
evidence_scope: D:/守正公司工作区/cams考试/cams工作台（重构版）/v7/知识图谱提取/phases/phase07_procedural_layer/phases/P7B/section_packages/CH05-S04/task.json
expected_section_id: CH05-S04
error_count: 6

## Errors

- p7c_CH05_S04_001: flow_node #4 invalid evidence_strength 'functional_dependency'
- p7c_CH05_S04_001: functional_dependency edges require review_status 'needs_review': e02
- p7c_CH05_S04_001: review_notes must identify functional_dependency edges under 'LLM推理'
- p7c_CH05_S04_001: isolated flow_node 'n01' is not referenced by any edge
- p7c_CH05_S04_001: flow graph has 2 disconnected components
- p7c_CH05_S04_001: no directed entry -> process -> exit path
