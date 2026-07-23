# P7C-S1.1 候选 Card Frame 主发现 v1

## 阶段角色

你是 **P7C-S1.1：候选 card frame 主发现器**。

阅读一个 section，找出所有有证据支持的局部程序、判断、法律适用或归因单元，这些单元后续可能成为 P7 card。在定义的候选框架内优先保证召回，而不是抽取每一个教材事实。

你的输出将先传给独立的 S1.2 补漏器进行只增不删的遗漏检查；合并后的候选再传给 S2 做 **KG 边界裁决**，最后由 S3 做正式语义构图。你不依赖 S1.2 替你完成扫描，仍须独立覆盖完整 section。

你必须遵守以下限制：

- 不判断基础 KG 是否已经能表达该候选；
- 不创建 `flow_nodes`、`flow_edges`、`node_type`、`edge_type`、`relation_type`、`derivation` 或审核状态；
- 不读取题目、选项、答案、其他 section 或外部知识。

## 候选 Card Frame 定义

候选 card frame 是一个 section 内、有证据支撑的局部程序或判断单元。它围绕一个核心处理、判断、法律适用或归因来组织，当原文提供时，将关联的触发/背景、依据/条件、结果、分支或后续动作整合在一起。

其概念形态为：

```text
触发 / 背景 / 输入 / 标准 / 条件
                    →
核心处理 / 判断 / 法律适用 / 归因
                    →
结果 / 分支 / 后续动作
```

核心处理或判断为必选项。触发/背景、依据/条件或结果/路径中至少还需要一项。当原文仅给出条件或标准导向具体处理或判断时，允许输出原文支撑的开放式框架；不得为了闭合框架而虚构出口。

这里的"有向"不表示时间顺序或因果关系。它可以是条件、判断所依据的标准、处理所参照的输入、结果、法律适用链、分支或反馈关系。保留原文措辞和情态；不要仅仅因为 because 出现在动作之前就把它改写成触发。

## 发现流程

输出 JSON 之前，在内部完成以下两步。不要输出排查清单或任何解释。

1. 按段落、主体、案例事实、调查或审查动作、法律规则、条件、结果、例外和对象变化，扫描整个 section。内部识别每一个有证据支持的候选 frame。前一个候选不成为跳过后文段落或同一规则在另一案例中不同适用场景的理由。
2. 将识别到的材料围绕其核心处理或判断进行分组，然后输出每一个有效的候选 frame。对每一段可能合资格的原文，内部判断是候选还是纯定义/分类/孤立阈值/普通事实/一般机制。不要在发现第一个有效候选之后就停止扫描。

## 纳入与分组规则

- 一个候选对应一个局部业务问题或判断单元。将围绕同一核心处理或判断的所有原文支撑角色放在一起，不对每个细小关系分别输出候选。
- 当候选具有不同核心处理/判断、不同业务目标或无可证实原文连接时，分开建候选。
- 仅当原文包含连接词或互相引用，或它们共享同一核心处理与对象且可直接连读为一条规则、案例或判断链时，才合并多个 unit。仅凭相邻并不充分。
- 当输入、计算、适用标准和正/反结果都服务于同一判断时，放在同一个 frame 中。例如直接和间接持股加上适用阈值应归属于 UBO 判断。设定风险为本阈值与将已设定阈值用于判断特定 UBO 是不同的核心判断，可以是独立的 frame。
- 风险为本规则加上高风险阈值例外是一个关于"设定或调整适用阈值"的候选。保留 `might`、`could` 和例外阈值数值；不要将其降级为孤立阈值事实或"机构采用风险为本方法"的一般陈述。
- 将 `if`、`when`、`unless`、`must`、`should`、`may`、`might`、`could`、`only`、`not`、`potentially` 和 `typically` 等明示情态和限定词保留在整合后的 proposition 和相关 frame 字段中。
- 具体的机构动作、评估、决策、应对、法律适用或归因可以是核心字段。有名有姓的主体有用但对于法律适用或归因链并非强制。
- 案例中实际发生的制度响应应被记录。具名主体的调查、审查、审计、筛查、分析、跟进或升级，只要产生了发现、结论、分类或后续动作，就是候选 frame——即使以过去时态叙述也同样处理。
- 当案例事实、当事方关系、指控或地点引发法律适用、管辖权、责任或监管关切时，输出该案例特有的适用性 frame。后续仅包含一般规则的候选不能替代前述案例特有 frame。
- 不要将没有核心处理、判断、法律适用或归因的犯罪手法、一般机制或普通案例事实变成候选 frame。

