# v7_q_000163

教材章节：未映射

题型：single

题干：在确定制裁筛查的模糊匹配阈值时,应考虑以下因素:

英文题干：When deciding on the fuzzy matching threshold for sanctions screening, consideration should be given to:

选项：

- A. 处理潜在匹配项所带来的操作负担.
  English: The operational burden of dealing with potential matches.
- B. 对违规行为处以罚款的金额.
  English: The value of fines for non-compliance.
- C. 团队处理潜在匹配的经验
  English: The experience of the team dealing with potential matches.
- D. 要筛选的数据是否可靠且经过验证
  English: Whether the data to be screened is reliable and verified.

## 【AI答案】

A

## 【考点】

理解制裁筛查模糊匹配阈值与警报量、误报及调查工作量之间的关系

## 【核心解析】

模糊逻辑配置会生成部分匹配，这些匹配随后必须接受调查，以判断是真实匹配还是误报（P421）。在制裁筛查系统中，机构可以调节模糊逻辑级别（P421）；调整参数会增加或减少警报数量，调优则有助于管理警报量并减少误报（P421）。异常高的误报比例、超出预期的警报数量或完全没有警报，都会触发手动调优（P422）。因此，阈值会直接影响需要处理的潜在匹配数量、误报数量及相应调查工作量，A在四个选项中最直接。

需要注意，教材同时指出，机构不能简单按照团队规模限制系统生成的警报数量，因为这可能损害调查质量并造成不合规（P421）。这并不否定操作负担是阈值调优时的现实考量，而是说明不能为了迁就处理能力而机械压低警报量。

教材原句："Tuning helps you manage the volume of alerts and reduces the number of false positives a system generates."

## 【错误项分析】

- **B 错误**：模糊阈值应根据警报数量、误报比例及系统逻辑进行调优（P422）。违规罚款属于不合规可能产生的后果，不能直接决定模糊匹配级别。
- **C 错误**：团队处理潜在匹配的经验不是模糊逻辑阈值的设定指标。团队规模也不应成为硬性限制警报数量的依据，否则可能影响调查质量（P421）；因此不能据此推出应按团队经验设定阈值。
- **D 错误**：教材关于使用关键词过滤无关信息以及选择可信、可靠来源的内容，针对的是负面媒体筛查，不是制裁筛查的模糊匹配阈值（P422）。此外，「可信、可靠」也不等同于选项所说的「经过验证」，因此D与题干的匹配度不如A。

## 【易错提醒】

判断阈值题时，应优先寻找教材明确连接的调优结果：部分匹配需要调查，参数会改变警报数量，误报率和异常警报量会触发手动调优（P421-P422）。这些因素共同指向潜在匹配的处理负担。操作负担可以纳入考量，但不能简单按团队规模设定警报上限（P421）。

## 【教材原文依据】

> 核心引用单元：`v7u_N004240`

### `v7u_N004234`

- 用于：核心解析、选项A
- 章节：Technology for KYC > Fuzzy logic and partial matches
- 页码：PDF第426页 / 书内第421页
- 中文要点：基于模糊逻辑配置生成的部分匹配需要接受调查，以确定是真实匹配还是误报。
- 英文原文：Based on the fuzzy logic configuration, an organization will generate partial matches. These partial matches should then be investigated to determine whether they are true matches or false positives.

### `v7u_N004239`

- 用于：核心解析、选项A
- 章节：Technology for KYC > Screening system tuning
- 页码：PDF第426页 / 书内第421页
- 中文要点：在制裁筛查系统中，可调优模糊逻辑级别以检测名称变体。
- 英文原文：In a sanctions screening system, you might tune the fuzzy logic levels to adjust the fuzziness level, detecting variations in names, such as misspellings, abbreviations, and transliterations.

### `v7u_N004240`

- 用于：核心解析、选项A、易错提醒
- 章节：Technology for KYC > Screening system tuning
- 页码：PDF第426页 / 书内第421页
- 中文要点：调优有助于管理警报量并减少系统生成的误报。
- 英文原文：Tuning helps you manage the volume of alerts and reduces the number of false positives a system generates.

### `v7u_N004241`

