# -*- coding: utf-8 -*-
"""机械合规检查薄包装：所有实现已合并到 解析撰写/s5_explanation_review.py。"""

import sys
from pathlib import Path as _Path
_PARENT = str(_Path(__file__).resolve().parent.parent)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

from 解析撰写.s5_explanation_review import (
    check_single_question, run_review, main, validate_for_software,
    REVIEW_SCHEMA_VERSION,
)

if __name__ == "__main__":
    main()
