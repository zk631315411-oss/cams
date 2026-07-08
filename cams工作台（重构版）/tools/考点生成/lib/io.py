"""读写 q_*.json 和中间产物"""
import json
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parents[1]
_WORK = _HERE / "work"
_QUESTIONS_DIR = Path(
    r"D:\守正公司工作区\cams考试\cams工作台（重构版）"
    r"\tools\选项证据生成\新题解析模块复用\output\questions"
)


def read_question(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_questions():
    """遍历所有 q_*.json，yield (question_id, data)"""
    for p in sorted(_QUESTIONS_DIR.glob("q_*.json")):
        yield p.stem.replace("q_", ""), read_question(p)


def read_work(filename: str) -> Any:
    return json.loads((_WORK / filename).read_text(encoding="utf-8"))


def write_work(filename: str, data: Any):
    _WORK.mkdir(parents=True, exist_ok=True)
    (_WORK / filename).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
