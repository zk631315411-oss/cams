# V3.1解析母版与题库软件版导出

解析母版只消费正式盲判结果，不修改检索、补充池或盲判字段。参考答案和
参考解析不进入解析模型提示词，只在母版生成后由本地代码追加。

## 数据流

```text
新版盲判JSON
→ stage_explanation_run.py复制盲判结果并附加人工章节映射
→ generate_evidence_explanations.py生成V3.1母版
→ export_software_explanations.py执行发布校验和字段裁剪
→ 章节软件预览与待复核清单
```

V3.1母版同时保留教研栏目、完整教材证据、参考附录和
`software_readiness`。核心解析包含一个从真实 `en_quote` 逐字截取的
`source_quote`，软件版只展示这一个英文短引。

V3.1提示词接收中英文题干、选项、盲判标签、共享框架unit、已裁判证据，
以及每个选项前2个独立补充候选。盲判生成的
`decision_reason`、证据卡`reason`、框架摘要和必要条件不作为事实材料进入
提示词，避免把盲判解释中的扩写再次传播到成稿。

选项依据分为：

- `textbook_direct`：使用本选项已裁判证据或补充候选中的逐字教材片段。
- `textbook_definition_application`：允许额外使用共享框架定义unit。
- `stem_contrast`：使用题干与选项逐字片段说明明确冲突。
- `stem_entailment`：使用题干与选项逐字片段完成直接复述或直接逻辑推导。
- `insufficient`：现有材料不能形成可靠解析。

模型不再自由生成选项分析正文，只输出`source_claims`、`stem_quotes`、
`option_quotes`和`inference_type`。本地标准化层按固定模板生成选项正文，
并执行以下处理：

- 清除正文中的内部`v7u_*`标识。
- 校验`source_claims`是否为对应unit原文的连续子串。
- 校验题干与选项证据是否逐字存在。
- 将无法安全修复的越界正文降级为`insufficient`。
- 用已通过校验的正确选项分析恢复混入伴随事实的核心解析。
- 用真实`knowledge_zh`恢复夸大程度或范围的易错提醒，并记录
  `normalization_recovered`风险。

增量生成后，索引和章节合并稿会从输出目录中重新汇总全部V3.1母版，不会
只保留本次命令指定的题目。

## 建立V3.1运行目录

```powershell
python phase4_evidence/scripts/stage_explanation_run.py `
  --source-dir phase4_evidence/output/ch01_definition_driven_draft_v2_20260713 `
  --target-dir phase4_evidence/output/ch01_definition_driven_v3_1_draft_20260713 `
  --chapter-map phase4_evidence/chapter_mapping/question_chapter_mappings.jsonl
```

目标目录必须不存在，脚本拒绝覆盖已有运行；盲判源目录不会被修改。

## 生成V3.1母版

```powershell
python phase4_evidence/scripts/generate_evidence_explanations.py `
  --output-dir phase4_evidence/output/ch01_definition_driven_v3_1_draft_20260713 `
  --limit 0 --concurrency 4 --model deepseek-v4-pro --write-back
```

## 导出软件版

```powershell
python phase4_evidence/scripts/export_software_explanations.py `
  --output-dir phase4_evidence/output/ch01_definition_driven_v3_1_draft_20260713 `
  --chapter-id CH01
```

输出：

```text
software_export/
├── chapters/CH01.md
├── review_required.md
└── export_results.json
```

软件正文只包含答案、考点、核心解析、一条教材英文原句、逐项分析和易错
提醒。它不包含 unit_id、完整原文附录、参考材料或内部证据标签。

## 发布门槛

以下任一条件阻断软件版导出：

- 任一选项 `basis_type=insufficient`。
- AI答案与题库最终、中文或英文参考答案冲突。
- 盲判状态或机械校验失败。
- 出现被过滤的非法引用。
- 选项引用不属于本选项证据卡。
- 核心英文短引不是对应教材原文的连续子串。
- 教材正文出现无所引unit支持的强分类、强必要性、频率或关联论断，且本地层
  无法安全恢复。

OCR风险和成功执行的确定性恢复只写入导出结果，不自动阻断。
