# v7_q_000382

教材章节：未映射

题型：multiple

题干：使用人工智能(AI)与传统基于规则的交易监控相结合或替代其进行交易监控的优势包括:(选择两项.)

英文题干：Benefits of using artificial intelligence (AI) in conjunction with, or in place of, traditional rules-based transaction monitoring include that AI can: (Select Two.)

选项：

- A. 增加误报警报的数量
  English: Increase the number of false positive alerts
- B. 在机器训练阶段创建无偏场景
  English: Create unbiased scenarios during the machine training phase
- C. 识别客户行为的变化,以更准确地评估风险
  English: Identify changes in customer behavior to more accurately assess risk
- D. 生成客户风险评分以预测潜在的金融犯罪活动
  English: Generate customer risk scores to predict potential financial crime activity

## 【AI答案】

C、D

> **需人工复核**
>
> - 部分选项证据不足：B

## 【考点】

AI/机器学习在交易监控中相比传统规则系统的核心优势

## 【核心解析】

教材通过案例展示了交易监控技术的演进：从静态的IF:THEN规则系统，逐步转向采用机器学习和AI驱动的工具，这些工具能够「分析客户行为和上下文，将当前交易与历史模式、同业群体活动和外部数据集进行比较」（P439）。这意味着AI的核心优势在于动态地理解客户，而非机械地执行预设阈值。选项C「识别客户行为的变化，以更准确地评估风险」正是对这一动态分析能力的直接描述——系统通过对比客户历史行为画像来检测异常偏差，从而减少误报，实现更精准的风险评估（P398、P439）。选项D「生成客户风险评分以辅助识别和评估潜在的金融犯罪风险」则对应了AI将这些行为分析、交易异常和外部风险指标综合量化的能力。教材案例中，Magnify Bank正是基于交易异常、历史行为和外部风险指标来计算客户风险评分，生成如「平均交易规模」「高风险交易数量」等属性，可用于更有针对性地识别和评估异常活动（P478）。

教材原句："The bank is moving away from static rules and is adopting tools that analyze customer behavior and context by comparing current transactions to historical patterns, peer group activities, and external datasets."

## 【错误项分析】

- **A 错误｜方向相反**：与传统规则系统产生大量误报不同，机器学习算法能够减少交易监控中的误报（P398、P448），而不是增加误报警报。
- **B 错误**：AI模型训练需要使用广泛且具有代表性的交易样本，以降低可能扭曲结果的统计偏差（P385）。AI本身不能保证自动创建无偏场景；相比之下，C和D更直接体现AI在风险识别准确性方面的优势。

## 【易错提醒】

注意区分「避免偏差」与「创建无偏场景」。教材的立场是，AI系统本身会从数据中学习模式，如果输入数据存在统计偏差，模型结果就会被扭曲（P385）。因此，机构的职责是通过确保数据集广泛且高质量来「避免」偏差，但这不等于AI能自动创建无偏的客观真理。

## 【教材原文依据】

> 核心引用单元：`v7u_N004404`

### `v7u_N004404`

- 用于：核心解析
- 章节：Technology for payment and batch screening > Case example: Evolution of transaction monitoring
- 页码：PDF第444页 / 书内第439页
- 中文要点：交易监控从静态规则演进到机器学习和AI驱动的分析
- 英文原文：Reviewing more-recent history, Thomas notices the gradual incorporation of machine learning and other forms of AI, enabling more holistic and advanced approaches. The bank is moving away from static rules and is adopting tools that analyze customer behavior and context by comparing current transactions to historical patterns, peer group activities, and external datasets.

### `v7u_N003988`

- 用于：核心解析
- 章节：Technology and tools used across the customer life cycle > Behavioral and profile monitoring
- 页码：PDF第403页 / 书内第398页
- 中文要点：行为交易监控通过分析客户历史行为构建动态画像并检测异常
- 英文原文：Instead of relying solely on static rules-based thresholds, behavioral transaction monitoring analyzes a customer’s historical transaction behavior to build dynamic profiles and detect anomalies that may signal suspicious activity.

### `v7u_N004810`

- 用于：核心解析
- 章节：Data as an input for solutions > Case example: Handling increased alert volume
- 页码：PDF第483页 / 书内第478页
- 中文要点：银行基于交易异常、历史行为和外部风险指标计算客户风险评分，生成平均交易规模等属性。
- 英文原文：To aggregate customers’ data and thus benefit from synergies among the data, Magnify Bank calculates the customer risk scores based on transaction anomalies, historical behaviors, and external risk indicators. The bank generates attributes such as "average transaction size," "number of high-risk transactions," and "recent adverse media mentions.”

### `v7u_N003844`

- 用于：选项A
- 章节：Understanding AFC technology > Artificial intelligence and machine learning
- 页码：PDF第390页 / 书内第385页
- 中文要点：机器学习相比规则系统能减少交易监控中的误报
- 英文原文：The use of machine learning algorithms has shown improvements in reducing false positives in transaction monitoring and screening. Traditional rules-based systems generate high volumes of alerts, many of which are false positives requiring manual review. Machine learning models can analyze vast datasets, detect patterns, and refine alert thresholds dynamically, allowing financial institutions to focus on truly suspicious activity.

### `v7u_N004482`

- 用于：易错提醒
- 章节：未标注
- 页码：PDF第453页 / 书内第448页
- 中文要点：数据集必须包含广泛的交易样本以避免统计偏差。
- 英文原文：To avoid statistical bias that might skew results, ensure the dataset includes a broad sample of transactions, not only those transactions that generated an alert.

## 【参考答案与参考解析】

- 题库最终参考答案：C、D
- 中文参考答案：C、D

### 中文参考解析

人工智能(AI)通过模式学习和异常检测,能够 更有效地识别客户行为的细微变化(C),并基 于多维数据生成动态的风险评分来预测潜在犯罪 活动(D).结合或替代基于规则的传统系统, 可以提高监控的准确性和适应性,减少误报.A 项描述的是劣势而非优势.B项“创建无偏场景”并 非A在此应用中的核心优势描述

- 英文参考答案：C、D

### 英文参考解析

AI应用于反洗钱和反恐融资合规项目,与传统基 于规则的交易监控相比,优势在于:C选项,AI 能通过分析客户交易数据,识别客户行为变化 从而更准确评估风险:D选项,AI可利用算法模 型,根据客户历史交易、身份信息等多维度数 据,生成客户风险评分,预测潜在金融犯罪活 动.A选项增加误报数量是端,B选项机器训 练阶段难以做到完全无偏见.易错提醒:注意区 分AI的优势与潜在问题,避免选择描述弊端的选 项.

### 答案冲突提示

- 未发现答案冲突。