不输出纯定义、分类、孤立阈值、产品列表、控制列表、普通案例事实、普通风险指标或一般机制。例如：

```text
"UBO 是指……的自然人。"                              → 不构成候选
"大多数司法管辖区使用 25% 的阈值。"                    → 不构成候选
"该公司使用了空壳公司。"                              → 不构成候选
"贿赂可能导致洗钱。"                                 → 不构成候选
```

这些内容，并不因为它们包含了一个关系或一个数值，就属于候选 card frame。S2 在 S1 发现有效候选 frame 之后，才判断 KG 是否已经充分。

## 跨 Unit 归纳

`induction="cross_unit"` 仅用于完整的跨 unit 分支：section 提供了通用规则或判断标准，以及在该同一标准下由原文支持的正例和反例。候选必须引用全部三组。

不要从孤立实例或相邻事实推广出分支。此时应保持独立的原文支撑候选 frame（如有）。

## 证据规则

`section_text_with_unit_anchors` 是唯一事实来源。Unit ID 出现在原文中的方括号内，例如 `[v7u_N000496|496]`。

- 只引用这些锚点中可见的 ID。
- 每个引用的 unit 必须有且仅有一条 `evidence_spans` 条目，其中包含该 unit 中一段精确、连续的短引述。精确引述中不使用省略号。
- 逐字复制 `evidence_spans.quote` 中的内容。不要在引述内部将代词还原为具名主体、修复语法、翻译或改写；主体名称和简明释义应分别放在 `proposition` 或 `candidate_frame` 中。
- `source_quotes` 为下游兼容而保留。每一项必须与 `evidence_spans` 中的某一条引述字符串完全相同；不要把自由概括当作引述。
- proposition 和 frame 字段可以使用简明中文或英文描述，但必须保留原文含义、已列明的主体以及情态。

## 示例

### 1. 完整处理到结果链

```text
[v7u_N000801|801] When a transaction is flagged, the institution must review it and file a report when suspicion remains.
```

```json
{
  "candidate_id": "s1c_001",
  "unit_ids": ["v7u_N000801"],
  "proposition": "当交易被标记时，机构必须审查；如仍有怀疑，则提交报告。",
  "source_quotes": ["When a transaction is flagged, the institution must review it and file a report when suspicion remains."],
  "relation_cues": ["when", "must"],
  "candidate_frame": {
    "trigger_or_context": ["交易被标记"],
    "basis_or_condition": ["如仍有怀疑"],
    "focal_handling_or_judgment": "机构审查交易",
    "outcomes_or_paths": ["仍有怀疑时提交报告"]
  },
  "evidence_spans": [
    {"unit_id": "v7u_N000801", "quote": "When a transaction is flagged, the institution must review it and file a report when suspicion remains."}
  ],
  "induction": null,
  "cross_unit_basis": null
}
```

### 2. 开放条件到处理 frame

```text
[v7u_N000496|496] where there is no natural beneficial owner, a controller or a notional beneficial owner should be identified and verified.
```

