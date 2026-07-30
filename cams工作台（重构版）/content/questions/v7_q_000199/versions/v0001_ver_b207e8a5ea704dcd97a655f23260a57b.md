# v7_q_000199

教材章节：未映射

题型：single

题干：有三类因素可用于验证某人的身份：持有因素、知识因素和固有因素。以下哪个因素属于固有因素？

英文题干：There are three types of factors that can be used to authenticate someone: ownership, knowledge, and inherent factors. Which of the following factors falls under inherent factors?

选项：

- A. 挑战-响应
  English: Challenge-response
- B. 指纹
  English: Fingerprint
- C. 安全令牌
  English: Security token
- D. 密码短语
  English: Passphrase

## 【AI答案】

B

## 【考点】

区分多因素认证中inherence与ownership/knowledge的类别归属

## 【核心解析】

认证方法通常分为三类：Ownership（持有因素，即你拥有的东西）、knowledge（知识因素，即你知道的东西）和inherence（固有因素，即你本身的特征）（P410）。教材随后以强多因素认证为例，将security token标为ownership、password或安全问题答案标为knowledge、fingerprint或facial recognition标为inherence（P410）。题干问哪一项属于inherence，选项B「指纹」正是身体固有特征；C属于持有因素，D与密码同属知识因素，A也不是身体固有特征，因此答案唯一为B。

教材原句："An example of strong MFA would be the combination of a security token, such as a one-time code received on the phone (ownership), a password or answer to a security question (knowledge), and a fingerprint or facial recognition (inherence)."

## 【错误项分析】

- **A 错误**：「挑战-响应」描述的是一种认证交互方式，其具体类别取决于响应所使用的凭据；这一名称本身不表示「你本身的特征」。相比之下，指纹明确属于inherence。
- **C 错误**：「安全令牌」在教材强MFA示例中明确被归入ownership（持有因素）类别——收到手机上的一次性验证码就是你持有所属移动设备的证明（P410）。题干问的是inherence，ownership虽然也是认证因素之一，但与题干要求不匹配。
- **D 错误**：「密码短语」与教材列举的password一样，是用户知道的信息，属于knowledge，而非inherence（P410）。

## 【易错提醒】

三类因素可按「something you have / know / are」区分：安全令牌是ownership，密码或安全问题答案是knowledge，指纹或面部识别是inherence（P410）。判断时看验证依赖的是持有物、记忆信息还是个人身体特征。

## 【教材原文依据】

> 核心引用单元：`v7u_N004111`

### `v7u_N004109`

- 用于：核心解析、选项A、易错提醒
- 章节：Technology for KYC > Authentication and security technology
- 页码：PDF第415页 / 书内第410页
- 中文要点：认证方法分为三类：拥有、知识、固有特征。
- 英文原文：Typically, authentication methods fall into three main categories: Ownership (something you have), knowledge (something you know), and inherence (something you are).

### `v7u_N004111`

- 用于：核心解析、选项A、选项C、选项D
- 章节：Technology for KYC > Authentication and security technology
- 页码：PDF第415页 / 书内第410页
- 中文要点：强MFA示例：安全令牌、密码与指纹或面部识别组合。
- 英文原文：An example of strong MFA would be the combination of a security token, such as a one-time code received on the phone (ownership), a password or answer to a security question (knowledge), and a fingerprint or facial recognition (inherence).

## 【参考答案与参考解析】

- 题库最终参考答案：B
- 中文参考答案：B

### 中文参考解析

在验证身份的三种因素中,拥有物指如身份证 安全令牌等物品;知识指如密码、短语等需记忆 的内容;固有因素即内在因素,是与生俱来或长 期形成的生物特征.分析选项,A选项挑战-响应 不属于身份验证因素分类;B选项指纹是生物特 征,属于固有因素;C选项安全令牌是拥有物; D选项密码短语属于知识.因此,属于固有因素 的是指纹,答案选B.

- 英文参考答案：B

### 英文参考解析

未提供。

### 答案冲突提示

- 未发现答案冲突。
