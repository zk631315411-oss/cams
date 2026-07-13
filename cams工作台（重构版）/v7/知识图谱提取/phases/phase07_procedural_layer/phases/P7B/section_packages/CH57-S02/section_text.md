[v7u_N004463|4463] Once financial institutions develop, calibrate, and deploy transaction monitoring scenarios, they should continuously test and tune them to ensure effectiveness.
ZH: 金融机构应持续测试和调优交易监控场景以确保有效性。

[v7u_N004464|4464] This process occurs periodically and due to special circumstances, such as regulatory changes, emerging financial crime trends, or shifts in customer transaction behavior.
ZH: 定期及特殊情形（如监管变化、新兴金融犯罪趋势、客户交易行为变化）触发测试。

[v7u_N004465|4465] Rules-based systems are typically easier to test and tune.
ZH: 基于规则的交易监控系统通常更易于测试和调优。

[v7u_N004466|4466] Without proper testing, monitoring scenarios might become outdated. This could lead to inefficiencies such as excessive false positives or undetected suspicious activity. Testing ensures that scenarios remain aligned with evolving risks while balancing effective detection and operational efficiency.
ZH: 缺乏测试会导致监控场景过时，产生过多误报或漏报可疑活动。

[v7u_N004467|4467] If predefined thresholds are repeatedly breached, it might indicate a change in transaction patterns or regulatory expectations, requiring an adjustment.
ZH: 预设阈值被反复突破表明交易模式或监管预期已变化，需要调整。

[v7u_N004468|4468] For example, if false positives are excessively high, the threshold might be too strict, flagging many legitimate transactions as suspicious. In such cases, lowering the threshold can help reduce unnecessary alerts and improve compliance team efficiency.
ZH: 误报率过高时，阈值可能过于严格，应适当降低以减少不必要告警。

[v7u_N004469|4469] Conversely, if false positives drop significantly, the threshold might be too lenient, allowing illicit activity to go undetected. In such cases, raising the threshold might improve risk detection.
ZH: 误报率显著下降时，阈值可能过于宽松，应适当提高以加强风险检测。

[v7u_N004470|4470] When tuning the transaction monitoring system, organizations should consider such data as transaction thresholds, frequency, and geolocation mismatches.
ZH: 调优交易监控系统时应考虑交易阈值、频率、地理位置不匹配等数据。

[v7u_N004471|4471] While there is no universal standard that dictates testing frequency, industry best practices recommend structured reviews, such as semi-annual or annual, to maintain effectiveness and regulatory alignment.
ZH: 行业最佳实践建议每半年或每年进行结构化审查以保持有效性和监管一致性。

[v7u_N004472|4472] Depending on the business scale of the organization, more frequent testing may be required.
ZH: 根据机构业务规模，可能需要更频繁的测试。

[v7u_N004473|4473] Testing should also occur in response to significant risk factors, such as emerging financial crime trends, regulatory changes, or shifts in transaction behavior.
ZH: 测试还应在重大风险因素出现时进行，如新兴金融犯罪趋势、监管变化或交易行为变化。

[v7u_N004474|4474] Monitoring false positives is an ongoing process in business-as-usual operations.
ZH: 监控误报是日常运营中的持续过程。

[v7u_N004475|4475] Fluctuations in false positive rates might be normal due to seasonal changes, shifts in customer behavior, or updates in organizational policies.
ZH: 误报率波动可能源于季节性变化、客户行为变化或政策更新。

[v7u_N004476|4476] However, fluctuations do not always require immediate tuning.
ZH: 波动并不总是需要立即调优。

[v7u_N004477|4477] Instead, organizations should conduct tuning in response to continuous breaches or sustained deviations from expected performance.
ZH: 机构应在持续突破或持续偏离预期表现时进行调优。

[v7u_N004478|4478] Before making any adjustments, conduct an impact analysis to ensure that tuning improves efficiency without introducing new risks.
ZH: 调整前应进行影响分析，确保调优提升效率且不引入新风险。

[v7u_N004479|4479] To ensure that scenarios are optimal, financial institutions should maintain a structured approach to testing and tuning. This ensures that their transaction monitoring systems remain effective, adaptive, and aligned with both regulatory expectations and operational goals.
ZH: 金融机构应保持结构化的测试和调优方法，确保交易监控系统有效、适应性强且符合监管与运营目标。

