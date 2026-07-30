# V7 构建工作区

本目录保存教材来源快照、双语知识单元构建过程、冻结产物和审计记录。

- `sources/`：与教材 PDF/MD 对齐相关的本地来源资产。
- `base_units/units/`：4,973 个正式冻结双语知识单元。
- `base_units/structural_releases/`：旧前端教材结构发布快照。
- `base_units/draft/`、`llm_*`、`patched/`、`fullbook_ds_v2_run/`：构建过程和模型运行留痕。
- `audit/`：构建与清理审计。

下游正式证据只读取 `base_units/units/v7_bilingual_units.json` 或其 card 适配文件，不直接读取 LLM runs、draft 或 patched 目录。
