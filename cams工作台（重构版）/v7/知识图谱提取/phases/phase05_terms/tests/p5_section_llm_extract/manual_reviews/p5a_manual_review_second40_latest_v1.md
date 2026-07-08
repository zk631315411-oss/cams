# P5A manual review: second40 latest v1

来源产物：

```text
outputs/p5_section_llm_extract_second40_latest_v1.jsonl
outputs/p5_section_llm_extract_second40_latest_v1_ch14s02_retry.jsonl
```

范围：全书顺序第 41-80 个 section，CH07-S01 到 CH16-S02。

运行结果：

```text
主跑 selected_count：40
主跑 passed_count：39
主跑 failed_count：1
主跑 repair_count：29
retry：CH14-S02 单独重跑通过
最终可用：40/40
```

`CH14-S02` 首次失败原因是 `notes_too_long`，不是结构错误或术语抽取失败。单独重跑后通过。

## 对照原文后的判断

```text
CH07-S05 JMLSG：原文明确写 Joint Money Laundering Steering Group (JMLSG)。缩写/全称关系正确，但中文 `J洗钱SG` 错误，P5B 需修正或置空中文。
CH08-S02 UBO/PEPs/PBWM/SWF：原文分别写 UBO、PEPs、PBWM、SWFs，缩写有效。PEPs/SWFs 是复数缩写，最新版校验可保留。
CH10-S02 MSB/AML/KYC/EMI/NBFIs：原文均有明确缩写或缩写复数。NBFI 是复数 NBFIs，保留正确。
CH12-S04 PEPs/CDD/ETF：原文明确写 PEPs、CDD、Exchange-traded funds (ETF)，有效。金融工具和产品进入 retrieval_aux 或 financial_product category。
CH13-S01 DLT/DeFi/VASPs/NFTs/USDT/USDC：原文明确给出或反复使用，适合保留。虚拟资产相关术语进入 cryptoasset category。
CH14-S02 DNFBPs/TCSP/AML/CFT：原文明确出现 DNFBPs、trust or company service providers (TCSP)、AML/CFT。DNFBP/DNFBPs 需 canonical 合并。
CH16-S02 Goodwish Jade/TRF Bank/Teh Ong：原文是案例实体和人物。按用户口径组织名/职位名保留 category，但案例人物通常不进核心词表，可放 occurrence/entity index。
```

## 进入 P5B 的处理规则

```text
1. DNFBP/DNFBPs、TCSP/TCSPs、VASP/VASPs、PEP/PEPs、SWF/SWFs、UBO/UBOs：统一 singular canonical，保留复数 alias。
2. JMLSG 中文错误必须修正或置空。
3. 证券、经纪、基金、衍生品、ETF、swaps、forward rate agreements 等金融工具/产品：进入 retrieval_aux 或 financial_product，不进核心 AML/CFT 主词表。
4. 组织名、法律名、职位名保留单独 category。
5. 案例中的公司、人名、银行名保留为 entity/case_entity，但不进入核心术语主词表。
6. 只出现缩写但模型补 full form 的项，证据层级标为 inferred_or_cross_section，由 P5B 汇总全书证据确认。
```

## 人工关注项

| 项 | 判断 | 处理 |
|---|---|---|
| `JMLSG` | 抽取关系正确，中文错误 | P5B 修中文或置空 |
| `DNFBP/DNFBPs` | 有效核心术语 | 合并 canonical |
| `TCSP` | 有显式展开 | 保留 role/category |
| `VASP/VASPs` | 有效虚拟资产服务主体 | 合并 canonical |
| `PEP/PEPs` | 有效缩写 | 合并 canonical |
| `SWF/SWFs` | 有效缩写 | 合并 canonical，category 可为 financial_entity/product |
| 金融工具/证券产品 | 原文有效 | retrieval_aux / financial_product |
| 案例实体和人物 | 原文有效 | entity/case_entity，不进核心主词表 |
| `CH14-S02` 首次失败 | notes 过长 | retry 产物通过，使用 retry 结果 |
