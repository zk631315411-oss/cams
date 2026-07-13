# Phase 4.0 — 检索质量验证报告
生成时间: 2026-07-06 14:51:24
抽样题数: 15 | 总候选记录: 900
---

## v7_q_000048 | CH01 | single | tier=clean
**中文题干**: 哪种运营情况可能表明洗钱活动正在通过一家接受存款的金融机构进行？
**中文选项**: A: 该机构注意到客户对大面额钞票的需求有所增加. B: 该机构对其出售的货币工具进行连续编号并记录在案. C: 该机构注意到,在支持资金快速转移或汇款的交易服务中,结算时间有所缩短. D: 该机构注意到其数字产品和服务的采用率有所上升.
**英文题干**: Whichoperationalsi tuationmightindicatethatmoneylaunderingis occurringatorthroughaDeposit-takingfinancia Iinstitution? Theinstitutionhasobservedanincrea seincustomerdemandforlarge-deno minationbanknotes. Theinstitutionmaintainsasequentially
**英文选项**: B: numberedlogofthemonetaryinstrum entsitsells. Theinstitutionhasobservedareduced settlementtimeinthetransactionservi C: cesthatsupportTherapidmovement orremittanceoffunds. Theinstitutionhasobservedanincrea seintheadoptionofitsdigitalproduct

### BGE 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 0.7247 | v7u_N004531 | 网络分析识别快速大额交易、循环资金流等洗钱可疑模式 | fact |
| 2 | 0.7213 | v7u_N000923 | 持续监控交易活动以识别异常模式，防范洗钱 | process |
| 3 | 0.7203 | v7u_N002344 | 例如，若A银行怀疑某客户洗钱，可能终止其账户 | case |
| 4 | 0.7193 | v7u_N001573 | 银行应持续监控交易以发现可疑活动 | risk_indicator |
| 5 | 0.7091 | v7u_N000283 | 金融机构通过交易监控系统发现可疑活动，包括结构化存款和异常资金流动 | process |

### 中文 BM25 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 99.6844 | v7u_N003532 | 该客户此前在该机构无SAR申报记录。 | fact |
| 2 | 75.1196 | v7u_N002868 | 组织可能注意到新产品或现有产品中先前未识别的风险。 | fact |
| 3 | 72.6962 | v7u_N000776 | Emma 注意到该请求涉及部分与新买家相关的异常交易。 | case |
| 4 | 70.5471 | v7u_N002806 | 无论自动化还是手动，工具必须根据机构量身定制，包含正确计算并纳入该机构特有的风险 | rule |
| 5 | 64.2252 | v7u_N003541 | MLRO 注意到两个账户持有人均为当地公司董事会成员。 | case |

### 英文 BM25 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 0.0000 | v7u_N000001 | 介绍洗钱及其他金融犯罪及其后果与风险 | definition |
| 2 | 0.0000 | v7u_N000002 | 学习目标：犯罪分子如何利用金融机构、贸易网络和新兴技术洗钱 | fact |
| 3 | 0.0000 | v7u_N000003 | 通过了解金融犯罪类型，加强合规计划、交易监控和风险为本策略 | rule |
| 4 | 0.0000 | v7u_N000004 | 案例：翻译公司Linguistix交易量异常激增引发怀疑 | case |
| 5 | 0.0000 | v7u_N000005 | 调查发现Linguistix收入激增且交易来自高风险司法管辖区 | case |

---

## v7_q_000009 | CH01 | single | tier=clean
**中文题干**: 在通过组织的全企业制裁风险评估发现可能存在漏洞,即与业务规模和运营情况相比,生成的制裁筛查警报数量过少时,以下哪项行动最能确保该风险领域得到妥善管理和尽可能彻底的整改？
**中文选项**: A: 审查企业范围的风险评估方法 B: 加强员工关于已关闭警报的合理化说明文档编制方面的培训 C: 重新审视交易后监控系统的参数和阀值 D: 审查筛选系统当前采用的模糊逻辑
**英文题干**: 9395 单选 Uponlearningofap otentialweaknessthroughanorganization'sent erprise-widesanctionsriskAssessmentrelating toalownumberofsanctions screening alertsg eneratedcomparedto theBusinesssizeandop erationsidentified,whichactionwouldbestens uretheriskareaisproperlyManagedandreme diatedtothebestpossibleextent? Reviewing theenterprise-wideriskass
**英文选项**: A: essmentmethodology B: entationofjustificationonclosedalerts RevisitingThepost-transachionmonito ring systemparametersand threshold S Daiinnhf IaaiOurrntld E: nhancingstafftrainingonthedocum

### BGE 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 0.6996 | v7u_N004413 | 进行全面的产品风险评估以识别漏洞并定制监控规则 | process |
| 2 | 0.6857 | v7u_N004208 | 有效制裁筛查需规划筛查对象、选用名单并测试名单管理流程。 | process |
| 3 | 0.6792 | v7u_N004216 | 应建立名单审查流程和技术保证流程，确保制裁名单正确集成并产生相关警报。 | fact |
| 4 | 0.6720 | v7u_N004468 | 误报率过高时，阈值可能过于严格，应适当降低以减少不必要告警。 | case |
| 5 | 0.6690 | v7u_N003035 | 机构必须筛查每笔交易以检测制裁风险 | process |

### 中文 BM25 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 109.4164 | v7u_N001454 | 不存在通用的风险评估方法 | fact |
| 2 | 95.6147 | v7u_N002162 | 企业范围风险评估（EWRA）可能需要根据新识别的风险进行调整。 | rule |
| 3 | 93.6598 | v7u_N000406 | 对组织的银行产品和服务进行彻底的风险评估 | rule |
| 4 | 79.7474 | v7u_N004239 | 在制裁筛查系统中，可调优模糊逻辑级别以检测名称变体。 | definition |
| 5 | 75.9105 | v7u_N002870 | 可能需要重新审视产品风险评估并设定交易数量、金额阈值或限制产品面向特定客户群体。 | rule |

