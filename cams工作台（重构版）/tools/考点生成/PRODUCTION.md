# V6 考点生成历史复现清单

本文记录 V6 考点研究链曾使用的生产脚本和输入。部分上游路径已迁移或缺失，当前不保证可直接复现；不得作为 V7 生产命令执行。

本文用于把当前已经跑通的考点生成链路，从历史试验脚本里单独拎出来。原则是先固定生产入口，再逐步归档旧脚本；本文件不要求删除任何历史产物。

## 当前生产版本

- 版本名：`v15_current_v10_822_ds_full_prompt_v3_rules_v4b`
- 最终资产包：`work/preview_v15_full_dry_run_v15_current_v10_822_ds_full_prompt_v3_rules_v4b/`
- 当前基线：`v10 strict` 的 822 个考点本体
- 当前命名：DeepSeek 全量 822 条，`prompt_v3`
- 当前门禁：`rules_v4b`
- 当前状态：适合进入前端复核页/教研抽检页原型，不建议直接替换正式 HTML 资产

## 正式脚本

### 从逐题证据重建考点本体

这些脚本用于从上游 `q_*.json` 重新生成当前 v10 strict 考点本体。

1. `preview_v1_seed_points.py`
   - 输入：`../选项证据生成/新题解析模块复用/output/questions/q_*.json`
   - 输出：`work/preview_v1/seed_points.json`、`strong_edges.json`
   - 用途：抽取强证据句卡种子和题目-句卡边。

2. `preview_v5_structure_preview.py`
   - 输入：`work/preview_v1/seed_points.json`、`strong_edges.json`
   - 输出：`work/preview_v5/all_candidate_points.json`、`contrast_classification.json`、`merge_parent_child_candidates.json`
   - 用途：生成全量候选点、contrast 分类和关系召回队列。

3. `preview_v6_structure_draft.py`
   - 输入：`work/preview_v5/`
   - 输出：`work/preview_v6/relation_draft.json`、`contrast_draft.json`
   - 用途：用当前规则给关系和 contrast 做结构草稿。

4. `preview_v10_full828_materialize.py`
   - 输入：`work/preview_v1/strong_edges.json`、`work/preview_v5/`、`work/preview_v6/`
   - 输出：`work/preview_v10_full828/exam_point_system_full828.json`、`exam_point_question_card_edges.json`
   - 用途：生成当前稳定的 `v10 strict` 考点本体。默认只应用 `merge_same_point`，父子/兄弟关系只保留 trace。

### 命名、门禁和资产包

这些脚本用于把 v10 strict 本体转成可复核资产包。

5. `preview_v8_naming_sample.py`
   - 输入：`work/preview_v10_full828/`
   - 输出：`work/preview_v8_naming_sample/agent_naming_input_<batch>.json`
   - 用途：生成受限命名任务；拿到 DS 输出后再次运行同一脚本做校验与整合。

6. `preview_v11_ds_naming_executor.py`
   - 输入：`work/preview_v8_naming_sample/agent_naming_input_<batch>.json`
   - 输出：`work/preview_v8_naming_sample/agent_naming_output_<batch>.json`
   - 用途：调用 DeepSeek 做受限命名。会产生 API 成本，批量生产前必须确认 batch 名和输入数量。

7. `preview_v9_admission_gate.py`
   - 输入：`work/preview_v8_naming_sample/named_exam_points_sample_<batch>.json`
   - 输出：`work/preview_v9_admission_gate/admission_decisions_<batch>.json`、`formal_candidate_draft_<batch>.json`
   - 用途：把命名结果转成工程门禁和复核队列。

8. `preview_v15_full_dry_run_asset.py`
   - 输入：v10 本体、v8 命名结果、v9 门禁、v14 关系层
   - 输出：`full_dry_run_asset.json`、`risk_queues.json`、`summary.json`、`full_dry_run_report.md`
   - 用途：组装最终复核资产包。

当前稳定版本的 v15 打包入口是：

```powershell
.\run_current_full_dry_run.ps1
```

该入口只重打包已有产物，不调用 DeepSeek。

如果要从上游逐题证据重新跑到 v15，但复用已有 DS 命名输出、不重新调用 API，使用：

```powershell
.\run_current_pipeline_no_api.ps1
```

这个入口会显式设置 v5 全量关系队列参数：

