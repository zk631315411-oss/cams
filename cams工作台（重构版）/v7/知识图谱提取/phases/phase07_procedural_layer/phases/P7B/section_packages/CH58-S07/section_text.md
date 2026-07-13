[v7u_N004711|4711] Data comes from many different sources in the organization. Therefore, it has different labels, structures, and levels of accuracy and completeness.
ZH: 机构内数据来源多样，标签、结构、准确性和完整性各异

[v7u_N004712|4712] For example, monitoring and payment screening systems receive customer account data from one data store and attempt to match it with transactional data from payment systems.
ZH: 示例：监控和支付筛查系统从不同数据存储匹配客户账户与交易数据

[v7u_N004713|4713] The data labels across these disparate systems likely vary, and therefore the compliance system must standardize them before use.
ZH: 合规系统必须在使用前标准化不同系统的数据标签

[v7u_N004714|4714] For a compliance system to use internal data, it must first assemble the data into tables in accordance with definitions from a common data dictionary or glossary.
ZH: 合规系统需根据通用数据字典的定义将内部数据组装成表格

[v7u_N004715|4715] System requirements dictate data table structures.
ZH: 系统需求决定数据表结构

[v7u_N004716|4716] For example, if a compliance system requires three fields, <name>, <address>, and <date of birth>, then the data table will have three columns corresponding to these labels.
ZH: 示例：合规系统要求三个字段，数据表则对应三列

[v7u_N004717|4717] Compliance systems only consume data that is relevant to the operation of the system, so some data in the source systems will not populate in the data tables. This is because overpopulated data tables reduce the efficiency of compliance systems. This is more complicated for systems incorporating AI solutions, in which required data tables are more comprehensive and inclusive.
ZH: 合规系统只消费相关数据，避免数据表过载；AI系统需要更全面的数据表

[v7u_N004718|4718] Data from older systems may not be compatible with newer systems, as naming conventions and storage protocols have changed.
ZH: 旧系统数据可能因命名约定和存储协议变化而与新系统不兼容

[v7u_N004719|4719] Crossing jurisdictional and language boundaries complicates these processes further.
ZH: 跨司法管辖区和语言边界使数据处理更加复杂

[v7u_N004720|4720] To address this, the compliance system assembles, cleans, enriches, and standardizes the data in staging tables before populating it into final data tables.
ZH: 合规系统在最终数据表前对数据进行组装、清洗、丰富和标准化

[v7u_N004721|4721] Data use is either passive or active. Passive use refers to instances in which the value of the data is inherent, such as the "country code" field, which holds inherent value without further action.
ZH: 数据使用分为被动使用和主动使用两类

[v7u_N004722|4722] Active use is interactive, such as when the compliance system compares two data fields to identify instances in which transaction activity deviates from the expected pattern for that profile. Comparing these data elements allows the compliance system to either detect an anomaly that requires further investigation or apply additional active data fields.
ZH: 主动使用指合规系统交互式比较数据字段以检测异常