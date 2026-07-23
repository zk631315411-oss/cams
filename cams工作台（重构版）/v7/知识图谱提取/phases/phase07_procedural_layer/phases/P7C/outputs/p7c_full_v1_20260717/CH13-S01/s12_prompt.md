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

## S1.1 候选列表

```json
[]
```
