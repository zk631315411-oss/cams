# v7_q_000027

教材章节：未映射

题型：single

题干：关于使用基于人工智能（AI）的系统来审查并识别适用的隐私和数据保护规则，以下哪一项陈述是正确的？

英文题干：Which of the following statements is true regarding using an artificial intelligence (AI)-based system to review and identify applicable privacy and data protection rules?

选项：

- A. 生成的结果仍需评估所识别规则的完整性和适用性。
  English: Generated results will still have to be assessed for the completeness and applicability of the identified rules
- B. 培训应侧重于所使用的规则，而不是人工智能如何执行其功能。
  English: Training should focus on the rules used and not how the AI performs its function
- C. 由于分析的规则数量众多，生成的结果很可能是准确且有效的。
  English: Generated results are likely to be accurate and valid because of the large number of rules analyzed
- D. 人工智能可能效果不佳，因为它无法被训练以识别适用于特定银行的规则。
  English: AI may be ineffective because it cannot be trained to identify rules applicable to a specific bank

## 【AI答案】

A

## 【考点】

AI系统输出须经人工验证，不能默认准确

## 【核心解析】

教材指出，AI产品提供有用信息，但AI响应应像任何外部数据一样被验证（P473）。更恰当的做法是使用AI定位主要来源，然后验证其准确性（P473）。数据验证必须包括完整性测试（确保包含所有被要求的数据）和准确性测试（确保数据符合业务需求）（P483）。因此，在隐私和数据保护规则的审查中，AI生成的结果不能被直接假设为完整且准确，必须有人工评估其识别规则的完整性和适用性。选项A「生成的结果仍需评估所识别规则的完整性和适用性」直接吻合这一原则。

教材原句："AI products provide useful information, but AI responses should be verified like any external data."

## 【错误项分析】

- **B 错误（教材直接依据）｜概念混淆**：教材明确指出有效使用AI工具需要「理解模型如何做出决策」（P448），培训若完全忽略AI如何执行其功能，与这一要求不符。B选项的表述「应侧重于规则而非AI如何执行功能」所暗示的侧重方向，不如A更契合教材强调的人机结合与验证要求。
- **C 错误（教材直接依据）｜范围或程度偏差**：题干并没有支持「规则数量众多」就能带来准确有效的因果关系。教材反而提醒AI可能产生幻觉、测试数据偏差等局限（P385），准确性取决于训练数据质量和持续调优，而非规则数量。A选项要求评估，比C的默认准确态度更符合教材对AI风险的审慎立场。
- **D 错误（范围或程度偏差）**：银行可以将静态规则演进为机器学习与AI驱动的分析（P439-440）。因此，D项声称AI无法被训练以识别适用于特定银行的规则，表述过于绝对；A项所述的人工评估和验证更符合审慎使用AI的要求。

## 【易错提醒】

（无）

## 【教材原文依据】

> 核心引用单元：`v7u_N004880`

### `v7u_N004755`

- 用于：核心解析
- 章节：Data as an input for solutions > External data
- 页码：PDF第478页 / 书内第473页
- 中文要点：AI产品提供有用信息，但AI响应应像外部数据一样被验证。
- 英文原文：AI products provide useful information, but AI responses should be verified like any external data.

### `v7u_N004756`

- 用于：核心解析
- 章节：Data as an input for solutions > External data
- 页码：PDF第478页 / 书内第473页
- 中文要点：更合适的方式是使用AI定位主要来源，然后验证其准确性。
- 英文原文：It is more appropriate to use AI to locate primary sources, which can then be verified for accuracy.

### `v7u_N004880`

- 用于：核心解析
- 章节：Data as an input for solutions > Data validation and testing
- 页码：PDF第488页 / 书内第483页
- 中文要点：数据验证必须包括完整性和准确性测试
- 英文原文：Data validation should include testing for completeness to ensure the data includes all that was asked for. It should also include testing for accuracy to ensure data is aligned to intended business requirements for the system or solution.

### `v7u_N004481`

- 用于：选项B
- 章节：Transaction monitoring scenario calibration testing > Ongoing testing and tuning for rules-based systems
- 页码：PDF第453页 / 书内第448页
- 中文要点：有效使用AI工具需要理解模型决策并确保数据集大、相关且高质量。
- 英文原文：To make effective use of AI-based tools, organizations need to understand how the models make decisions and ensure the dataset is large, relevant, and of high quality.

### `v7u_N004493`

- 用于：选项B
- 章节：Transaction monitoring scenario calibration testing > Ongoing testing and tuning for rules-based systems
- 页码：PDF第453页 / 书内第448页
- 中文要点：模型应具备高可解释性，分析师需理解并记录决策理由。
- 英文原文：When completing any cycle of training and tuning, remember that models should have high explainability. Analysts should easily understand and act on the model's decisions. They should also document the rationale for decisions for auditing purposes.

