# v7_q_000238

教材章节：未映射

题型：multiple

题干：在基于规则的交易监控方法中,用于检测可疑活动的最常见技术有哪些？(选择两项.)

英文题干：Which techniques are most commonly used in a rules-based approach to transaction monitoring for detecting suspicious activities? (Choose two.)

选项：

- A. 利用预设规则标记特定的交易模式
  English: Using predefined rules to flag specific transaction patterns
- B. 随机标记交易以作进一步调查
  English: Randomly flagging transactions for further investigation
- C. 通过统计方法调整监测场景以提高准确性
  English: Statistical tuning of monitoring scenarios to improve accuracy
- D. 利用先进的机器学习模型检测异常值
  English: Using advanced machine learning models to detect outliers
- E. 设置用于自动警报的交易阀值
  English: Setting transaction thresholds for automated alerts

## 【AI答案】

A、E

## 【考点】

区分规则监控的技术手段与调优、AI等其他概念

## 【核心解析】

基于规则的交易监控是监控客户交易的基本方法（P436）。金融机构根据已知风险因素或监管要求创建预定义规则，设定静态、可预测的阈值（P436）。其核心检测机制包含两类技术：一是利用预设规则对特定交易模式进行标记——当交易命中某个已知风险特征（如特定金额区间、特定司法管辖区）时即触发标记；二是设置交易阈值以驱动自动警报——阈值定义了触发警报所需的最低活动水平，超限交易自动产生警报（P331）。题干问的是「在基于规则的方法中」用于检测可疑活动的技术，A（利用预设规则标记特定交易模式）和E（设置用于自动警报的交易阈值）正是该方法的两个基本构件，二者共同构成了规则监控的运作骨架。

教材原句："Financial institutions create rules based on known risk factors or regulatory requirements. They set predefined rules or thresholds, which are static, predictable, and easy to implement and understand."（P436）

## 【错误项分析】

- **B 错误**：基于规则的监控本质上是「命中即触发」的确定性机制，而非随机抽样。教材中没有任何单元将随机标记列为规则监控的技术手段；规则系统依赖于预设条件的有序匹配，随机标记不属于这一框架下的检测逻辑。
- **C 错误**：阈值校准（calibration/tuning）是基于统计数据调整已有规则的参数以提高效率，属于部署后的优化与维护环节（P445-P446），而非检测可疑活动的初始技术手段本身。题干更直接匹配「创建规则和设定阈值」这一核心检测机制，而非「调优已有规则」。
- **D 错误**：教材指出传统上使用基于规则的系统，但组织正逐步采用基于AI的控制来改进可疑活动检测（P328）。机器学习属于AI-based controls，与rules-based approach属于不同代际的监控范式。题干明确限定在「基于规则的方法中」，D所描述的技术超出了该范畴。

## 【易错提醒】

注意调优（tuning）和规则监控本身的区别：调优涉及场景设置、客户细分、阈值设置和频率四个组成部分，是对已有规则的事后优化（P445-P446），不替代「预设规则」和「阈值警报」本身作为检测手段的地位（P436）。

## 【教材原文依据】

> 核心引用单元：`v7u_N004361`

### `v7u_N004361`

- 用于：核心解析、选项C
- 章节：Technology for payment and batch screening > Rules-based transaction monitoring
- 页码：PDF第441页 / 书内第436页
- 中文要点：基于规则的交易监控是监控客户交易的基本方法。
- 英文原文：Rules-based transaction monitoring is a fundamental approach to monitoring customer transactions.

### `v7u_N004362`

- 用于：核心解析、选项B、选项D
- 章节：未标注
- 页码：PDF第441页 / 书内第436页
- 中文要点：金融机构根据已知风险因素或监管要求创建规则，设定静态、可预测的阈值。
- 英文原文：Financial institutions create rules based on known risk factors or regulatory requirements. They set predefined rules or thresholds, which are static, predictable, and easy to implement and understand.

### `v7u_N003280`

- 用于：核心解析
- 章节：Transaction monitoring > Transaction monitoring system tuning
- 页码：PDF第336页 / 书内第331页
- 中文要点：阈值设置定义了触发警报所需的最低活动水平。
- 英文原文：Threshold setting defines the minimum level of activity required for a transaction to trigger an alert.

### `v7u_N004364`

- 用于：选项B、选项D
- 章节：Technology for payment and batch screening > Rules-based transaction monitoring
- 页码：PDF第441页 / 书内第436页
- 中文要点：举例：金融机构设定1万美元阈值，超限交易触发警报和加强审查。
- 英文原文：For example, many financial institutions establish rule thresholds, such as US$10,000, to limit the potential impact of financial crime. Conducting a transaction above the threshold results in alerts, required reporting, and increased scrutiny of the transaction.

### `v7u_N003236`

- 用于：选项B、选项D
- 章节：Transaction monitoring > Transaction monitoring controls
- 页码：PDF第333页 / 书内第328页
- 中文要点：交易监控从基于规则的系统向基于AI的控制演进。
- 英文原文：Traditionally, rules-based systems were used. However, organizations are increasingly adopting AI-based controls to improve suspicious activity detection.

### `v7u_N004445`

- 用于：选项C
- 章节：Transaction monitoring scenario calibration testing
- 页码：PDF第450页 / 书内第445页
- 中文要点：交易监控场景校准涉及基于交易数据、风险模型和风险为本方法调整参数
- 英文原文：Transaction monitoring scenarios require careful calibration to effectively detect suspicious activities while minimizing false positives. Calibration, or threshold tuning, involves adjusting parameters based on empirical transaction data, risk models, and a broader risk-based approach.

### `v7u_N004465`

- 用于：选项C
- 章节：Transaction monitoring scenario calibration testing > Ongoing testing and tuning for rules-based systems
- 页码：PDF第451页 / 书内第446页
- 中文要点：基于规则的交易监控系统通常更易于测试和调优。
- 英文原文：Rules-based systems are typically easier to test and tune.

## 【参考答案与参考解析】

- 题库最终参考答案：A、E
- 中文参考答案：A、E

### 中文参考解析

在基于规则的交易监控中,检测可疑活动的常见 技术需直接关联规则应用与阈值触发.选项A通 过预设规则标记特定交易模式,直接匹配已知风 险特征,是规则监控的核心手段;选项E设置交 易阈值触发自动警报,属于规则驱动的量化监控 方法.选项B依赖随机标记,缺乏规则指向性; 选项C涉及统计调整监测场景,属动态优化而非 基础检测技术:选项D的机器学习模型属于基于 行为的异常检测,与规则监控无关.因此,答案 为A、E.易错提醒:注意区分规则监控与行为 分析、动态优化等高级技术. 食食文

- 英文参考答案：A、E

### 英文参考解析

emostcommonlyusedinarules-basedapproa chtotransactionmonitoringforDetectingsuspi ciousactivities?(Choosetwo.) Usingpredefinedrulestoflagspecifict ransactionpatterns Randomlyflaggingtransactionsforfurt B herinvestigation Statisticaltuningofmonitoringscenari C ostoimproveaccuracy Usingadvancedmachinelearningmo D delstodetectoutliers Settingtransactionthresholdsforauto matedalerts 正确答案AE您选择/ 试题详解

### 答案冲突提示

- 未发现答案冲突。
