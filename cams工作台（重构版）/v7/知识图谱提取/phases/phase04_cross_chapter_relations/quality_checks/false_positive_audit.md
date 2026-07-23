# P4B 跨章关系假阳性审计报告

**审计日期**: 2026-07-20
**抽样方式**: 从 1404 条 accepted 决策中随机抽样 50 条（random seed=42）
**数据来源**:
- 决策文件: `p4_full_final_decisions.json`
- CP 原文: `input_candidates.json`

---

## 总览

| 指标 | 数值 |
|------|------|
| 抽样数 | 50 |
| 假阳性数 | 17 |
| 假阳性率 | **34.0%** |
| 通过数 | 33 |

---

## 假阳性明细（17 条）

### 1. p4vec_2340 -- illustrates

- **源 CP** (CH53): "Facial recognition verification deficiency at OneFrance"
- **目标 CP** (CH54): "Facial recognition technology definition and methods"
- **判定理由**: 源 CP 描述 OneFrance 一家银行供应商系统的具体缺陷（无活体检测、与证件系统未集成、匹配率仅 80%），目标 CP 是面部识别技术的学术定义与方法分类（eigenfaces、Fisherfaces、DeepFace、3D、热成像等）。源 CP 是一个实施失败的案例，并非对目标 CP 中任何技术方法的说明或示例。两 CP 共享"面部识别"主题，但案例不构成对技术定义的"illustrates"。

关键原文证据：
- 目标 CP 定义："The eigenfaces method identifies the principal components of a dataset of face images..."; "The Fisherfaces method builds upon the eignefaces method..."
- 源 CP 内容："The system does not incorporate strong liveness checks and is not properly integrated with the document processing system..." -- 这是具体供应商缺陷，与技术方法无关。

---

### 2. p4vec_0851 -- grounds

- **源 CP** (CH54): "Automated Data Gathering and Batch Screening"
- **目标 CP** (CH58): "Data Mining and Data Matching in AFC"
- **判定理由**: 方向反了。源 CP 描述的是技术应用（自动化数据采集与批量筛查），目标 CP 定义的是底层分析技术（数据挖掘、数据匹配）。数据挖掘/数据匹配是基础技术，自动化采集和批量筛查是对这些技术的应用。grounds 关系应是数据挖掘技术（目标）→ 筛查应用（源），而非当前方向。LLM 的 reason 自身也说"CH58 defines data mining...CH54 applies these techniques"，确认了基础在目标、应用在源，但 accept 了反向关系。

---

### 3. p4vec_4016 -- summarizes

- **源 CP** (CH42): "Pre-Onboarding Screening"
- **目标 CP** (CH47): "Payment Screening and Its Types"
- **判定理由**: 源 CP 专注于准入前筛查（客户 onboarding 之前），目标 CP 专注于支付筛查（交易进行时），两者是客户生命周期不同阶段的筛查类型。源 CP 没有概括目标 CP 的内容 -- 它只讨论 pre-onboarding 阶段的三类筛查（制裁、负面媒体、PEP），而目标 CP 涵盖了姓名筛查、支付/交易筛查、负面媒体筛查、PEP 筛查等多个类型，scope 不同。源 CP 不具备对目标 CP 的"summarizes"关系。

---

### 4. p4vec_0129 -- grounds

- **源 CP** (CH50): "AFC Technology Definition and Key Functions"
- **目标 CP** (CH51): "Regulatory Technology Definition and Role in AFC"
- **判定理由**: 方向反了。源 CP 第一句即声明"AFC technology, a subset of regulatory technology (RegTech)"，明确 AFC 技术是 RegTech 的子集。目标 CP 定义的是 RegTech（父概念）。逻辑上应是父概念（RegTech）ground 子概念（AFC Technology），而非子概念 ground 父概念。

---

### 5. p4vec_0477 -- grounds

- **源 CP** (CH36): "Benefits of Risk Assessments: Resource Allocation, Risk Management, AFC Controls"
- **目标 CP** (CH19): "Risk-Based Approach and National Risk Assessment Obligations"
- **判定理由**: 源 CP 描述风险评估的实践益处（资源分配、风险管理、强化内控），目标 CP 描述 FATF 建议1的监管要求（司法管辖区必须识别和评估风险）。两者是同一主题的平行视角（"为什么要做"vs"法规要求做"），不存在一者奠基另一者的关系。目标 CP 中的 FATF 要求独立存在，不依赖源 CP 的"益处"描述。

关键原文证据：
- 源 CP："Allocate resources efficiently by making informed decisions based on risk levels."
- 目标 CP："Recommendation 1 of FATF standards requires jurisdictions to identify, assess, and understand their money laundering and terrorist financing risks..." -- 这是独立的监管规定，非源 CP 中益处的"应用"。

