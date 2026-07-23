<!-- allowed_unit_ids is intentionally not sent to the model. Unit IDs remain
     visible in section_text_with_unit_anchors and are validated by the Runner. -->

# P7C-S1.2 候选 Card Frame 独立补漏 v1

## 阶段角色

你是 **P7C-S1.2：候选 card frame 独立补漏器**。

S1.1 已经生成一组候选。你必须重新阅读完整 section，并将原文中所有可能合格的 frame 与 S1.1 候选逐项比较。只输出 S1.1 没有承接的候选；不得删除、改写或重复输出已有候选。

你不做 KG 边界裁决，不构建 flow node 或 flow edge，也不输出审核结论。你的输出与 S1.1 合并后才进入 S2。

## 候选 Card Frame 定义

候选 frame 是 section 内有原文证据支持的局部程序或判断单元。它围绕一个中心处理、判断、法律适用或归责组织；原文提供时，应同时纳入相关的触发/情境、输入/标准、依据/条件、结果、分支或后续行动。

```text
触发 / 情境 / 输入 / 标准 / 条件
                  -> 中心处理 / 判断 / 法律适用 / 归责
                  -> 结果 / 分支 / 后续行动
```

中心字段必有，且触发/依据/结果三类外围角色中至少有一类。上述概念图不要求三段齐全：原文仅支持“标准或条件 -> 具体处理/判断”，或“调查/审查动作 -> 发现/结论”时，允许开放候选，不得补造入口或出口。

这里的有向关系不等于时间顺序或因果关系，也可以是条件、判断标准、处理所参照的输入、法律适用、分支或反馈。必须保留原文中的 if、when、unless、may、might、could、should、must、only、not 等限定。

## 独立扫描与比对

在内部完成以下步骤，不输出扫描台账或推理过程：

1. 按自然段、主体变化、对象变化、案例事实、调查或审查动作、法律规则、条件、结果和例外扫描完整 section，先独立识别全部潜在 frame。
2. 围绕中心处理或判断组织 frame。前文已有候选不能成为停止扫描后文的理由。
3. 将每个独立识别的 frame 与全部 S1.1 候选比较。核心处理/判断及其关键证据已被同一候选覆盖时，视为已承接；只有主题相同但遗漏独立处置链、法律适用链或调查发现链时，仍视为缺口。
4. 只为未承接的 frame 输出 gap proposition。

## 必须识别的候选类型

- **同中心判断链**：同一对象的输入、计算、适用标准和正反结果应合并。例如，直接持股、间接持股、适用阈值与是否认定 UBO 属于同一判断 frame。
- **阈值设定与阈值适用**：风险为本地设定或调整阈值，与使用既有阈值判断具体对象，是不同中心，可以分别形成候选。
- **案例法律适用链**：案件事实、主体关系、地点或指控引发法律适用、管辖、责任或监管关切时，应输出“案例情境 -> 法律适用/归责判断 -> 原文结果（如有）”。通用法律规则不能替代案例中的实际适用候选。
- **调查发现链**：具名主体进行调查、审查、审计、筛查、分析或跟进并得出发现、结论、分类或升级时，应输出“调查/判断动作 -> 发现/结论”。
- **条件处置链**：if、when、unless、requires 等条件导向特定动作、禁止、批准、升级或结果时，应保留条件和情态。

## 不构成候选的内容

不输出纯定义、分类、产品列表、控制组成列表、孤立阈值、孤立红旗、普通案例事实或没有特定判断/应对的一般机制。

正例：

- `分析师初步调查 -> 发现高风险中间人安排`
- `案例主体关系和指控 -> 引发域外法律适用关切`
- `退出超出风险容忍度且仍有贷款余额的客户 -> 核销通常需要充分理由和批准`

反例：

- `公司使用中间人`
- `犯罪分子通过复杂网络洗钱`
- `受益所有权阈值通常为25%`

这些事实若没有原文中的机构动作、适用判断、条件化结果或特定应对，不单独形成候选。

## 合并边界

- 围绕同一中心处理/判断、同一对象且能由原文直接连读的材料合并为一个 frame。
- 不同中心处理/判断、不同业务目标或没有原文连接的材料分开。
- 只有相邻文本不足以跨 unit 合并；必须存在连接词、指代、共享中心判断或可验证的规则与正反例证据链。
- 不得仅换一种措辞重复 S1.1 候选。

## 证据合同

`section_text_with_unit_anchors`是唯一事实证据。只能引用锚点中可见的 unit ID。

- 每个`unit_id`必须由`evidence_spans`中的一项覆盖。
- 每个`evidence_spans.quote`必须是对应 unit 中精确、连续、可定位的原文短引。
- 每个`source_quotes`条目必须与某个`evidence_spans.quote`完全一致。
- `relation_cues`保留原文关系词；没有字面连接词时，填写能够体现原文关系的短语，不得留空。
- 只有跨 unit 归纳规则及其正反例时，`induction`填写`cross_unit`，并在`cross_unit_basis`中列出规则、正例和反例 unit；否则两者均为`null`。

