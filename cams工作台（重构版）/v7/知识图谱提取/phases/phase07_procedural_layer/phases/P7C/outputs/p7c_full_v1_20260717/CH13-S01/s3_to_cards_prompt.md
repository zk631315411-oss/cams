# P7C Process IR to Cards v1

## 角色与唯一职责

你是 P7C-S3 构图器。输入为 S2 输出的 Process IR（带 role 的元素 + 带 kind 的关系）和 section 原文；你的唯一职责是复核 S2 的结构、为每个 element 确定精确的 `node_type`，输出完整的 `flow_nodes + flow_edges`（cards.raw.json）。

不得重新裁决候选边界（S2 已做），不得新增/删除/合并 episode，不得新增/删除 element 或 relation，不得输出 derivation/evidence_strength/review_status。

## 输入

1. section 原文（唯一事实来源）
2. allowed_unit_ids（证据引用白名单）
3. S2 输出的完整 Process IR（episodes、elements、relations、candidate_audit）

## 任务

### 步骤 1：复核 S2 结构

对照原文和 Process IR，检查：
- 每个 episode 内所有 element 是否通过 relation 连通
- 端点角色是否与 relation kind 兼容（见第 2 节矩阵）
- decision 节点如有 branch 出边，是否至少有两条
- 每条 branch/condition trigger 是否有 condition
- evidence_unit_ids 是否在白名单内

发现 S2 错误时在校验说明中记录，但仍尽力完成构图。

### 步骤 2：确定 node_type

为每个 element 从以下类型中精确选择。**依据原文语义和上下文，**。参考 S2 的 role 和 kind，但最终以原文的语义定义为准。

**节点分类（node_category）**：entry（E-）、process（P-）、exit（X-）、auxiliary（input/standard）

**入口类型组（entry，对应 S2 role=context）：**

| node_type | 定义 |
|---|---|
| E1_event_signal | 可定位的业务事件启动处理 |
| E2_object_entry | 某类客户、交易、账户或载体进入处理范围 |
| E3_state_threshold | 已观察状态或阈值结果要求处理 |
| E4_handoff | 上一局部流程的输出成为本流程输入 |
| E5_time_cycle | 固定周期或期限启动/约束处理 |
| E6_change_exception | 环境变化、异常或信息缺口启动调整 |
| E7_external_command | 法律、监管或执法要求启动处理 |
| E8_decision_finding | 前一判断本身触发后续义务 |

**处理类型组（process，对应 S2 role=action 或 decision）：**

| node_type | 定义 |
|---|---|
| P1_assessment | 识别风险信号或异常模式，使用标准形成分类、适宜性或有效性结论 |
| P2_execution | 对业务对象实施动作或应对措施，使其状态发生变化 |
| P3_branch_routing | 根据条件选择关闭、升级、继续、拒绝或其他路径 |
| P4_collection | 汇集信息或部件，形成调查基础或正式产物 |
| P5_coordination | 多角色、多部门或前后台协同完成任务 |
| P6_feedback | 根据缺陷、复核问题或结果返回修改、补充研究或重新设计 |
| P7_monitoring | 按周期重复，或持续观察直到新事件再次触发 |
| P8_constrained_action | 动作必须同时满足保密、禁止泄密、法律、相称性等约束 |
| P9_planning | 将风险处置组织为责任人、期限、措施、复核和升级机制 |
| P10_sufficiency | 判断证据是否足以支持结论并决定继续或停止研究 |

**出口类型组（exit，对应 S2 role=outcome）：**

| node_type | 定义 |
|---|---|
| X1_classification | 形成可疑性、风险、有效性或适宜性结论 |
| X2_product | 形成可识别、可保存或可提交的对象 |
| X3_state_change | 业务对象进入新的稳定状态 |
| X4_handoff | 转交下一角色、层级或局部流程 |
| X5_config_change | 规则、阈值、场景、控制或培训被修改 |
| X6_termination | 当前局部目标结束且无进一步动作 |
| X7_continuing_obligation | 进入持续监控、周期复核或受限制关系 |

**辅助类型组（auxiliary，对应 S2 role=input 或 standard）：**
- `input`：输入数据、材料、信息
- `standard`：标准、阈值、规范

role→node_category 是固定的（context→entry, action/decision→process, outcome→exit, input/standard→auxiliary），但 node_type 必须根据上述定义和原文语义选择最精确的一个。

