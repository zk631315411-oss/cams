# v7_q_000150

教材章节：未映射

题型：single

题干：哪种交易监控工具的特性最能帮助金融机构迅速应对新兴的金融犯罪风险和威胁？

英文题干：Which transaction monitoring tool characteristic would best support financial institutions in rapidly responding to emerging financial crime risks and threats?

选项：

- A. 基于云的部署
  English: Cloud-based deployment
- B. 可配置的报告功能
  English: Configurable reporting
- C. 完全集成的人工智能(AI)
  English: Fully integrated artificial intelligence (AI)
- D. 构建、迭代和测试规则的能力
  English: Ability to build, iterate, and test rules

## 【AI答案】

D

## 【考点】

交易监控规则的测试与调优机制如何响应新兴风险

## 【核心解析】

金融机构在开发、校准和部署交易监控场景后，应持续测试和调优（continuously test and tune）以确保有效性（P446）。测试除定期开展外，也会由监管变化、新兴金融犯罪趋势或客户交易行为变化等特殊情形触发（P446）。选项D所述构建、迭代和测试规则的能力，使机构能够针对新风险调整监控规则并验证调整效果。基于规则的系统通常也更易于测试和调优（P446），因此D与题干强调的快速响应最直接匹配。

教材原句："This process occurs periodically and due to special circumstances, such as regulatory changes, emerging financial crime trends, or shifts in customer transaction behavior."

## 【错误项分析】

- **A 错误**：「基于云的部署」在教材中主要关联的是总拥有成本（total cost of ownership）的考量——机构需评估云端系统与本地服务器的成本对比。题干关注的是能否迅速应对新兴威胁，而非基础设施的部署方式。云部署可能为系统提供可扩展性，但它本身不是直接检测、调整、验证新风险规则的能力，匹配度不如D项直接。
- **B 错误**：「可配置的报告功能」在教材中出现的语境是治理委员会（governance committees）的评估汇报流程——报告需平衡收益与风险以支持知情决策。这类报告功能侧重于输出端的信息呈现与合规文书，而非输入端对新威胁的主动检测与规则调整。题干问的是「迅速应对」威胁的工具特性，生成报告更接近于应对之后的记录与沟通环节。
- **C 错误**：「完全集成的人工智能」确实能增强检测能力——AI可以优先排序筛查结果、检测异常和减少误报，且能通过模式识别持续学习和改进。然而，教材也指出AI工具的测试和调优是一个「复杂且动态的过程」，涉及训练、测试和再训练，对数据集的质量和广度要求高（P448）。相比之下，基于规则的系统「通常更易于测试和调优」（P446），在面对新兴威胁时需要的是快速响应，D项所描述的能力在操作上更直接、更灵活。AI并非不能应对，而是其调优路径不如基于规则的迭代测试那样轻量和快速。

## 【易错提醒】

AI和规则系统都能检测犯罪，但二者响应新兴威胁的机制不同：规则系统靠人工快速构建和调优新规则，路径短、速度快（P446）；AI系统则需要训练数据积累和模型再训练，过程更复杂（P448）。题干强调「迅速」，规则迭代路径更直接匹配。

## 【教材原文依据】

> 核心引用单元：`v7u_N004464`

### `v7u_N004463`

- 用于：核心解析
- 章节：Transaction monitoring scenario calibration testing > Ongoing testing and tuning for rules-based systems
- 页码：PDF第451页 / 书内第446页
- 中文要点：金融机构应持续测试和调优交易监控场景以确保有效性。
- 英文原文：Once financial institutions develop, calibrate, and deploy transaction monitoring scenarios, they should continuously test and tune them to ensure effectiveness.

### `v7u_N004464`

- 用于：核心解析
- 章节：Transaction monitoring scenario calibration testing > Ongoing testing and tuning for rules-based systems
- 页码：PDF第451页 / 书内第446页
- 中文要点：定期及特殊情形（如监管变化、新兴金融犯罪趋势、客户交易行为变化）触发测试。
- 英文原文：This process occurs periodically and due to special circumstances, such as regulatory changes, emerging financial crime trends, or shifts in customer transaction behavior.

### `v7u_N004465`

- 用于：核心解析、选项C、易错提醒
- 章节：Transaction monitoring scenario calibration testing > Ongoing testing and tuning for rules-based systems
- 页码：PDF第451页 / 书内第446页
- 中文要点：基于规则的交易监控系统通常更易于测试和调优。
- 英文原文：Rules-based systems are typically easier to test and tune.

### `v7u_N004480`

- 用于：易错提醒
- 章节：未标注
- 页码：PDF第453页 / 书内第448页
- 中文要点：AI工具在交易监控中的测试和调优是一个复杂动态过程，涉及训练、测试和再训练。
- 英文原文：Ongoing testing and tuning of AI tools in transaction monitoring is a complex and dynamic process. This process involves training the systems, testing the results they generate, and retraining them if the results are not ideal.

## 【参考答案与参考解析】

- 题库最终参考答案：D
- 中文参考答案：D

### 中文参考解析

金融机构需迅速应对新兴金融犯罪风险,这要求 交易监控工具具备灵活调整监控规则的能力.选 项A“基于云的部署”主要提升部署便捷性和可扩展 性,与应对新兴风险无直接关联;选项B“可配置 的报告功能”虽能提供定制化报告,但无法直接增 强风险应对能力:选项C“完全集成的人工智能 (AI)”虽能提升监控效率,但需依赖既有规则和 模型,难以迅速适应新风险;选项D“构建、迭代 和测试规则的能力"则允许金融机构根据新兴风险 特征,快速调整监控规则,从而有效应对新威 胁.因此,选项D最符合题意.

- 英文参考答案：D

### 英文参考解析

未提供。

### 答案冲突提示

- 未发现答案冲突。
