# CAMS 教研工作台 MVP 产品契约

> 历史决策文档：`workbench-v2/` 已完成原型验证并退出正式主线。文中的“待实现”、示例文件名和产品入口不代表当前状态；正式应用以 `D:/守正公司工作区/cams考试工作台（正式版）/` 为准。

版本：v0.1
状态：已确认方案，待实现
范围：题目内容编辑、教材证据绑定、版本审核、交付发布跟踪

## 1. 产品定位

工作台是题目内容、教材证据、版本、审核和交付的管理工具。Codex 是推理和修改执行层，工作台不在内部复刻 RAG + 普通模型 API，也不嵌入聊天窗口。

工作台通过远程 MCP 为 Codex 提供受控的题目读取、证据检索和正式 Markdown 写入能力。工作台消费现有 KG 和原料库，但第一版不编辑或重建 KG。

## 2. 不可变原则

- `question_id` 是永久内部 ID，不因章节、小节、题号或语言变化而改变。
- `option_id` 是选项的稳定身份。A-F 只是当前语言和题库版本中的显示位置。
- 已发布版本不可修改；后续修改必须创建新修订。
- 原始 Markdown、教材 PDF、KG 发布包只读保留。
- 正式题目内容以复制导入后的 Markdown 为准，旧目录和旧管线不回写。
- 每次保存产生底层版本；界面默认按一次 Codex 任务合并展示，必要时展开逐次保存。

## 3. 主要对象

### Question

```yaml
question_id: v7_q_000003
source_file: content/questions/v7_q_000003/question.md
languages: [zh, en]
question_type: single | multiple
current_position: {bank_version: v7, chapter: 3, section: "3.2", number: 113}
primary_core_point_id: cp_CHxx_Sxx_xxx
supporting_core_point_ids: []
evidence_unit_ids: [v7u_N002556]
status: editing | pending_review | in_review | returned | approved | published
published_version_id: null
```

中文和英文是同一题目的语言变体，共用题目 ID、题型和知识绑定；导出时按目标语言生成内容。

### Option

选项内容存储在题目语言变体中，但身份由 `option_id` 维持。翻译、润色和移动位置保留 ID；语义替换创建新 ID；删除选项停用原 ID。答案底层引用 `option_id`，导出时再换算为 A-F。

### Evidence binding

教材证据只从 KG 的 `unit_id` 选择。选择后自动带入章节路径、PDF 页码、书内页码、中文要点和英文原文，并可一键打开 PDF 原页。`core_point` 用于题目统计，`unit` 用于原文证据和跳转。

题目可以有一个主 CP 和多个辅助 CP。默认统计只计主 CP；覆盖分析时再计入辅助 CP。

### Edit task and versions

- 一个编辑任务锁定一题；不同题可以并行，同题只能有一个写任务。
- Codex 任务可以包含多次保存。
- 每个保存保存完整内容快照和结构化变更。
- 任务视图默认合并显示本次任务变更，可展开查看每次保存。
- 支持任意两个版本比较、单次保存回滚和整次任务回滚。

### Review task

审核任务可以批量包含多道题，但每道题独立记录审核结论、意见和操作者。编辑人与批准人默认必须是不同的人。

### Release

每次导出生成不可变的 `release_id`，保存题目版本清单和导出文件哈希。发布状态按题追踪，而不是按整个 DOCX 批次统一标记：待录入、已录入、已核对、录入失败/需返工、已发布。

## 4. 页面与工作流

### 4.1 题目工作台

默认展示可搜索、可筛选的题目列表，支持永久 ID、题库版本、章/小节/当时题号、题干片段、状态、编辑人、审核人和主 CP 查询。位置查询通过发布快照解析到永久 ID，避免题号重排导致错题。

### 4.2 题目详情

分块展示中文和英文题干、选项、答案、解析、教材证据、当前 CP 绑定、任务和历史版本。结构化编辑器为主，高级 Markdown 模式为辅；二者必须读写同一份正式 Markdown。

### 4.3 差异视图

默认基线：未发布题目为导入原始版本，已发布题目为当前已发布版本。支持字段级和文本级差异，突出题干、选项、答案、解析、证据和绑定变化；支持任意历史版本比较。

### 4.4 证据选择器

通过章节、section、CP、关键词和术语检索 KG。选择 unit 后自动带入页码和原文，支持打开 PDF 原页。OCR、表格、流程图或争议证据只显示人工核对提示，不在 MVP 内建立工单或勘误层。

### 4.5 审核队列

责任编辑确认后手动提交审核；Codex 完成任务不自动提交。审核人查看默认差异、题目最终预览、证据原页和修改说明后逐题批准或退回。

### 4.6 交付与发布

批准版本生成符合第三方题库格式的 DOCX/交付包。人工录入第三方后台并在小程序核对后，逐题更新发布状态。工作台不模拟小程序，不把导出成功视为线上发布成功。

## 5. Codex MCP 最小接口

接口必须使用题目级锁和版本校验，所有正式写入经过 MCP：

```text
find_question(query, bank_version?, position?, text_fragment?)
get_question(question_id, version_id?)
begin_edit_task(question_id, purpose, base_version_id?)
search_kg(query, chapter_id?, section_id?, core_point_id?)
get_unit(unit_id)
open_source_page(unit_id)
save_question(task_id, content_patch, bindings_patch, note)
get_task_diff(task_id, detail_level?)
finish_edit_task(task_id, summary)
```

`finish_edit_task` 只结束 Codex 任务，不改变审核状态。责任编辑另行调用提交审核操作。

## 6. 导入规则

扫描现有 Markdown，复制到正式题目目录，记录来源路径、文件哈希和导入时间。导入尽可能全量完成；格式异常或字段缺失的题目进入`待整理`，不阻塞其他题目导入，也不静默补写原内容。

极简测试目录中的早期 `kp_id` 不进入正式编号体系；正式证据使用现有 KG 的 `core_point` 和 `unit_id`。

## 7. 权限与状态

状态流转：

```text
编辑中 → 待提交审核 → 审核中 → 退回/已批准 → 已发布
```

- 编辑者：创建编辑任务、修改题目、提交审核。
- 审核者：查看差异、批准或退回；不能批准自己发起的修订。
- 发布操作人：生成交付物、录入第三方后台、确认逐题发布状态。
- 管理员：可处理锁、失败任务和紧急越权；必须留下审计记录。

## 8. 明确不在 MVP

- 工作台内嵌 Codex 聊天或复刻 RAG 推理。
- KG/core point/unit 的编辑、重建和版本治理。
- OCR 勘误工单、统一 OCR 修订层。
- 自动操作第三方后台或小程序。
- 题目频率统计和复杂 Excel 反向编辑。
- 将自由文本考点另建为 `exam_point` 实体。

## 9. MVP 验收标准

1. 可复制导入全部现有 Markdown，原文件无变化，并为每题生成唯一永久 ID。
2. 可通过题库版本 + 章节/小节/历史题号或题干片段定位到正确题目。
3. 中英文同题可分别编辑；选项移动不会造成答案字母错误。
4. Codex 能在题目级锁内读取题目、检索 KG/unit、保存 Markdown 并结束编辑任务。
5. 工作台能展示任务合并差异、逐次保存、任意版本比较和回滚。
6. 责任编辑可提交审核；不同审核人可逐题批准或退回并留下意见。
7. 可选择 CP/unit 并自动带入证据元数据和 PDF 原页链接。
8. 批准版本可生成第三方格式 DOCX/交付包，并逐题跟踪后台录入和小程序核对结果。
9. 已发布版本不可覆盖；后续修改产生新修订并保留完整历史。