```json
{
  "candidate_id": "s1c_001",
  "unit_ids": ["v7u_N000496"],
  "proposition": "当不存在自然人受益所有人时，应识别并核实控制人或名义受益所有人。",
  "source_quotes": ["where there is no natural beneficial owner, a controller or a notional beneficial owner should be identified and verified."],
  "relation_cues": ["where", "should"],
  "candidate_frame": {
    "trigger_or_context": ["不存在自然人受益所有人"],
    "basis_or_condition": [],
    "focal_handling_or_judgment": "识别并核实控制人或名义受益所有人",
    "outcomes_or_paths": []
  },
  "evidence_spans": [
    {"unit_id": "v7u_N000496", "quote": "where there is no natural beneficial owner, a controller or a notional beneficial owner should be identified and verified."}
  ],
  "induction": null,
  "cross_unit_basis": null
}
```

### 3. 无名主体的法律适用 frame

```text
[v7u_N000136|136] It applies to any company with a UK connection.
```

```json
{
  "candidate_id": "s1c_002",
  "unit_ids": ["v7u_N000136"],
  "proposition": "具有英国关联的公司适用该法律。",
  "source_quotes": ["It applies to any company with a UK connection"],
  "relation_cues": ["applies to"],
  "candidate_frame": {
    "trigger_or_context": ["公司具有英国关联"],
    "basis_or_condition": [],
    "focal_handling_or_judgment": "法律适用于该公司",
    "outcomes_or_paths": []
  },
  "evidence_spans": [
    {"unit_id": "v7u_N000136", "quote": "It applies to any company with a UK connection"}
  ],
  "induction": null,
  "cross_unit_basis": null
}
```

### 4. 案例特有的法律适用 frame

```text
[v7u_N000900|900] Company A is incorporated in Country A and is a subsidiary of a Country B parent.
[v7u_N000901|901] Allegations of overseas bribery raised concerns under Country B's extraterritorial anti-bribery provisions.
```

即使后续 unit 单独陈述了国家 B 法律的一般适用范围，这仍然是一个候选。引发适用关切的具体事实与一般规则不能互相替代。

```json
{
  "candidate_id": "s1c_004",
  "unit_ids": ["v7u_N000900", "v7u_N000901"],
  "proposition": "公司A的主体关系和海外贿赂指控引发对国家B反贿赂法域外适用的关切。",
  "source_quotes": ["Company A is incorporated in Country A and is a subsidiary of a Country B parent.", "Allegations of overseas bribery raised concerns under Country B's extraterritorial anti-bribery provisions."],
  "relation_cues": ["subsidiary", "raised concerns", "extraterritorial"],
  "candidate_frame": {
    "trigger_or_context": ["公司A是国家B母公司的境外子公司，并面临海外贿赂指控"],
    "basis_or_condition": ["国家B反贿赂法的域外条款"],
    "focal_handling_or_judgment": "引发对该法域外适用的法律关切",
    "outcomes_or_paths": []
  },
  "evidence_spans": [
    {"unit_id": "v7u_N000900", "quote": "Company A is incorporated in Country A and is a subsidiary of a Country B parent."},
    {"unit_id": "v7u_N000901", "quote": "Allegations of overseas bribery raised concerns under Country B's extraterritorial anti-bribery provisions."}
  ],
  "induction": null,
  "cross_unit_basis": null
}
```

### 5. 案例调查到发现 frame

```text
[v7u_N000902|902] The analyst's initial investigation revealed that the customer had engaged intermediaries in high-risk jurisdictions.
```

这是一个候选：分析师调查是核心动作，中间人安排是其发现。相比之下，单独一句 `The customer engaged intermediaries in high-risk jurisdictions.` 是普通案例事实，不是候选 frame。

### 6. 跨 unit 判断分支

```text
[v7u_N000489|489] ... identified at a threshold of 25% or more.
[v7u_N000493|493] ... identify indirect ownership stakes in addition to direct ownership.
[v7u_N000494|494] Individual D is then considered a UBO with 82% shareholding.
[v7u_N000495|495] Individual C ... is not a UBO.
```

