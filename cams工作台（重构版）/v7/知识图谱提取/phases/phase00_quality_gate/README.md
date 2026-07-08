# Phase 00 输入门禁

Phase 00 是 v7 知识图谱流程的第一道入口。可以把它理解成“安检”：它不建图，不识别 core_point，不判断 unit 在知识点中的角色，只判断原始冻结知识单元能不能进入后续 KG 流程。

## 它在流程里的位置

当前 KG 主线是：

```text
P0 输入门禁
  -> P1 章/节/unit 索引
  -> P2 小节内 core_point 与 unit 归属边
  -> P3 同章小节间 core_point 关系
  -> P4 跨章 core_point 关系
  -> P5 术语、别名、缩写检索辅助索引
  -> P6 KG 总装、阅读视图、验收报告
```

P0 只负责第一步：把 v7 的 frozen units 转成后续阶段可使用的 `eligible_units` 输入池，并把不合格的 unit 放进 `blocked_units`。

## 输入文件

当前脚本实际读取一个输入文件：

```text
../../work/base_units/units/v7_bilingual_units.json
```

这个文件是 v7 冻结后的双语知识单元主文件。每个 unit 通常包含：

```text
unit_id
unit_order
unit_status
chapter
heading_context
type / unit_type
evidence_status
can_be_direct_evidence
knowledge_zh / knowledge_en / zh_display_text
en_quote
terms
pdf_page / printed_page / page_span / printed_page_span
risk_flags
```

目录中还有一个上游文件：

```text
../../work/base_units/units/unit_freeze_manifest.json
```

注意：当前 P0 脚本还没有读取 `unit_freeze_manifest.json`。如果后续要把冻结清单校验纳入 P0，需要单独补实现。

## 它做什么处理

P0 对输入文件中的每个 unit 做四类处理。

第一，按 `unit_order` 排序。

这样后续输出保持教材顺序，P1 可以直接基于顺序建立章节和小节索引。

第二，检查重复 `unit_id`。

如果同一个 `unit_id` 出现多次，相关 unit 会被阻断，原因是：

```text
duplicate_unit_id
```

第三，执行硬门禁检查。

命中以下任一条件，unit 会进入 `blocked_units.jsonl`：

```text
unit_id 缺失或不符合正式格式 v7u_N000001
unit_id 重复
unit_status 不是 frozen
缺少 chapter
缺少 unit_order
非 context 类型缺少 en_quote
risk_flags 包含 unit_too_broad
risk_flags 包含 sentence_group_conflict
risk_flags 包含 knowledge_needs_review
```

其中正式 ID 格式由脚本里的正则控制：

```text
^v7u_N\d{6}$
```

也就是合法 ID 应该类似：

```text
v7u_N000001
v7u_N000002
v7u_N004973
```

第四，生成 P0 标准记录。

P0 不把原始 unit 的所有字段原样复制出来，而是裁剪成 KG 后续阶段需要的基础字段。当前 `eligible_units.jsonl` 每条记录保留：

```text
unit_id
unit_order
chapter
heading_context
type
unit_type
evidence_status
can_be_direct_evidence
knowledge_zh
knowledge_en
zh_display_text
en_quote
terms
pdf_page
printed_page
page_span
printed_page_span
risk_flags
phase0_status
```

如果 unit 被阻断，还会额外带：

```text
blocked_reasons
```

## 它不做什么

P0 的边界很重要。它不做以下事情：

```text
不修改 frozen unit 源文件
不生成 chapter_id
不生成 section_id
不建立 章 -> 节 -> unit 索引
不识别 core_point
不判断 unit 是 center、member、example、risk 还是 measure
不生成图谱边
不做跨章关系
```

这些工作分别属于 P1、P2、P3 之后的阶段。

## 输出产物

P0 输出三个文件。

```text
outputs/eligible_units.jsonl
outputs/blocked_units.jsonl
reports/unit_quality_report.md
```

### `outputs/eligible_units.jsonl`

这是后续 KG 流程的正式输入池。

特点：

```text
JSONL 格式，一行一个 unit
按 unit_order 排序
每条记录都有 phase0_status: eligible
只保留后续 KG 需要的基础字段
保留定位字段：chapter / heading_context / page
保留展示字段：knowledge_zh / knowledge_en / zh_display_text / en_quote
保留证据字段：evidence_status / can_be_direct_evidence
保留风险字段：risk_flags
不包含 core_point 或角色判断字段
```

### `outputs/blocked_units.jsonl`

这是被 P0 阻断的 unit 清单。

特点：

```text
JSONL 格式，一行一个 blocked unit
每条记录都有 phase0_status: blocked
每条记录都有 blocked_reasons
当前最新运行结果为空
```

### `reports/unit_quality_report.md`

这是给人看的质量报告。

报告会汇总：

```text
输入 unit 总数
eligible unit 数
blocked unit 数
unit type 分布
risk flag 分布
全书 chapter 顺序
每章 eligible unit 数
每章页码范围
每章第一个 unit_id
如果存在 blocked unit，会列出 blocked samples
```

## 当前运行结果

最新一次运行结果：

```text
input_units: 4973
eligible_units: 4973
blocked_units: 0
```

也就是说，当前 v7 frozen unit 全部通过 P0 门禁，没有 unit 被阻断。

## 运行方式

在 KG 根目录下可以直接运行：

```powershell
python phases/phase00_quality_gate/scripts/phase0_quality_gate.py
```

也可以通过 P0+P1 联合脚本运行：

```powershell
phases/phase01_chapter_index/scripts/run_phase0_phase1.ps1
```

P0 脚本支持指定输入和输出目录：

```powershell
python phases/phase00_quality_gate/scripts/phase0_quality_gate.py `
  --units ../../work/base_units/units/v7_bilingual_units.json `
  --out-dir phases/phase00_quality_gate/outputs
```

## 新人阅读建议

第一次看 P0 时，按这个顺序读：

```text
1. README.md：先理解 P0 只做输入门禁
2. reports/unit_quality_report.md：看本次运行总体结果
3. outputs/eligible_units.jsonl：看一两条 eligible unit 长什么样
4. scripts/phase0_quality_gate.py：再看具体检查规则
```

不要把 P0 理解成知识图谱抽取阶段。P0 只是把原始 frozen units 整理成干净、可追溯、可继续处理的 KG 输入池。