### 英文 BM25 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 10.3868 | v7u_N004775 | 客户活动，如交易发送接收及涉及方。 | fact |
| 2 | 10.0882 | v7u_N003293 | 往返交易：汇出的汇款立即或不久后作为收到的汇款返回 | fact |
| 3 | 9.7864 | v7u_N003240 | 阈值是行为的标准。 | definition |
| 4 | 9.3442 | v7u_N004313 | 批量筛查是对机构整个客户群进行制裁和恐怖名单筛查的过程 | definition |
| 5 | 9.2590 | v7u_N003281 | 货币交易报告（CTR）阈值示例：超过10,000美元的任何货币交易 | case |

---

## v7_q_000117 | CH01 | single | tier=clean
**中文题干**: 以下哪一项是表明通过贵金属或高价值物品经销商进行潜在洗钱或恐怖主义融资的危险信号？
**中文选项**: A: 一位客户想用现金和加密货币的组合来购买金条. B: 一位顾客明确要求购买经过金伯利进程认证的切割钻石 C: 一位顾客用信用卡向古董商支付了一件高价古董的款项 D: 一位顾客想要为其用现金购买的一款高端限量版豪华手表索取一张手写收据.
**英文题干**: Whichofthefollowin gisaredflagindicatingpotentialmoneylaunde ringorterrorismfinancingThroughdealersofpr eciousmetalsorhigh-valueitems?
**英文选项**: A: customerwantsahand-writtenrecei ptforacashpurchaseofahigh-end,li mited-editionLuxurywatch B: rchaseaKimberlyProcess-certifiedcu tdiamond

### BGE 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 0.7294 | v7u_N001005 | 客户购买加密资产的资金远超其已知财富或资金来源是洗钱红旗信号 | fact |
| 2 | 0.6937 | v7u_N000520 | 信用卡等信贷产品存在洗钱风险，犯罪分子可用非法资金还款 | risk_indicator |
| 3 | 0.6913 | v7u_N001065 | 贵金属和宝石经销商因商品便携且易变现而面临较高洗钱风险 | fact |
| 4 | 0.6896 | v7u_N002869 | 例如，新的预付卡可能显示来自高风险客户的高频交易。 | case |
| 5 | 0.6888 | v7u_N001260 | 大额现金交易可能表明潜在的非法活动 | fact |

### 中文 BM25 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 82.2761 | v7u_N001156 | 购买珠宝的买家是 Ong 企业的经理，月薪约2500美元，却购买高价值物品 | case |
| 2 | 69.1748 | v7u_N001714 | 反洗钱合规范围扩大至加密货币及艺术品和古董经销商 | fact |
| 3 | 63.8128 | v7u_N001899 | 除当铺外的宝石和贵金属经销商不属于DNFBP行业。 | classification |
| 4 | 59.3136 | v7u_N001141 | 大额现金购买缺乏明确资金来源或证明文件 | fact |
| 5 | 56.4874 | v7u_N000567 | 信用卡洗钱风险虽低于预付卡，但仍需警惕超额还款、快速还款及购买高价值商品等行为。 | risk_indicator |

### 英文 BM25 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 0.0000 | v7u_N000001 | 介绍洗钱及其他金融犯罪及其后果与风险 | definition |
| 2 | 0.0000 | v7u_N000002 | 学习目标：犯罪分子如何利用金融机构、贸易网络和新兴技术洗钱 | fact |
| 3 | 0.0000 | v7u_N000003 | 通过了解金融犯罪类型，加强合规计划、交易监控和风险为本策略 | rule |
| 4 | 0.0000 | v7u_N000004 | 案例：翻译公司Linguistix交易量异常激增引发怀疑 | case |
| 5 | 0.0000 | v7u_N000005 | 调查发现Linguistix收入激增且交易来自高风险司法管辖区 | case |

---

## v7_q_000096 | CH01 | single | tier=clean
**中文题干**: 虽然信托和公司服务提供商(TCSP)有正当理由任命代名股东,但代名股东的哪一特征会带来最大的金融犯罪风险？
**中文选项**: A: 支持公司流动性及退出策略的便捷性 B: 通过将受益所有人的身份从公共登记册中隐匿起来为其提供匿名性 C: 简化与持股相关的行政事务 D: 协助非居民遵守本地所有权法规
**英文题干**: Whiletherearelegiti matereasonsfortrustandcompanyservicepro viders(TCSPs)toappointaNomineesharehold er,whichfeatureofanomineeshareholderpres entsthegreatestfinancialcrimeRisk? Supportingcompanyliquidityandease
**英文选项**: A: ofexitstrategies Providinganonymityforthebeneficial ownerbykeepingtheiridentityhidden fromthepublicRegister Simplifyingadministrativetasksassoci C: atedwithshareholding Helpingnon-residentscomplywithloc D: alownershiplaws

### BGE 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 0.7332 | v7u_N001123 | 犯罪分子可能利用信托与公司服务提供商掩盖资产真实所有权或交易资金来源。 | risk_indicator |
| 2 | 0.7048 | v7u_N001126 | 信托与公司服务提供商常提供名义服务，由第三方代表客户担任董事、高管或股东。 | definition |
| 3 | 0.6943 | v7u_N001127 | 名义董事或股东可被用于隐藏最终受益所有人身份，增加洗钱风险。 | risk_indicator |
| 4 | 0.6895 | v7u_N001070 | 信托或公司服务提供商设立的结构会掩盖受益所有人和资金来源 | fact |
| 5 | 0.6727 | v7u_N000616 | 犯罪分子利用信托中法定所有权与受益所有人的分离来掩盖与金融犯罪的关联 | fact |