---

### 6. p4vec_5102 -- summarizes

- **源 CP** (CH50): "Enhance AFC Compliance through Review and Technology Upgrade"
- **目标 CP** (CH51): "Conducting targeted risk assessments for AFC technology selection"
- **判定理由**: 源 CP 只有一句话："Enhance your AFC compliance program by conducting a comprehensive review and upgrading existing technology." 而目标 CP 详细阐述了针对每项 AFC 控制（CDD、筛查、监控）进行针对性风险评估的方法论。源 CP 过于泛化，未涵盖目标 CP 的核心内容（针对性风险评估方法论），不具备"summarizes"所要求的概括关系。

---

### 7. p4vec_6527 -- illustrates

- **源 CP** (CH20): "Case Study: The 1999 Convention and UNSC Resolutions in the Madrid Bombings"
- **目标 CP** (CH18): "Historical milestones in global AFC frameworks"
- **判定理由**: 目标 CP 的历史里程碑是巴勒莫公约（2000年）和 9/11 袭击（2001年），而源 CP 的马德里爆炸案（2004年）使用的是 1999 年公约和安理会第 1267/1373 号决议。源 CP 描述的案例涉及更早或不同的法律文书，并非对目标 CP 中列出的特定历史里程碑的说明。两者同属"国际 AFC 框架"大主题，但案例不illustrate目标中的具体里程碑事件。

---

### 8. p4vec_5890 -- grounds

- **源 CP** (CH51): "AI governance requirements in AFC"
- **目标 CP** (CH47): "AI-powered transaction monitoring"
- **判定理由**: 源 CP 仅一句话（"AI 的使用引入额外治理要求..."), 讨论 AI 治理。目标 CP 讨论 AI 驱动的交易监控技术能力（实时分析大量数据、识别可疑模式）。两者是完全不同的话题 -- 一个是治理/合规需求，一个是技术功能描述。源 CP 不构成目标 CP 的概念基础。

---

### 9. p4vec_7620 -- grounds

- **源 CP** (CH20): "Governing Documents of the Egmont Group (2013)"
- **目标 CP** (CH19): "International Cooperation (Recs 36-40)"
- **判定理由**: 方向反了。FATF 建议 36-40 是国际合作的标准性框架（上级规范），埃格蒙特集团的治理文件是金融情报机构（FIU）层面对该框架的操作性实施。应是 FATF 建议（目标）ground 埃格蒙特文件（源），而非反向。LLM reason 称"Egmont documents operationalize the FATF's international cooperation framework"恰好说明实施者（源）不能 ground 框架制定者（目标）。

---

### 10. p4vec_1634 -- grounds

- **源 CP** (CH06): "PEP Risk Management and Monitoring Approaches"
- **目标 CP** (CH44): "FATF Guidance on PEP Risk Levels"
- **判定理由**: 方向反了。目标 CP 提供的是 FATF 的监管指引（外国 PEP 始终高风险、国内 PEP 需风险评估），这是监管层级的规范。源 CP 描述的是机构层面的实际操作方式（"once a PEP, always a PEP"、根据风险偏好调整监控）。监管指引是操作实践的规范性基础，应 ground 实践，而非实践 ground 指引。

---

### 11. p4vec_2966 -- summarizes

- **源 CP** (CH47): "External information sources for alert investigation"
- **目标 CP** (CH58): "Internal and External Data Sources"
- **判定理由**: 源 CP 仅涵盖外部信息来源（公开资源、社交媒体、合作伙伴、执法机构），且限定了场景为"alert investigation"。目标 CP 涵盖内部和外部数据来源，场景更广泛（包括制裁名单等运营数据）。源 CP 是目标 CP 的子集且场景更窄，无法作为目标 CP 的摘要（summarizes 要求源是目标的概括，必须覆盖目标的全部核心内容）。

---

### 12. p4vec_1568 -- grounds

- **源 CP** (CH31): "Law enforcement role: investigation, prosecution, and asset recovery"
- **目标 CP** (CH19): "Criminalizing Money Laundering and Asset Confiscation"
- **判定理由**: 方向反了。目标 CP 描述的是 FATF 建议 3 和 4--要求司法管辖区将洗钱定为犯罪并赋予主管当局冻结、扣押、没收资产的权力。这是法律框架的建立。源 CP 描述的是执法机构在这一法律框架下的实际操作（调查、起诉、追回资产）。法律框架（目标）是执法操作（源）的前提和基础，而非反向。

---

### 13. p4vec_3419 -- grounds