## 输出 Contract

只输出严格 JSON。顶层字段为`section_id`和`gap_propositions`。

每个 gap proposition 必须保留 S1.1 的全部字段，并增加`gap_evidence`：

```json
{
  "section_id": "CH07-S03",
  "gap_propositions": [
    {
      "candidate_id": "s1c_gap_ch07_s03_writeoff_approval",
      "unit_ids": ["v7u_N000555"],
      "proposition": "退出超出银行风险容忍度且仍有贷款余额的客户关系时，核销贷款通常需要充分理由和批准。",
      "source_quotes": [
        "When exiting customer relationships that fall outside the bank's risk tolerance, the loan balance complicates the process, as writing off a loan is a significant financial decision, often requiring extensive justification and approval."
      ],
      "relation_cues": ["When", "requiring"],
      "candidate_frame": {
        "trigger_or_context": ["退出超出银行风险容忍度且仍有贷款余额的客户关系"],
        "basis_or_condition": ["核销是重大财务决策"],
        "focal_handling_or_judgment": "决定是否核销贷款余额并履行相应审批要求",
        "outcomes_or_paths": ["核销通常需要充分理由和批准"]
      },
      "evidence_spans": [
        {
          "unit_id": "v7u_N000555",
          "quote": "When exiting customer relationships that fall outside the bank's risk tolerance, the loan balance complicates the process, as writing off a loan is a significant financial decision, often requiring extensive justification and approval."
        }
      ],
      "induction": null,
      "cross_unit_basis": null,
      "gap_evidence": {
        "compared_with_candidate_ids": ["s1c_ch07_s03_illicit_repayment"],
        "gap_reason": "已有候选只承接怀疑非法资金还贷时不得接受资金，没有承接退出客户且仍有贷款余额时核销通常需要理由和批准这一独立处置链。"
      }
    }
  ]
}
```

`candidate_id`必须以`s1c_gap_`开头，且不得与 S1.1 ID 重复。

`gap_evidence.compared_with_candidate_ids`只能引用输入中的 S1.1 候选 ID；S1.1 列表非空时至少列出一个最相关候选。若 S1.1 为空，可以使用空数组。`gap_reason`必须用中文说明缺失的中心处理/判断及已有候选为何没有承接。

如果独立扫描后确认没有遗漏，输出：

```json
{"section_id":"<section_id>","gap_propositions":[]}
```

## 当前section

section_id: `CH04-S01`

section_title: `Consequences of financial crime > Consequences of financial crime`

section_text_with_unit_anchors:

```text
[v7u_N000290|290] Financial crime is a global problem that has dire consequences for nations.
ZH: 金融犯罪是全球性问题，对国家造成严重后果

[v7u_N000291|291] It weakens governments and economies. It lowers the standard of living for populations.
ZH: 金融犯罪削弱政府和经济，降低民众生活水平

[v7u_N000292|292] It especially hurts developing nations and emerging economies, who can least afford the financial losses these crimes cause.
ZH: 金融犯罪对发展中国家和新兴经济体影响尤为严重

[v7u_N000293|293] The worldwide proceeds of financial crime are estimated to be up to 5% of global gross domestic product, or US$2 trillion.
ZH: 全球金融犯罪收益估计高达全球GDP的5%，约2万亿美元

[v7u_N000294|294] Financial crime weakens nations by shifting control of finances and economic policy from governments to criminals.
ZH: 金融犯罪将财政和经济政策控制权从政府转移到犯罪分子手中，削弱国家

[v7u_N000295|295] It discourages foreign investment because nations where financial crime is widespread are unstable and present high risk to investors.
ZH: 金融犯罪盛行导致国家不稳定，阻碍外国投资

[v7u_N000296|296] Because criminals do not typically report the proceeds of crime as income, nations lose massive amounts of tax revenue.
ZH: 犯罪分子不申报犯罪收益，导致国家损失大量税收

[v7u_N000297|297] Financial crime damages the reputation of nations.
ZH: 金融犯罪损害国家声誉

[v7u_N000298|298] The loss of income to nations due to financial crime and the need to divert funds to fight it take funding away from vital social programs.
ZH: 金融犯罪导致国家收入损失并需转移资金打击犯罪，削减重要社会项目资金

[v7u_N000299|299] International agencies and donors are less likely to provide aid where financial crime is rampant.
ZH: 金融犯罪猖獗的国家较难获得国际机构和捐助者的援助

[v7u_N000300|300] As a result, social services, education, and health care programs may be unfunded or underfunded. This loss of funding contributes to poverty, lack of education, and poor health.
ZH: 资金不足导致社会服务、教育和医疗项目缺乏资金，加剧贫困、教育缺失和健康问题

[v7u_N000301|301] Financial crime hurts organizations, including financial institutions, in many ways.
ZH: 金融犯罪以多种方式损害包括金融机构在内的组织。

[v7u_N000302|302] It gives an unfair advantage to individuals and companies that engage in illegal activity.
ZH: 金融犯罪为从事非法活动的个人和公司提供不公平优势。

[v7u_N000303|303] It threatens the operations and reputation of organizations that become involved in it, whether intentionally or unintentionally.
ZH: 金融犯罪威胁涉事组织的运营和声誉，无论有意或无意。

[v7u_N000304|304] It can lead to loss of market share and even bankruptcy.
ZH: 金融犯罪可能导致市场份额损失甚至破产。

[v7u_N000305|305] Legitimate, law-abiding companies are at a disadvantage when competing against companies that are fronts for illegal activity and that evade paying taxes.
ZH: 守法公司在与非法活动掩护公司竞争时处于劣势。

[v7u_N000306|306] Financial institutions are hurt when criminals use them to conduct illicit financial activity.
ZH: 犯罪分子利用金融机构进行非法金融活动会损害金融机构。

[v7u_N000307|307] This activity destabilizes them and costs them money in terms of direct losses, regulatory fines, and legal and compliance costs.
ZH: 非法活动使金融机构不稳定并造成直接损失、监管罚款及合规成本。

[v7u_N000308|308] It also damages their reputation in the marketplace, leading to customer distrust and loss of business.
ZH: 金融犯罪损害市场声誉，导致客户不信任和业务流失。

[v7u_N000309|309] Financial crime has far-reaching social and economic consequences, undermining institutions, eroding public trust, and inflicting long-term economic harm.
ZH: 金融犯罪具有深远的社会和经济后果，破坏制度、侵蚀公众信任。

[v7u_N000310|310] Corruption and fraud erode confidence in governments and public bodies that have been entrusted with the mandate to improve services such as infrastructure and health care.
ZH: 腐败和欺诈侵蚀对政府和公共机构的信任。

[v7u_N000311|311] This can lead to reduced civic engagement and can discourage foreign investment.
ZH: 腐败和欺诈导致公民参与度降低并阻碍外国投资。

[v7u_N000312|312] Money laundering facilitates the financing of human trafficking, drug cartels, terrorism, and arms smuggling, which foster widespread criminality and societal disruption.
ZH: 洗钱助长人口贩运、贩毒、恐怖主义和武器走私等严重犯罪。

[v7u_N000313|313] In regions where anti-money laundering measures are weak, these risks are magnified, often resulting in higher crime rates, capital flight, and even civil unrest.
ZH: 反洗钱措施薄弱的地区风险加剧，导致犯罪率上升、资本外逃甚至内乱。

[v7u_N000314|314] Jurisdictions with lax AML enforcement often experience broad reputational damage that extends beyond individual companies.
ZH: 反洗钱执法松懈的司法管辖区常遭受超出单个公司的广泛声誉损害。

[v7u_N000315|315] Such regions can find themselves subject to international sanctions and trade restrictions, which discourage economic growth and job creation.
ZH: 此类地区可能面临国际制裁和贸易限制，阻碍经济增长和就业。

[v7u_N000316|316] Other countries might be reluctant to engage in business with countries with high levels of financial crime, which can isolate the affected country politically as well as economically.
ZH: 其他国家可能不愿与金融犯罪高发国家开展业务，导致政治和经济孤立。

[v7u_N000317|317] Lasting reputational damage can severely impact their ability to operate effectively in the global market.
ZH: 持久的声誉损害严重影响其在全球市场的有效运营能力。

[v7u_N000318|318] Financial crime can also disrupt businesses, leading to a loss of productivity. Companies might spend significant resources on compliance and legal issues, diverting attention from their core operations and limiting their ability to grow and innovate.
ZH: 金融犯罪扰乱业务，导致生产力下降，公司资源被合规和法律问题分散。

[v7u_N000319|319] Victims of financial scams, fraud, and identity theft frequently suffer severe personal setbacks. In addition to significant financial losses, victims might experience psychological distress, depression, and a profound loss of security.
ZH: 金融诈骗、欺诈和身份盗窃的受害者遭受严重个人挫折，包括财务损失和心理困扰。

[v7u_N000320|320] Elderly populations are disproportionately affected by financial scams, which can lead to financial ruin and social isolation due to a loss of money, trust, and stigmatization associated with being a victim.
ZH: 老年人受金融诈骗影响尤为严重，可能导致财务破产和社会孤立。
```

## S1.1 候选列表

```json
[]
```
