[v7u_N004445|4445] Transaction monitoring scenarios require careful calibration to effectively detect suspicious activities while minimizing false positives. Calibration, or threshold tuning, involves adjusting parameters based on empirical transaction data, risk models, and a broader risk-based approach.
ZH: 交易监控场景校准涉及基于交易数据、风险模型和风险为本方法调整参数

[v7u_N004446|4446] Calibration begins with segmenting the customer base and establishing the optimal threshold for each segment. Then, conduct pre-launch testing on the segmentation and thresholds as an impact analysis to ensure effectiveness.
ZH: 校准从客户群细分和设定最优阈值开始，然后进行上线前测试作为影响分析

[v7u_N004447|4447] It is not advisable to leave a transaction monitoring system at its default settings. Instead, calibrating and tuning it for the specific circumstances that the organization faces ensures optimal performance.
ZH: 不应使用交易监控系统的默认设置，而应针对具体情况进行校准调优

[v7u_N004448|4448] The goal is to refine monitoring thresholds and segmentation criteria so that alerts are generated only for truly anomalous behavior.
ZH: 校准目标是细化监控阈值和细分标准，仅对真正异常行为生成警报

[v7u_N004449|4449] Proper calibration improves operational team efficiency, reduces operational burdens, and ensures alignment with regulatory expectations.
ZH: 适当校准可提高运营团队效率、减轻操作负担并确保符合监管期望

[v7u_N004450|4450] For example, monthly conversions of Bitcoin to fiat currency, followed by equal deposits to a business checking account, would make sense for a restaurant that accepts cryptocurrency for payment. Since these deposits match the business’s profile, the bank calibrates its monitoring scenario to avoid unnecessary alerts.
ZH: 以接受加密货币支付的餐厅为例，银行校准监控场景以避免对匹配业务画像的交易产生不必要警报

[v7u_N004451|4451] Another key aspect of scenario calibration is detecting structuring.
ZH: 场景校准的另一个关键方面是检测拆分交易

[v7u_N004452|4452] For example, if regulatory guidelines require reporting for cash deposits above US$10,000, a customer consistently depositing US$9,900 in multiple transactions might be structuring.
ZH: 例如，若监管要求报告超过1万美元的现金存款，客户多次存入9900美元可能构成拆分交易

[v7u_N004453|4453] Effective calibration includes setting velocity checks, monitoring aggregate transactions over specific time frames, and analyzing behavioral patterns to detect such activity.
ZH: 有效校准包括设置频率检查、监控特定时间段内的总交易量以及分析行为模式

[v7u_N004454|4454] To validate the effectiveness of calibrated scenarios, financial institutions use three different testing methods:
ZH: 金融机构使用三种测试方法验证校准场景的有效性

[v7u_N004455|4455] Close testing examines transactions near the defined threshold to ensure borderline cases trigger alerts.
ZH: 临界测试检查阈值附近的交易以确保边界情况触发警报

[v7u_N004456|4456] Above-threshold testing assesses whether truly suspicious transactions consistently trigger alerts, capturing high-risk activity.
ZH: 阈值以上测试评估真正可疑交易是否持续触发警报以捕获高风险活动

[v7u_N004457|4457] Below-threshold testing identifies potential gaps, such as structuring, where criminals intentionally keep transactions slightly below reporting limits.
ZH: 阈值以下测试识别潜在漏洞，如犯罪分子故意使交易略低于报告限额的拆分交易

[v7u_N004458|4458] Above-the-line and below-the-line testing are related concepts used in tuning and testing transaction monitoring. The "line" may refer to the current threshold; however, these tests are typically performed at differing levels above and below the thresholds set to tune alerts for optimal performance.
ZH: 线上测试和线下测试是调优交易监控的相关概念，分别在阈值上下不同水平进行测试

[v7u_N004459|4459] This layered testing approach ensures that thresholds are neither too sensitive nor too lenient, maintaining a well-balanced monitoring system. A well-calibrated system minimizes both false positives (legitimate transactions mistakenly flagged as suspicious) and false negatives (suspicious activities that go undetected).
ZH: 分层测试方法确保阈值既不过于敏感也不过于宽松，最小化误报和漏报

[v7u_N004460|4460] The overall volume of alerts generated is a key metric.
ZH: 警报总量是监控校准的关键指标

[v7u_N004461|4461] Excessive alerts can overwhelm compliance teams and lead to inefficiencies and missed high-risk transactions.
ZH: 过多告警会压垮合规团队，导致效率低下并遗漏高风险交易。

[v7u_N004462|4462] By continuously refining monitoring parameters, organizations can strike the right balance between risk sensitivity and operational efficiency. This strengthens their AML framework as they maintain regulatory compliance.
ZH: 持续优化监控参数可在风险敏感性与运营效率间取得平衡，强化反洗钱框架。