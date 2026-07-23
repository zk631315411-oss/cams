# vulture whitelist — 经人工确认的误报

# rerank_server.py 是独立 FastAPI 服务，函数通过 HTTP 端点调用，
# vulture 无法检测路由
document   # FastAPI query parameter (rerank_server.py:36)
rerank     # FastAPI POST /rerank endpoint (rerank_server.py:63)
health     # FastAPI GET /health endpoint (rerank_server.py:99)

# 从 run_bindings.py 拆分出的备用模块，当前管线未调用但保留供未来使用
answerless_question_for_blind  # retrieval/blind_guard.py — 盲判题目脱敏
blind_repair_hint              # retrieval/repair_hint.py — 盲判修复提示
