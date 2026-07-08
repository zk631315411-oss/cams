from pathlib import Path
import xml.etree.ElementTree as ET


p = next(Path.cwd().glob("CAMS_V7*.drawio"))
text = p.read_text(encoding="utf-8")
root = ET.fromstring(text)
cells = root.findall(".//mxCell")
vertices = [c for c in cells if c.attrib.get("vertex") == "1"]
edges = [c for c in cells if c.attrib.get("edge") == "1"]

print("file", p)
print("title_ok", "CAMS V7 教研工作台" in text)
print("banner_ok", "AI 给候选，教研定结论" in text)
print("cell_count", len(cells))
print("vertex_count", len(vertices))
print("edge_count", len(edges))
for c in vertices[:5]:
    print("vertex", c.attrib.get("id"), c.attrib.get("value", "")[:60])
