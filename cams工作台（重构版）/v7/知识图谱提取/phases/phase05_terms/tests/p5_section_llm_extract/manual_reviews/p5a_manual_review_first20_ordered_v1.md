# P5A manual review: first20 ordered v1

来源产物：`outputs/p5_section_llm_extract_first20_ordered_v1.jsonl`

范围：全书顺序前 20 个 section，CH01-S01 到 CH03-S05。

总体结论：P5A 抽取质量可以作为候选层使用。缩写、全称、中文、英文和 unit 证据基本可追溯。问题主要是少量普通词、过宽金融工具词、以及需要后续合并的同义/近义词。

## 全局判断

```text
keep：AML、KYC、CFT、AFC、CRS、OECD、FinCEN、TCO、BMPE、TBML、money laundering、predicate crime、terrorist financing、sanctions evasion、bribery、corruption 等核心词。
merge：front -> front business/front company；predicate offense -> predicate crime；dirty money -> proceeds of criminal activity/money laundering 语境下别名；shell company/shell companies 统一。
review：stocks、bonds、hedge funds、derivatives、private equity investments 是否进入最终字典，取决于 P5 是否保留金融工具检索词。
drop：单独的 front 不建议作为最终词条。
```

## 分 section 初审

| section | 初审结论 | 备注 |
|---|---|---|
| CH01-S01 | keep | `money laundering`、`financial crime`、`compliance`、`transaction monitoring` 有价值；`risk-based strategies` 可保留为方法类候选。 |
| CH01-S02 | review | 大部分术语有效；`front` 太短，应 merge 到 `front business/front company`，不独立保留。 |
| CH01-S03 | keep | `KYC`、`predicate crime`、`suspicious activity` 等有效；修复记录合理。 |
| CH01-S04 | keep | 金融犯罪类型词有效；`tax evasion`、`sanctions evasion` 后续补中文。 |
| CH01-S05 | keep | `AML`、三阶段 `placement/layering/integration`、`predicate crime` 有价值。 |
| CH01-S06 | keep | 洗钱技术类术语较完整；`NFTs`、`DeFi` 作为 mention-only 缩写可保留候选，后续合并补全。 |
| CH01-S07 | review | TBML/MBML 与贸易洗钱手法有效；金融工具清单偏宽，P5B 标记为 review，不直接删除。 |
| CH01-S08 | keep | `commodity-based money laundering`、`high-value commodities` 有价值。 |
| CH01-S09 | keep | `shell company`、`front business`、`money mule`、`structuring` 有价值；组织名可按 occurrence 索引保留。 |
| CH02-S01 | keep | 上游犯罪清单有效，适合做检索字典；`FATF` 只有缩写出现，后续跨 section 合并全称。 |
| CH02-S02 | keep | `sanctions evasion`、`shell company` 等有效。 |
| CH02-S03 | keep | 贿赂腐败术语有效；`ABC policies` 与 `anti-bribery and corruption` 后续合并。 |
| CH02-S04 | keep | 案例中的法规、控制、主体术语有效；`AFC`、`ABC` 可与其他 section 合并。 |
| CH02-S05 | keep | 税务犯罪、CRS/OECD、Fraud Triangle 有价值。 |
| CH02-S06 | keep | 网络犯罪术语质量较好，FinCEN 缩写全称明确。 |
| CH03-S01 | keep | 人口贩运/偷运、TCO、funnel account、TBML 等有效。 |
| CH03-S02 | keep | 环境犯罪、TCO、wildlife trafficking、front company 有价值。 |
| CH03-S03 | keep | BMPE、TBML、hawala、crypto-laundering 等有效；`FinCEN` 后续补全。 |
| CH03-S04 | keep | 恐怖融资与洗钱对比术语有效。 |
| CH03-S05 | keep | 恐怖融资资金阶段、上游犯罪类型有效。 |

## 给 P5B 的处理建议

```text
1. 建立 canonical 合并：predicate offense -> predicate crime；shell companies -> shell company；front -> front business/front company。
2. 缩写合并按全书证据做：FATF、FinCEN、TBML、NFTs、DeFi 在单 section 中可能只有缩写，不能直接删除。
3. 金融工具类词先标记 review，后续按“复习检索价值”决定是否进入最终字典。
4. 中文名冲突由 P5B 选择出现最多、最标准或 terms_hint 支持的中文。
```

## 教材原文复核结论

```text
CH01-S02 front：原文是 “used as a front to launder...”。这里不是完整术语，应并入 front business/front company，不独立进入最终字典。
CH01-S07 TBML：section 标题含 “Trade-based money laundering (TBML)”，原始 P5A repair 未把标题作为缩写证据，导致 TBML 被误删。已修正脚本，标题会计入缩写证据。
CH01-S07 金融工具清单：stocks、bonds、hedge funds、derivatives、private equity investments 原文明确列为 MBML 可利用的工具。它们不是噪声，但应作为金融工具类检索词，优先级低于 AML/CFT 核心术语。
```
