# P2C section core_point relations v1

You are helping build Phase 2C for a CAMS v7 textbook knowledge graph.

Task: For one section, identify useful relations between core_points inside the same section.

Definitions:

- `core_point`: a review-outline node already accepted by P2A/P2A_review.
- `unit_edges_summary`: P2B semantic edges from each core_point to its units, provided only to help understand the CP boundary.
- `relation`: a section-local relation from one core_point to another core_point.

Hard rules:

1. Work only inside the provided `section_id`.
2. Use only provided `core_point_id` values.
3. Do not create, split, merge, rename, or delete core_points.
4. Do not create core_point -> unit edges.
5. Do not create cross-section or cross-chapter relations.
6. Output only strong relations useful for a review mind map.
7. Do not connect every adjacent pair by default.
8. Do not output all possible `parallels` pairs. If a `contains` relation already gives the structure, avoid redundant `parallels`.
9. If a CP is mainly a case, example, scenario, or concrete illustration, prefer `illustrates`; do not also output a redundant `contains` relation between the same two CPs in either direction.
10. It is valid to output an empty `core_point_relations` array.
11. Return exactly one JSON object. No markdown.

Allowed relation_type values:

```text
contains
illustrates
prepares
parallels
contrasts
```

Relation definitions and direction:

- `contains`: source is an upper topic, framework, class, or overview; target is a sub-concept, subtype, component, or elaboration.
- `illustrates`: source is a case, example, scenario, or concrete illustration of target.
- `prepares`: source provides prerequisite definition, background, foundation, or setup for target. Direction must be from the more basic / earlier / foundational CP to the later expansion or application CP.
- `parallels`: source and target are same-level parallel topics. Use textbook order for direction.
- `contrasts`: source and target have an explicit contrast, distinction, legal/illegal difference, or comparison. Use textbook order for direction.

Relation priority:

1. If one CP is explicitly a case/example/scenario and the other CP is the concept it demonstrates, use only `illustrates` from example CP to concept CP.
2. Do not add `contains` for that same example-concept pair, even if the example belongs under the broader concept in an outline.
3. Use `contains` for true topic-to-subtopic, class-to-subclass, or framework-to-component relations, not for concrete examples.

Examples:

Example 1: total-to-parts structure.

Input CPs:

```text
CP1: 主要风险类型：运营、法律、集中度、声誉
CP2: 运营风险：定义与监管挑战
CP3: 法律风险：来源、后果及AFC保护
CP4: 集中度风险：过度敞口、缓解与管理
CP5: 声誉风险：特征与信任因素
```

Good output:

```json
[
  {"source_core_point_id":"CP1","target_core_point_id":"CP2","relation_type":"contains"},
  {"source_core_point_id":"CP1","target_core_point_id":"CP3","relation_type":"contains"},
  {"source_core_point_id":"CP1","target_core_point_id":"CP4","relation_type":"contains"},
  {"source_core_point_id":"CP1","target_core_point_id":"CP5","relation_type":"contains"}
]
```

Do not additionally output all sibling pairs unless the section lacks an explicit parent CP.

Example 2: mixed key takeaways.

Input CPs:

```text
CP1: 避税与逃税
CP2: 激进避税
CP3: 逃税作为洗钱的上游犯罪
CP4: 监控客户活动以发现逃税指标
CP5: 共同申报准则（CRS）
CP6: 欺诈定义与一般特征
CP7: 欺诈三角
CP8: 常见欺诈红旗信号
```

Good output:

```json
[
  {"source_core_point_id":"CP1","target_core_point_id":"CP2","relation_type":"contains"},
  {"source_core_point_id":"CP1","target_core_point_id":"CP3","relation_type":"prepares"},
  {"source_core_point_id":"CP3","target_core_point_id":"CP4","relation_type":"prepares"},
  {"source_core_point_id":"CP6","target_core_point_id":"CP7","relation_type":"contains"},
  {"source_core_point_id":"CP6","target_core_point_id":"CP8","relation_type":"contains"}
]
```

Do not force relations between tax CPs and fraud CPs.

Example 3: case relation.

Input CPs:

```text
CP1: 制裁规避手段与处罚
CP2: 案例研究：Alexei Komarov的制裁规避计划
```

Good output:

```json
[
  {"source_core_point_id":"CP2","target_core_point_id":"CP1","relation_type":"illustrates"}
]
```

Example 4: prepares direction.

Input CPs:

```text
CP1: 网络犯罪的定义与范围
CP2: 基于信任的网络犯罪手段
CP3: 网络犯罪与洗钱和恐怖融资的关联
```

Good output:

```json
[
  {"source_core_point_id":"CP1","target_core_point_id":"CP2","relation_type":"prepares"},
  {"source_core_point_id":"CP1","target_core_point_id":"CP3","relation_type":"prepares"}
]
```

Bad output:

```json
[
  {"source_core_point_id":"CP3","target_core_point_id":"CP1","relation_type":"prepares"}
]
```

Reason: a later application or association topic must not prepare an earlier definition. If the direction is uncertain, omit the relation.

Example 5: examples are not contains.

Input CPs:

```text
CP1: 网络犯罪的定义与范围
CP2: 网络犯罪的示例
```

Good output:

```json
[
  {"source_core_point_id":"CP2","target_core_point_id":"CP1","relation_type":"illustrates"}
]
```

Bad output:

```json
[
  {"source_core_point_id":"CP1","target_core_point_id":"CP2","relation_type":"contains"},
  {"source_core_point_id":"CP2","target_core_point_id":"CP1","relation_type":"illustrates"}
]
```

Reason: the second relation already captures the useful review relation. The `contains` edge is redundant for a concrete examples CP.

Return shape:

```json
{
  "section_id": "CH05-S04",
  "core_point_relations": [
    {
      "relation_id": "p2c_rel_CH05_S04_001_002",
      "source_core_point_id": "cp_CH05_S04_001",
      "target_core_point_id": "cp_CH05_S04_002",
      "relation_type": "contains",
      "reason": "CP1 lists the main risk types, and CP2 explains operational risk as one of those types."
    }
  ],
  "review_items": []
}
```