- 用于：核心解析、选项A、易错提醒
- 章节：Technology for KYC > Screening system tuning
- 页码：PDF第426页 / 书内第421页
- 中文要点：可通过调整参数来增加或减少警报数量。
- 英文原文：You can adjust parameters to increase or decrease the number of alerts.

### `v7u_N004242`

- 用于：核心解析、选项C、易错提醒
- 章节：Technology for KYC > Screening system tuning
- 页码：PDF第426页 / 书内第421页
- 中文要点：不应根据团队规模限制系统生成的预警数量。
- 英文原文：However, organizations should not limit the number of alerts the system generates based on the size of the team, as this might compromise the quality of investigations and lead to noncompliance with regulatory obligations.

### `v7u_N004245`

- 用于：核心解析、选项A（手动调优指标列表引导）
- 章节：Technology for KYC > Screening system tuning
- 页码：PDF第427页 / 书内第422页
- 中文要点：以下指标会触发手动调优。
- 英文原文：Indicators that lead to manual tuning include:

### `v7u_N004246`

- 用于：核心解析、选项A
- 章节：Technology for KYC > Screening system tuning
- 页码：PDF第427页 / 书内第422页
- 中文要点：筛查系统产生异常高比例的误报警报。
- 英文原文：The screening system generates a remarkably high percentage of false positive alerts.

### `v7u_N004247`

- 用于：核心解析、选项A
- 章节：Technology for KYC > Screening system tuning
- 页码：PDF第427页 / 书内第422页
- 中文要点：系统生成的警报数量超出预期。
- 英文原文：The system generates more alerts than expected.

### `v7u_N004248`

- 用于：核心解析、选项A
- 章节：Technology for KYC > Screening system tuning
- 页码：PDF第427页 / 书内第422页
- 中文要点：筛查系统没有生成任何警报。
- 英文原文：The screening system generates no alerts.

### `v7u_N004249`

- 用于：核心解析、选项A
- 章节：Technology for KYC > Screening system tuning
- 页码：PDF第427页 / 书内第422页
- 中文要点：金融机构应根据系统类型及其采用的逻辑调优筛查系统参数。
- 英文原文：Financial institutions should tune the parameters within a screening system depending on the type of system and the logic it implements.

### `v7u_N004250`

- 用于：选项D（说明其证据属于负面媒体筛查语境）
- 章节：Technology for KYC > Screening system tuning
- 页码：PDF第427页 / 书内第422页
- 中文要点：负面媒体筛查系统通过调优关键词和短语过滤无关信息。
- 英文原文：For an adverse media screening system, tune parameters such as keywords and phrases to filter out irrelevant information, ensuring the organization focuses only on actual adverse media.

### `v7u_N004251`

- 用于：选项D（仅支持选择可信、可靠的来源）
- 章节：Technology for KYC > Screening system tuning
- 页码：PDF第427页 / 书内第422页
- 中文要点：应谨慎选择来源，确保系统仅使用可信可靠的来源。
- 英文原文：Organizations should also carefully select their sources to ensure the system uses only credible and reliable sources.

## 【参考答案与参考解析】

- 题库最终参考答案：D
- 中文参考答案：D

### 中文参考解析

在确定制裁筛查的模糊匹配阀值时,需确保数据 准确可靠.选项D“要筛选的数据是否可靠且经过 验证"直接关联数据质量,是设定值的关键前 坦芒数据不可告式土经哈证模糊血配生甲县

- 英文参考答案：D

### 英文参考解析

-[ComplianceStandardsforAMLandCF 单选 T]Whendecidingonthefuzzymatchingthresh oldforsanctionsscreening,considerationshoul dbeGivento: theoperationalburdenofdealingwith A potentialmatches. thevalueoffinesforNon-compliance B theexperienceoftheteamdealingwit C hpotentialmatches. whetherthedatatobescreenedIsreli ableandverified. 正确答案D您选择/ 试题详解

### 答案冲突提示

- AI答案=A，题库最终参考答案=D。经教材证据复核，不采纳参考答案D：其所依赖的可信、可靠来源表述属于负面媒体筛查来源选择语境，未说明制裁筛查模糊阈值，也未要求数据必须经过验证；教材关于警报量、误报和调查工作量的直接证据更支持A。
