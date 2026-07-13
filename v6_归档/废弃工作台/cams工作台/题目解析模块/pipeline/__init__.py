"""题目解析模块 — 借用新题解析模块的检索思路，实现题目与全书句卡的链接。"""

# 加载工作区 .env（DEEPSEEK_API_KEY 等），必须在依赖 run_step1 之前完成
from env_setup import _load_env  # noqa: F401
_load_env()
