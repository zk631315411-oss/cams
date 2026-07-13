# CAMS 教研工作台 — 教材知识图谱项目

## 项目目标

建设 CAMS 反洗钱考试教材（V6 第2章）的知识图谱。教研拿到一道新题，把题干和选项往图里查：
- 每个选项落到图上的知识节点
- 节点之间有边连着——这些边是概念之间的客观关系（主体不同、方向相反等）
- 看图上的分布和连线，直接理解这道题考了什么

## 目录结构

```
cams工作台/
├── README.md                    ← 本文件
├── CLAUDE.md                    ← 项目指令（Claude Code 读取）
├── index.html                   ← 教研工作台 Web 界面（含教材阅读器+知识关联面板）
├── reader.html                  ← 备用阅读器
├── css/, js/                    ← 前端资源
│
├── data/                        ← 所有数据
│   ├── cards_ch2.json           ← 1950张教材句卡/原文证据句（非教研确认考点）
│   ├── questions.json           ← 179道题目（题干+选项+答案+解析）
│   ├── qa.json                  ← 37条学生答疑记录
│   ├── qa_bindings.json         ← 答疑→题目→卡片绑定
│   ├── question_card_map.json   ← 题目→卡片匹配
│   ├── card_relations.json      ← 旧版卡片关联关系（co-occurrence）
│   ├── chapters/                ← 教材章节结构化数据
│   │   └── ch2.json             ← V6第2章（MinerU提取，8节×24小节）
│   ├── lightrag_index/          ← LightRAG 索引（5798节点，12080边）
│   ├── lightrag_eval/           ← LightRAG 评估结果
│   ├── agentic_search_eval_v2/  ← **当前实验产出**
│   │   ├── ch2_full_text.txt    ← 教材第2章完整文本
│   │   ├── toc_ch2_compact.txt  ← 教材目录
│   │   ├── kg/                  ← **知识图谱产出（冻结）**
│   │   │   ├── sections.json    ← 99个概念节点（教材小节+definition+别名）
│   │   │   ├── edges.json       ← 23条跨节关系边（含类型+详情）
│   │   │   └── card_section_map.json ← 1950张卡片→节点挂载
│   │   └── ...                  ← 四角色法、P3-P7等中间产物
│   ├── 证据包_*.md              ← 教研人工整理的证据包（验证用，不参与构建）
│   └── archive/                 ← 早期一次性分析文件归档
│
├── ai自主尝试/                  ← **当前主线探索**
│   ├── plans/                   ← 计划文档
│   │   ├── plan_concept_tree.md ← 教材知识图谱建设计划（最新版）
│   │   └── plan.md              ← 四角色法探索计划
│   ├── step1_annotate_edges.py  ← 第一步：LLM读全文标注跨节关系（边）
│   ├── step2_card_mount.py      ← 第二步：卡片→节点挂载
│   ├── step3_validate.py        ← 第三步：2.1_19端到端验证
│   ├── run_four_roles.py        ← 四角色法实验
│   ├── build_query_layer.py     ← 方案B：题目→节点映射表构建
│   └── tests/                   ← 各题测试脚本
│       ├── test_hybrid.py       ← **混合策略：图谱优先+四角色兜底**
│       ├── test_2.1_4.py        ← 处置阶段题
│       ├── test_2.1_19.py       ← FI后果多选题
│       ├── test_2.1_30.py       ← 资本市场洗钱题
│       ├── test_2.2_1.py        ← 代理银行尽职调查题
│       ├── test_2.2_6.py        ← PEP风险重分类题
│       └── test_2.2_9.py        ← 巢状交易题
│
├── pipeline/                    ← 旧版实验管线（P3-P7 agentic search）
├── retrieval/                   ← 检索工具（LightRAG、BM25+BGE+RRF）
├── data_pipeline/               ← 一次性数据处理（解析题目、匹配卡片）
├── tests_prototypes/            ← 早期测试与原型脚本
├── docs/                        ← 项目文档
│   ├── 教研需求理解.md          ← 教研需求说明（含最终效果示意）
│   ├── 反馈.md                  ← 教研反馈汇总（四轮）
│   ├── 项目记录.md              ← 项目开发记录
│   └── ...
└── 文献支持/                    ← Agentic Search 相关论文
```

## 当前进展

### 图谱建设（已完成）

| 组件 | 文件 | 内容 |
|---|---|---|
| 节点 | `kg/sections.json` | 99个概念节点，每个有definition+别名 |
| 边 | `kg/edges.json` | 23条跨节关系，含类型（主体不同/方向相反/互为因果等） |
| 卡片挂载 | `kg/card_section_map.json` | 1950张全挂载（citation 1707 + BGE 243） |

### 查询验证（6/6通过）

混合策略：图谱优先（BGE+别名匹配），失败时四角色法兜底（教材全文+LLM）。

| 题 | 类型 | 方法 | 结果 |
|---|---|---|---|
| 2.1_4 处置阶段 | 教材直给 | 图谱 | ✅ |
| 2.1_19 FI后果 | 跨节辨析 | 图谱→兜底 | ✅ |
| 2.1_30 资本市场 | 迹象识别 | 图谱 | ✅ |
| 2.2_1 代理银行 | 规则应用 | 图谱→兜底 | ✅ |
| 2.2_6 PEP | 规则应用 | 图谱→兜底 | ✅ |
| 2.2_9 巢状交易 | 术语翻译 | 图谱→兜底 | ✅ |

### 已知问题

1. **v6_b04_N09挂载位置**：在"社会成本"小节而非预期的"削弱金融组织"（实为教材结构理解偏差，已确认正确）
2. **四角色API稳定性**：DeepSeek API 对8.8万字符prompt偶发空响应（重试可恢复）
3. **未在全量179题上验证**：当前只测了6题
4. **Web界面未对接新图谱数据**：`index.html` 仍使用旧版 `card_relations.json`

## 铁律

1. 旧解析、教研答疑、人工证据包**绝不作为输入**，只能事后验证
2. 教材原文全量可用
3. 每一步的LLM输出驱动下一步，不人手写结论塞进prompt
4. 节点和边不人工编造
5. 每条推理必须可追溯card_id
6. 教研数据只验证，不参与构建
7. 过程可审计（每次LLM调用的prompt和输出均保存）

## 快速开始

### 运行图谱构建

```bash
cd ai自主尝试
export DEEPSEEK_API_KEY="sk-xxx"
python step1_annotate_edges.py   # LLM读全文标注边（~3万token，一次性）
python step2_card_mount.py       # 卡片→节点挂载
python step3_validate.py         # 2.1_19端到端验证
```

### 运行混合策略测试

```bash
cd ai自主尝试/tests
python test_hybrid.py            # 6题全测，图谱优先+四角色兜底
```

### 产出示意

```
选项D"公司税的增加" → 图谱定位 → [税收损失]节点
    → 挂载卡片v6_b03_N18"洗钱使政府税收缩水"
    → 边→[削弱金融组织]"主体不同"
    → 推理链：政府税收缩水≠FI公司税增加，主体错配
```

## 模型与API

- LLM: DeepSeek v4-pro（通过 `https://api.deepseek.com`）
- Embedding: BAAI/bge-small-zh-v1.5（本地加载）
- 环境变量: `DEEPSEEK_API_KEY`
