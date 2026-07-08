from html import escape
from pathlib import Path


OUT = Path.cwd() / "CAMS_V7_教研沟通版_流程图.drawio"


def attr(s: str) -> str:
    return escape(s).replace("\n", "&#xa;")


def node(id_, value, x, y, w, h, fill, stroke, font="1F2933", extra=""):
    style = (
        "rounded=1;whiteSpace=wrap;html=1;spacing=8;"
        f"fillColor={fill};strokeColor={stroke};fontColor=#{font};"
        "align=center;verticalAlign=middle;" + extra
    )
    return f'''      <mxCell id="{id_}" value="{attr(value)}" style="{style}" vertex="1" parent="1">
        <mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/>
      </mxCell>'''


def edge(id_, source, target, stroke="64748B"):
    style = (
        "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;"
        "html=1;endArrow=block;endFill=1;"
        f"strokeColor=#{stroke};"
    )
    return f'''      <mxCell id="{id_}" value="" style="{style}" edge="1" parent="1" source="{source}" target="{target}">
        <mxGeometry relative="1" as="geometry"/>
      </mxCell>'''


cells = []

# Background / section cards
cells.append(node("2", "教材底座", 40, 35, 300, 26, "E0F2FE", "93C5FD", "0F172A", "fontStyle=1;"))
cells.append(node("3", "题目与教材绑定", 430, 35, 300, 26, "DCFCE7", "86EFAC", "0F172A", "fontStyle=1;"))
cells.append(node("4", "学生答疑沉淀", 430, 610, 300, 26, "F3E8FF", "D8B4FE", "0F172A", "fontStyle=1;"))
cells.append(node("5", "共享证据底座：教材句卡 + 教材知识图谱", 60, 320, 310, 120, "D9F3F0", "14B8A6", "0F172A", "fontStyle=1;"))

# Left foundation chain
cells.extend([
    node("10", "教材 PDF\nCAMS中文版教材-V6.51.pdf", 60, 70, 260, 46, "EFF6FF", "93C5FD"),
    node("11", "MinerU 解析\n版面、段落、表格初步还原", 60, 135, 260, 46, "FFFFFF", "93C5FD"),
    node("12", "v6_clean.md\n稳定教材底稿", 60, 200, 260, 46, "FFFFFF", "93C5FD"),
    node("13", "句卡生成\n5199 张可追溯原文句卡", 60, 265, 260, 46, "FFFFFF", "93C5FD"),
    node("14", "教材知识图谱\n知识点 / 关系 / 挂载", 60, 385, 260, 46, "D9F3F0", "14B8A6"),
])

# Question line
cells.extend([
    node("20", "V7 官方题库\nquestions.json", 430, 70, 190, 46, "DCFCE7", "86EFAC"),
    node("21", "题目-选项拆解\nstem / options / answer", 650, 70, 190, 46, "FFFFFF", "86EFAC"),
    node("22", "证据检索 + AI 候选答案\nBGE / BM25 / KG / 句卡", 870, 70, 240, 46, "FFFFFF", "86EFAC"),
    node("23", "q_{id}.json\n每题完整绑定过程", 1140, 70, 170, 46, "FFFFFF", "86EFAC"),
    node("24", "教研复核 / 上架\n短、准、能回到知识点", 1340, 70, 220, 46, "FEF3C7", "F59E0B"),
])

# Answer / QA line
cells.extend([
    node("30", "学生答疑\n历史问答 / 题目", 430, 645, 190, 46, "F3E8FF", "D8B4FE"),
    node("31", "结构化 Markdown\n一条答疑一个文件", 650, 645, 190, 46, "FFFFFF", "D8B4FE"),
    node("32", "候选答疑 + 是否回挂\nAI 先写，教研决定沉淀", 870, 645, 240, 46, "FFFFFF", "D8B4FE"),
    node("33", "答疑沉淀 / FAQ\n反哺解析与易错点", 1140, 645, 190, 46, "FFFFFF", "D8B4FE"),
])

# Bottom banner
cells.append(node("40", "核心原则：AI 给候选，教研定结论；所有结果尽量回到教材句卡。", 220, 845, 1260, 52, "1E3A5F", "1E3A5F", "FFFFFF", "fontStyle=1;"))

# Edges
edges = [
    ("e1", "10", "11", "93C5FD"),
    ("e2", "11", "12", "93C5FD"),
    ("e3", "12", "13", "93C5FD"),
    ("e4", "13", "14", "14B8A6"),
    ("e5", "14", "5", "14B8A6"),
    ("e6", "20", "21", "86EFAC"),
    ("e7", "21", "22", "86EFAC"),
    ("e8", "22", "23", "86EFAC"),
    ("e9", "23", "24", "F59E0B"),
    ("e10", "30", "31", "D8B4FE"),
    ("e11", "31", "32", "D8B4FE"),
    ("e12", "32", "33", "D8B4FE"),
    ("e13", "5", "22", "14B8A6"),
    ("e14", "5", "32", "14B8A6"),
]


xml = f'''<mxfile host="app.diagrams.net" modified="2026-06-30T00:00:00.000Z" agent="Codex" version="24.7.17" type="device">
  <diagram id="cams-v7" name="CAMS V7 教研工作台">
    <mxGraphModel dx="1700" dy="1000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1700" pageHeight="1000" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
{chr(10).join(cells)}
{chr(10).join(edge(*e) for e in edges)}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
'''

OUT.write_text(xml, encoding="utf-8")
print(OUT)
