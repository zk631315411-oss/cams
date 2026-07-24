# -*- coding: utf-8 -*-
"""s3 — 候选记录工厂。薄包装，实际实现在 公共函数.candidate。"""

import sys
from pathlib import Path as _Path
_PARENT = str(_Path(__file__).resolve().parent.parent)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

from 公共函数.candidate import make_candidate
