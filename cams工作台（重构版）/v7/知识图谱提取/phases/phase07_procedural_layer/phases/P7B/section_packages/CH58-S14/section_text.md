[v7u_N004801|4801] Magnify Bank has expanded and grown significantly over the past several years, and its transaction monitoring system has had issues keeping up with the increasing volume and complexity of alert activity. A central issue is that data comes to the system from several sources, and this data is often incomplete or provided in different formats, making the downstream analysis unreliable and, in some cases, obsolete. Magnify Bank has initiated a project to integrate data from multiple source systems and prepare it for various end-user applications.
ZH: Magnify Bank因交易量增长和告警复杂性增加，启动数据整合项目以解决数据不完整和格式不一致问题。

[v7u_N004802|4802] Magnify Bank begins by collecting data from internal systems, such as the KYC and customer onboarding systems and the transaction processing system. It also collects external data from sanctions and PEP lists, as well as adverse media reports.
ZH: Magnify Bank从内部系统（了解你的客户、客户准入、交易处理）和外部来源（制裁名单、政治敏感人物名单、负面媒体）收集数据。

[v7u_N004803|4803] The bank prepares the data by extracting it from source databases, document stores, and external sources.
ZH: 银行从源数据库、文档存储和外部来源提取数据。

[v7u_N004804|4804] A review of the data reveals several issues that the bank needs to address before it can integrate and use that data. The data includes inconsistent formats and fields, missing information, and duplication.
ZH: 数据审查发现格式不一致、字段缺失、信息重复等质量问题。

[v7u_N004805|4805] The bank starts by standardizing the data into a common schema, according to the data dictionary.
ZH: 银行根据数据字典将数据标准化为通用模式。

[v7u_N004806|4806] In the cleaning and transformation process, Magnify Bank performs deduplication and standardization protocols.
ZH: 在清洗和转换过程中，Magnify Bank执行去重和标准化协议。

[v7u_N004807|4807] It addresses missing data by using automated techniques and flagging incomplete records for manual review and remediation.
ZH: 通过自动化技术处理缺失数据，并标记不完整记录供人工审查和修正。

[v7u_N004808|4808] It performs entity resolution to consistently identify customer identities across different datasets by using fuzzy logic and machine learning.
ZH: 使用模糊逻辑和机器学习进行实体解析，跨数据集一致识别客户身份。

[v7u_N004809|4809] Next, Magnify Bank performs data integration by merging the data into a centralized warehouse for analytics and reporting. The bank creates a unified profile for customers, including consolidated attributes from all sources. The bank then enriches the data by linking customer behavior with external risk indicators.
ZH: Magnify Bank将数据合并到中央仓库，创建统一客户档案，并关联外部风险指标进行数据丰富。

[v7u_N004810|4810] To aggregate customers’ data and thus benefit from synergies among the data, Magnify Bank calculates the customer risk scores based on transaction anomalies, historical behaviors, and external risk indicators. The bank generates attributes such as "average transaction size," "number of high-risk transactions," and "recent adverse media mentions.”
ZH: 银行基于交易异常、历史行为和外部风险指标计算客户风险评分，生成平均交易规模等属性。

[v7u_N004811|4811] The bank leverages outputs in several end-user systems to make informed decisions regarding customer risk level. This includes the financial crime detection system, regulatory compliance dashboard, and customer record management system. All of these systems work together to produce a comprehensive risk assessment for the customer.
ZH: 银行利用金融犯罪检测系统、合规仪表板和客户记录管理系统等终端系统进行客户风险评估。

[v7u_N004812|4812] Magnify Bank integrates the customer risk profiles with transaction data in the TM system to detect anomalies and trigger alerts.
ZH: Magnify Bank将客户风险档案与交易数据整合到交易监控系统中，以检测异常并触发告警。

[v7u_N004813|4813] By ensuring that the data going into the TM system has been properly standardized and integrated, the transaction monitoring process is now more reliable and efficient, reducing the number of false positives and the risk of missing suspicious behavior.
ZH: 标准化和整合的数据使交易监控更可靠高效，减少误报和漏报风险。