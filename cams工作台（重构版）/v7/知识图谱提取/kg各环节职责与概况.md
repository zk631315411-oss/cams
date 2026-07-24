# v7 KG 各环节职责与概况

本文记录 v7 知识图谱提取各阶段的主线职责。当前主口径是：

```text
v7 KG = 以章节为主线的教材复习思维导图
```

核心层级：

```text
章 -> section -> core_point -> unit
```

这里的 `section` 指 P1 生成的教材小节片段，由 `section_id` 稳定标识，例如 `CH02-S05`。中文可称为“节”或“小节片段”。

## Phase 0：输入门禁

职责：读取正式冻结知识单元，检查 ID、状态、基本字段和阻断风险，只放行可参与当前 KG 构建的 eligible units。

输入：v7 冻结知识单元源文件（双语 unit 主文件 + 冻结清单）

输出：
- eligible units：通过门禁的 unit 池，供后续阶段使用
- blocked units：被阻断的 unit 清单
- 质量报告：输入总数、eligible/blocked 分布、风险标记统计

边界：

- 不修改 frozen unit。
- 不生成章、节、core point 或 edge。
- 只做进入 KG 的硬门槛。

## Phase 1：章节/小节索引

职责：把 P0 放行的 eligible units 按教材章节、heading、页码和 unit 顺序组织起来，建立 unit 与章、节的索引归属关系。

输入：P0 放行的 eligible units

输出：章 -> section -> unit 索引（全书 + 章节范围可控的样本）

核心产出：
- section_id：章内稳定小节片段 ID（如 CH02-S05）
- section_order：章内小节片段顺序
- section_title：heading_context 拼接的标题路径

实际完成的关系：

```text
章 -> section -> unit
```

当前实现说明：

- `chapter_id` 是全书章节顺序编号，例如 `CH01`。
- `section_id` 是章内稳定小节片段 ID，例如 `CH02-S05`。
- `section_order` 是章内小节片段顺序。
- `section_title` 来自 `heading_context` 拼接。
- P1 是索引层，不生成 core point，不判断语义关系，不生成图谱边。

边界：

- 不改 frozen unit。
- 不做 core point 合并、拆分或命名。
- 不做语义关系判断。

## Phase 2：小节内 core point、unit 归属边与同 section CP 关系

状态：P2A/P2B/P2C 已进入当前主线；P2C 正式全量输出已物化。

职责：在 P1 建立的章-section-unit 索引基础上，完成单个 section 内部的 core point 识别、core point 与 section 内 unit 的归属关系，以及同一个 section 内 core point 之间的结构关系。

分为三步：

```text
P2A：确定小节内 core_point。
P2B：确定 core_point 与小节内 unit 的归属/角色边。
P2C：确定同一个 section 内 core_point 之间的结构关系。
```

P2A 输出小节内的复习骨架节点。P2B 输出 `core_point -> unit` 的归属/角色边。P2C 输出同 section 内 `core_point -> core_point` 的结构关系。

输入：
- P1 章节索引（全书 unit 归属）
- P2A 人工审核记录

输出：
- P2A：core_point 草案 + unit 功能标签
- P2A_review：人工审核后 CP 边界
- P2B：core_point -> unit 语义边（defines / classifies / explains 等 10+1 种）
- P2C：同 section CP 间关系边（contains / illustrates / prepares / parallels / contrasts 等 5 种）

边界：

- 不修改 frozen unit。
- 不生成正式考试考点。
- 不处理相邻小节、同章跨 section 或跨章关系。

## Phase 3：同章小节间 core point 关系

状态：已按当前 P3 口径收口。

职责：在同一章节内，判断不同 section 的 core_point 之间是否存在对复习有用的关系，并为审核通过的关系绑定 unit 级证据。

分为三步：

```text
P3A：按章生成同章跨 section 的 core_point 关系候选。
P3A_review：人工审核候选关系，删除同 section 边、过宽边、弱边、方向错误边。
P3B：为审核通过的 core_point -> core_point 关系绑定 source/target 双方的 unit 级证据。
```

当前 P3 主关系类型：

```text
summarizes：Key takeaways CP -> 正文/案例 CP
illustrates：Case/example CP -> 概念/风险/控制 CP
grounds：基础概念/框架/概述 CP -> 展开/应用 CP
```

当前生产口径不输出 `alias_of`。重复主题如果不能归入上述三类关系，就不进入 P3 主边。


## Phase 4：跨章 core point 关系

状态：P4A/P4B/P4B_review/P4C 已完成一轮全书 Top300 候选流程。

职责：建立不同章节之间的 core_point 关系。跨章关系先作为候选和审核对象，不直接改变 P1/P2/P3 的章内结构。

当前 P4 主图关系类型：

```text
summarizes
illustrates
grounds
contrasts
```

