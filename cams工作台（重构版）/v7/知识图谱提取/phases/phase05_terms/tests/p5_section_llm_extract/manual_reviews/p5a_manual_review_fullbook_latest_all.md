# P5A manual review: fullbook latest all

来源产物：`outputs/p5_section_llm_extract_fullbook_latest_all.jsonl`

范围：全书 339 个 section。

## 运行结果

```text
section_count：339
term_count：3880
review_flag_count：291
coverage：无漏 section、无重复 section、无额外 section
```

本次全书运行按 40 section 一批执行。`CH14-S02` 与 `CH55-S01` 首次运行失败，原因均为 `notes_too_long`，不是结构错误或术语抽取失败；两者已单独 retry 并通过。合并版产物使用 retry 结果替换首次失败结果。

## 批次结果

| run | selected | passed | failed | repairs | 处理 |
|---|---:|---:|---:|---:|---|
| first40_latest_v1 | 40 | 40 | 0 | 22 | 可用 |
| second40_latest_v1 | 40 | 39 | 1 | 29 | CH14-S02 retry |
| offset080 | 40 | 40 | 0 | 39 | 可用 |
| offset120 | 40 | 40 | 0 | 19 | 可用 |
| offset160 | 40 | 40 | 0 | 44 | 可用 |
| offset200 | 40 | 40 | 0 | 47 | 可用 |
| offset240 | 40 | 40 | 0 | 41 | 可用 |
| offset280 | 40 | 39 | 1 | 41 | CH55-S01 retry |
| offset320 | 19 | 19 | 0 | 11 | 可用 |

## 总体判断

P5A 全书产物可作为 P5B 输入。P5A 完成的是候选抽取，不是最终字典。主要质量特征：

```text
1. 缩写、全称、中英文、出现位置基本可追溯。
2. repair 主要是把非显式 abbreviation_full_form 降级为 mention。
3. 少量缩写在单 section 未展开，但可由 P5B 汇总全书证据合并。
4. 金融工具、产品、行业主体、组织名、法律名、职位名数量较多，需要 P5B 分 category。
5. 个别中文异常仍需 P5B 修正，例如 JMLSG。
```

## P5B 注意点

```text
1. canonical 合并：PEP/PEPs、UBO/UBOs、DNFBP/DNFBPs、VASP/VASPs、TCSP/TCSPs、SWF/SWFs。
2. 缩写低优先级：ML -> money laundering。
3. 金融工具和金融产品：进入 retrieval_aux 或 financial_product，不进核心术语主词表。
4. 组织名、法律名、职位名：保留独立 category。
5. 案例实体和人物：保留 entity/case_entity，不进核心术语主词表。
6. 只出现缩写但模型补 full form 的项：标记 evidence_level = inferred_or_cross_section，由 P5B 全书证据确认。
7. 中文异常或缺失：P5B 依据 terms_hint、出现频率和人工规则修正。
```