### 中文 BM25 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 114.3500 | v7u_N001120 | 信托与公司服务提供商（TCSP）提供代名服务、设立壳公司等业务 | definition |
| 2 | 104.2003 | v7u_N001070 | 信托或公司服务提供商设立的结构会掩盖受益所有人和资金来源 | fact |
| 3 | 96.3301 | v7u_N000612 | 信托通常在公司服务提供商的指导下设立 | fact |
| 4 | 91.8478 | v7u_N001123 | 犯罪分子可能利用信托与公司服务提供商掩盖资产真实所有权或交易资金来源。 | risk_indicator |
| 5 | 75.6978 | v7u_N001126 | 信托与公司服务提供商常提供名义服务，由第三方代表客户担任董事、高管或股东。 | definition |

### 英文 BM25 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 11.0874 | v7u_N001123 | 犯罪分子可能利用信托与公司服务提供商掩盖资产真实所有权或交易资金来源。 | risk_indicator |
| 2 | 10.1579 | v7u_N001126 | 信托与公司服务提供商常提供名义服务，由第三方代表客户担任董事、高管或股东。 | definition |
| 3 | 10.0642 | v7u_N001055 | 房地产中介和TCSP无需遵守反洗钱/反恐怖融资法规或进行合规审计。 | fact |
| 4 | 0.0000 | v7u_N000001 | 介绍洗钱及其他金融犯罪及其后果与风险 | definition |
| 5 | 0.0000 | v7u_N000002 | 学习目标：犯罪分子如何利用金融机构、贸易网络和新兴技术洗钱 | fact |

---

## v7_q_000084 | CH01 | single | tier=clean
**中文题干**: 在以下哪种情况下,公司指定的反洗钱合规官最有必要对公司反洗钱计划进行全面审查,包括识别风险和相应的控制措施？
**中文选项**: A: 外部审计发现了一些不足之处 B: 该公司正在与另一实体合并或收购另一实体 C: 公司所在辖区的立法机构提议制定广泛的反洗钱立法 D: 另一起涉及其他行业的重大洗钱案被公开报道
**英文题干**: Inwhichofthefollo wingsituationswoulditbemostcrucialforthed esignatedAMLcomplianceOfficerofacompan ytoperformacompletereviewofthecompan y'sAMLprogram,includingIdentifyingtherisks andcommensuratecontrols?
**英文选项**: A: iciencies Thecompanyismergingwithoracquir inganotherentity C: byalegislativebodyinthecompany's jurisdiction D: nvolvinganotherindustryispublicized E: xtensiveAMLlegislationisproposed

### BGE 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 0.7345 | v7u_N000402 | 了解近期高调洗钱起诉案例有助于洞察其他银行合规计划的缺陷 | fact |
| 2 | 0.7289 | v7u_N003355 | 各业务条线的政策程序可补充企业级反洗钱标准。 | fact |
| 3 | 0.7094 | v7u_N002559 | 董事会应设立专门的反洗钱或风险管理委员会，配备有知识的成员以监督实施和审查政策。 | rule |
| 4 | 0.7092 | v7u_N001920 | 根据《反洗钱法》，义务实体必须遵守强化合规义务，包括实施强化内部控制、进行客户尽 | rule |
| 5 | 0.7073 | v7u_N000451 | 丑闻重申了健全反洗钱控制和海外子公司监管的重要性 | rule |

### 中文 BM25 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 117.0996 | v7u_N002398 | 指定的反洗钱合规官负责监督反洗钱项目。 | fact |
| 2 | 77.0527 | v7u_N001692 | 《银行保密法》要求义务实体基于五大支柱制定、实施和维护有效的反洗钱计划 | classification |
| 3 | 71.7689 | v7u_N000449 | 丹麦银行总部对爱沙尼亚分行的反洗钱合规失败不知情 | fact |
| 4 | 71.2502 | v7u_N000453 | 金融机构应保持警惕并实施严格的反洗钱控制措施 | fact |
| 5 | 66.1299 | v7u_N001056 | 工作组建议制定全面的反洗钱/反恐怖融资法规以弥补现有差距。 | rule |

### 英文 BM25 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 9.9648 | v7u_N001404 | 技术审查：评估团队分析司法管辖区的法律法规 | fact |
| 2 | 8.6891 | v7u_N002174 | 新红旗信号信号涉及一个银行现有清单中未包含的额外司法管辖区。 | risk_indicator |
| 3 | 8.4638 | v7u_N001512 | OECD贿赂工作组评估并建议各司法管辖区实施和执行公约的情况，发布详细报告。 | fact |
| 4 | 7.9873 | v7u_N003049 | 司法管辖区标签 | context |
| 5 | 7.7563 | v7u_N001402 | 司法管辖区培训：为被评估司法管辖区的代表提供培训 | process |

---

## v7_q_000054 | CH01 | single | tier=clean
**中文题干**: 折 一家机构 单选 正在制定一套全面的反洗钱(AML)框架.以 下哪项陈述最能描述反洗钱政策与程序之间的关 系？ 政策是宽泛的指导方针.程序是针对特 定流程的详细说明.只有程序是必须了
**中文选项**: A: 解和遵守的. 政策规定了组织的原则,并影响程序的 制定.程序是针对特定流程的详细说 明. 政策是针对特定流程的详细说明,程序 则是总体框架.政策和程序都不是强制 要求知晓和遵守的. 政策是针对特定流程的详细说明,程序 D: 则是总体框架.政策和程序都必须了解 并遵守
**英文题干**: Anorganizationisd evelopingacomprehensiveanti-moneylaunderi ng(AML)framework.Whichofthefollowingstat ementsbestdescribestherelationshipbetween
**英文选项**: A: cprocesses.Onlyproceduresareman datoryforknowledgeandadherence. Policiesdefinetheprinciplesofanorg anizationandinfluencethedraftingof procedures.Proceduresaredetailedin structionsforspecificprocesses. Policiesaredetailedinstructionsforsp ecificprocesses.Proceduresareanov erarchingFramework.Neitherpolicies norproceduresaremandatorvforkno