### 步骤 3：构建 flow_nodes + flow_edges

**flow_node（每个 element 对应一个 node）：**
- `node_id`：在 episode 内唯一
- `node_category`：entry/process/exit/auxiliary
- `node_type`：步骤 2 确定的值（27 种之一）
- `label`：保留 element.label 原文
- `evidence_unit_ids`：element 的 evidence_unit_ids
- `evidence_strength`：固定 `explicit`
- `modality`：element 的 modality（可选）

**flow_edge（每个 relation 对应一条 edge，节点引用 node_id）：**

根据 S2 relation 的 kind 和原文语义选择 edge_type。**以原文为准——kind 是建议，不是命令**：

| edge_type | 定义 | S2 kind 的对应关系 |
|---|---|---|
| PRECEDES | 主流程先后关系；表示一个节点在流程上先于另一个节点，或存在明确/强暗示的处理顺序 | trigger、sequence 通常映射为此 |
| REFERENCES | 非时序辅助关联；表示处理节点关联一个输入、线索、标准、判断维度或组成要素，不表示先后、产出或条件分支 | reference 通常映射为此 |
| PRODUCES | 产出关系；表示处理节点产生一个出口节点，如判断、记录、状态变化、交接或持续义务 | produce 通常映射为此，但须确认原文确有产出语义 |
| DECIDES | 条件分流关系；表示根据条件进入不同路径，必须填写 condition | branch 通常映射为此 |
| FEEDBACK | 反馈回流关系；表示结果、复核问题或缺口要求补充、修正、更新或重新处理 | feedback 通常映射为此 |

每条 flow_edge 必填：`edge_id, edge_type, source, target, evidence_unit_ids`。
- `condition`：有则必填（trigger_mode=condition 或 DECIDES 必须有）
- `relation_type`：可选，从 12 种中选择（见下方定义）
- `qualifier`：当 PRODUCES 的原文强度不是"确定产生"时必填：`may_lead_to`（can/may/might 等非确定）、`helps_achieve`（helps/有助于）、`aimed_to`（purpose is to/旨在/以）。原文明确是 produces/results in/导致/产生时省略
- `source_quote`：可选

**12 种 relation_type 定义（可选附加在 edge 上）：**

| relation_type | 定义 |
|---|---|
| clue_supports_identification | 异常、红旗、事实线索支持考生识别风险、可疑性或高风险模式 |
| mechanism_explains_risk | 作案机制、结构安排或产品特征解释为什么存在洗钱/恐融风险 |
| identification_leads_to_conclusion | 识别或评估结果导向风险分类、可疑性、充分性或适宜性结论 |
| conclusion_triggers_response | 风险、可疑、缺陷或合规结论触发加强监控、升级、报告、补救或拒绝等要求 |
| branch_condition_routes_path | 分支条件把流程路由到某条路径；只能用于 DECIDES 边且必须有 condition |
| component_assembles_product | 信息字段、证据、叙述组件或记录要素共同构成正式产物 |
| standard_constrains_action | 法律、保密、相称性、准确性、监管期限等标准限定动作如何执行 |
| result_handoffs_stage | 当前处理结果成为下一角色、层级、系统或外部机构继续处理的输入 |
| feedback_requests_completion | 复核问题、缺失信息或叙述不足要求补充研究、修订或重新处理 |
| cycle_requires_monitoring | 周期、持续义务、后评估或 ongoing monitoring 关系要求复核或继续观察 |
| standard_transmits_requirement | 国际标准、监管原则、指南或评估结果传导为辖区或机构控制要求 |
| parallel_alternative_no_sequence | 多个 typology、标准、组件或案例点互为并列，不应强制串成时间先后边 |

**不得输出**：`derivation`、边级 `evidence_strength`、`review_status`。

## 2. Relation 端点兼容矩阵

| kind | 起点 role | 终点 role | 额外约束 |
|---|---|---|---|
| `trigger` | context | action 或 decision | trigger_mode 必须为 event 或 condition |
| `sequence` | action/decision/outcome | action/decision/outcome | 原文明示先后；context 起点应改用 trigger |
| `reference` | action 或 decision | input 或 standard | 固定 process→auxiliary |
| `produce` | action 或非 P3 的 decision | outcome | target 必须是独立语义结果 |
| `branch` | decision | action 或 outcome | 至少两个互斥分支；每条 condition 必填 |
| `feedback` | outcome 或 decision | action 或 decision | 原文支持复核、补充、更新或调优 |

