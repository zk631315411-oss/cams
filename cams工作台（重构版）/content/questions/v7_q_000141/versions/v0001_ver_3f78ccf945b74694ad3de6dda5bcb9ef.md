# v7_q_000141

教材章节：未映射

题型：single

题干：为了验证反洗钱模型的"概念合理性",这一点很重要,具体原因在于:

英文题干：It is important to validate the conceptual soundness of an AML model in order to:

选项：

- A. 核实是否符合监管指导方针和行业最佳实践
  English: Verify alignment with regulatory guidance and industry best practices
- B. 评估该模型的方法论和假设是否合乎逻辑且适合用于检测洗钱活动
  English: Assess whether the model's methodology and assumptions are logical and appropriate for detecting money laundering
- C. 验证模型预测能力的统计显著性
  English: Validate the statistical significance of the model's predictive capabilities
- D. 展示与当前技术基础设施的兼容性
  English: Demonstrate compatibility with current technological infrastructure

## 【AI答案】

B

## 【考点】
区分模型概念合理性、统计性能、监管对齐与系统兼容性

## 【核心解析】
概念合理性（conceptual soundness）关注模型的设计逻辑是否与检测目标相符，而不只是看统计结果或系统能否接入。模型验证不足可能引发决策错误（P243）；模型风险管理职能负责AFC模型的验证与治理，并通过评估模型有效性确保准确性和监管合规性（P251）。在交易监控治理中，机构还应选择合适的场景并应用适当的方法论（P449）。结合这些要求，验证AML模型的概念合理性，主要是检查其方法论和基础假设是否合乎逻辑，以及是否适合用于检测洗钱活动，因此B项与题干所问的验证目标最直接匹配。

## 【错误项分析】
- **A 错误**：核实是否符合监管指导方针和行业最佳实践，属于合规与治理对齐维度。它可能是模型治理的一部分，但不如B项直接回答模型的方法论和基础假设是否合理。
- **C 错误**：统计显著性属于预测性能或实证结果检验。测试、验证和调优AI模型有助于确保准确性（P386），但统计性能不等同于模型概念合理性；C项关注的是结果表现，而不是模型设计逻辑。
- **D 错误**：与当前技术基础设施兼容属于系统实施和集成问题。教材将“与遗留技术和核心银行系统兼容”作为技术实施事项（P378），它不能直接说明模型的方法论和假设是否适合洗钱检测。

## 【易错提醒】
“方法论和假设是否适合检测洗钱”是概念层面的判断（P449）；“预测能力是否具有统计显著性”是统计性能判断；“是否符合监管要求”是合规治理判断；“能否接入现有技术环境”是实施兼容性判断（P378）。四者属于不同的验证维度。

## 【教材原文依据】

> 核心引用单元：`v7u_N002376`

### `v7u_N002376`

- 用于：核心解析
- 章节：AFC program > AFC program components
- 页码：PDF第248页 / 书内第243页
- 中文要点：模型风险可能由模型验证不足导致的决策错误引起。
- 英文原文：Operational risk arises from inadequate internal processes, people, systems, or external events. A subset of this is model risk, caused by decision-making errors due to inadequate model validation.

### `v7u_N002464`

- 用于：核心解析、易错提醒
- 章节：Three lines of defense > Financial crime functions' structure
- 页码：PDF第256页 / 书内第251页
- 中文要点：模型风险管理职能负责AFC模型（含交易监控系统）的验证与治理，并评估模型有效性以确保准确性和合规性。
- 英文原文：The model risk management function is responsible for overseeing the validation and governance of AFC models, including transaction monitoring systems. Such systems evaluate the effectiveness of these models to ensure accuracy and compliance with regulatory standards.

### `v7u_N004500`

- 用于：核心解析
- 章节：Transaction monitoring scenario calibration testing > Governance for transaction monitoring
- 页码：PDF第454页 / 书内第449页
- 中文要点：机构通过治理机制确保选择正确的场景并应用适当的方法论。
- 英文原文：To ensure they select the right scenarios and apply appropriate methodologies, institutions establish governance committees, such as for model risk governance.

### `v7u_N003866`

- 用于：C项
- 章节：Understanding AFC technology > Transitioning from traditional systems to AI-based tools
- 页码：PDF第391页 / 书内第386页
- 中文要点：测试、验证和调优AI模型可以确保准确性并防止覆盖范围出现意外漏洞。
- 英文原文：The process of testing, validating, and tuning AI models ensures accuracy and prevents unintended gaps in coverage.

### `v7u_N003779`

- 用于：D项
- 章节：Understanding AFC technology > Technology implementation considerations
- 页码：PDF第383页 / 书内第378页
- 中文要点：技术实施需要与遗留技术和核心银行系统兼容。
- 英文原文：Integration with existing systems: Ensure compatibility with legacy technology and core banking systems.