### BGE 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 0.7524 | v7u_N000944 | 需要了解客户的反洗钱政策。 | fact |
| 2 | 0.7332 | v7u_N002406 | 反洗钱政策应包含向高级管理层和董事会上报问题的程序。 | rule |
| 3 | 0.7299 | v7u_N002900 | 政策和程序确保监管合规，机构通常与FATF建议、巴塞尔委员会指南及国家反洗钱法律 | fact |
| 4 | 0.7223 | v7u_N002885 | 反洗钱政策必须动态且基于风险 | rule |
| 5 | 0.7207 | v7u_N003354 | 反洗钱项目应建立合理设计的最低标准以遵守法律法规。 | rule |

### 中文 BM25 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 192.8039 | v7u_N002391 | 政策与程序是管理风险的指南。 | definition |
| 2 | 173.5578 | v7u_N004263 | 政策和程序应包含添加和移除名单条目的流程 | rule |
| 3 | 159.5910 | v7u_N002472 | 合规监控与测试职能评估组织流程的有效性，确保政策和程序得到正确执行并持续改进。 | definition |
| 4 | 157.4697 | v7u_N003674 | 应遵循机构的政策和程序。 | rule |
| 5 | 157.2431 | v7u_N002392 | 政策解释法律法规并提供框架，程序是实施政策的逐步说明。 | definition |

### 英文 BM25 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 6.4370 | v7u_N002491 | 反洗钱咨询 | fact |
| 2 | 5.9545 | v7u_N002505 | 反洗钱合规官负责监督反洗钱合规计划并确保在所有运营司法管辖区遵守反洗钱法规 | fact |
| 3 | 5.9161 | v7u_N000944 | 需要了解客户的反洗钱政策。 | fact |
| 4 | 5.5414 | v7u_N001798 | 欧盟推出反洗钱单一规则手册（含第六项反洗钱指令）。 | fact |
| 5 | 5.5276 | v7u_N001546 | 第二道防线包括反洗钱合规和内部控制 | classification |

---

## v7_q_000045 | CH01 | single | tier=clean
**中文题干**: 国家风险评估(NRA)可以通过以下方式影响金融机构(FI)基于风险的反洗钱和反恐怖融资方法:
**中文选项**: A: 规定在FI的风险评估中必须考虑哪些犯罪行为. B: 就风险最高的客户类型和交易类型提供指导. C: 明确规定必须实施的具体政策和程序. D: 确定可对反洗钱违规行为处以的最高罚款金额.
**英文题干**: ANationalRiskAsse ssment(NRA)canimpactafinancialinstitutio n's(Fl's)risk-basedapproachtoAnti-moneyla underingandterrorismfinancingby: dictatingwhatpredicateoffencesmust beconsideredintheFl'sriskassessm
**英文选项**: A: ent. providingguidanceonthetypesofcus tomersandtransactionsthatposethe highestrisk D: efiningexactlywhatpoliciesandproc eduresmustbeimplemented. determiningthemaximumfinesthatca

### BGE 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 0.8333 | v7u_N002642 | 国家风险评估识别国家层面的洗钱与恐怖融资威胁和风险，并审查高风险行业 | definition |
| 2 | 0.8211 | v7u_N002183 | 国家风险评估（NRA）是司法管辖区识别和评估洗钱威胁与脆弱性的文件。 | definition |
| 3 | 0.7998 | v7u_N002644 | 行业风险评估由国家机关、监管机构等执行，识别并分析特定行业的洗钱与恐怖融资风险 | definition |
| 4 | 0.7622 | v7u_N002125 | 反洗钱/反恐怖融资法规要求组织评估和管理洗钱与恐怖融资风险 | rule |
| 5 | 0.7513 | v7u_N002721 | 企业级风险评估（EWRA）的定义与范围，涵盖洗钱、恐怖融资、制裁规避、欺诈等多种 | definition |

### 中文 BM25 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 104.9797 | v7u_N001732 | 要求维持基于风险的 反洗钱/反恐怖融资 计划，包括强制性风险评估流程 | fact |
| 2 | 102.5719 | v7u_N002184 | NRA应全面并基于广泛数据。 | rule |
| 3 | 102.2181 | v7u_N002634 | 国家风险评估（NRA）作为风险评估类型之一 | context |
| 4 | 98.0850 | v7u_N002183 | 国家风险评估（NRA）是司法管辖区识别和评估洗钱威胁与脆弱性的文件。 | definition |
| 5 | 97.5842 | v7u_N002190 | 司法管辖区可开展行业风险评估（SRA）或专题风险评估以补充NRA。 | fact |

### 英文 BM25 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 13.8824 | v7u_N003294 | 一对多或多对一：无合理解释向多方汇款或反之 | fact |
| 2 | 11.3473 | v7u_N002634 | 国家风险评估（NRA）作为风险评估类型之一 | context |
| 3 | 8.6298 | v7u_N000900 | Tom的兄弟拥有为Tom客户提供保费贷款的金融公司 | fact |
| 4 | 8.5242 | v7u_N004600 | 评估数据与现有格式的兼容性以及系统的处理能力 | fact |
| 5 | 8.4427 | v7u_N000899 | Mary的分析已标记Tom的交易异常，Peter的投诉确认了担忧并触发深入调查， | classification |

---

## v7_q_000158 | CH03 | single | tier=clean
**中文题干**: 对于金融机构的高级管理层而言,哪项关键指标能为其提供有关反洗钱控制措施有效性的最有价值的数据？
**中文选项**: A: 自动监测系统生成的真阳性与假阳性之比 B: 监测名单筛查系统生成的洗钱警报数量 C: 每月新引入的高风险客户数量 D: 因商业原因退出的客户数量
**英文题干**: Which key metric provides senior management information about the effectiveness of its A ML controls? The ratio of true positives to false positives generated by the automated monitoring system. The number of money laundering alerts generated by the watchlist screening system. The number of high-risk customers onboarded each month. The number of clients exited for commercial reasons.
**英文选项**: 