```powershell
$env:PREVIEW_V5_RELATION_REVIEW_LIMIT = "3814"
$env:PREVIEW_V5_MAX_RELATION_CANDIDATES_PER_POINT = "999"
$env:PREVIEW_V5_RELATION_MIN_SCORE = "50"
```

不要用 v5 默认参数复现当前生产版本。默认参数只选 600 条 relation review 候选，会导致 v10 strict 本体变成 823 个点，无法和当前 822 条 DS 命名/门禁结果完全对齐。

### 关系层复核

关系层目前是生产候选增强层，不是生成考点本体的硬依赖。

9. `preview_v13_relation_review.py`
   - 输入：`work/preview_v10_full828/relation_judgement_records.jsonl`
   - 输出：`work/preview_v13_relation_review/relation_review_input_*.json`
   - 用途：生成/校验父子、兄弟、合并关系的人工或 DS 复核批次。

10. `preview_v14_apply_relation_review.py`
    - 输入：`work/preview_v13_relation_review/relation_review_decisions_*.json`
    - 输出：`work/preview_v14_relation_layer/relation_layer_*.json`
    - 用途：把复核决策转成可被 v15 合并的关系层。

## 辅助脚本

- `preview_v12_evidence_context.py`：用于补教材上下文/证据上下文，适合支持 `evidence_supplement_candidate` 队列。
- `check_preview_v6_regression.py`、`check_preview_v6_dry_run.py`、`inspect_preview_v6_samples.py`：v6 规则调试和回归检查，不属于生产主流程。

## 已归档脚本

以下脚本不应再被生产流程直接调用，已移动到 `archive/legacy_scripts_20260703_110354/`：

- `historical_preview_scripts/preview_v2_merge_candidates.py`
- `historical_preview_scripts/preview_v3_reviewed_groups.py`
- `historical_preview_scripts/preview_v4_name_high_frequency.py`
- `historical_preview_scripts/preview_v7_materialize_sample.py`
- `deprecated_patch_scripts/step1_aggregate.py`
- `deprecated_patch_scripts/step2_cluster.py`
- `deprecated_patch_scripts/step3_merge.py`
- `deprecated_patch_scripts/step4_name.py`
- `deprecated_patch_scripts/step5_stats.py`
- `deprecated_patch_scripts/fix_duplicates.py`
- `deprecated_patch_scripts/fix_fallbacks.py`
- `deprecated_patch_scripts/fix_names_final.py`
- `deprecated_patch_scripts/fix_titles_final.py`
- `deprecated_patch_scripts/retry_last.py`
- `deprecated_patch_scripts/retry_stubborn.py`
- `deprecated_patch_scripts/patch_last.py`
- `deprecated_patch_scripts/test_max_tokens.py`
- `deprecated_patch_scripts/test_run_sample.py`

归档目录内有 `manifest.json` 记录移动清单。需要查历史时从 archive 读取，不再从顶层入口调用。

## 当前推荐操作顺序

只复现当前资产包：

```powershell
.\run_current_full_dry_run.ps1
```

从上游逐题证据重新生成：

```powershell
.\run_current_pipeline_no_api.ps1
```

手工分步运行时必须带上 v5 全量关系队列参数：

```powershell
python -X utf8 preview_v1_seed_points.py

$env:PREVIEW_V5_RELATION_REVIEW_LIMIT = "3814"
$env:PREVIEW_V5_MAX_RELATION_CANDIDATES_PER_POINT = "999"
$env:PREVIEW_V5_RELATION_MIN_SCORE = "50"
python -X utf8 preview_v5_structure_preview.py
python -X utf8 preview_v6_structure_draft.py
python -X utf8 preview_v10_full828_materialize.py

$env:PREVIEW_V8_SOURCE_DIR = "work/preview_v10_full828"
$env:PREVIEW_V8_BATCH_NAME = "v15_current_v10_822_ds_full_prompt_v3"
$env:PREVIEW_V8_SAMPLE_LIMIT = "822"
python -X utf8 preview_v8_naming_sample.py
```

DeepSeek 命名和后续门禁需按实际 batch 名运行。不要直接使用脚本默认值跑 v9/v15，因为部分默认值仍指向历史样本版本；生产命令必须显式设置 batch，或使用 `run_current_pipeline_no_api.ps1` / `run_current_full_dry_run.ps1`。
