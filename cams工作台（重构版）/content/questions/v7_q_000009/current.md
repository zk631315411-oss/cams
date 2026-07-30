# v7_q_000009

教材章节：未映射

题型：single

题干：在通过组织的全企业制裁风险评估发现可能存在漏洞,即与业务规模和运营情况相比,生成的制裁筛查警报数量过少时,以下哪项行动最能确保该风险领域得到妥善管理和尽可能彻底的整改？

英文题干：Upon learning of a potential weakness through an organization's enterprise-wide sanctions risk assessment relating to a low number of sanctions screening alerts generated compared to the business size and operations identified, which action would best ensure the risk area is properly managed and remediated to the best possible extent?

选项：

- A. 审查企业范围的风险评估方法
  English: Reviewing the enterprise-wide risk assessment methodology
- B. 加强员工关于已关闭警报的合理化说明文档编制方面的培训
  English: Enhancing staff training on the documentation of justification on closed alerts
- C. 重新审视交易后监控系统的参数和阈值
  English: Revisiting the post-transaction monitoring system parameters and thresholds
- D. 审查筛选系统当前采用的模糊逻辑
  English: Reviewing the fuzzy logic currently used by the screening system

## 【AI答案】

D

> **需人工复核**
>
> - 答案冲突：解析{'D'} vs 题库{'C'}

## 【考点】

制裁筛查中模糊逻辑级别调优对警报数量的影响

## 【核心解析】

制裁筛查系统依赖模糊逻辑技术来检测名称的近似匹配，如拼写错误、缩写和音译等变体（P421）。机构需要定期调整模糊逻辑算法，以在检测准确性与减少误报之间取得平衡。题干中全企业制裁风险评估已经指出「警报数量过少」这一漏洞，且该漏洞「与业务规模和运营情况不匹配」。在给定选项中，问题更可能出在筛查系统本身的匹配灵敏度上，而非风险评估方法论或员工操作环节；因此，审查当前筛选系统采用的模糊逻辑是最直接的整改方向，可用于提升名称变体的检出率。

教材原句："In a sanctions screening system, you might tune the fuzzy logic levels to adjust the fuzziness level, detecting variations in names, such as misspellings, abbreviations, and transliterations."

## 【错误项分析】

- **A 错误（题干对照）｜范围或程度偏差**：审查风险评估方法论针对的是风险评估框架本身是否完善，但题干已说明漏洞是通过该评估发现的，问题出在筛查执行层面而非评估方法。直接调整系统参数比重新审视方法论更能精准解决「警报数量过少」的根因。
- **B 错误（题干对照）｜题干要素不匹配**：加强员工针对已关闭警报的文档编制培训，聚焦的是警报产生之后的人工处理环节。题干的核心问题是警报「生成」数量过少，而非已生成警报的关闭理由记录不佳，培训无法提升系统本身的检出灵敏度。
- **C 错误（教材直接依据）｜概念混淆**：交易后监控系统（transaction monitoring）主要用于识别可疑交易模式，其参数和阈值调整与异常行为检测相关（P328）；而题干所指的「制裁筛查警报」属于制裁名单筛选系统（sanctions screening），二者在教材中分属不同的控制模块（P420-421与P306/P436）。审查模糊逻辑更直接命中制裁筛查系统特有的匹配灵敏度问题。

## 【易错提醒】

制裁筛查系统（sanctions screening）与交易监控系统（transaction monitoring）容易混淆。制裁筛查针对制裁名单、PEP名单等进行名称匹配，核心调优手段包括模糊逻辑级别（P421）；交易监控则针对客户交易行为模式设置规则和阈值，以识别可疑活动（P328）。题干明确说的是「制裁筛查警报」，应围绕筛选系统而非监控系统寻找整改措施。

## 【教材原文依据】

> 核心引用单元：`v7u_N004239`

### `v7u_N004239`

- 用于：核心解析、易错提醒
- 章节：Technology for KYC > Screening system tuning
- 页码：PDF第426页 / 书内第421页
- 中文要点：在制裁筛查系统中，可调优模糊逻辑级别以检测名称变体。
- 英文原文：In a sanctions screening system, you might tune the fuzzy logic levels to adjust the fuzziness level, detecting variations in names, such as misspellings, abbreviations, and transliterations.

### `v7u_N004325`

- 用于：核心解析
- 章节：Technology for payment and batch screening > Types of ongoing screening
- 页码：PDF第437页 / 书内第432页
- 中文要点：机构需要定期调整模糊逻辑算法以平衡检测准确性与减少误报。
- 英文原文：Organizations need to regularly tune their fuzzy logic algorithms to balance detection accuracy with minimizing false positives.

### `v7u_N003035`

- 用于：选项C
- 章节：Onboarding AFC controls > • Ongoing due diligence, screening, monitoring, and KYC refresh:
- 页码：PDF第311页 / 书内第306页
- 中文要点：机构必须筛查每笔交易以检测制裁风险
- 英文原文：The organization must screen each transaction the customer carries out to detect any sanctions exposure.

### `v7u_N003231`

- 用于：选项C
- 章节：Transaction Monitoring and Investigation > Case example: AML control failures at a UK Bank
- 页码：PDF第331页 / 书内第326页
- 中文要点：NatWest虽未共谋洗钱，但其失职助长了非法交易，此案为FCA首例反洗钱刑事起诉。
- 英文原文：Although NatWest was not complicit in money laundering, the court emphasized that its failures were instrumental in facilitating illicit transactions. This case marked the FCA's first criminal prosecution for AML violations and highlighted the need for robust transaction monitoring systems and adherence to risk-sensitive ongoing monitoring protocols.

### `v7u_N003233`

- 用于：易错提醒
- 章节：Transaction monitoring > Transaction monitoring controls
- 页码：PDF第333页 / 书内第328页
- 中文要点：交易监控系统在客户活动超出正常参数时生成警报。
- 英文原文：Transaction monitoring systems generate alerts when customer activity or behavior is beyond normal parameters for the customer profile.

## 【参考答案与参考解析】

- 题库最终参考答案：C
- 中文参考答案：C

### 中文参考解析

制裁筛查警报数量过少,可能意味着监控系统存 在漏洞,未能有效识别潜在风险.选项C“重新审 视交易后监控系统的参数和间值”,直接针对监控 系统的有效性进行改进,通过调整参数和间值, 可提高系统对可疑交易的识别能力,确保风险领 域得到妥善管理和整改.其他选项或侧重于评估 方法、培训或筛选逻辑,均未直接解决监控系统 灵敏度问题.因此,选项C最为有效.易错提 醒:需注意监控系统参数调整需基于充分的数据 分析和风险评估.

- 英文参考答案：C

### 英文参考解析

未提供。

### 答案冲突提示

- 盲判与题库最终参考答案冲突：盲判=D，题库最终=C