### BGE 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 0.7005 | v7u_N001138 | 健全的尽职调查和交易监控系统对于识别潜在洗钱活动至关重要。 | rule |
| 2 | 0.6912 | v7u_N004541 | 反洗钱系统整合多源信息、自动化风险评级、持续监控客户活动并加速调查数据访问。 | fact |
| 3 | 0.6755 | v7u_N004377 | 通过风险评级，模型帮助反洗钱调查员优先处理高风险警报，减少误报。 | process |
| 4 | 0.6673 | v7u_N004571 | 维持有效的报告机制是证明反洗钱和制裁合规的重要要求。 | rule |
| 5 | 0.6647 | v7u_N002166 | 反洗钱报告官（洗钱RO）考虑将红旗信号信号纳入机构的 反洗钱/反恐怖融资 控制措 | process |

### 中文 BM25 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 131.7996 | v7u_N004247 | 系统生成的预警数量超出预期 | fact |
| 2 | 117.1316 | v7u_N004242 | 不应根据团队规模限制系统生成的预警数量 | rule |
| 3 | 102.3235 | v7u_N004240 | 调优有助于管理警报量并减少系统生成的误报。 | fact |
| 4 | 66.1064 | v7u_N000453 | 金融机构应保持警惕并实施严格的反洗钱控制措施 | fact |
| 5 | 65.5119 | v7u_N004658 | 内部数据包括应避免的客户名单（如因合规原因退出的客户）以及经调查认定为低金融犯罪 | fact |

### 英文 BM25 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 55.5361 | v7u_N003283 | 减少误报是设定阈值的关键目标，以高效利用资源 | rule |
| 2 | 50.8253 | v7u_N004240 | 调优有助于管理警报量并减少系统生成的误报。 | fact |
| 3 | 49.3219 | v7u_N003819 | 减少交易监控中的误报可降低客户查询需求并减轻运营压力。 | fact |
| 4 | 49.0008 | v7u_N004460 | 警报总量是监控校准的关键指标 | fact |
| 5 | 42.5361 | v7u_N004813 | 标准化和整合的数据使交易监控更可靠高效，减少误报和漏报风险。 | fact |

---

## v7_q_000173 | CH03 | single | tier=clean
**中文题干**: 以下哪些属性会增强反洗钱计划的有效性？
**中文选项**: A: 对所有员工进行基本的反洗钱培训 B: 任命一名反洗钱专员作为董事会成员,使其成为管理层的正式成员,并赋予其更大的权力 C: 审计人员在审计结果不尽如人意的情况下,为项目提供具体的指导和支持 D: 通过反洗钱工作人员提供有效的挑战以及持续的交叉培训
**英文题干**: Whic 单选 hofthefollowingattributeswouldenhanceanA MLprogram'seffectiveness? ProvidingbasicAMLtrainingtoallemp
**英文选项**: A: uditorsprovidingprescriptiveguidanc B: boardasaworkingmemberofmanag ementwithincreasedAuthority C: eandsupporttotheprogramfollowing alessthanSatisfactoryaudit ProvidingeffectivechallengewithAML staffandcontinuouscross-training

### BGE 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 0.7138 | v7u_N002559 | 董事会应设立专门的反洗钱或风险管理委员会，配备有知识的成员以监督实施和审查政策。 | rule |
| 2 | 0.7106 | v7u_N003355 | 各业务条线的政策程序可补充企业级反洗钱标准。 | fact |
| 3 | 0.7029 | v7u_N001694 | 指定一名反洗钱官负责计划的日常活动 | fact |
| 4 | 0.7019 | v7u_N002410 | 培训应涵盖内部控制并清晰说明员工在反洗钱计划中的角色与职责。 | rule |
| 5 | 0.6961 | v7u_N000944 | 需要了解客户的反洗钱政策。 | fact |

### 中文 BM25 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 119.3288 | v7u_N002408 | 第三大支柱要求对员工进行定期、持续的反洗钱培训。 | rule |
| 2 | 82.4200 | v7u_N001694 | 指定一名反洗钱官负责计划的日常活动 | fact |
| 3 | 80.6544 | v7u_N001692 | 《银行保密法》要求义务实体基于五大支柱制定、实施和维护有效的反洗钱计划 | classification |
| 4 | 75.3985 | v7u_N000907 | 向经纪人提供针对性的反洗钱培训，强调红旗信号信号和合规义务。 | fact |
| 5 | 69.2340 | v7u_N000483 | 控制权和所有权在反洗钱工作中至关重要 | fact |

### 英文 BM25 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 0.0000 | v7u_N000001 | 介绍洗钱及其他金融犯罪及其后果与风险 | definition |
| 2 | 0.0000 | v7u_N000002 | 学习目标：犯罪分子如何利用金融机构、贸易网络和新兴技术洗钱 | fact |
| 3 | 0.0000 | v7u_N000003 | 通过了解金融犯罪类型，加强合规计划、交易监控和风险为本策略 | rule |
| 4 | 0.0000 | v7u_N000004 | 案例：翻译公司Linguistix交易量异常激增引发怀疑 | case |
| 5 | 0.0000 | v7u_N000005 | 调查发现Linguistix收入激增且交易来自高风险司法管辖区 | case |

---

## v7_q_000216 | CH03 | single | tier=clean
**中文题干**: 一个健全的反洗钱合规计划需要一个全面的治理框架,涵盖关键要素,以确保金融体系的完整性.哪个要素构成有效的反洗钱合规计划的起点？
**中文选项**: A: 持续监测 B: 风险评估 C: 政策与程序 D: 可疑活动报告 E: 客户尽职调查
**英文题干**: Asou ndAMLcomplianceprogramrequiresacompre hensivegovernanceframeworkthataddresses keyElementstoensuretheintegrityofthefinan cialsystem.Whichelementformsthestartingp ointofaneffectiveAMLcomplianceprogram? Ongoingmonitoring
**英文选项**: A: Riskassessment C: Policiesandprocedures D: Suspiciousactivityreporting E: Customerduediligence