## 输出 Contract

```json
{
  "section_id": "CH06-S10",
  "cards": [
    {
      "card_id": "p7card_CH06-S10_001",
      "section_id": "CH06-S10",
      "card_nature": "assessment",
      "title": "依据直接和间接持股及适用阈值认定UBO",
      "flow_nodes": [
        {
          "node_id": "n001",
          "node_category": "auxiliary",
          "node_type": "input",
          "label": "直接持股比例",
          "evidence_unit_ids": ["v7u_N000477"],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "edge_001",
          "edge_type": "REFERENCES",
          "source": "n004",
          "target": "n001",
          "evidence_unit_ids": ["v7u_N000477"]
        }
      ],
      "source_unit_ids": ["v7u_N000477", "v7u_N000478"],
      "candidate_status": "candidate",
      "review_notes": "局部命题：...；证据范围：...；待P7D逐边审核。"
    }
  ],
  "coverage_audit": [
    {
      "candidate_id": "s1c_001",
      "disposition": "mapped",
      "card_ids": ["p7card_CH06-S10_001"],
      "reason": "..."
    }
  ],
  "node_type_reasons": {
    "ep_001": {
      "e001": "input role → node_type=input",
      "e005": "decision role + 2 branch relations → P3_branch_routing"
    }
  },
  "skip_reason": null
}
```

- 一个 episode 对应一张 card
- card_id 格式 `p7card_{section_id}_{NNN}`
- 每个 flow_node 有 `node_id, node_category, node_type, label, evidence_unit_ids, evidence_strength`
- 每条 flow_edge 有 `edge_id, edge_type, source, target, evidence_unit_ids`
- 条件必填 `condition`，不输出 `derivation`
- candidate_status 固定 `candidate`
- review_notes 中文说明增量命题、证据范围、待 P7D 审核
- `node_type_reasons` 记录每个 element 的 node_type 选择理由（至少记录非平凡选择）

`coverage_audit` 沿用 S2 的 `candidate_audit.disposition`，映射规则：
- `mapped/support_only` → `decision: "p7c_card"`，card_ids 至少一张
- `excluded_nonprocedural` → `decision: "kg_only"`，card_ids 为空
- `ungraphable` → `decision: "p7c_ungraphable"`，card_ids 为空

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

allowed_unit_ids:

```json
[
  "v7u_N000955",
  "v7u_N000956",
  "v7u_N000957",
  "v7u_N000958",
  "v7u_N000959",
  "v7u_N000960",
  "v7u_N000961",
  "v7u_N000962",
  "v7u_N000963",
  "v7u_N000964",
  "v7u_N000965",
  "v7u_N000966",
  "v7u_N000967",
  "v7u_N000968",
  "v7u_N000969",
  "v7u_N000970",
  "v7u_N000971",
  "v7u_N000972",
  "v7u_N000973",
  "v7u_N000974",
  "v7u_N000975",
  "v7u_N000976",
  "v7u_N000977",
  "v7u_N000978",
  "v7u_N000979",
  "v7u_N000980",
  "v7u_N000981",
  "v7u_N000982",
  "v7u_N000983",
  "v7u_N000984",
  "v7u_N000985",
  "v7u_N000986",
  "v7u_N000987",
  "v7u_N000988",
  "v7u_N000989",
  "v7u_N000990",
  "v7u_N000991",
  "v7u_N000992",
  "v7u_N000993",
  "v7u_N000994",
  "v7u_N000995",
  "v7u_N000996",
  "v7u_N000997",
  "v7u_N000998",
  "v7u_N000999",
  "v7u_N001000",
  "v7u_N001001",
  "v7u_N001002",
  "v7u_N001003",
  "v7u_N001004",
  "v7u_N001005"
]
```

## S2 Process IR

