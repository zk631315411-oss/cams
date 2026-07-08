# P5A manual review: next40 ordered v1

来源产物：`outputs/p5_section_llm_extract_next40_ordered_v1.jsonl`

范围：全书顺序第 21-60 个 section，CH03-S06 到 CH11-S02。

总体结论：本轮 P5A 可继续作为术语候选层。银行、私人银行、公司投行、非银、MSB/PSP 相关术语抽取较完整，缩写覆盖较好。主要问题是修复次数上升、个别缩写需要全书合并判断、少量中文名或普通词需要 review。

## 运行质量

```text
selected_count：40
passed_count：40
failed_count：0
repair_count：31
```

修复类型主要有两类：

```text
1. 模型把非显式缩写展开误标为 abbreviation_full_form，已降级为 mention。
2. 模型给了当前 section 未出现的缩写，已从 abbreviations 移除。
```

这些修复说明 P5A 的校验层有必要保留。

## 全局判断

```text
keep：ARS、AFC、KYC、AML、CFT、FATF、MLRO、BSA、CDD、PEP、BO、UBO、LLP、SLP、SPV、EDD、MSB、PSP、TPPP、IVTS、ACH、IPO、M&A 等。
merge：obliged entity/obliged entities；PEP 与 foreign/domestic/international organization PEP；beneficial owner/beneficial ownership/ultimate beneficial owner；wire transfer/funds transfer；shell/front/shelf company。
review：ML、ABC、first LoD、JMLSG 中文、SWIFT、FinCEN 仅缩写项、组织名/职位名是否进入最终字典。
drop_or_downgrade：best practice、vulnerabilities、controls、financial institutions、financial services 这类普通词如无复习检索价值，应降级或过滤。
```

## 重点问题

| term | section | 初审结论 | 备注 |
|---|---|---|---|
| money laundering / ML | CH06-S02 | review | `ML` 可作缩写候选，但 CAMS 语境更常用 `AML`，P5B 需全书证据确认是否保留。 |
| ABC | CH04-S02 | review | 单独 `ABC` 低置信度，应与 `anti-bribery and corruption` 或 `ABC policies` 合并，不独立成最终词条。 |
| first LoD | CH04-S03 | review | `first line of defense` 有价值，但 `first LoD` 是否作为标准缩写需看原文和全书证据。 |
| JMLSG | CH07-S05 | review | 缩写和全称有价值，但中文抽成 `J洗钱SG` 明显异常，P5B 必须修正。 |
| SWIFT | CH09-S02 | keep/review | 作为支付系统有检索价值；若无全称证据，先作为缩写型 canonical 保留。 |
| FinCEN | CH11-S02 | keep/review | 本 section 只有缩写也可保留，后续与 `Financial Crimes Enforcement Network` 合并。 |
| Europol / Interpol / Department of Justice / SEC | 多处 | review | 组织名有证据，但是否进入最终术语大字典取决于是否保留机构检索词。 |
| Global Head of Compliance / TD Bank | CH05-S02 / CH06-S03 | review/drop | 案例角色或机构名，通常不作为核心术语；可保留 occurrence 索引，不进入主词表。 |
| best practice / vulnerabilities / controls | CH06-S01/CH06-S03 | drop_or_downgrade | 偏普通词，除非与具体合规控制绑定，否则不建议进入最终词表。 |

## 分组初审

| 范围 | 初审结论 | 备注 |
|---|---|---|
| CH03-S06 - CH03-S07 | keep | 恐怖融资移动资金方式、ARS、hawala、crypto、SAR/FIU 线索有价值；SAR/FIU 被当前 section 规则移除缩写时，P5B 应从全书补回。 |
| CH04-S01 - CH04-S03 | review | 后果与问责章节抽取完整；法律、监管机构、职位名偏多，主词表与 occurrence 索引应分层。 |
| CH05-S01 - CH05-S04 | keep | 风险类型、DPA、de-risking、CDD、reputational/legal/operational/concentration risk 有价值。 |
| CH06-S01 - CH06-S11 | keep/review | 银行业风险术语质量较好；`ML`、普通词、案例银行名需 review；PEP/UBO/BO/FATF 等应保留。 |
| CH07-S01 - CH07-S05 | keep/review | 零售/商业银行产品风险术语可用于复习检索；JMLSG 中文异常需修正。 |
| CH08-S01 - CH08-S05 | keep | 私人银行、信托、OFC、SPV、PIV、EDD/CDD 抽取有价值；PEP/UBO 与前文合并。 |
| CH09-S01 - CH09-S06 | keep | 公司投行、汇款、IPO、M&A、SPV、NGO、FX 等有价值；金融产品词按检索价值保留。 |
| CH10-S01 - CH11-S02 | keep | NBFI、MSB、PSP、TPPP、IVTS、FinCEN、KYC/AML/CFT 等适合进入术语大字典候选层。 |

## 给 P5B 的处理建议

```text
1. P5B 不要因为单 section 移除了缩写就删除该缩写，应按全书证据重新合并。
2. 中文异常项必须进 review，例如 JMLSG。
3. 组织名、法律名、职位名建议保留为可选 category，不与核心 AML/CFT 概念混在一个优先级。
4. 普通词和宽泛词进入 drop_or_downgrade，而不是在 P5A 阶段压制。
5. 缩写冲突需要重点审：ABC、ML、BO、PEP、SWIFT、FinCEN。
```

## 教材原文复核结论

```text
CH03-S07 FIU/SAR：原文是 “FIUs synthesized bank SARs...”。FIU/SAR 是有效缩写，原始 repair 因复数 FIUs/SARs 未匹配而误删。已修正脚本，允许大写缩写匹配简单复数。
CH04-S02 ABC：原文只写 “ABC and sanctions regulations”，没有展开 anti-bribery and corruption。ABC 可保留为缩写候选，但不能在该 section 内自动绑定全称，需 P5B 跨 section 合并。
CH04-S02 CDD/SAR/DPA：原文写 customer due diligence、suspicious activity、deferred prosecution agreement，但未写 CDD/SAR/DPA。当前 section 不应强行绑定缩写，P5B 可用全书证据补。
CH04-S03 first LoD：原文写 “first LoD or operational staff”。该缩写有效，但 full form 来自术语常识，不是本句显式展开；应保留候选并在 P5B 确认 canonical。
CH06-S02 ML：原文写 “key ML risks”。ML 在该句确实指 money laundering，但不如 AML 常见。保留为低优先级缩写候选，P5B 标记 review。
CH07-S05 JMLSG：原文明确写 “Joint Money Laundering Steering Group (JMLSG)”。抽取关系正确，但中文 `J洗钱SG` 明显错误，P5B 必须修正或置空中文。
CH08-S01/CH08-S02 PEP/UBO：原文使用 PEPs、UBO。复数缩写有效，已修正脚本避免误删。
CH09-S03 UBO：原文写 UBOs，属于有效复数缩写，已修正脚本避免误删。
CH10-S02 NBFI：原文写 “NBFIs, unlike traditional banks...”，有效缩写；脚本已修正复数匹配。
```
