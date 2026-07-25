# p1-ch1-h7 题库软件版解析预览

可导出题目数：1

教材章节：未映射

题型：single

题干：一位金融机构(FI)的客户投诉称,他们收到了多封看似来自该金融机构的电子邮件,催促他们点击链接或打开汇款附件进行确认.客户打开附件后,后来才发现自己银行账户中的资金在他们不知情的情况下被有计划地转走了.此情景中描述的是哪种类型的网络犯罪？

英文题干：A customer of a financial institution (FI) complained that they had received multiple emails appearing to originate from the FI, urging them to click a link or open a remittance attachment for confirmation. After opening the attachment, the customer later realized that funds had been systematically transferred out of their bank account without their knowledge. Which type of cybercrime is described in this scenario?

选项：

- A. 语音钓鱼（vishing）
  English: Vishing
- B. 域名欺骗（pharming）
  English: Pharming
- C. 短信钓鱼（SMiShing）
  English: SMiShing
- D. 鱼叉式网络钓鱼
  English: Spear phishing

## 【AI答案】

D

> **本题为教材覆盖缺口，经教研手动撰写解析**
>
> 教材P30网络犯罪章节未对phishing的四种亚型（vishing/pharming/SMiShing/spear phishing）分别定义，但描述了本题对应的行为模式。

## 【考点】

从题干攻击媒介（电子邮件）和攻击手法（冒充+欺诈链接+紧迫感）识别对应网络犯罪类型

## 【核心解析】

教材将网络犯罪的基础归结为一个词：信任（P30）。网络犯罪分子必须取得目标的信任才能成功——为此采用的手段包括冒充（impersonation）和钓鱼欺诈（phishing and spoofing）。教材进一步描述这类欺骗手法的运作方式：犯罪分子需要"说服目标点击欺诈链接""制造一种紧迫感和来源可靠性的组合"（P30）。

将题干拆解对应：收到多封"看似来自该金融机构"的邮件 → 冒充（impersonation），伪造来源可靠性；"催促点击链接或打开附件" → 说服目标点击欺诈链接（fraudulent link），制造紧迫感。教材描述的行为模式与题干场景逐条吻合。

进一步锁定具体类型：题干明确攻击媒介为**电子邮件**（而非电话、短信或DNS劫持），冒充的是**特定**金融机构（针对该机构客户，而非群发），附带恶意附件导致资金被转走。这四要素——电子邮件、定向冒充、欺诈链接/附件、紧迫感——恰好对应鱼叉式网络钓鱼（Spear Phishing）的核心定义。

**教材覆盖说明**：教材P30仅笼统提及"phishing and spoofing"为冒充手段，未将phishing进一步拆分为以下四种亚型。四种类型的定义来自网络安全通用知识补充：

- Spear Phishing（鱼叉式钓鱼）：以电子邮件为媒介，冒充特定可信实体，向定向目标发送定制化欺诈邮件，诱导点击恶意链接或附件。
- Vishing（语音钓鱼）：以电话或VoIP为媒介，冒充机构客服或权威人士来电，口头诱骗受害者透露敏感信息或执行转账。
- SMiShing（短信钓鱼）：以SMS短信为媒介，发送伪装成银行、快递或政府机构的短信，含恶意链接诱导点击。
- Pharming（域名欺骗）：以DNS/网络层为媒介，通过DNS缓存投毒或hosts篡改，将用户输入的合法网址静默重定向至假冒网站，用户全程无感知。

本题通过题干的"电子邮件"媒介和"主动发送欺诈邮件+诱导打开附件"的攻击路径，排除A（电话）、B（DNS静默重定向）、C（短信），锁定D。

教材原句："The foundation of all cyber-enabled crime is trust... to convince the target to click on a fraudulent link, cybercriminals must create a combination of urgency and source reliability."

## 【错误项分析】

- **A 错误（媒介不匹配）**：Vishing 的攻击媒介为电话或 VoIP 语音通话。题干明确攻击媒介为"电子邮件"，媒介层面直接排除。
- **B 错误（攻击路径不匹配）**：Pharming 通过 DNS 缓存投毒或 hosts 篡改，将用户静默重定向至假冒网站——用户全程不会"收到邮件并打开附件"。攻击路径与题干不符。
- **C 错误（媒介不匹配）**：SMiShing 的攻击媒介为 SMS 短信。题干攻击媒介为电子邮件，渠道不匹配。

## 【易错提醒】

四种网络钓鱼亚型的区分维度是**攻击媒介**——题干"电子邮件"一词直接排除 A（电话）和 C（短信），"收到欺诈邮件"的主动诱导路径排除 B（DNS 静默重定向）。锁定媒介后，再判断是否"定向冒充特定机构"即可确认 spear phishing。

---