```json
{
  "section_id": "CH13-S01",
  "episodes": [
    {
      "episode_id": "ep_001",
      "source_candidate_ids": [
        "s1c_gap_ch13_s01_regulator_monitoring"
      ],
      "focal_question": "监管机构如何监控加密资产以阻止非法活动？",
      "title": "监管机构监控加密资产旨在阻止非法活动",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "action",
          "label": "监管机构监控加密资产的法律和合规方面",
          "evidence_unit_ids": [
            "v7u_N000970"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "outcome",
          "label": "阻止欺诈和洗钱等非法活动",
          "evidence_unit_ids": [
            "v7u_N000970"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "produce",
          "process_element_id": "e001",
          "outcome_element_id": "e002",
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N000970"
          ],
          "source_quote": "Regulators monitor the legal and compliance aspects of cryptoassets to deter illegal activities, such as fraud and money laundering."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_002",
      "source_candidate_ids": [
        "s1c_gap_ch13_s01_block_verification"
      ],
      "focal_question": "区块链被挖掘后必须如何操作？",
      "title": "区块链挖掘后必须由网络其他节点验证",
      "card_nature": "execution",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "区块链被挖掘",
          "evidence_unit_ids": [
            "v7u_N000984"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "必须由网络上的其他节点验证",
          "evidence_unit_ids": [
            "v7u_N000984"
          ],
          "modality": "required"
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "trigger",
          "trigger_mode": "event",
          "trigger_element_id": "e001",
          "process_element_id": "e002",
          "condition": null,
          "relation_type": "conclusion_triggers_response",
          "evidence_unit_ids": [
            "v7u_N000984"
          ],
          "source_quote": "Once a blockchain is mined, it also must be verified by other nodes on the network."
        }
      ],
      "split_reason": null
    },
    {
      "episode_id": "ep_003",
      "source_candidate_ids": [
        "s1c_gap_ch13_s01_cdd_monitoring"
      ],
      "focal_question": "如何在加密资产兑换点识别可疑活动？",
      "title": "在兑换点易受洗钱背景下通过CDD和监控识别可疑活动",
      "card_nature": "control",
      "elements": [
        {
          "element_id": "e001",
          "role": "context",
          "label": "加密资产与法定货币的兑换点易受洗钱影响",
          "evidence_unit_ids": [
            "v7u_N000995"
          ],
          "modality": null
        },
        {
          "element_id": "e002",
          "role": "action",
          "label": "实施客户尽职调查和监控",
          "evidence_unit_ids": [
            "v7u_N000995"
          ],
          "modality": null
        },
        {
          "element_id": "e003",
          "role": "outcome",
          "label": "帮助识别可疑活动",
          "evidence_unit_ids": [
            "v7u_N000995"
          ],
          "modality": null
        }
      ],
      "relations": [
        {
          "relation_id": "r001",
          "kind": "trigger",
          "trigger_mode": "event",
          "trigger_element_id": "e001",
          "process_element_id": "e002",
          "condition": null,
          "relation_type": "conclusion_triggers_response",
          "evidence_unit_ids": [
            "v7u_N000995"
          ],
          "source_quote": "Without proper controls, the conversion point between cryptoassets and fiat is particularly vulnerable to money laundering, but CDD checks and monitoring can help identify suspicious activities."
        },
        {
          "relation_id": "r002",
          "kind": "produce",
          "process_element_id": "e002",
          "outcome_element_id": "e003",
          "qualifier": "aimed_to",
          "evidence_unit_ids": [
            "v7u_N000995"
          ],
          "source_quote": "CDD checks and monitoring can help identify suspicious activities."
        }
      ],
      "split_reason": null
    }
  ],
  "candidate_audit": [
    {
      "candidate_id": "s1c_gap_ch13_s01_regulator_monitoring",
      "disposition": "mapped",
      "episode_ids": [
        "ep_001"
      ],
      "reason": "该候选独立支持一个程序性关系：监管机构的监控行动旨在阻止非法活动，可完整建模为独立 episode。"
    },
    {
      "candidate_id": "s1c_gap_ch13_s01_block_verification",
      "disposition": "mapped",
      "episode_ids": [
        "ep_002"
      ],
      "reason": "该候选提供了区块链挖掘后触发强制验证的条件-动作关系，构成完整的程序性单元。"
    },
    {
      "candidate_id": "s1c_gap_ch13_s01_cdd_monitoring",
      "disposition": "mapped",
      "episode_ids": [
        "ep_003"
      ],
      "reason": "该候选描述了在兑换点易受洗钱背景下，采取CDD和监控以帮助识别可疑活动的程序性关系，可独立建模。"
    }
  ],
  "skip_reason": null
}
```
