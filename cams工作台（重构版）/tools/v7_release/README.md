# V7 工作台发布包

> 历史前端发布器：本工具只服务 `../../frontend/` 旧原型，不是当前正式应用的发布入口。2026-07-22 教材包依赖的语义标题对齐账本已缺失，因此旧结构包保留为不可原样重建的历史快照，无需恢复。

目录中的 `rebuild_textbook_structure.py` 曾用于将新版中英文 MD、语义标题锚点、冻结 unit 和 PDF 页码重组为结构发布包。其 `--semantic-alignment` 与 `--semantic-audit` 输入当前不存在；不要用不完整输入覆盖现有历史包。

此目录包含两个独立发布器，不会触发检索、LLM 调用或读取临时实验目录。

## 1. 先发布双语教材

教材基础包与题目证据包独立。它包含中英文 PDF、547 页映射和冻结单元，可在题目跑批完成前先激活：

```powershell
python build_textbook_release.py `
  --units "../../v7/work/base_units/units/v7_bilingual_units.json" `
  --freeze-manifest "../../v7/work/base_units/units/unit_freeze_manifest.json" `
  --zh-pdf "../../v7/work/sources/v7_zh_split.pdf" `
  --en-pdf "../../v7/work/sources/v7_en_split.pdf" `
  --page-map "../../v7/work/sources/v7_split_page_map.json" `
  --aligned-pages "../../v7/work/sources/v7_page_aligned_text.json" `
  --output-dir "../../frontend/data/releases/v7/textbook/v7-textbook-<发布日期>" `
  --release-id "v7-textbook-<发布日期>" `
  --activate
```

这会更新 `frontend/data/releases/v7/textbook-active.json`。它是教材阅读器唯一读取的 PDF 入口。

## 2. 后续发布题目证据

```powershell
python build_release.py `
  --units "../../v7/work/base_units/units/v7_bilingual_units.json" `
  --freeze-manifest "../../v7/work/base_units/units/unit_freeze_manifest.json" `
  --questions "../../v7/选项证据与解析生成/phase3.5_questions/output/v7_questions.json" `
  --evidence-dir "../../v7/选项证据与解析生成/phase4_evidence/output/<已完成批次>" `
  --output-dir "../../frontend/data/releases/v7/v7-<发布日期>" `
  --release-id "v7-<发布日期>" `
  --activate
```

发布器在写入前校验所有 `unit_id` 与题目引用，拒绝 v6 句卡标识、重复题目结果、未知证据状态和悬空引用。`active.json` 是前端唯一入口；前端不会扫描或加载跑批目录。

`active.json` 仅控制题目证据覆盖层；尚未存在时，工作台仍可完整阅读双语教材。
