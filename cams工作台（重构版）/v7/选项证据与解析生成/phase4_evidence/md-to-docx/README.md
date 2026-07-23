# md-to-docx 小节 md → 题库 DOCX 转换

## 用法

```bash
# 单文件
python md_to_docx.py -i sections/p1-ch1-h2.md -o output/p1-ch1-h2.docx

# 批量（目录下所有 p*-ch*-h*.md）
python md_to_docx.py --batch sections/
# → 输出到 sections/docx/
```

## 输出格式

```
试卷名称:CAMS CH01
一、单项选择题
1. 题目 ( )
A. 选项A
B. 选项B
答案:B
解析：
考点
核心解析：...
A项错误：...
B项错误：...
易错提醒：...
```

## 格式转换

- `（P28）` `（书内第28页）` `<sup>P28</sup>` → Word 上角标
- `**bold**` → Word 加粗
- `「」` → `""`
- 解析标签（考点、核心解析、X项错误、易错提醒）→ 蓝底加粗小标题

## 源格式

输入 md 由 `export_software_explanations.py` 生成，解析部分为标准导入格式：
```
考点：text
核心解析：text
A项错误：text
易错提醒：text
```