- **源 CP** (CH30): "Adjusting EWRA based on new risk information from external reports"
- **目标 CP** (CH56): "Scenario Development from Product Risk Assessment"
- **判定理由**: 源 CP 讨论的是根据外部报告更新 EWRA（企业全面风险评估），涉及风险识别后的评估调整。目标 CP 讨论的是交易监控场景开发--将产品风险评估结果转化为具体的 TM 监控规则。两者虽同属风险管理流程，但涉及的是不同的活动：EWRA 维护 vs. TM 场景工程。源 CP 不构成目标 CP 的概念基础，目标 CP 的场景开发方法论独立存在。

---

### 14. p4vec_3170 -- illustrates

- **源 CP** (CH47): "Internal information sources for alert investigation"
- **目标 CP** (CH57): "Identifying data for a new TM system: core data, risk mapping, supplemental sources, and evaluation"
- **判定理由**: 源 CP 是告警调查中使用的四类内部信息源（KYC 数据、交易数据、告警历史、账户历史）的清单。目标 CP 是 Sarah 为新建 TM 系统选择数据源的案例研究（核心交易数据、客户画像、风险映射、补充来源、评估）。源是调查活动中的信息类型参考，目标是系统设计中的数据选型过程--两个完全不同的业务流程。源不"illustrate"目标。

---

### 15. p4vec_6611 -- grounds

- **源 CP** (CH49): "SAR Narrative Writing Best Practices"
- **目标 CP** (CH57): "Legal and Regulatory Requirements for Documentation and Reporting"
- **判定理由**: 方向反了。目标 CP 阐明了文档记录的法律和监管要求（民事和刑事责任、无记录则无法证明合规），这是"为什么需要做好文档"的规范性基础。源 CP 讨论的是 SAR 叙事的具体写法（plain English、5W1H、清晰标题）。法律要求（目标）是 SAR 写作规范（源）存在的原因，而非写作规范 ground 法律要求。

---

### 16. p4vec_5537 -- grounds

- **源 CP** (CH51): "Definition and Role of PETs in AFC"
- **目标 CP** (CH26): "Fundamental Data Security and Privacy Obligations"
- **判定理由**: 方向反了。目标 CP 阐述的是金融机构保护客户数据的根本义务（安全存储、授权访问、目的限制、安全销毁），这是监管层面的基本要求。源 CP 介绍的是隐私增强技术（PETs）--一种帮助满足这些隐私义务的工具。基本隐私义务（目标）是 PETs（源）存在的理由，而非 PETs 定义 ground 隐私义务。

关键原文证据：
- 目标 CP："Financial institutions have a high duty to care for--and often a legal obligation to ensure the security and privacy of--customer data." -- 这是独立的法律义务。
- 源 CP："PETs...ensure compliance with data protection regulations such as the GDPR..." -- PETs 是合规工具，义务先于工具。

---

### 17. p4vec_3350 -- illustrates

- **源 CP** (CH58): "Magnify Bank's Data Integration Process for Enhanced Transaction Monitoring"
- **目标 CP** (CH47): "Transforming Collected Data into Actionable Intelligence"
- **判定理由**: 源 CP 是 Magnify Bank 的技术案例--描述数据工程流程（提取、标准化、合并、去重、实体解析、特征工程），核心是数据集成和准备。目标 CP 讨论的是调查分析工作--分析师如何将收集到的数据转化为可操作情报（验证怀疑、决定是否需要进一步调查）。源是数据工程技术流程，目标是调查分析思维过程，两者虽都涉及"数据到价值"，但属于完全不同的专业领域和流程阶段。源不"illustrate"目标。

---

## 假阳性模式总结

17 条假阳性呈现以下四类模式：

| 模式 | 数量 | 典型表现 |
|------|------|----------|
| **方向反转** (direction reversed) | 8 条 | 应是 target grounds source 但 LLM accept 了 source grounds target；常见于"监管框架 vs 操作实施"、"父概念 vs 子概念"的关系 |
| **共同主题无特定关系** (shared topic only) | 5 条 | 两 CP 共享大主题但无 grounds/illustrates/summarizes 关系，例如技术数据工程 vs 调查分析、AI 治理 vs AI 功能 |
| **scope 不匹配** (scope mismatch) | 3 条 | 源 CP 的 scope 与目标 CP 不一致（如仅覆盖外部来源却声称总结内外部来源、准入前筛查声称总结支付筛查） |
| **过于泛化** (too generic) | 1 条 | 源 CP 只有一句话且过于泛化，无法作为目标 CP 的有效摘要 |

其中"方向反转"是最突出的假阳性类型（8/17 = 47%），说明 LLM 在判断 grounds 方向时存在系统性弱点：当看到两个 CP 有明确的概念关联时，容易 accept 而不能正确判断依赖关系的方向。

---

## 通过审核的 33 条摘要

以下 33 条经逐条对照原文审核，LLM 指定的 relation_type 可被原文支持：

