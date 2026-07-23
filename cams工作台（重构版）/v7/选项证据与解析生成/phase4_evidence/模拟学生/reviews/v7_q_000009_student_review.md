# 模拟学生反馈 — v7_q_000009

**追问1：**  
解析说：“教材指出，在制裁筛查系统中可以通过调整参数来增加或减少生成的警报数量（书内第421页），而模糊逻辑级别的设定直接影响系统对名称变体的检测能力（书内第421页）。”  
我翻了两段教材原文：  
- v7u_N004241：“You can adjust parameters to increase or decrease the number of alerts.”  
- v7u_N004239：“you might tune the fuzzy logic levels to adjust the fuzziness level, detecting variations in names...”  
这两句话是分开写的，原文并没有说“参数”就是指“模糊逻辑级别”。参数可能还包括匹配分数阈值、相似度权重等。如果警报数量过少，为什么一定是调模糊逻辑，而不是先调其他参数？解析把“调整参数”直接等同成“审查模糊逻辑”，这个推导在教材里能找到依据吗？

**追问2：**  
解析说：“交易后监控系统的参数和阈值属于交易监控领域（书内第331页）”。但教材原文第331页的标题是“Transaction monitoring system tuning”，里面写的是“TM system tuning is the process of refining and
