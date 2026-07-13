# 历史 / 中间 / 测试产物说明

归档时间：2026-06-21

本目录用于存放 `题目与kg关系建立流水线（四角色法）` 中已经不属于当前主线运行入口、但仍有追溯价值的历史实验、测试输出、中间构建结果和一次性脚本。

这样处理的目的：

- 保持流水线根目录清爽。
- 保留历史试验和中间产物，便于追溯。
- 避免误删早期实验结果。
- 不影响当前新题解析、学生答疑和第二章题目证据绑定主线。

## 当前主线仍保留在原位

以下内容仍在上一级目录或 `output` 主目录中，不应随意移动：

- `README.md`
- `数据/`
- `run_step1.py`
- `run_agentic_search_experiment.py`
- `run_blind_q212_experiment.py`
- `run_step2_option_mapping.py`
- `run_parallel_agentic_batch.py`
- `audit_option_mapping.py`
- `build_v6_sentence_cards.py`
- `build_ch2_sentence_cards.py`
- `build_v6_except_ch2_sentence_cards.py`
- `build_combined_evidence_pool.py`
- `build_exam_point_mapping.py`
- `output/agentic_full_ch2_20260615`
- `output/step2_full_ch2_20260615`
- `output/agentic_patch_2.2_20_20260615`

其中，`run_step1.py`、`run_agentic_search_experiment.py`、`run_blind_q212_experiment.py` 和 `数据/` 仍被 `cams工作台` 的新题解析、学生答疑模块复用。

## 子目录说明

### `root_files`

保存从流水线根目录移出的旧脚本、一次性脚本、早期计划文档和 Python 缓存。

当前包括：

- `audit.py`
- `test_one.py`
- `run_50_combined.ps1`
- `选项级教材依据绑定改造计划.md`
- `__pycache__/`

这些内容目前不属于主线入口，但可用于追溯早期设计、调试方式和一次性批处理方法。

### `output_artifacts`

保存从 `output/` 移出的历史试跑、中间构建、测试输出和旧口径结果。

当前包括：

- `agentic_search_experiment`
- `blind_no_answer_experiment`
- `agentic_parallel_teacher_hints`
- `agentic_teacher_hints_compare`
- `agentic_missing_formal_trial20`
- `agentic_missing_formal_trial20_grouped`
- `step1_ai_responses`
- `step1_ai_responses_backup_before_50_20260607_024203`
- `step1_ai_responses_backup_ch2s_20260607_013523`
- `step2_option_mapping`
- `step2_option_mapping_test_20260615`
- `step2_full_ch2_test_20260615`
- `exam_point_mapping`
- `run_logs`
- `ch2_sentence_cards`
- `v6_sentence_cards`
- `v6_except_ch2_sentence_cards`
- `textbook_amld_check.txt`
- `v6_full_amld_check.txt`

这些目录/文件主要用于追溯历史实验，不作为当前工作台直接读取的正式产物。

## 恢复方式

如后续需要恢复某个文件或目录：

- `root_files` 中的内容可移回：
  `D:\守正公司工作区\cams考试\题目与kg关系建立流水线（四角色法）`

- `output_artifacts` 中的内容可移回：
  `D:\守正公司工作区\cams考试\题目与kg关系建立流水线（四角色法）\output`