1. **p4vec_7419** (illustrates): 德银罚款案例真实说明了"未提交 SAR 将面临罚款、监管限制等处罚"。
2. **p4vec_0615** (grounds): 规则型 TM 的定义→规则型 TM 的测试与调优，直接应用。
3. **p4vec_0091** (grounds): FATF 风险为本方法→国家风险评估的具体实施。
4. **p4vec_1949** (illustrates): MSB 合规职能重组案例真实说明了"机构必须投资合规"的原则。
5. **p4vec_1686** (grounds): NRA 定义→行业/专题/全企业风险评估，后者明确表示"补充 NRA"。
6. **p4vec_0558** (grounds): 区块链基础（区块、哈希、节点）→区块链浏览器（查询区块信息的工具），直接应用。
7. **p4vec_8074** (grounds): SPV 定义与合法用途→SPV 为高风险客户类型的原因，直接应用。
8. **p4vec_5713** (grounds): BSA 五大支柱→第四支柱（独立审计）的详细展开。
9. **p4vec_6336** (grounds): 腐败的定义/类型→ABC 合规的重要性（腐败是洗钱上游犯罪），直接应用。
10. **p4vec_0121** (grounds): 银行服务分类及其风险→商业银行具体风险的详细展开。
11. **p4vec_0512** (grounds): 第二道防线定义/角色→第二道防线与第一道防线的互动方式。
12. **p4vec_1596** (grounds): EWRA 框架→产品风险评估（EWRA 的具体输入），目标明确说"影响 EWRA"。
13. **p4vec_1781** (grounds): 批量筛查流程→名单管理，筛查中的"名单匹配"步骤直接关联名单管理。
14. **p4vec_0099** (grounds): RBA 原则→RBA 在技术投资中的应用。
15. **p4vec_1403** (grounds): 区块链特性（不可篡改、透明）→区块链追踪技术（利用这些特性进行 AML）。
16. **p4vec_3975** (grounds): CDD 要求→高风险客户的具体管控措施，直接应用。
17. **p4vec_4345** (grounds): 数据转换/清洗→实施新系统前评估数据质量的重要性。
18. **p4vec_6325** (grounds): 实时和批量筛查的类型/目的→筛查名单管理。
19. **p4vec_2375** (grounds): 数据安全与隐私基本义务→私营部门信息共享对隐私的考量。
20. **p4vec_0014** (summarizes): TM 和调查技术概述→监控与调查技术的模块总览。
21. **p4vec_1001** (grounds): AI 系统实施与测试→RPA/AI 的治理与审慎实施。
22. **p4vec_4029** (grounds): 洗钱三阶段（放置、离析、融合）→银行业涉及全部三个阶段的具体表现。
23. **p4vec_0954** (grounds): TM 文档记录与面向未来→文档记录的法律和监管要求。
24. **p4vec_2950** (grounds): FATF 六步 NRA 框架→NRA 的定义和产出。
25. **p4vec_0504** (grounds): AI 实施原则→AI 交易监控工具的具体测试调优方法。
26. **p4vec_0524** (grounds): PEP 风险管理方法→PEP 身份到期与审查的详细讨论。
27. **p4vec_2993** (grounds): 高风险法人的 EDD→高风险客户通用的限制与管控。
28. **p4vec_2179** (grounds): EWRA 的核心地位→各类风险评估类型概览。
29. **p4vec_0188** (grounds): FATF 风险为本方法→RBA 在技术投资中的应用。
30. **p4vec_4484** (grounds): 第二道防线的监督与协作→第二道防线中的典型职能列表。
31. **p4vec_0735** (grounds): 第二道防线详细定义→第二道防线的监督与协作角色。
32. **p4vec_0402** (grounds): 监管报告义务与后果→报告金融犯罪的法律义务与个人责任。
33. **p4vec_5796** (grounds): 供应商管理与第二道防线→KYV 供应商尽职调查（筛查与网络安全检查）。

---

## 建议

1. **grounds 方向判定需加强**: 8 条假阳性因方向反转导致，建议在 prompt 中增加方向校验指令，要求 LLM 明确论证"为什么源 CP 是目标 CP 的前提/基础，而不是反过来"。
2. **"共同主题"不等于"特定关系"**: 多条假阳性仅因共享主题被判 accept，建议在 prompt 中要求 LLM 证明两个 CP 之间存在特定的知识依赖或说明关系，而非仅凭主题相似。
3. **summarizes 需 scope 匹配校验**: 源 CP 的 scope 必须覆盖目标 CP 的全部核心内容，否则不构成摘要关系。
4. **极简 CP 应特殊处理**: 仅有 1 句话的 CP（如 p4vec_5102 的源）不应作为"summarizes"关系的源，因其信息量不足以概括目标。