### BGE 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 0.7556 | v7u_N002403 | 有效反洗钱计划的第一大支柱是确保持续合规的内部政策与控制系统。 | definition |
| 2 | 0.7281 | v7u_N000099 | 受监管实体必须建立强大的反洗钱和制裁合规计划，违规处罚包括： | classification |
| 3 | 0.7224 | v7u_N001138 | 健全的尽职调查和交易监控系统对于识别潜在洗钱活动至关重要。 | rule |
| 4 | 0.7166 | v7u_N003356 | 合规项目应包括洗钱和恐怖融资风险的公司治理和整体管理。 | rule |
| 5 | 0.7051 | v7u_N003355 | 各业务条线的政策程序可补充企业级反洗钱标准。 | fact |

### 中文 BM25 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 102.6239 | v7u_N002373 | 关键要素：风险评估、客户尽职调查、交易监控、可疑报告和资源分配 | risk_indicator |
| 2 | 97.6384 | v7u_N002363 | TD银行《银行保密法》/反洗钱合规项目存在风险评估、客户尽职调查、交易监控和可疑 | case |
| 3 | 96.1878 | v7u_N001876 | 该法案要求报告实体实施并维护反洗钱/反恐怖融资合规计划 | rule |
| 4 | 94.7847 | v7u_N002505 | 反洗钱合规官负责监督反洗钱合规计划并确保在所有运营司法管辖区遵守反洗钱法规 | fact |
| 5 | 90.3098 | v7u_N002398 | 指定的反洗钱合规官负责监督反洗钱项目。 | fact |

### 英文 BM25 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 0.0000 | v7u_N000001 | 介绍洗钱及其他金融犯罪及其后果与风险 | definition |
| 2 | 0.0000 | v7u_N000002 | 学习目标：犯罪分子如何利用金融机构、贸易网络和新兴技术洗钱 | fact |
| 3 | 0.0000 | v7u_N000003 | 通过了解金融犯罪类型，加强合规计划、交易监控和风险为本策略 | rule |
| 4 | 0.0000 | v7u_N000004 | 案例：翻译公司Linguistix交易量异常激增引发怀疑 | case |
| 5 | 0.0000 | v7u_N000005 | 调查发现Linguistix收入激增且交易来自高风险司法管辖区 | case |

---

## v7_q_000126 | CH03 | single | tier=clean
**中文题干**: 反洗钱审计独立性的一个关键因素在于审计员应当:
**中文选项**: A: 从未在AML/CFT部门的以往职位上工作过. B: 与该组织的反洗钱/打击资助恐怖主义合规人员没有任何关联. C: 在审计开始前已由董事会审查过 D: 接受过充分的反洗钱培训,能够进行独立审查.
**英文题干**: Ake factorintheindependenceofanAMLauditist attheauditorshould. haveneverworkedinpreviousassign mentswithintheAMUCFTdepartment
**英文选项**: A: S. havenoInvolvementwiththeorganiza B: tion'sAML/CPTcompliancestaff. havebeenscreenedbytheboardofdi C: rectorsbeforetheauditstarts besufficientlytrainedinAMLtobeabl etoprovideanindependentreview

### BGE 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 0.7744 | v7u_N002412 | 独立审计职能必须具备足够的知识和经验来理解与分析反洗钱计划。 | rule |
| 2 | 0.7481 | v7u_N002534 | 独立审计评估第一、二道防线控制的有效性和效率，确保反洗钱项目符合监管要求。 | fact |
| 3 | 0.7282 | v7u_N002521 | 独立审计职能是反洗钱项目的第四道防线。 | definition |
| 4 | 0.7189 | v7u_N000325 | 受监管实体必须遵守详细的反洗钱/反恐怖融资要求，包括实施反洗钱计划、客户尽职调查 | rule |
| 5 | 0.7161 | v7u_N001811 | 反洗钱R要求义务实体评估反洗钱人员的技能、声誉、诚实和正直 | rule |

### 中文 BM25 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 91.6089 | v7u_N002523 | 独立审计职能直接向审计委员会或董事会报告以确保独立性。 | rule |
| 2 | 87.1864 | v7u_N001696 | 确保基于风险频率进行独立审计以监控和维护充分计划 | fact |
| 3 | 74.1363 | v7u_N000907 | 向经纪人提供针对性的反洗钱培训，强调红旗信号信号和合规义务。 | fact |
| 4 | 73.4896 | v7u_N002408 | 第三大支柱要求对员工进行定期、持续的反洗钱培训。 | rule |
| 5 | 70.3224 | v7u_N002521 | 独立审计职能是反洗钱项目的第四道防线。 | definition |

### 英文 BM25 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 0.0000 | v7u_N000001 | 介绍洗钱及其他金融犯罪及其后果与风险 | definition |
| 2 | 0.0000 | v7u_N000002 | 学习目标：犯罪分子如何利用金融机构、贸易网络和新兴技术洗钱 | fact |
| 3 | 0.0000 | v7u_N000003 | 通过了解金融犯罪类型，加强合规计划、交易监控和风险为本策略 | rule |
| 4 | 0.0000 | v7u_N000004 | 案例：翻译公司Linguistix交易量异常激增引发怀疑 | case |
| 5 | 0.0000 | v7u_N000005 | 调查发现Linguistix收入激增且交易来自高风险司法管辖区 | case |

---

## v7_q_000011 | CH04 | single | tier=clean
**中文题干**: 以下哪一项描述了金融情报机构(FIU)在进行跨境洗钱调查时正式的信息共享与合作方式？
**中文选项**: A: 金融行动特别工作组(FATF)、欧洲委员会打击洗钱组织(MONEYVAL)及其他作为金融情报机构联络点的区域机构 B: 狼堡集团作为金融情报机构的沟通平台 C: 反洗钱金融情报机构之间为建立结构化信息共享而签订的谅解备忘录(MOU) D: 互助法律援助条约(MLATS),允许金融情报机构请求逮捕和获取证据
**英文题干**: Whichofthefollowingdescribesaforma Imethodofinformationsharingandcooperation betweenFinancial IntelligenceUnits(FIUs)whe nconductingcross-bordermoneylaunderingin vestigations?
**英文选项**: A: bodiesactingasacontactpointforFl Us TheWolfsbergGroupservingasaco B: mmunicationplatformforFiUs MemorandaofUnderstanding(Mous) betweenFiUsestablishingstructuredi nformationsharing Mutual LegalAssistanceTreaties(ML D: ATs)allowingFlUstorequestarrestsa ndevidence F: ATF,MONEYVAL,andotherregional

