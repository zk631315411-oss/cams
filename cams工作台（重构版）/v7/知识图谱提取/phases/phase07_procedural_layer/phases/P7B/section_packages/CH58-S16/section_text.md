[v7u_N004819|4819] Data lineage is the process of tracking and mapping dataflows from the source system to the end user.
ZH: 数据血缘是跟踪和映射从源系统到最终用户的数据流的过程。

[v7u_N004820|4820] It provides a clear view of how organizations source data, including external sources and staging processes, where and how data transforms, and ultimately how end-user systems consume it.
ZH: 数据血缘清晰展示组织如何获取、转换数据以及最终用户系统如何消费数据。

[v7u_N004821|4821] Data lineage can help rebuild fragmented or damaged data flows and reconstruct system outputs by recreating point-in-time data feeds.
ZH: 数据血缘可帮助重建碎片化或受损的数据流，通过重现特定时间点的数据馈送来重构系统输出。

[v7u_N004822|4822] It can also assist in debugging systems by pinpointing incorrect data points such as inconsistencies, duplications, or missing information.
ZH: 数据血缘通过定位不一致、重复或缺失等错误数据点，辅助系统调试。

[v7u_N004823|4823] Data lineage can be either backward or forward. Backward data lineage goes from the end-user system to the source, while forward lineage goes from the source to the end-user system.
ZH: 数据血缘分为向后追溯（从终端到源头）和向前追溯（从源头到终端）两种方向。

[v7u_N004824|4824] Both processes are required for complete data reconciliation.
ZH: 完整的数据对账需要同时进行向后和向前两种血缘追溯。

[v7u_N004825|4825] Reconciled data allows organizations to see and understand each step along the data flow and use this information to quantify some aspects of data quality.
ZH: 对账后的数据使组织能够理解数据流的每一步，并量化数据质量的某些方面。

[v7u_N004826|4826] Quantified data reconciliation is a key metric for governance and regulatory reporting.
ZH: 量化的数据对账是治理和监管报告的关键指标。

[v7u_N004827|4827] Compliance and internal audit benefit from data lineage, as it can demonstrate how organizations adhere to strict regulations such as the GDPR or ESG-based directives and expectations.
ZH: 数据血缘有助于合规和内部审计，展示组织如何遵守《通用数据保护条例》或ESG等严格法规。

[v7u_N004828|4828] Data lineage also plays a role in data preparation processes by ensuring that data transformations are documented and efficient.
ZH: 数据血缘在数据准备过程中确保数据转换被记录且高效。

[v7u_N004829|4829] Another key advantage of data lineage is facilitation of root cause analysis when errors occur.
ZH: 数据血缘的另一个关键优势是促进错误发生时的根本原因分析。

[v7u_N004830|4830] If incorrect data appears in reports, lineage tracing helps identify the original source and transformation steps, allowing for quick resolution and reducing the risk of data corruption.
ZH: 当报告中出现错误数据时，血缘追溯有助于识别原始来源和转换步骤，实现快速解决并降低数据损坏风险。

[v7u_N004831|4831] By tracking data movements and transformations, organizations can show compliance and improve data governance.
ZH: 通过跟踪数据移动和转换，组织可以展示合规性并改进数据治理。

[v7u_N004832|4832] However, full data lineage is not always possible.
ZH: 完整的数据血缘并非总是可行的。

[v7u_N004833|4833] Source systems or in-process transformations can corrupt dataflows and disrupt how transformation outcomes are interpreted.
ZH: 源系统或过程中的转换可能破坏数据流，干扰转换结果的解读。

[v7u_N004834|4834] In these instances, it is still possible—and beneficial—to complete partial data lineage to maximize process benefit.
ZH: 在无法实现完整血缘时，完成部分数据血缘仍然可能且有益，以最大化流程收益。

[v7u_N004835|4835] The critical need for clear data lineage was highlighted in July 2024, when Citibank was fined $136 million through a joint action by the Federal Reserve and the Office of the Comptroller. Citibank was penalized for making insufficient progress in fixing data management issues identified in 2020. These prior data management issues had then resulted in a fine of $400 million after regulators identified various deficiencies, including in data quality management.
ZH: 2024年7月花旗银行因数据管理问题被美联储和货币监理署联合罚款1.36亿美元，凸显清晰数据血缘的迫切需求。

[v7u_N004836|4836] Spreadsheets and data tables present data in neatly organized rows and columns, which make reading and adjusting easier and assist with manual analysis.
ZH: 电子表格和数据表以整齐的行列呈现数据，便于阅读、调整和手动分析。

[v7u_N004837|4837] Data storage, however, often relies on relational databases, distributed file systems, and cloud architectures to optimize data for ease of retrieval and processing rather than ease of reading.
ZH: 数据存储通常依赖关系数据库、分布式文件系统和云架构，以优化检索和处理而非易读性。

[v7u_N004838|4838] Extract, transform, and load (ETL) processes bridge the gap between the complexity of how systems store data and the simplicity and readability of a spreadsheet or table.
ZH: ETL（提取、转换、加载）流程弥合了系统存储数据的复杂性与电子表格或表格的简单可读性之间的差距。

[v7u_N004839|4839] ETL processes require data to first be structured according to predefined schemas.
ZH: ETL流程要求数据首先按照预定义的模式进行结构化。

[v7u_N004840|4840] Business and IT teams have to agree on field definitions, data types, and unique data identifiers to prevent mismatches and misinterpretations and ensure consistency and uniformity across systems.
ZH: 业务和IT团队必须就字段定义、数据类型和唯一数据标识符达成一致，以防止不匹配和误解，确保跨系统的一致性和统一性。

