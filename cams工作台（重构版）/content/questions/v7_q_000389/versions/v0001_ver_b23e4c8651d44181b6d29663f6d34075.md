# v7_q_000389

教材章节：未映射

题型：multiple

题干：以下哪些方法应结合使用,以确保客户数据保护和反洗钱合规？(选择三项.)

英文题干：Which of the following approaches should be used in combination to ensure customer data protection and AML compliance? (Select Three.)

选项：

- A. 数据加密
  English: Data encryption
- B. 数据最小化
  English: Data minimization
- C. 全面的数据收集
  English: Comprehensive data collection
- D. 访问控制
  English: Access controls
- E. 超出监管要求保存客户数据
  English: Saving customer data beyond regulatory requirements

## 【AI答案】

A、B、D

> **需人工复核**
>
> - 部分选项证据不足：E

## 【考点】

数据保护原则（加密、最小化、访问控制）在反洗钱合规中的具体实践要求

## 【核心解析】

GDPR等数据保护法规对处理个人数据施加严格限制，明确要求组织遵守数据最小化、目的限制等原则（P392）。在反洗钱合规中，这转化为三项具体要求：一是数据加密，组织应实施强加密方法保护敏感数据，并确保安全数据存储、加密和访问控制以降低网络安全风险（P392）；二是数据最小化，在客户尽职调查过程中，组织应与法律团队合作确保合法处理、数据最小化及客户同意管理（P378）；三是访问控制，基于角色的访问控制模型根据最终用户角色授权其对特定系统和数据的访问，参与数据共享的组织必须实施控制以防止未经授权的访问（P426、P209）。题干中的「数据保护相关良好实践」直接对应这些法规要求，A、B、D分别对应加密、最小化、访问控制三项核心技术措施。

教材原句："GDPR imposes strict rules on handling the personal data of EU citizens, emphasizing principles such as data minimization, purpose limitation, storage limitation, and the right to erasure."

## 【错误项分析】

- **C 错误｜概念混淆**：「数据越全面，识别可疑模式的机会越大」强调的是金融犯罪检测所需的数据覆盖；数据保护则要求只收集特定目的所必需的数据（P392）。题干聚焦数据保护，因此应遵循数据最小化原则，而不是无边界地全面收集。
- **E 错误**：教材指出许多司法管辖区对数据保留期限有规定，数据在完成目的后必须安全销毁。存储限制是GDPR明确强调的原则之一。超出监管要求保存客户数据会增加数据泄露风险，与数据保护中「目的限制」和「存储限制」原则相悖，不如A、B、D项直接匹配数据保护要求。

## 【易错提醒】

「全面的数据收集」在反洗钱检测中看似合理——数据越多，发现可疑模式的机会越大。但在数据保护框架下，GDPR要求的是高质量、有针对性的数据而非大量未聚焦的个人数据（P392）。真正的区分标准是：反洗钱合规同时受两套规则约束——金融犯罪检测需要充分的数据覆盖，而数据保护法规要求严格限制数据收集范围和存储期限。两者之间需要通过数据最小化原则取得平衡，而非简单地追求数据量的最大化。

## 【教材原文依据】

> 核心引用单元：`v7u_N003925`

### `v7u_N003925`

- 用于：核心解析、选项C、易错提醒
- 章节：Understanding AFC technology > Impact of privacy regulations on technology use
- 页码：PDF第397页 / 书内第392页
- 中文要点：《通用数据保护条例》 对处理欧盟公民个人数据施加严格规则，强调数据最小化、目的限制等原则。
- 英文原文：GDPR imposes strict rules on handling the personal data of EU citizens, emphasizing principles such as data minimization, purpose limitation, storage limitation, and the right to erasure.

### `v7u_N004274`

- 用于：核心解析
- 章节：Technology for KYC > Integrating screening technology with other systems
- 页码：PDF第431页 / 书内第426页
- 中文要点：集成过程中应特别关注数据安全和隐私，遵守《通用数据保护条例》等法规
- 英文原文：Organizations should also pay special attention to data security and privacy during integration. They should ensure compliance with all relevant data protection regulations, such as the GDPR in Europe. Organizations should implement strong encryption methods to protect sensitive data and restrict access to authorized individuals.

### `v7u_N003778`

- 用于：核心解析、选项C
- 章节：Understanding AFC technology > Technology implementation considerations
- 页码：PDF第383页 / 书内第378页
- 中文要点：数据隐私与安全：需遵守《通用数据保护条例》等隐私法律，确保数据加密和访问控制
- 英文原文：Data privacy and security: Comply with privacy laws, such as the GDPR and the Gramm-Leach-Bliley Act, and ensure secure data storage, encryption, and access controls to mitigate cybersecurity risks.

### `v7u_N002027`

- 用于：选项C
- 章节：未标注
- 页码：PDF第214页 / 书内第209页
- 中文要点：数据不得无限期保留，必须按销毁政策销毁。
- 英文原文：Data should not be retained indefinitely and must be destroyed in accordance with your organization’s destruction policy.

## 【参考答案与参考解析】

- 题库最终参考答案：A、B、D
- 中文参考答案：A、B、D

### 中文参考解析

为确保客户数据保护和反洗钱合规性,需综合运 用多种方法.数据加密(A)能保护数据在传输和 存储中的安全,防止泄露;数据最小化(B)可限 制数据收集范围,仅保留必要信息,降低泄露风 险;访问控制(D)能确保只有授权人员可访问敏 感数据,防止滥用.而全面数据收集(C)可能增 加数据泄露风险,超出监管要求保存数据(E)则 可能违反数据保护原则.因此,正确选项为 ABD.易错提醒:注意数据最小化不是不收集 数据,而是仅收集必要数据.

- 英文参考答案：A、B、D

### 英文参考解析

翻译 -[AML/CFTCompliancePrograms]Whic 多选 hofthefollowingapproachesshouldbeusedin combinationtoensurecustomerdataprotection AndAMLcompliance?(SelectThree.) Dataencryption Dataminimization Comprehensivedatacollection C Accesscontrols Savingcustomerdatabeyondregulato E ryrequirements 正确答案ABD 您选择/ 试题详解

### 答案冲突提示

- 未发现答案冲突。
