"""Pipeline 编排模块。

llm.py      → LLM 客户端配置、阶段路由
planner.py  → 盲态检索规划 (待从 run_bindings.py 迁出)
retrieval.py → 多路召回编排 (待从 run_bindings.py 迁出)
question.py → 题目加载与盲态处理 (待从 run_bindings.py 迁出)
review.py   → 分歧二审与校验 (待从 run_bindings.py 迁出)
core.py     → run_question_core 主流水线 (待从 run_bindings.py 迁出)
"""
