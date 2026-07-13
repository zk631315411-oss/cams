# P7C Grounded Edge Induction v1

## 目的

在 `flow_node` 已改为 E/P/X 语义编码后，本轮用扎根理论方式归纳 `flow_edge` 关系类型。目标不是直接修改 schema，而是先回答：

```text
当节点已经能表达入口、处理、出口时，节点之间真实需要哪些边关系？
```

## 方法

1. 选取 20 个 section，覆盖严格流程、案例推理、红旗/typology、监管标准传导和边界/负例。
2. 先按现有 E/P/X 节点编码理解每个 section 的候选节点。
3. 不预设旧 `PRECEDES / USES / PRODUCES / DECIDES / FEEDBACK`，而是记录节点之间的自然语言关系。
4. 对自然语言关系做持续比较，归纳候选 `flow_edge` 语义类型。
5. 连续多个异质 section 不再出现新一级边关系时，判断本轮达到初步饱和。

## 样本

```text
严格流程：
CH47-S08, CH49-S04, CH49-S12, CH47-S16

案例推理：
CH11-S05, CH14-S02, CH01-S02, CH03-S07

红旗/typology：
CH03-S06, CH17-S02, CH08-S03, CH13-S01

监管/标准传导：
CH19-S01, CH20-S05, CH20-S06, CH19-S07

边界/负例：
CH13-S03, CH20-S08, CH49-S16, CH01-S01
```

## 产物

```text
EDGE_OPEN_CODING_MATRIX.md  section 级开放编码和候选边
EDGE_CODEBOOK_V1.md         候选 flow_edge 语义类型
EDGE_SATURATION_LOG.md      新增关系类型和饱和判断
```