[v7u_N004841|4841] Before extraction, validation rules check for missing values, incorrect formats, or duplicate records.
ZH: 数据提取前应用验证规则检查缺失值、格式错误或重复记录。

[v7u_N004842|4842] If quality issues or inconsistencies are found, a separate process is applied to correct, reject, or manually review the problematic data.
ZH: 发现数据质量问题或不一致时，通过单独流程进行纠正、拒绝或人工复核。

[v7u_N004843|4843] Automated extraction tools use API or database queries to pull data efficiently, reducing manual errors and ensuring completeness.
ZH: 自动化提取工具通过API或数据库查询高效拉取数据，减少人工错误并确保完整性。

[v7u_N004844|4844] API enables automated retrieval of data from various sources, such as databases, cloud services, or third-party applications, without manual intervention.
ZH: API支持从数据库、云服务或第三方应用自动检索数据，无需人工干预。

[v7u_N004845|4845] After extraction, data transitions to one of two destinations: the “landing zone” for raw data storage or the intermediary “staging area” for cleaning and preparation for loading. During this interim stage, data transformation prepares the data for use within the compliance system.
ZH: 提取后数据进入原始存储的“着陆区”或清洗准备的“暂存区”，并在此阶段进行转换。

[v7u_N004846|4846] Depending on its intended use, the data then loads into a data warehouse, data lake, or similar technology.
ZH: 根据预期用途，数据加载到数据仓库、数据湖或类似技术中。

[v7u_N004847|4847] Data warehouses store structured data optimized for analysis and reporting, while data lakes store unstructured or semi-structured data at scale.
ZH: 数据仓库存储结构化数据以优化分析和报告，数据湖大规模存储非结构化或半结构化数据。

[v7u_N004848|4848] The compliance solution then accesses the data lake, data warehouse, or similar technology through further APIs or direct feeds.
ZH: 合规解决方案通过API或直接馈送访问数据湖、数据仓库等存储。

[v7u_N004849|4849] Correctly executed extract, transform, and load processes ensure that data flows correctly from source to destination while maintaining accuracy, security, and usability.
ZH: 正确执行的ETL流程确保数据从源到目标准确、安全、可用地流动。

[v7u_N004850|4850] Data mining and data matching use advanced analytical techniques to uncover hidden patterns, correlations, anomalies, and connections within large datasets. These methods use various algorithms and analytical techniques, including machine learning models and statistical analyses, to detect anomalies and recognize patterns indicative of fraudulent behavior.
ZH: 数据挖掘和数据匹配利用高级分析技术发现大型数据集中的隐藏模式、关联、异常和连接。

[v7u_N004851|4851] Data mining and data matching help AFC professionals save time by efficiently sifting through large amounts of data. They offer a more precise and effective method of identifying potential financial crimes. This allows for quicker and more accurate responses to financial crime threats.
ZH: 数据挖掘和数据匹配帮助金融犯罪防控专业人员高效筛选大量数据，快速准确识别潜在金融犯罪。

[v7u_N004852|4852] Data mining and data matching are essential techniques in AFC systems.
ZH: 数据挖掘和数据匹配是金融犯罪防控系统中的关键技术。

[v7u_N004853|4853] Data mining extracts useful information from large complex datasets, revealing valuable patterns, insights, relationships, and trends.
ZH: 数据挖掘从大型复杂数据集中提取有用信息，揭示有价值的模式、洞察、关系和趋势。

[v7u_N004854|4854] Data mining can uncover unusual transaction patterns, such as large purchases from unexpected locations, or frequent small transactions that add up to a significant sum.
ZH: 数据挖掘可发现异常交易模式，如来自意外地点的大额购买或累计金额可观的小额频繁交易。

[v7u_N004855|4855] By analyzing these patterns, AFC professionals can recognize behaviors that deviate from typical activities.
ZH: 通过分析这些模式，金融犯罪防控专业人员可以识别偏离典型活动的行为。

[v7u_N004856|4856] Data matching involves comparing and linking data from different sources to identify inconsistencies or discrepancies.
ZH: 数据匹配涉及比较和链接不同来源的数据，以识别不一致或差异。

[v7u_N004857|4857] For example, data matching can be used to compare a customer's address with public records to verify accuracy, or cross-check insurance claims with medical records to find inconsistencies.
ZH: 数据匹配可用于将客户地址与公共记录比对以验证准确性，或交叉核对保险索赔与医疗记录以发现不一致。

[v7u_N004858|4858] This process helps to verify the authenticity of the data to detect fraudulent claims or false information.
ZH: 数据匹配有助于验证数据真实性，检测欺诈性索赔或虚假信息。

[v7u_N004859|4859] Combining data mining and data matching enhances the accuracy and effectiveness of the AFC systems.
ZH: 结合数据挖掘和数据匹配可提升金融犯罪防控系统的准确性和有效性。

[v7u_N004860|4860] Data mining might identify a cluster of suspicious transactions from a specific geographical region or demographic group.
ZH: 数据挖掘可能识别出来自特定地理区域或人口群体的可疑交易集群。

[v7u_N004861|4861] Data matching can then be used to verify the legitimacy of the customers and addresses involved in these transactions.
ZH: 数据匹配用于验证客户和地址的合法性

[v7u_N004862|4862] By cross-referencing various data sources, data matching helps confirm or rule out potential suspicious activities.
ZH: 数据匹配通过交叉引用确认或排除可疑活动

[v7u_N004863|4863] Using these techniques helps maintain strong detection rates and minimizes false positives.
ZH: 这些技术有助于维持高检测率并减少误报