P4 只保留少而硬的跨章 CP 关系。共享术语、方法或宽泛相似性进入 P5 或人工 review，不作为 P4 主图关系。

## Phase 5：术语、别名、缩写检索辅助索引

状态：已生成基础术语大字典，出现位置索引待扩展。

职责：整理教材和 KG 相关术语、别名、缩写和中英文表达，作为后续选项证据生成的检索辅助索引。

输入：P0 放行的 eligible units（主要使用 en_quote / knowledge_zh / terms / heading_context 字段）

输出：术语检索索引（缩写↔全称、中↔英、别名/同义词，含检索等价标记）

P5 是独立术语大字典，不进入 KG 主图，不进入 P6 阅读视图，不生成 core_point，也不生成 P3/P4 主图关系。

旧实现已归档：

```text
phases/archive/legacy_after_p6_20260706/phase09_terms/
```

## Phase 6：KG 总装、阅读视图、验收报告

状态：P6 全书机器检索 JSON、Markdown 树、Obsidian 阅读库和轻量验收报告均已生成。

职责：总装 KG 主资产，生成机器检索 JSON、人读 Markdown 知识树、Obsidian 阅读库和轻量验收报告。

输入：
- P1 章节索引
- P2 core_points + core_point -> unit 语义边
- P3 同章 CP 关系
- P4 跨章 CP 关系

输出：
- 机器母版 JSON（含 chapters / sections / core_points / units / edges / metadata）
- 单文件 Markdown 知识树（chorus 阅读视图）
- Obsidian 阅读库（每章一个 markdown + 总索引）
- 轻量验收报告

旧实现已归档：

```text
phases/archive/legacy_after_p6_20260706/phase10_assembly_review/
```

## Phase 7：流程型/操作型知识图谱 overlay

状态：P7A-P7E 已完成阶段构建，P7C 已进入全书分批抽取（batch runs 正在进行），P7G 证明路径运行时已建立。

职责：在 P6 教材复习型 KG 母版之上，构建流程型/操作型 overlay，用于表达教材中有证据支持的业务动作、输入、输出、条件、分叉、反馈和桥接关系。

P7 不修改 P0-P6 产物，不重判 P3/P4 的 CP 关系，不把 P5 术语索引写入主图。P5C 只用于节点命名和术语归一化。

核心产物：

```text
process cards：按章/节顺序阅读后留下的结构化流程卡片
procedural nodes：Activity / Object / Event / Condition / Decision / Record 等节点
procedural edges：有 unit 证据的短流程边
process subgraphs：多个局部闭环流程子图
bridge edges：子图之间的桥接边
micro-textbook previews：面向解析系统的微缩教材文本
```

推荐执行方式：

```text
P7A：生成 chapter reading tasks，不删上下文
P7B：双路独立顺序阅读，输出 chapter_flow_overview 和 process_cards
P7C：流程节点归一化、边级对齐、双路差异比较（全书分批抽取）
P7D：冲突裁决、桥接边审核、证据校验
P7E：组装局部闭环流程子图
P7G：按题生成证明路径（card内最小路径运行时；跨card路径待P7E桥接完成后支持）
```

边界：

- 按教材原文顺序完整阅读，不用关键词片段替代上下文。
- 每条正式边必须绑定 unit 级证据。
- 只抽短边，不让 LLM 直接生成全书长链。
- 流程子图允许局部自环，但反馈边必须与普通顺序边区分。
- explicit / strong_inference / weak_inference 必须分层；weak_inference 不进入正式层。

阶段目录：

```text
phases/phase07_procedural_layer/
```

## 辅助层：向量隐藏召回、LLM review

状态：保留为辅助层，不进入主干编号。

这些能力有用，但不是主层级的一部分：

```text
章 -> section -> core_point -> unit
```

建议定位：

- 向量隐藏召回：诊断漏召回，不改变主结构。
- LLM review：审核建议层，不得静默覆盖主产物。

当前旧实现位置：

```text
phases/archive/legacy_after_p6_20260706/phase08b_vector_hidden/
phases/archive/legacy_after_p6_20260706/phase10b_llm_review/
```

处理建议：保留，但从主 pipeline 中拆成 optional/review-only 辅助模块。

## 重构后的推荐主线

```text
P0 输入门禁
  -> P1 章/section/unit 索引
  -> P2 严格小节内 core_point
  -> P3 同章小节间 core_point 关系
  -> P4 跨章 core_point 关系
  -> P5 术语、别名、缩写检索辅助索引
  -> P6 KG 总装、阅读视图、验收报告
  -> P7 流程型/操作型 KG overlay
    P7A -> P7B -> P7C -> P7D -> P7E -> P7G
```

辅助模块：

```text
vector_hidden_candidates
llm_review
```
