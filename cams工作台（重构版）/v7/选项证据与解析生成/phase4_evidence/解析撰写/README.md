# 解析撰写

## 生产脚本

| 脚本 | 用途 |
|------|------|
| `generate_evidence_explanations.py` | 核心：盲判结果 → V3.1 教研解析（含 ±4 上下文扩展） |
| `export_software_explanations.py` | question JSON → 小节 md（p1-ch1-h2 格式） |
| `review_check.py` | 复核检测，输出 review_required.md |
| `apply_superscript.py` | 小节 md 中 `（书内第XX页）` → `<sup>PXX</sup>` |

## 典型流程

```
盲判结果 (questions/q_*.json)
    ↓ generate_evidence_explanations.py --write-back --concurrency 25
解析母版 (questions/q_*.json + explanations_export/*.md)
    ↓ export_software_explanations.py --output-dir output
小节 md (software_export/sections/p*-ch*-h*.md)
    ↓ md-to-docx/md_to_docx.py --batch sections/
题库 docx
```
