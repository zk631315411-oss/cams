# v7_q_000166

教材章节：未映射

题型：single

题干：以下哪一项是机构采用机器学习识别可疑交易的好处？

英文题干：Which of the following is a benefit of an institution implementing machine learning to identify suspicious transactions?

选项：

- A. 通过持续的模型训练适应新的金融犯罪类型和手法
  English: Adaptable to new AFC typologies through continuous model training
- B. 通过持续的模型训练实现完全无偏且无错误
  English: Completely unbiased and without error through continuous model training
- C. 更加一致和可靠的检测结果
  English: More consistent and reliable detection outcomes
- D. 对监管机构和合规要求而言透明且易于解释的算法
  English: Transparent and easy to explain algorithms for regulator and compliance purposes

## 【AI答案】

A

## 【考点】

识别机器学习适应并发现新兴犯罪类型的能力

## 【核心解析】

机器学习模型可以分析大量数据、检测模式并动态调整预警阈值，使机构更聚焦真正可疑的活动（P385）。在行为和客户画像监控中，机器学习还能够从历史案例中学习并随时间适应，识别细微、非显性的模式，并标记传统规则可能遗漏的新兴类型（P398）。因此，A项所说的通过持续模型训练适应新的金融犯罪类型和手法，与教材中的「learn from past cases」「adapt over time」和「flag emerging typologies」直接对应，是题干所问的机器学习优势。

教材原句："Machine learning algorithms detect subtle, nonobvious patterns and can flag emerging typologies that traditional rules might miss."

## 【错误项分析】

- **B 错误**：训练数据中的偏差或不准确可能被AI算法放大（P448），因此「完全无偏且无错误」是绝对化表述。持续训练可以改善模型，但不能消除所有偏差和错误。
- **C 错误**：机器学习确实可能减少误报、提高检测效果（P385），所以C项并非毫无合理性；但更加一致和可靠的结果仍取决于训练数据的质量及其中是否存在偏差或不准确（P448）。相比之下，A项与教材明确描述的随时间适应和识别新兴类型直接对应（P398），作为单选答案更准确。
- **D 错误**：机器学习模型的决定可能难以向监管机构解释（P417），许多黑箱模型在未充分理解其局限时还可能带来风险（P449）。监管机构要求算法透明是一项治理要求，并不表示机器学习算法天然透明且易于解释。

## 【易错提醒】

「适应新兴类型」是机器学习的能力特征（P398）；「一致、可靠」是训练数据质量良好且偏差得到控制时可能达到的结果（P448）。前者可直接归于模型的学习和适应机制，后者则带有条件，不能视为无条件保证。

## 【教材原文依据】

> 核心引用单元：`v7u_N003993`

### `v7u_N003844`

- 用于：核心解析、选项C
- 章节：Understanding AFC technology > Artificial intelligence and machine learning
- 页码：PDF第390页 / 书内第385页
- 中文要点：机器学习相比规则系统能减少交易监控中的误报，并可分析数据、检测模式和动态调整预警阈值。
- 英文原文：The use of machine learning algorithms has shown improvements in reducing false positives in transaction monitoring and screening. Traditional rules-based systems generate high volumes of alerts, many of which are false positives requiring manual review. Machine learning models can analyze vast datasets, detect patterns, and refine alert thresholds dynamically, allowing financial institutions to focus on truly suspicious activity.

### `v7u_N003992`

- 用于：核心解析
- 章节：Technology and tools used across the customer life cycle > Behavioral and profile monitoring
- 页码：PDF第403页 / 书内第398页
- 中文要点：机器学习通过从历史案例中学习并随时间适应来增强行为分析。
- 英文原文：Machine learning further enhances behavioral analysis by allowing systems to learn from past cases and adapt over time.

### `v7u_N003993`

- 用于：核心解析、易错提醒
- 章节：Technology and tools used across the customer life cycle > Behavioral and profile monitoring
- 页码：PDF第403页 / 书内第398页
- 中文要点：机器学习算法能检测传统规则可能遗漏的细微非明显模式和新兴类型。
- 英文原文：Machine learning algorithms detect subtle, nonobvious patterns and can flag emerging typologies that traditional rules might miss.

### `v7u_N004195`

- 用于：选项D
- 章节：Technology for KYC > Understanding screening system logic
- 页码：PDF第422页 / 书内第417页
- 中文要点：机器学习模型决策难以向监管机构解释。
- 英文原文：However, it can be difficult to interpret and explain the decisions of these models to local regulators.

### `v7u_N004494`

- 用于：选项B、选项C、易错提醒
- 章节：Transaction monitoring scenario calibration testing > Ongoing testing and tuning for rules-based systems
- 页码：PDF第453页 / 书内第448页
- 中文要点：训练数据的多样性和强度决定AI算法成功与否，偏差或不准确可能被放大。
- 英文原文：The diversity and strength of the training data often dictate the success of AI algorithms. Any biases or inaccuracies in the training data may be magnified when AI algorithms recognize these patterns.

### `v7u_N004498`

- 用于：选项D
- 章节：Transaction monitoring scenario calibration testing > Ongoing testing and tuning for rules-based systems
- 页码：PDF第454页 / 书内第449页
- 中文要点：黑箱AI模型若未充分理解其局限性可能带来风险。
- 英文原文：While some AI algorithms offer explainability, many black-box models exist and may present risk if used without adequate understanding of its limitations.

## 【参考答案与参考解析】

- 题库最终参考答案：A
- 中文参考答案：A

### 中文参考解析

机器学习模型可以通过持续学习和训练,适应新 的可疑金融犯罪(AFC)类型,这是其重要优 势.选项B错误,因为机器学习无法实现完全无 偏且无误:选项C虽有一定道理,但一致性并非 机器学习独有的优势:选项D错误,因为部分机 器学习算法并不透明,难以解析.因此,选项A 正确描述了采用机器学习来识别可疑交易的好 处. 使里【深闻解],质取余面融考过程

- 英文参考答案：A

### 英文参考解析

机器学习模型可通过持续训练适应新型反洗钱和 反恐融资(AFC)模式.选项B错误,因任何模 型均无法做到完全无偏或无错;选项C虽有一定 合理性,但并非机器学习独有优势;选项D错 误,因机器学习算法(如神经网络)通常具有黑 箱特性,解释性较差.因此,选项A正确,体现

### 答案冲突提示

- 未发现答案冲突。
