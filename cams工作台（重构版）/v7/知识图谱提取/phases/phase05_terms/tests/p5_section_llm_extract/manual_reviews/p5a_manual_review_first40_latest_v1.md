# P5A manual review: first40 latest v1

来源产物：`outputs/p5_section_llm_extract_first40_latest_v1.jsonl`

范围：全书顺序前 40 个 section，CH01-S01 到 CH06-S10。

运行结果：

```text
selected_count：40
passed_count：40
failed_count：0
repair_count：22
```

总体结论：第一轮可用。新版缩写校验已经修复 `TBML` 标题证据和复数缩写问题；主干术语、缩写、组织名、法律名、职位名抽取基本稳定。P5A 仍然是候选层，最终合并和分层交给 P5B。

## 对照原文后的判断

```text
CH01-S02 front：原文是 used as a front to launder...，应 merge 到 front business/front company，不独立进主词表。
CH01-S07 TBML：标题明确含 Trade-based money laundering (TBML)，新版已正确保留 TBML。
CH01-S07 stocks/bonds/hedge funds/derivatives/private equity：原文明确列为 MBML 可利用工具，只进 retrieval_aux，不进核心术语主词表。
CH03-S07 FIU/SAR：原文写 FIUs 和 SARs，缩写有效；模型补出的 Financial Intelligence Unit / Suspicious Activity Report 事实正确，但本 section 没有显式展开，P5B 需按全书证据确认 full form。
CH04-S02 CDD/SAR/DPA/MSB：原文有全称或业务描述，但没有写对应缩写；本 section 不自动绑定缩写，P5B 跨 section 合并。
CH04-S03 first LoD：原文写 first LoD，缩写有效；full form 需 P5B 确认 canonical。
CH05-S01 PEP/EDD/DeFi：原文写 politically exposed persons、enhanced due diligence、decentralized finance，但没有 PEP/EDD/DeFi 缩写；本 section 移除缩写是正确的。
CH06-S02 ML：原文写 key ML risks，按用户口径作为 money laundering 的低优先级缩写保留。
```

## 进入 P5B 的处理规则

```text
1. ML -> money laundering：低优先级缩写，进入最终字典。
2. 金融工具词：进入 retrieval_aux，不进核心术语主词表。
3. 组织名、法律名、职位名：保留单独 category。
4. ABC、FIU、SAR、CDD、DPA、MSB：P5A 记录出现；是否绑定全称由 P5B 汇总全书证据决定。
5. 只出现缩写但模型补出 full form 的项：标记为 evidence_level = inferred_or_cross_section，不当作 section-explicit。
```

## 人工关注项

| 项 | 判断 | 处理 |
|---|---|---|
| `front` | 不独立保留 | merge 到 `front business/front company` |
| `FIU/SAR` | 缩写有效，全称待全书确认 | P5B 合并 |
| `ABC` | CH04-S02 未展开 | P5B 合并到 `anti-bribery and corruption`，需全书证据 |
| `first LoD` | 有原文证据 | P5B 确认 canonical 与中文 |
| `JMLSG` | 不在本轮范围 | 第二轮继续关注中文异常 |
| 金融工具清单 | 原文有效 | retrieval_aux |