### BGE 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 0.7479 | v7u_N002223 | 机构应与国际同行共享信息以打击跨境洗钱和恐怖融资 | rule |
| 2 | 0.7023 | v7u_N001381 | FATF建议要求当局通过信息交换和联合调查促进国际合作以打击金融犯罪。 | rule |
| 3 | 0.6977 | v7u_N001554 | 信息共享使金融情报机构能够共享可疑金融活动的情报 | risk_indicator |
| 4 | 0.6934 | v7u_N001549 | 埃格蒙特集团是各国金融情报机构的国际网络，促进合作与情报共享以打击洗钱、恐怖融资 | definition |
| 5 | 0.6925 | v7u_N001321 | 与全球机构合作加强反洗钱/反恐怖融资框架 | fact |

### 中文 BM25 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 294.7442 | v7u_N002218 | 国家金融情报机构接收、分析和传播金融情报 | definition |
| 2 | 292.1364 | v7u_N001554 | 信息共享使金融情报机构能够共享可疑金融活动的情报 | risk_indicator |
| 3 | 269.1991 | v7u_N002275 | 金融情报机构与执法机构合作可促成执法行动 | fact |
| 4 | 268.9499 | v7u_N001364 | 金融机构有义务向金融情报机构报告可疑交易 | rule |
| 5 | 267.5893 | v7u_N001743 | FinCEN 作为美国 FIU，与全球 100 多个 FIU 合作共享金融情报。 | fact |

### 英文 BM25 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 10.6927 | v7u_N001653 | 巴塞尔AML指数数据来源包括FATF互评估报告、美国国务院国际 narcotic | fact |
| 2 | 9.6802 | v7u_N001407 | 起草互评估报告：完成互评估报告 | fact |
| 3 | 9.0118 | v7u_N001399 | 互评估流程包含七个阶段。 | fact |
| 4 | 8.7489 | v7u_N002218 | 国家金融情报机构接收、分析和传播金融情报 | definition |
| 5 | 8.7356 | v7u_N002308 | 适当的谅解备忘录、政策和程序能提供确定性并促进信任发展。 | fact |

---

