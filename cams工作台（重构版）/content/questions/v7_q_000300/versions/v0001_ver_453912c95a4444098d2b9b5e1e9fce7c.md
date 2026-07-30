# v7_q_000300

教材章节：未映射

题型：multiple

题干：在虚拟货币点对点交易中，哪些客户行为是危险信号？(选择两项。)

英文题干：Which customer actions are red flags for virtual currency peer-to-peer transactions? (Choose two.)

选项：

- A. 一位客户从一个流行的去中心化混币器那里收到了资金
  English: A customer receives funds from a popular decentralized mixer.
- B. 一位顾客用其每月收入中的资金购买虚拟货币
  English: A customer uses funds from their monthly income to purchase virtual currency.
- C. 一位客户在区块链上进行了一笔交易，而其传统金融机构对此并不知情
  English: A customer makes a transaction on the blockchain that their traditional financial institution is unaware of.
- D. 一位客户从不同来源收到多笔电汇，并使用这些资金购买虚拟货币
  English: A customer receives multiple wires from different sources and uses those funds to purchase virtual currency.

## 【AI答案】

A、D

## 【考点】

识别虚拟货币点对点交易中与资金来源相关的洗钱危险信号

## 【核心解析】

在反洗钱框架下，危险信号的核心在于交易是否涉及刻意掩盖资金来源或使用来源不明的资金。选项A中，去中心化混币器通过混淆技术混合不同实体资金，使追踪变得极其困难甚至不可能；犯罪分子和受制裁实体也会使用此类服务清洗非法资金，因此VASP应将与混币器相关的交易视为高风险（P114-P115）。客户从混币器接收资金，构成典型的洗钱危险信号。选项D中，多笔来自不同来源的电汇随后被用于购买虚拟货币，资金来源分散且关系不明，与教材所列「来源不明或可疑资金」及「加密资产购买资金与已知财富或资金来源不符」等风险特征相符（P111-P112）。由此，A和D比B、C更直接地指向高风险行为。

教材原句："virtual asset service providers should treat transactions linked to mixers and tumblers as high risk and take appropriate diligence measures to reduce potential risk."（P115）

## 【错误项分析】

- **B 错误（缺少异常要素）**：题干只说明资金来自每月收入，未给出收入与已知财富明显不匹配、来源可疑或其他异常事实；仅凭“用月收入购买虚拟货币”不足以认定为红旗。
- **C 错误（技术常态不等于红旗）**：教材说明区块链账本的去中心化特性消除了单一中心账本并支持点对点交易（P38）。因此，传统金融机构不知情这一事实单独并不构成红旗；相较之下，A的混币器关联和D的可疑资金来源更直接体现风险。

## 【易错提醒】

不要将区块链的「去中心化」特性本身误认为危险信号。去中心化是技术设计，点对点交易无需中介方知情是正常现象（P38）。真正的危险信号在于资金是否经过混币器等特意设计的匿名化工具来掩盖来源（P114-P115），而非区块链本身的匿名性。

## 【教材原文依据】

> 核心引用单元：`v7u_N001040`

### `v7u_N001034`

- 用于：核心解析、易错提醒
- 章节：Money laundering risks associated with cryptoassets and other FinTechs > Mixers and tumblers
- 页码：PDF第119页 / 书内第114页
- 中文要点：去中心化混合器使用协议以完全协调或点对点方式混淆交易。
- 英文原文：Decentralized mixers use a protocol to obfuscate transactions using a fully coordinated or peer-topeer method.

### `v7u_N001038`

- 用于：核心解析
- 章节：未标注
- 页码：PDF第120页 / 书内第115页
- 中文要点：犯罪分子和受制裁实体广泛使用混合器和翻滚器清洗非法资金。
- 英文原文：Criminals have widely used mixers and tumblers to launder illicitly acquired funds. Various sanctioned entities and users of dark web marketplaces use these mixing and tumbling services in their money laundering process to hide the trail between the illegal funding source and the destination.

### `v7u_N001040`

- 用于：核心解析
- 章节：Money laundering risks associated with cryptoassets and other FinTechs > Mixers and tumblers
- 页码：PDF第120页 / 书内第115页
- 中文要点：加密资产服务提供商应将与混合器相关的交易视为高风险，并采取适当尽职调查措施。
- 英文原文：However, virtual asset service providers should treat transactions linked to mixers and tumblers as high risk and take appropriate diligence measures to reduce potential risk.

### `v7u_N000997`

- 用于：选项C、易错提醒
- 章节：Money laundering risks associated with cryptoassets and other FinTechs > Cryptoassets industry ecosystem
- 页码：PDF第116页 / 书内第111页
- 中文要点：账本网络的去中心化消除了单一中心账本，实现快速点对点交易。
- 英文原文：The decentralized nature of these ledger networks eliminates the need for one centralized ledger, allowing for fast, peer-to-peer transactions.

### `v7u_N001140`

- 用于：核心解析、选项D
- 章节：High-risk business sectors
- 页码：PDF第133页 / 书内第128页
- 中文要点：涉及来源不明或可疑资金的交易是洗钱红旗信号
- 英文原文：Transactions which involve funds from unknown or suspicious sources

### `v7u_N001005`

- 用于：核心解析、选项D
- 章节：Money laundering risks associated with cryptoassets and other FinTechs > Cryptoassets industry ecosystem
- 页码：PDF第117页 / 书内第112页
- 中文要点：购买加密资产的资金远超已知财富或资金来源是洗钱红旗信号
- 英文原文：A customer who purchases cryptoassets with funds that significantly exceed their known wealth or source of funds.

### `v7u_N000266`

- 用于：核心解析、选项D（组合推理参照）
- 章节：Examples of predicate crimes > How terrorists move and store funds
- 页码：PDF第43页 / 书内第38页
- 中文要点：大量看似无关的加密货币存款随后快速兑换并提取是潜在红旗信号
- 英文原文：A potential red flag could be numerous, seemingly unrelated deposits of cryptocurrency. Afterward, the deposits are quickly converted to stablecoins, or into fiat currency and withdrawn through a virtual asset service provider and/or in a jurisdiction with poor AFC controls.

## 【参考答案与参考解析】

- 题库最终参考答案：A、D
- 中文参考答案：A、D

### 中文参考解析

在虚拟货币点对点交易中，A 直接涉及去中心化混币器，混币会削弱资金可追踪性，是典型红旗。D 同时出现多笔、不同来源的电汇，并将资金用于购买虚拟货币，结合了来源不明或可疑资金与异常加密资产购买两个风险信号。B 仅说明资金来自月收入，题干没有给出与财富不匹配或来源异常的事实；C 只是区块链交易及传统金融机构未知这一技术场景，题干未给出其他异常因素。因此答案为 A、D。

- 英文参考答案：A、D

### 英文参考解析

Option A involves receiving funds from a decentralized mixer, which can obscure the source and transaction trail. Option D combines multiple wires from different sources with a subsequent virtual-currency purchase, indicating potentially unknown or suspicious funds. B and C do not contain an additional suspicious fact on the stated record. Therefore, the answer is A and D.

### 答案冲突提示

- 未发现答案冲突。