仅当共用阈值以及正、反结果全部被引用时，才能作为一个候选：

```json
{
  "candidate_id": "s1c_005",
  "unit_ids": ["v7u_N000489", "v7u_N000493", "v7u_N000494", "v7u_N000495"],
  "proposition": "合计直接和间接持股达到适用阈值时认定为UBO，未达到时不认定为UBO。",
  "source_quotes": ["identified at a threshold of 25% or more", "identify indirect ownership stakes in addition to direct ownership", "considered a UBO with 82% shareholding", "is not a UBO"],
  "relation_cues": ["threshold", "direct", "indirect", "considered", "not"],
  "candidate_frame": {
    "trigger_or_context": ["需要判断持股是否达到适用阈值"],
    "basis_or_condition": ["受益所有权识别阈值"],
    "focal_handling_or_judgment": "合计直接和间接持股，并根据阈值判断是否认定为UBO",
    "outcomes_or_paths": ["达到阈值：认定为UBO", "未达到阈值：不认定为UBO"]
  },
  "evidence_spans": [
    {"unit_id": "v7u_N000489", "quote": "identified at a threshold of 25% or more"},
    {"unit_id": "v7u_N000493", "quote": "identify indirect ownership stakes in addition to direct ownership"},
    {"unit_id": "v7u_N000494", "quote": "considered a UBO with 82% shareholding"},
    {"unit_id": "v7u_N000495", "quote": "is not a UBO"}
  ],
  "induction": "cross_unit",
  "cross_unit_basis": {
    "rule_unit_ids": ["v7u_N000489"],
    "positive_example_unit_ids": ["v7u_N000494"],
    "negative_example_unit_ids": ["v7u_N000495"]
  }
}
```

### 7. 风险为本阈值例外 frame

```text
[v7u_N000910|910] The organisation sets the appropriate ownership threshold using a risk-based approach.
[v7u_N000911|911] For high-risk customers, the threshold might be 10% and could be 5% for significantly higher-risk customers.
```

这是一个关于"设定适用阈值"的候选。它与后续将特定客户的直接和间接持股与该阈值进行比较的判断是不同 frame。

### 8. `because` 是线索，不是自动触发

```text
because of adverse news, the institution reviews the customer relationship
```

如果原文支持该审查，这可以是一个候选 frame。在 `relation_cues` 和依据字段中保留 `because`。例如使用 `basis_or_condition: ["because of adverse news"]`，而不是 `trigger_or_context`——除非原文本身陈述了触发顺序。

## 输出 Contract

只输出严格 JSON。顶层字段为 `section_id`、`section_title`、`propositions` 和 `skip_reason`。

每个 proposition 必填：

```text
candidate_id
unit_ids
proposition
source_quotes
relation_cues
candidate_frame
evidence_spans
induction
cross_unit_basis
```

`candidate_frame` 始终包含：

```text
trigger_or_context
basis_or_condition
focal_handling_or_judgment
outcomes_or_paths
```

非跨 unit 候选时 `induction` 和 `cross_unit_basis` 设为 `null`。没有任何有效候选 frame 时，输出空 `propositions` 数组和中文 `skip_reason`。

## 当前section

section_id: `CH13-S01`

section_title: `Money laundering risks associated with cryptoassets and other FinTechs > Cryptoassets industry ecosystem`

section_text_with_unit_anchors:

```text
[v7u_N000955|955] The cryptoassets industry ecosystem is a dynamic and interconnected network that facilitates the creation, exchange, and management of digital assets. The industry continues to evolve, and as technology advances, new participants and services emerge, broadening the scope of the ecosystem.
ZH: 加密资产生态系统是动态互联的网络，促进数字资产的创建、交换和管理。

[v7u_N000956|956] The key structures within the ecosystem include:
ZH: 生态系统内的关键结构包括区块链、DeFi、矿工和VASP。

[v7u_N000957|957] Blockchains: Blockchains are a form of "distributed ledger technology" (DLT). They provide the infrastructure for the development and deployment of decentralized applications and smart contracts.
ZH: 区块链是区块链技术，为去中心化应用和智能合约提供基础设施。

[v7u_N000958|958] Decentralized Finance or DeFi: DeFi refers to a collection of financial services that operate on smart contract protocols. These protocols aim to replicate traditional financial systems, such as lending, borrowing, and exchanges, without intermediaries.
ZH: DeFi指基于智能合约协议的金融服务集合，旨在无中介复制传统金融系统。

[v7u_N000959|959] Miners: Validate transactions on blockchain networks by solving complex mathematical problems, a process called mining. In return, miners earn newly created cryptoassets for mining a block.
ZH: 矿工通过解决复杂数学问题验证区块链交易，并获得新创建的加密资产作为奖励。

[v7u_N000960|960] VASPs: VASPs include cryptocurrency exchanges, wallet providers, and other entities. They facilitate activities involving virtual assets, such as transactions with cryptocurrency, and are subject to strict regulations in many jurisdictions.
ZH: VASP包括加密货币交易所、钱包提供商等，受严格监管。

[v7u_N000961|961] Wallet providers: Digital wallets allow users to store, send, and receive cryptoassets. They come in two forms: hot wallets, which are connected to the internet for easy access, and cold wallets, which are offline and provide enhanced security.
ZH: 钱包提供商分为热钱包和冷钱包，分别提供便捷访问和增强安全性。

[v7u_N000962|962] Cryptocurrency exchanges: Facilitate the buying, selling, and trading of cryptoassets. These platforms can either be centralized or decentralized.
ZH: 加密货币交易所促进加密资产的买卖和交易，可分为中心化和去中心化。

[v7u_N000963|963] Access and infrastructure providers, such as cryptocurrency ATMs: Allow users to exchange cryptocurrencies for fiat currency (and vice versa) at physical locations. These machines can be used for facilitating peer-topeer crypto transactions.
ZH: 加密货币ATM等接入和基础设施提供商允许用户在物理位置兑换加密货币与法定货币。

[v7u_N000964|964] While these form the operational backbone of the cryptoassets ecosystem, their roles revolve around a diverse set of digital assets—each with distinct characteristics and functions. The main categories are:
ZH: 加密资产生态系统的运营支柱围绕多种数字资产，主要类别如下。

[v7u_N000965|965] Cryptocurrencies: Primarily used for transactions and value storage. Examples include Bitcoin, Ethereum, and Solona.
ZH: 加密货币主要用于交易和价值存储，例如比特币、以太坊和Solana。

[v7u_N000966|966] Stablecoins: Digital currencies that are pegged to traditional assets, such as the US Dollar, to reduce volatility. This stability facilitates the connection between cryptoassets and traditional currencies, enabling cross-border payments. Examples include Tether (USDT) and Circle (USDC).
ZH: 稳定币是与传统资产挂钩的数字货币，用于减少波动性并促进跨境支付。

[v7u_N000967|967] Tokens: Represent assets, rights, or access within a blockchain ecosystem and can be traded across borders, bypassing traditional financial systems. They might be swapped on decentralized platforms, obscuring the origin and destination of illicit funds.
ZH: 代币代表区块链生态系统中的资产、权利或访问权限，可跨境交易，可能模糊非法资金来源。

[v7u_N000968|968] Non-Fungible Tokens or NFTs: Represent unique digital assets, often used to demonstrate ownership of digital art and collectibles. Their uniqueness can make it difficult to accurately assess their true market value. Money laundering risks include overpricing and anonymity in selling NFTs using illicit funds, particularly on decentralized platforms.
ZH: NFT代表独特数字资产，用于数字艺术和收藏品所有权，存在洗钱风险如定价过高和匿名销售。

[v7u_N000969|969] The supporting elements of the ecosystem include:
ZH: 生态系统的支持要素包括以下内容。

[v7u_N000970|970] Regulatory bodies: Regulators monitor the legal and compliance aspects of cryptoassets to deter illegal activities, such as fraud and money laundering.
ZH: 监管机构监控加密资产的法律和合规方面，以阻止欺诈和洗钱等非法活动。

[v7u_N000971|971] DeFi: DeFi refers to a collection of financial services that operate on smart contract protocols. These protocols aim to replicate traditional financial systems, such as lending, borrowing, and exchanges, without intermediaries.
ZH: DeFi指基于智能合约协议的金融服务，旨在无需中介复制传统金融系统。

[v7u_N000972|972] A blockchain is a decentralized, distributed public ledger. It is a database that uses encryption to store blocks of data and chains them together chronologically. It serves as the single source of this data and is immutable, or very difficult to alter.
ZH: 区块链是去中心化、分布式的公共账本，使用加密技术按时间顺序存储数据块。

[v7u_N000973|973] This shared, immutable ledger allows the recording of transactions and tracking of assets in a business network.
ZH: 共享的不可变账本允许在业务网络中记录交易和跟踪资产。

[v7u_N000974|974] Assets traded on a blockchain network can be tangible assets, such as machinery or land, or intangible assets, such as patents or bonds.
ZH: 区块链网络上的资产可以是机器、土地等有形资产，或专利、债券等无形资产。

[v7u_N000975|975] There are many characteristics of blockchain technology that provide benefits for users.
ZH: 区块链技术的许多特性为用户带来益处。

[v7u_N000976|976] A blockchain always consists of nodes, miners, and blocks.
ZH: 区块链由节点、矿工和区块组成。

[v7u_N000977|977] Nodes are computers used to access blockchain networks.
ZH: 节点是用于访问区块链网络的计算机。

[v7u_N000978|978] Miners are users who verify transactions and add new blocks to the blockchain.
ZH: 矿工是验证交易并向区块链添加新区块的用户。

[v7u_N000979|979] Blocks are structures of transaction data for cryptocurrency transactions.
ZH: 区块是加密货币交易数据的结构。

[v7u_N000980|980] Every chain of data consists of multiple data-filled blocks.
ZH: 每条数据链由多个充满数据的区块组成。

[v7u_N000981|981] The data in the block is sealed forever and is attached to a random number called a “nonce” and is the result of a cryptographic function called a “hash.”
ZH: 区块链数据通过随机数（nonce）和哈希函数（hash）密封，确保不可篡改。

[v7u_N000982|982] In a blockchain, each block has a unique nonce and hash, which makes it extremely difficult to manipulate the blockchain.
ZH: 区块链中每个区块拥有唯一的nonce和hash，防止篡改。

[v7u_N000983|983] To make a change, the entire block would need to be re-mined along with any other blocks in its chain. This would require an enormous amount of time and computing power.
ZH: 修改区块链数据需要重新挖掘整个区块及其后续区块，耗费大量时间和算力。

[v7u_N000984|984] Once a blockchain is mined, it also must be verified by other nodes on the network.
ZH: 区块链挖掘后需经网络其他节点验证。

[v7u_N000985|985] Blockchain technology offers many benefits.
ZH: 区块链技术提供诸多优势。

[v7u_N000986|986] Blockchains are immutable, which means they are permanent and cannot be altered.
ZH: 区块链具有不可篡改性，数据永久且无法更改。

[v7u_N000987|987] They also offer transparency, as all users can access a copy of the ledger.
ZH: 区块链提供透明性，所有用户可访问账本副本。

[v7u_N000988|988] Blockchains are usually decentralized, meaning that no central governing authority has decision-making power over them.
ZH: 区块链通常去中心化，无中央管理机构。

[v7u_N000989|989] They are also secure because they consist of individually encrypted records.
ZH: 区块链因独立加密记录而安全。

[v7u_N000990|990] Additionally, blockchain offers faster settlements than traditional banking system transactions.
ZH: 区块链比传统银行系统结算更快。

[v7u_N000991|991] Cryptoassets encompass virtual currencies, such as Bitcoin, and stablecoins, such as Tether (USDT) and USD Coin (USDC).
ZH: 加密资产包括虚拟货币（如比特币）和稳定币（如USDT、USDC）。

[v7u_N000992|992] Stablecoins are designed to minimize price volatility by pegging their value to traditional assets, such as fiat currencies.
ZH: 稳定币通过锚定传统资产（如法币）来最小化价格波动。

[v7u_N000993|993] In contrast, cryptoassets, such as Bitcoin and Ethereum, experience significant price fluctuations, making them more suitable for investment and speculative purposes rather than as stable mediums of exchange.
ZH: 比特币和以太坊等加密资产价格波动大，更适合投资和投机。

[v7u_N000994|994] Cryptoassets usually require third-party providers, known as VASPs, to assist in exchanging for fiat currency.
ZH: 加密资产通常需要VASP等第三方提供商协助兑换法币。

[v7u_N000995|995] Without proper controls, the conversion point between cryptoassets and fiat is particularly vulnerable to money laundering, but CDD checks and monitoring can help identify suspicious activities.
ZH: 加密资产与法币的兑换点易被洗钱利用，客户尽职调查和监控可识别可疑活动。

[v7u_N000996|996] These assets operate on public ledgers, such as blockchains, which use cryptography to secure transaction data. Cryptography secures cryptoasset data via a distributed ledger, which publicly stores the data of the cryptoassets.
ZH: 加密资产在公共账本（如区块链）上运行，使用密码学保护交易数据。

[v7u_N000997|997] The decentralized nature of these ledger networks eliminates the need for one centralized ledger, allowing for fast, peer-to-peer transactions.
ZH: 账本网络的去中心化消除了单一中心账本，实现快速点对点交易。

[v7u_N000998|998] Permissionless oversight allows for fast, easy payments and provides a payment method to individuals without access to mainstream financial services.
ZH: 无许可监督可实现快速便捷支付，并为无银行账户者提供支付方式。

[v7u_N000999|999] However, it can also facilitate criminal activities, and cryptoassets can attract individuals looking to exploit the system.
ZH: 加密资产可能便利犯罪活动，吸引利用系统漏洞的个人。

[v7u_N001000|1000] For instance, despite the inherent transparency of blockchain technology, tracing ownership can be challenging, making it attractive to criminals looking to engage in illicit activities with minimal traceability. Some privacy coins utilize nonpublic blockchains to facilitate anonymous fund transfers, further complicating efforts to attribute transactions and heightening the risk of illicit activity.
ZH: 尽管区块链透明，但追踪所有权困难；隐私币利用非公开区块链匿名转账，增加洗钱风险。

[v7u_N001001|1001] Criminals might exploit cryptoassets to launder illicit funds. Examples of red flags include:
ZH: 列举犯罪分子利用加密资产洗钱的红旗信号信号示例

[v7u_N001002|1002] Transactions involving wallet addresses that are sanctioned or linked to illegal activity.
ZH: 涉及受制裁或非法活动的钱包地址的交易是洗钱红旗信号

[v7u_N001003|1003] Large purchases made within a 24-hour period, withdrawn as fiat currency through multiple small transactions.
ZH: 24小时内大额购买后通过多笔小额交易提取为法定货币是洗钱红旗信号

[v7u_N001004|1004] Repeated transfers to fiat currency exchanges in jurisdictions with weak regulatory enforcement.
ZH: 反复向监管薄弱地区的法定货币交易所转账是洗钱红旗信号

[v7u_N001005|1005] A customer who purchases cryptoassets with funds that significantly exceed their known wealth or source of funds.
ZH: 客户购买加密资产的资金远超其已知财富或资金来源是洗钱红旗信号
```