## v7_q_000205 | CH05 | single | tier=clean
**中文题干**: 一家执法机构向一家金融机构提交了多项请求.哪项请求是合法的,并且需要银行作出回应？
**中文选项**: A: 应口头请求保留账户开通状态 B: 在未获传票的情况下提供文件和证词 C: 应书面请求获取特权文件 D: 根据法院命令冻结账户
**英文题干**: -[ComplianceStandardsforAMLandCF 单选 TJAlawenforcementagencysubmitsseveralre queststoafinancialinstitution.Whichrequestis Legitimateandrequiresthebanktorespond? Keepanaccountopenuponverbalreq
**英文选项**: A: uest Producedocumentsandtestimonywit B: houtasubpoena Seizeprivilegeddocumentsuponwritt C: enrequest F: reezeanaccountintermsofacourt order

### BGE 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 0.7725 | v7u_N003631 | 执法机构可能要求金融机构保持账户开放并监控以协助调查。 | fact |
| 2 | 0.7301 | v7u_N003562 | 执法指令可要求保留账户以进一步调查 | rule |
| 3 | 0.7136 | v7u_N003629 | 金融机构有义务回应FIU和执法机构关于交易和账户所有权的信息请求。 | rule |
| 4 | 0.7104 | v7u_N003322 | 法院命令可要求金融机构提供账户信息或交易记录 | fact |
| 5 | 0.7077 | v7u_N003636 | 收到执法请求后，金融机构应进行初步评估。 | rule |

### 中文 BM25 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 89.4794 | v7u_N003322 | 法院命令可要求金融机构提供账户信息或交易记录 | fact |
| 2 | 85.0250 | v7u_N003621 | 传票和法院命令是最正式的请求，规定记录提交的截止日期。 | definition |
| 3 | 77.8097 | v7u_N003620 | 执法部门必须提交书面请求，请求形式可能不同。 | rule |
| 4 | 69.8111 | v7u_N003629 | 金融机构有义务回应FIU和执法机构关于交易和账户所有权的信息请求。 | rule |
| 5 | 65.3020 | v7u_N003562 | 执法指令可要求保留账户以进一步调查 | rule |

### 英文 BM25 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 9.2577 | v7u_N002289 | 欧洲调查令（EIO）是欧盟内促进司法协助的措施 | definition |
| 2 | 7.6061 | v7u_N000819 | 货币服务企业的服务包括汇票 | fact |
| 3 | 7.4160 | v7u_N002091 | 美国2025年行政令14179鼓励AI创新而非监管，撤销先前AI治理蓝图 | fact |
| 4 | 6.2086 | v7u_N003622 | 正式请求的截止日期从几天到几周不等，取决于机构、复杂性、管辖权和命令类型。 | fact |
| 5 | 6.2086 | v7u_N003630 | 执法请求的类型包括法院传票、生产令和与调查相关的具体询问。 | classification |

---

## v7_q_000125 | CH05 | single | tier=clean
**中文题干**: 根据埃格蒙特集团原则,金融情报机构(FIU)之间的信息交换应遵循以下原则:
**中文选项**: A: 报. B: 仅当外国金融情报机构的地位与执法相关时. C: 自由地、自发地,并应请求,在互惠的基础上. D: 在提供财务和行政信息的数量上设定限制.
**英文题干**: Under the
**英文选项**: A: Without the expectation of reciprocity on how the information will be used B: Only if the status of the foreign C: Freely, spontaneously, and upon request, on the basis of reciprocity D: With set limits on the amount of financial and administrative information provided E: gmont F: IU is related to law enforcement G: roup Principles, information exchange among financial intelligence units (FIUs) should be conducted

### BGE 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 0.8455 | v7u_N002258 | 根据FATF标准和埃格蒙特集团原则，FIU应自发或应请求相互传播金融情报 | rule |
| 2 | 0.7122 | v7u_N001364 | 金融机构有义务向金融情报机构报告可疑交易 | rule |
| 3 | 0.7115 | v7u_N002250 | FATF要求各司法辖区设立FIU以接收、分析和传播金融情报 | rule |
| 4 | 0.7099 | v7u_N001940 | 金融公司提交可疑交易报告后，金融情报院可将相关信息分享给执法机构以采取进一步行动 | process |
| 5 | 0.7094 | v7u_N002218 | 国家金融情报机构接收、分析和传播金融情报 | definition |

### 中文 BM25 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 162.2908 | v7u_N001561 | 埃格蒙特集团2013年文件概述FIU在国际合作与信息交换中的运作 | fact |
| 2 | 156.5489 | v7u_N002258 | 根据FATF标准和埃格蒙特集团原则，FIU应自发或应请求相互传播金融情报 | rule |
| 3 | 149.8616 | v7u_N001743 | FinCEN 作为美国 FIU，与全球 100 多个 FIU 合作共享金融情报。 | fact |
| 4 | 143.4208 | v7u_N001549 | 埃格蒙特集团是各国金融情报机构的国际网络，促进合作与情报共享以打击洗钱、恐怖融资 | definition |
| 5 | 128.0459 | v7u_N001551 | 埃格蒙特集团的治理机构是金融情报机构负责人会议，以共识方式决策 | fact |

### 英文 BM25 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 54.9516 | v7u_N002258 | 根据FATF标准和埃格蒙特集团原则，FIU应自发或应请求相互传播金融情报 | rule |
| 2 | 45.2364 | v7u_N001554 | 信息共享使金融情报机构能够共享可疑金融活动的情报 | risk_indicator |
| 3 | 42.2360 | v7u_N000164 | 共同申报准则（CRS）要求司法管辖区每年自动交换金融账户信息以打击逃税。 | definition |
| 4 | 41.1920 | v7u_N002260 | FIU向执法部门传播的材料通常仅供情报使用，不能直接作为法庭证据 | fact |
| 5 | 41.1491 | v7u_N003651 | SAR最重要的目的是协助执法和分析人员收集潜在非法活动的信息和情报 | definition |

---

## v7_q_000020 | CH05 | single | tier=clean
**中文题干**: 金融行动特别工作组(FATF)定期发布一份需要加强监测的司法管辖区目录,该目录通常被称为:
**中文选项**: A: 红色通缉令 B: 白名单 C: 黄色通报 D: 灰名单
**英文题干**: TheFinancialActionTaskForce(FATF)routi nelypublishesacatalogueofjurisdictionsrequir ingEnhancedmonitoringwhichiscommonlycal led the: rednotice
**英文选项**: A: whitelist B: yellownotice grey list

### BGE 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 0.7682 | v7u_N001429 | FATF黑名单指反洗钱/反恐怖融资缺陷严重，需采取强化尽职调查和反制措施的司法管 | definition |
| 2 | 0.7557 | v7u_N001428 | FATF灰名单指在反洗钱/反恐怖融资体系存在战略缺陷但正积极整改的司法管辖区 | definition |
| 3 | 0.7388 | v7u_N001431 | 评估表现不佳的司法管辖区可能被列入FATF灰名单或黑名单 | risk_indicator |
| 4 | 0.7342 | v7u_N003459 | 金融行动特别工作组建议20要求金融机构在有合理理由怀疑资金来自犯罪活动或与恐怖融 | rule |
| 5 | 0.7217 | v7u_N001310 | FATF将未达标辖区列入灰名单或黑名单，可能导致金融孤立 | risk_indicator |

### 中文 BM25 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 108.1539 | v7u_N001952 | 阿联酋使其监管方法与金融行动特别工作组要求保持一致，包括其建议，以加强监督、风险 | fact |
| 2 | 88.8582 | v7u_N003459 | 金融行动特别工作组建议20要求金融机构在有合理理由怀疑资金来自犯罪活动或与恐怖融 | rule |
| 3 | 85.2939 | v7u_N001878 | 修正案旨在使澳大利亚法律符合FATF国际标准 | fact |
| 4 | 73.1223 | v7u_N001381 | FATF建议要求当局通过信息交换和联合调查促进国际合作以打击金融犯罪。 | rule |
| 5 | 66.6666 | v7u_N001431 | 评估表现不佳的司法管辖区可能被列入FATF灰名单或黑名单 | risk_indicator |

### 英文 BM25 检索 (top-5)
| rank | score | unit_id | knowledge_zh | type |
|------|-------|---------|-------------|------|
| 1 | 21.6140 | v7u_N001431 | 评估表现不佳的司法管辖区可能被列入FATF灰名单或黑名单 | risk_indicator |
| 2 | 19.8062 | v7u_N001428 | FATF灰名单指在反洗钱/反恐怖融资体系存在战略缺陷但正积极整改的司法管辖区 | definition |
| 3 | 18.4621 | v7u_N001441 | FATF 互评估报告对司法管辖区的影响示例：阿联酋从灰名单移除 | classification |
| 4 | 17.0425 | v7u_N001310 | FATF将未达标辖区列入灰名单或黑名单，可能导致金融孤立 | risk_indicator |
| 5 | 16.9399 | v7u_N004256 | 金融机构维护内部列表（私人列表或灰名单），包含可能带来金融犯罪风险的个人和实体 | definition |

---