### `v7u_N002088`

- 用于：选项B
- 章节：Other laws and regulations that impact organizations > AI regulations
- 页码：PDF第220页 / 书内第215页
- 中文要点：AI法规通常强调透明度（披露AI使用方式）和问责（治理框架与监督）
- 英文原文：While AI regulations vary, jurisdictions typically emphasize transparency by requiring disclosure of how and when they use AI. They emphasize accountability by stating their governance frameworks and oversight in the AI decision-making process. This emphasis on transparency and accountability ensures the jurisdiction’s ethical AI development and usage.

### `v7u_N003852`

- 用于：选项C
- 章节：Understanding AFC technology > Artificial intelligence and machine learning
- 页码：PDF第390页 / 书内第385页
- 中文要点：AI在金融犯罪防控中存在幻觉、测试数据偏差和可解释性不足等局限
- 英文原文：However, AI solutions are not perfect at mitigating financial crime. Hallucinations, bias in testing data, and lack of explainability in some AI models are some of the challenges that organizations will need to address to ensure a sustainable solution.

### `v7u_N004494`

- 用于：选项C
- 章节：Transaction monitoring scenario calibration testing > Ongoing testing and tuning for rules-based systems
- 页码：PDF第453页 / 书内第448页
- 中文要点：训练数据的多样性和强度决定AI算法成功与否，偏差可能被放大。
- 英文原文：The diversity and strength of the training data often dictate the success of AI algorithms. Any biases or inaccuracies in the training data may be magnified when AI algorithms recognize these patterns.

### `v7u_N004497`

- 用于：选项C
- 章节：Transaction monitoring scenario calibration testing > Ongoing testing and tuning for rules-based systems
- 页码：PDF第454页 / 书内第449页
- 中文要点：监管机构期望算法透明，即解释为何特定警报被判定可疑。
- 英文原文：Regulators around the world expect algorithms to be transparent. This means providing an explanation of why a specific alert was deemed suspicious when others were not.

### `v7u_N004404`

- 用于：选项D
- 章节：Technology for payment and batch screening > Case example: Evolution of transaction monitoring
- 页码：PDF第444页 / 书内第439页
- 中文要点：交易监控从静态规则演进到机器学习和AI驱动的分析
- 英文原文：Reviewing more-recent history, Thomas notices the gradual incorporation of machine learning and other forms of AI, enabling more holistic and advanced approaches. The bank is moving away from static rules and is adopting tools that analyze customer behavior and context by comparing current transactions to historical patterns, peer group activities, and external datasets.

### `v7u_N004480`

- 用于：选项D
- 章节：Transaction monitoring scenario calibration testing > Ongoing testing and tuning for rules-based systems
- 页码：PDF第453页 / 书内第448页
- 中文要点：AI工具在交易监控中的测试和调优是一个复杂动态过程，涉及训练、测试和再训练。
- 英文原文：Ongoing testing and tuning of AI tools in transaction monitoring is a complex and dynamic process. This process involves training the systems, testing the results they generate, and retraining them if the results are not ideal.

### `v7u_N002100`

- 用于：选项D
- 章节：Other laws and regulations that impact organizations > AI regulations around the world
- 页码：PDF第221页 / 书内第216页
- 中文要点：香港依赖行业特定指南，侧重伦理与隐私，2024年《伦理人工智能框架》仅适用于银行
- 英文原文：Hong Kong relies on sector-specific guidelines with a particular focus on ethical and privacy concerns. Its principles are laid out in its 2024 Ethical Artificial Intelligence Framework. This guideline is issued by the Hong Kong Monetary Authority and applies only to banks, not all financial institutions.

## 【参考答案与参考解析】

- 题库最终参考答案：A
- 中文参考答案：A

### 中文参考解析

AI系统审查和识别隐私及数据保护规则时,尽管 AI能高效分析大量规则,但生成的结论仍需评估 其完整性和适用性.这是因为A可能无法完全理 解复杂法规的细微差别或特定情境下的适用性. 选项B错误,因为培训应同时关注规则和A执行 功能:选项C错误,因为数量多不保证准确性; 选项D错误,因为AI可被训练识别特定规则.因 此,选项A正确.

- 英文参考答案：A

### 英文参考解析

能的系统审查和识别适用的隐私与数据保护规则 时,虽然AI可分析大量规则,但无法完全替代人 工判断.选项A指出,AI生成的结果仍需评估其 完整性和适用性,这符合技术应用的现实情况 因A可能存在误判或遗漏,需人工复核确保合 规.选项B错误,因训练需兼顾规则与AI功能逻 辑;选项C高估了AI的准确性,未考虑数据偏差 风险;选项D错误,因AI可通过定制化训练适配 特定银行需求.故正确答案为A.

### 答案冲突提示

- 未发现答案冲突。