[v7u_N004480|4480] Ongoing testing and tuning of AI tools in transaction monitoring is a complex and dynamic process. This process involves training the systems, testing the results they generate, and retraining them if the results are not ideal.
ZH: AI工具在交易监控中的测试和调优是一个复杂动态过程，涉及训练、测试和再训练。

[v7u_N004481|4481] To make effective use of AI-based tools, organizations need to understand how the models make decisions and ensure the dataset is large, relevant, and of high quality.
ZH: 有效使用AI工具需要理解模型决策并确保数据集大、相关且高质量。

[v7u_N004482|4482] To avoid statistical bias that might skew results, ensure the dataset includes a broad sample of transactions, not only those transactions that generated an alert.
ZH: 数据集必须包含广泛的交易样本以避免统计偏差。

[v7u_N004483|4483] An organization first performs testing and tuning when it develops the AI model, before deployment.
ZH: AI模型在部署前需进行测试和调优。

[v7u_N004484|4484] It splits a sample of data into two sets: a large training set and a smaller test set.
ZH: 将数据样本分为训练集和测试集。

[v7u_N004485|4485] The system learns from the training set by analyzing the data to create the model’s parameters and operations.
ZH: 系统通过分析训练集学习以创建模型参数和操作。

[v7u_N004486|4486] It then tests the model against the test set and fine-tunes it, as needed.
ZH: 使用测试集测试模型并根据需要微调。

[v7u_N004487|4487] After deploying the model, the organization should test and fine-tune it periodically.
ZH: 部署后应定期测试和微调模型。

[v7u_N004488|4488] This process typically involves back-testing, using 6 to 12 months of historical data and various sampling techniques.
ZH: 回测过程使用6至12个月历史数据和多种抽样技术。

[v7u_N004489|4489] Comparing flagged alerts with actual SAR filings helps find false positives.
ZH: 将警报与实际可疑交易报告比对以发现误报。

[v7u_N004490|4490] Identifying alerts in the test data that were not previously flagged helps identify false negatives, also known as missing alerts.
ZH: 识别测试数据中先前未标记的警报以发现漏报。

[v7u_N004491|4491] Organizations can use various sophisticated statistical methods to test AI tools, depending on the tools' complexity and available resources.
ZH: 可根据AI工具的复杂性和资源使用多种统计方法进行测试。

[v7u_N004492|4492] Human-in-the-loop training involves having a knowledgeable expert review test results and assess their reliability and accuracy. Human-in-the-loop testing provides qualitative feedback, helping data scientists fine-tune parameters and data to provide better results.
ZH: 人在回路训练由专家审查测试结果并提供定性反馈以优化参数。

[v7u_N004493|4493] When completing any cycle of training and tuning, remember that models should have high explainability. Analysts should easily understand and act on the model's decisions. They should also document the rationale for decisions for auditing purposes.
ZH: 模型应具备高可解释性，分析师需理解并记录决策理由。

[v7u_N004494|4494] The diversity and strength of the training data often dictate the success of AI algorithms. Any biases or inaccuracies in the training data may be magnified when AI algorithms recognize these patterns.
ZH: 训练数据的多样性和强度决定AI算法成功与否，偏差可能被放大。

[v7u_N004495|4495] Having an appropriately trained professional reviewing results for bias is one way of minimizing this risk.
ZH: 由经过适当培训的专业人员审查结果以降低偏差风险。

[v7u_N004496|4496] Additionally, other AI algorithms may be used to pinpoint deficiencies that can be corrected.
ZH: 可使用其他AI算法来发现可纠正的缺陷。

[v7u_N004497|4497] Regulators around the world expect algorithms to be transparent. This means providing an explanation of why a specific alert was deemed suspicious when others were not.
ZH: 监管机构期望算法透明，即解释为何特定警报被判定可疑。

[v7u_N004498|4498] While some AI algorithms offer explainability, many black-box models exist and may present risk if used without adequate understanding of its limitations.
ZH: 黑箱AI模型若未充分理解其局限性可能带来风险。