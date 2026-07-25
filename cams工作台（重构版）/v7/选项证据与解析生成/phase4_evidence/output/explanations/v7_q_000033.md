# v7_q_000033

教材章节：未映射

题型：single

题干：客户细分对于有效的交易监控很重要,原因在于:

英文题干：Customer segmentation is important for effective transaction monitoring because:

选项：

- A. 所有客户都以相同的方式进行交易，这使得交易模式易于被发现。
  English: All customers transact in the same way, allowing patterns to be easily spotted
- B. 在相似的同类群体中，客户行为能够得到最有效的比较和分析。
  English: Customer behavior can be compared and analyzed most effectively among similar peer groups
- C. 它允许将各种各样的客户类型归入一个大组进行比较。
  English: It allows a broad range of customer types to be compared in one large group
- D. 监管机构仅出于防范制裁风险的考虑而提出此建议。
  English: It is recommended by regulators solely to prevent sanctions risk

## 【AI答案】

B

## 【考点】

客户细分通过建立同质比较基准来提升交易监控有效性

## 【核心解析】

客户细分指根据业务类型、交易行为和风险状况对客户进行分类（P436）。完成细分后，对每个群体应用适当规则，以识别偏离该群体预期行为的客户（P436）。这意味着交易监控的核心逻辑不是跨群体横向比较所有客户，而是在同类群体内部建立行为基线——街头小贩定期存现金符合预期，政府职员突然频繁存现金则偏离预期（P436）。同行比较（peer-group comparisons）正是通过这种同类群体内的横向对比来优化监控规则（P444）。题干问客户细分为什么对有效交易监控重要，关键就在于它创造了「相似的同类群体」这一比较基础，使偏离常态的行为能被更精准地识别出来。选项B「在相似的同类群体中，客户行为能够得到最有效的比较和分析」直接对应了这一逻辑。

教材原句："Once organizations have identified customer segments, they apply appropriate rules to each segment. This provides an initial framework to identify customers who deviate from their expected behavior."

## 【错误项分析】

- **A 错误（教材定义应用）｜概念混淆**：选项A假设「所有客户以相同方式交易」，这与客户细分的核心理念相悖。教材恰恰指出不同业务类型的客户有截然不同的交易行为——街头小贩和受薪专业人士的现金存取模式完全不同（P436），交易监控必须基于群体差异来设定阈值，而不是假设所有人行为一致。题干条件更直接支持B的同群比较逻辑，而非A的同质化假设。
- **C 错误（教材定义应用）｜范围或程度偏差**：选项C主张将各种客户类型「归入一个大组进行比较」，这与客户细分的核心操作方向相反。教材强调细分是按业务类型、交易行为等因素将客户分类到不同群体中（P436），并明确指出仅使用行业代码将客户分入同一组会导致监控不充分——因为没有使用营业额、规模、产品、渠道等其他属性做更精细化的细分（P463）。细分的目的是拆分成更小的同质群体，而非合并为一个大组。
- **D 错误（教材定义应用）｜范围或程度偏差**：选项D将客户细分的目的限定为「仅防范制裁风险」，而教材中客户细分的目的是支持更广泛的交易监控有效性——识别偏离预期行为的客户（P436），覆盖洗钱、恐怖融资等多种金融犯罪风险，不限于制裁风险。相比之下，题干问的是交易监控有效性的一般原因，B的同群比较逻辑覆盖范围更完整、更直接匹配教材论述。

## 【易错提醒】

容易混淆的是「细分（segmentation）」与「归并（grouping）」的方向差异。细分是将客户按属性拆分成同质的较小群体（P436），而非把不同客户合并成一个大组。教材以负面案例说明：仅按行业代码把所有人塞进同一组会导致监控不充分（P463），因为这忽略了营业额、规模等关键维度。记一个判断口诀：细分是做「拆」，不是做「合」。

## 【教材原文依据】

> 核心引用单元：`v7u_N004367`

### `v7u_N004367`

- 用于：核心解析、选项A、选项C
- 章节：Technology for payment and batch screening > Rules-based transaction monitoring
- 页码：PDF第441页 / 书内第436页
- 中文要点：客户分群是根据业务类型、交易行为和风险状况对客户进行分类。
- 英文原文：Segmentation refers to categorizing customers based on factors such as business type, transaction behavior, and risk profile.

### `v7u_N004371`

- 用于：核心解析、选项D
- 章节：Technology for payment and batch screening > Rules-based transaction monitoring
- 页码：PDF第441页 / 书内第436页
- 中文要点：识别客户分群后，对每个群体应用适当规则，以识别偏离预期行为的客户。
- 英文原文：Once organizations have identified customer segments, they apply appropriate rules to each segment. This provides an initial framework to identify customers who deviate from their expected behavior.

### `v7u_N004433`

- 用于：核心解析、选项D
- 章节：Technology for payment and batch screening > Transaction monitoring scenario development
- 页码：PDF第449页 / 书内第444页
- 中文要点：金融机构按业务类型、交易行为、地理敞口和风险水平进行客户细分。
- 英文原文：Financial institutions perform customer segmentation for effective monitoring, either before or after developing the scenarios. They categorize customers by business type, transaction behavior, geographic exposure, and risk level.

### `v7u_N004437`

- 用于：选项A、选项C
- 章节：未标注
- 页码：PDF第449页 / 书内第444页
- 中文要点：利用历史数据、同行比较和严重性因素来优化监控规则。
- 英文原文：To mitigate these issues, financial institutions use historical transaction data, peer-group comparisons, and severity factors to refine monitoring rules.

### `v7u_N004368`

- 用于：选项A
- 章节：未标注
- 页码：PDF第441页 / 书内第436页
- 中文要点：分群使金融机构能为每个群体设定反映预期活动的阈值。
- 英文原文：Segmentation allows financial institutions to set thresholds that reflect expected activity within each segment.

### `v7u_N004626`

- 用于：选项C、易错提醒
- 章节：Data as an input for solutions > Coverage and gap assessment
- 页码：PDF第468页 / 书内第463页
- 中文要点：仅使用行业代码进行客户分群导致监控不充分的例子。
- 英文原文：One example is when a transaction monitoring solution uses industry codes to segment customers. This means all customers with the same code are segmented together and are subject to equal monitoring. This solution fails to use other attributes such as turnover, scale, products, and channels to complete a more detailed and accurate segmentation.

### `v7u_N004370`

- 用于：选项D
- 章节：Technology for payment and batch screening > Rules-based transaction monitoring
- 页码：PDF第441页 / 书内第436页
- 中文要点：适当的分群确保组织对不同客户群体进行适当的交易监控。
- 英文原文：Proper segmentation ensures that organizations apply transaction monitoring appropriately across different customer groups.

## 【参考答案与参考解析】

- 题库最终参考答案：B
- 中文参考答案：B

### 中文参考解析

客户细分能将客户按特征、行为等分成不同群

- 英文参考答案：B

### 英文参考解析

客户细分对于有效的交易监控至关重要,因为通 过将客户分为相似群体,能更有效地比较和分析 客户行为.选项A错误,因为不同客户交易方式 各异.难以通过单一模式识别异常:选项C错

### 答案冲突提示

- 未发现答案冲突。
