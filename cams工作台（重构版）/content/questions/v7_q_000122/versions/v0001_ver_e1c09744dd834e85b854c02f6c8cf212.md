# v7_q_000122

教材章节：未映射

题型：single

题干：以下哪一项最能描述模糊逻辑在客户筛选系统中的应用？

英文题干：Which of the following best describes the use of fuzzy logic in customer screening systems?

选项：

- A. 它产生的输出结果包括介于"是"和"否"之间的一系列中间可能性.
  English: It produces outputs that include a range of intermediate possibilities between "Yes" and "No"
- B. 它是一种先进的分析工具,被广泛用于实施AFC控制措施.
  English: It is an advanced analytics tool widely used to implement AFC controls
- C. 它能够实现更多的精确匹配,从而减少人工审核的需求.
  English: It allows for a greater number of exact matches, reducing the need for manual review
- D. 这是一种用于提升待审核警报质量的新技术
  English: It is a new technique for enhancing the quality of alerts for review

## 【AI答案】

A

## 【考点】

模糊逻辑输出相似度概率而非绝对的是/否判断

## 【核心解析】

模糊逻辑是一种通过算法计算名称间「相似度」来判断两名称属于同一人概率的匹配技术（P420）。这意味着它的核心输出不是二元的「匹配/不匹配」，而是一系列介于「是」和「否」之间的可能性分值。题干问的是模糊逻辑在客户筛选系统中的「应用描述」，选项A——「它产生的输出结果包括介于『是』和『否』之间的一系列中间可能性」——正与教材中对模糊逻辑使用「degrees of similarity」来决定「probability」的描述完全吻合，因此最能描述其本质特征。

教材原句："This technique is accomplished through algorithms that use degrees of similarity to determine the probability that two names are the same."

## 【错误项分析】

- **B 错误（教材定义应用）｜范围或程度偏差**：教材将模糊逻辑定位为一种「匹配技术（matching technique）」（P420），而非一项实施AFC控制措施的广义「先进分析工具」。虽然CAMS教材也讨论了用于AFC的先进分析P373，但就本题所问的「在客户筛选系统中的应用」而言，教材对模糊逻辑的定义支持A更直接。
- **C 错误（教材定义应用）｜概念混淆**：模糊逻辑的核心价值在于处理拼写错误、不完整名称等不一致数据（P420），它放宽了匹配条件以减少漏报，而非追求「精确匹配」。追求精确匹配是其对立面——确定性匹配（deterministic matching）的特征。教材在讨论模糊逻辑时强调它导致「部分匹配」，这本身就意味着它不是精确匹配。
- **D 错误（教材定义应用）｜概念混淆**：模糊逻辑是一种名称匹配技术，其直接作用是计算相似度并产生匹配结果，不是对既有警报进行调查或处置。「新技术」也不是其定义特征，因此D混淆了匹配生成与警报审核两个环节。

## 【易错提醒】

模糊逻辑的核心是「相似度」（不是精确匹配），它放松匹配条件以减少漏报，但代价是增加误报（部分匹配需人工调查）。容易将其与追求「精确匹配」的确定性匹配混淆。

## 【教材原文依据】

> 核心引用单元：`v7u_N004218`

### `v7u_N004218`

- 用于：核心解析、选项B、选项C、选项D、易错提醒
- 章节：Technology for KYC > Fuzzy logic and partial matches
- 页码：PDF第425页 / 书内第420页
- 中文要点：模糊逻辑通过相似度算法判断两个名称是否为同一人。
- 英文原文：This technique is accomplished through algorithms that use degrees of similarity to determine the probability that two names are the same.

### `v7u_N004217`

- 用于：选项B、选项C、选项D
- 章节：Technology for KYC > Fuzzy logic and partial matches
- 页码：PDF第425页 / 书内第420页
- 中文要点：模糊逻辑是一种匹配技术，用于克服记录缺陷和数据库问题，提高筛查有效性。
- 英文原文：Fuzzy logic is a matching technique that is used to increase the effectiveness of screening processes by overcoming problems such as flawed records and databases.

### `v7u_N004179`

- 用于：选项B
- 章节：Technology for KYC > How does technology help screening?
- 页码：PDF第421页 / 书内第416页
- 中文要点：模糊逻辑匹配使用算法匹配相似但不完全相同的名称，处理拼写、打字错误和翻译差异。
- 英文原文：Fuzzy logic matching uses algorithms to match names that are similar but not identical, accounting for variations in spelling, typos, and translations.

### `v7u_N004221`

- 用于：选项C
- 章节：Technology for KYC > Fuzzy logic and partial matches
- 页码：PDF第425页 / 书内第420页
- 中文要点：部分匹配指被筛查实体与名单条目基于模糊逻辑等因素相似。
- 英文原文：A partial match means the entity being screened is similar to an entry on a list, based on fuzzy logic and potentially other identifying factors, such as date of birth.

### `v7u_N004188`

- 用于：选项D
- 章节：Technology for KYC > Understanding screening system logic
- 页码：PDF第422页 / 书内第417页
- 中文要点：模糊逻辑匹配降低因名称细微差异或错误而遗漏匹配的风险
- 英文原文：It improves detection by reducing the risk of missing matches due to minor differences or errors in names.

### `v7u_N004222`

- 用于：易错提醒
- 章节：未标注
- 页码：PDF第425页 / 书内第420页
- 中文要点：部分匹配需要人工介入以判断是否为真实匹配。
- 英文原文：Partial matches require further human intervention to determine if the match is a true match.

## 【参考答案与参考解析】

- 题库最终参考答案：A
- 中文参考答案：A

### 中文参考解析

模糊逻辑在客户筛选系统中的应用,主要体现在 它能够处理不确定性和模糊性,产生的输出结果 包括介于“是”和“否”之间的一系列中间可能性.选 项A准确描述了这一特性.选项B中AFC控制措 施的描述不准确,模糊逻辑并非专为AFC设计; 选项C提到实现更精确匹配,模糊逻辑实际是处 理不确定性,而非追求精确;选项D提到提升待 审核警报质量的新技术,模糊逻辑并非新技术, 且主要功能是处理模糊性,而非直接提升警报质 量. 度 难 源

- 英文参考答案：A

### 英文参考解析

模糊逻辑在客户筛选系统中的应用,主要体现在 它能够处理不确定性和模糊性,产生的输出结果 包括介于“是”和“否”之间的一系列中间可能性.选 项A准确描述了这一特性.选项B中AFC控制措 施的描述不准确,模糊逻辑并非专为AFC设计; 选项C提到实现更精确匹配,模糊逻辑实际是处 理不确定性,而非追求精确;选项D提到提升待 审核警报质量的新技术,模糊逻辑并非新技术, 且主要功能是处理模糊性,而非直接提升警报质 量. 度 难 源

### 答案冲突提示

- 未发现答案冲突。
