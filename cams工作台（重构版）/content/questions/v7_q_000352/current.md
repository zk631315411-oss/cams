# v7_q_000352

教材章节：未映射

题型：multiple

题干：参考数据筛选包括对哪些类型的数据库进行筛选？(选择两项.)

英文题干：Reference data screening includes the screening of which types of datasets? (Select Two.)

选项：

- A. 支付消息的类型
  English: Types of payment messages
- B. 客户
  English: Customers
- C. 第三方服务提供商
  English: Third-party service providers
- D. 客户配偶
  English: Customer spouses

## 【AI答案】

B、C

## 【考点】

区分参考数据筛查（客户/第三方）与支付筛查（支付消息）的对象

## 【核心解析】

参考数据筛查（reference data screening）的核心是把静态的主体信息与外部名单做匹配，判断主体本身是否命中风险名单。教材明确指出，筛查系统需要「静态客户KYC详细信息」（static customer KYC details）与外部名单数据相结合（P467），同时第三方可以提供用于筛查目的的外部数据（P472），而数据提取本身就是从客户数据库和第三方提供商等来源收集数据的过程（P476）。可见，「客户」是筛查的第一类主体数据，「第三方服务提供商」既是筛查数据的来源，也是需要被筛查的关联主体。支付消息的类型是交易筛查（transaction/payment screening）的范畴，它筛查的是消息内容而不是数据主体（P317）；客户配偶只是客户附属信息中的一类，教材从未将其作为独立的筛查数据库类型，且其数据一般已涵盖在客户的KYC信息中，不具备单独的筛查维度。因此，B「客户」、C「第三方服务提供商」直接命中参考数据筛查的两类核心数据集，匹配度最高，而A、D均不构成教材所定义的独立筛查数据库类型。

教材原句："Another example is screening systems, as they require a combination of static customer KYC details and external data from list providers and other agencies."

## 【错误项分析】

- **A 错误（筛查类型不同）**：支付消息属于支付或交易筛查的对象（P317）；参考数据筛查侧重静态主体数据与风险名单的匹配。两者的筛查层面不同。
- **D 错误（不是独立数据集类型）**：配偶信息可在PEP等特定客户尽职调查中作为关联方信息受到关注，但通常不作为独立的参考数据集类型。

## 【易错提醒】

容易把支付筛查（payment screening）混同于参考数据筛查（reference data screening）。两者的根本区别在于：支付筛查针对的是交易消息的内容（有没有命中制裁名单中的名称），是交易层面的实时验证（P317）；而参考数据筛查针对的是数据主体（客户/第三方）本身是否在外部风险名单中，是主体层面的名单匹配（P467）。前者查「这笔钱能不能走」，后者查「这个人/机构能不能留存」。

## 【教材原文依据】

> 核心引用单元：`v7u_N004675`

### `v7u_N004675`

- 用于：核心解析、选项A、选项D、易错提醒
- 章节：Data as an input for solutions > Internal versus external data
- 页码：PDF第472页 / 书内第467页
- 中文要点：示例：筛查系统需要静态了解你的客户与外部名单数据相结合
- 英文原文：Another example is screening systems, as they require a combination of static customer KYC details and external data from list providers and other agencies.

### `v7u_N004744`

- 用于：核心解析
- 章节：Data as an input for solutions > External data
- 页码：PDF第477页 / 书内第472页
- 中文要点：第三方可提供外部数据，如筛查名单、政府情报或注册信息。
- 英文原文：Third parties can also provide external data, such as lists for screening purposes, intelligence from government agencies, or identification details from registries.

### `v7u_N004790`

- 用于：核心解析、选项A、选项D
- 章节：Data as an input for solutions > Data preparation
- 页码：PDF第481页 / 书内第476页
- 中文要点：数据提取是从客户数据库和第三方提供商等来源收集数据的过程
- 英文原文：Data extraction is the process of gathering data from various sources such as customer databases and third-party providers.

### `v7u_N004681`

- 用于：选项A、选项D
- 章节：Data as an input for solutions > Internal static data
- 页码：PDF第472页 / 书内第467页
- 中文要点：客户提供的静态数据示例包括姓名、地址、出生日期等了解你的客户信息。
- 英文原文：The data the customer provides includes KYC details such as name, address, date of birth, business registration number, and unique identifications such as passport or license numbers.

### `v7u_N003138`

- 用于：易错提醒
- 章节：Ongoing AFC controls > Ongoing due diligence
- 页码：PDF第322页 / 书内第317页
- 中文要点：支付筛查的定义：验证进出交易以防止金融犯罪，是资金转移机构的主要金融犯罪控制措施
- 英文原文：Payment or transaction screening is the process of verifying transactions, both incoming and outgoing, to prevent financial crime. It is a primary financial crime control for organizations that facilitate the transfer of funds for their customers, or on behalf of another entity.

## 【参考答案与参考解析】

- 题库最终参考答案：B、C
- 中文参考答案：B、C

### 中文参考解析

在制裁合规与筛查中,参考数据筛选是重要环 节.选项A支付消息的类型不属于核心筛选数据 库类型.选项B客户是筛查关键对象,需确认其 是不受制载选顶第二方服冬坦供高出雪笠

- 英文参考答案：B、C

### 英文参考解析

参考数据筛查在制裁合规中主要用于筛查可能涉 及制裁风险的实体.选项B“客户”是筛查的核心对 免用甘六目仁为可能发坝:选质第

### 答案冲突提示

- 未发现答案冲突。
