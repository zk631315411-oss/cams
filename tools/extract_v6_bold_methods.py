#!/usr/bin/env python3
"""Extract and synthesize bolded methods from the archived V6 DOCX question bank.

The source DOCX files are parsed at OOXML run level so direct and style-inherited
bold formatting remains traceable.  Generated outputs are deliberately kept in
an archive-analysis directory and are not wired into the V7 workbench.
"""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}
W = f"{{{W_NS}}}"

LABELS = {
    "answer": re.compile(r"^\s*答案\s*[:：]"),
    "explanation": re.compile(r"^\s*解析\s*[:：]"),
    "knowledge": re.compile(r"^\s*具体知识点\s*[:：]"),
    "option_analysis": re.compile(r"^\s*选项分析\s*[:：]"),
}
QUESTION_START = re.compile(r"^\s*(\d+)\s*[\.．、]\s*\S")
OPTION_START = re.compile(r"^\s*[A-HＡ-Ｈ]\s*[\.．、]\s*\S")
ANSWER_TOKEN = re.compile(r"^\s*答案\s*[:：]")


@dataclass
class Run:
    text: str
    bold: bool
    run_index: int


@dataclass
class Paragraph:
    paragraph_index: int
    text: str
    runs: list[Run]
    location: str
    section: str = "unknown"


def qname(name: str) -> str:
    return name if name.startswith("{") else W + name


def attr(element: ET.Element, name: str, default: str | None = None) -> str | None:
    return element.attrib.get(W + name, default)


def val_is_true(element: ET.Element | None) -> bool:
    if element is None:
        return False
    value = attr(element, "val")
    return value is None or value.lower() not in {"0", "false", "off", "no"}


def build_style_bold_map(styles_xml: bytes | None) -> dict[str, bool]:
    """Resolve paragraph and character style boldness, including basedOn chains."""
    if not styles_xml:
        return {}
    root = ET.fromstring(styles_xml)
    styles: dict[str, dict[str, str | bool | None]] = {}
    for style in root.findall("w:style", NS):
        sid = attr(style, "styleId")
        if not sid:
            continue
        based = style.find("w:basedOn", NS)
        styles[sid] = {
            "based": attr(based, "val") if based is not None else None,
            "bold": val_is_true(style.find("w:rPr/w:b", NS)),
        }

    resolved: dict[str, bool] = {}

    def resolve(sid: str, trail: set[str] | None = None) -> bool:
        if sid in resolved:
            return resolved[sid]
        trail = trail or set()
        if sid in trail or sid not in styles:
            return False
        trail.add(sid)
        item = styles[sid]
        result = bool(item["bold"]) or bool(item["based"] and resolve(str(item["based"]), trail))
        resolved[sid] = result
        return result

    for sid in styles:
        resolve(sid)
    return resolved


def run_text(run: ET.Element) -> str:
    chunks: list[str] = []
    for child in run.iter():
        if child.tag == W + "t":
            chunks.append(child.text or "")
        elif child.tag == W + "tab":
            chunks.append("\t")
        elif child.tag in {W + "br", W + "cr"}:
            chunks.append("\n")
    return "".join(chunks)


def parse_paragraph(p: ET.Element, index: int, location: str, style_bold: dict[str, bool]) -> Paragraph:
    p_style = p.find("w:pPr/w:pStyle", NS)
    p_style_bold = bool(p_style is not None and style_bold.get(attr(p_style, "val", "") or "", False))
    runs: list[Run] = []
    for run_index, run in enumerate(p.findall("w:r", NS)):
        text = run_text(run)
        if not text:
            continue
        rpr = run.find("w:rPr", NS)
        direct_bold = rpr.find("w:b", NS) if rpr is not None else None
        r_style = rpr.find("w:rStyle", NS) if rpr is not None else None
        if direct_bold is not None:
            bold = val_is_true(direct_bold)
        elif r_style is not None:
            bold = style_bold.get(attr(r_style, "val", "") or "", p_style_bold)
        else:
            bold = p_style_bold
        runs.append(Run(text=text, bold=bold, run_index=run_index))
    return Paragraph(index, "".join(r.text for r in runs), runs, location)


def iter_paragraphs(parent: ET.Element, prefix: str = "body") -> Iterable[tuple[ET.Element, str]]:
    """Yield paragraphs in document order, including paragraphs inside tables."""
    for child_index, child in enumerate(list(parent)):
        if child.tag == W + "p":
            yield child, f"{prefix}.p{child_index}"
        elif child.tag == W + "tbl":
            for row_index, row in enumerate(child.findall("w:tr", NS)):
                for cell_index, cell in enumerate(row.findall("w:tc", NS)):
                    yield from iter_paragraphs(cell, f"{prefix}.tbl{child_index}.r{row_index}.c{cell_index}")


def parse_docx(path: Path) -> list[Paragraph]:
    with zipfile.ZipFile(path) as archive:
        document_xml = archive.read("word/document.xml")
        styles_xml = archive.read("word/styles.xml") if "word/styles.xml" in archive.namelist() else None
    root = ET.fromstring(document_xml)
    body = root.find("w:body", NS)
    if body is None:
        return []
    style_bold = build_style_bold_map(styles_xml)
    paragraphs: list[Paragraph] = []
    for index, (element, location) in enumerate(iter_paragraphs(body)):
        paragraphs.append(parse_paragraph(element, index, location, style_bold))
    return paragraphs


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\u00a0", " ")).strip()


def bold_spans(paragraph: Paragraph) -> list[dict]:
    spans: list[dict] = []
    current: list[Run] = []
    for run in paragraph.runs + [Run("", False, -1)]:
        if run.bold and run.text:
            current.append(run)
        elif current:
            text = clean_text("".join(x.text for x in current))
            if text and re.search(r"[\w\u3400-\u9fff]", text):
                spans.append({
                    "text": text,
                    "run_start": current[0].run_index,
                    "run_end": current[-1].run_index,
                })
            current = []
    return spans


def detect_section(text: str, previous: str = "unknown") -> str:
    for section, pattern in LABELS.items():
        if pattern.search(text):
            return section
    if ANSWER_TOKEN.search(text):
        return "answer"
    if OPTION_START.search(text):
        return "options"
    if previous in {"explanation", "knowledge", "option_analysis"}:
        return previous
    return previous if previous != "unknown" else "stem"


def segment_questions(paragraphs: list[Paragraph]) -> list[dict]:
    starts = [i for i, p in enumerate(paragraphs) if QUESTION_START.match(clean_text(p.text))]
    if not starts and paragraphs:
        starts = [0]
    questions: list[dict] = []
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(paragraphs)
        chunk = paragraphs[start:end]
        if not chunk:
            continue
        question_number = re.match(r"^\s*(\d+)", clean_text(chunk[0].text))
        qid = question_number.group(1) if question_number else str(position + 1)
        current = "stem"
        fields: list[dict] = []
        for para in chunk:
            current = detect_section(clean_text(para.text), current)
            para.section = current
            fields.append({
                "paragraph": para,
                "section": current,
                "text": clean_text(para.text),
            })
        answer = next((x["text"] for x in fields if x["section"] == "answer"), "")
        qtype = "multiple_choice" if "多选" in fields[0]["text"] else "single_choice"
        questions.append({
            "question_id": qid,
            "question_type": qtype,
            "start_paragraph": start,
            "end_paragraph": end - 1,
            "fields": fields,
            "answer": answer,
        })
    return questions


def role_and_rule(text: str, section: str) -> tuple[str, str, str]:
    """Return role, stable rule id, and a conservative synthesis hint."""
    if text in {"具体知识点:", "具体知识点：", "选项分析:", "选项分析："}:
        return "解析标签", "label", "解析结构标签，不作为独立规律。"
    if re.search(r"选项.?[正确错误]|故.?[AB-H]项|因此选", text):
        return "选项排除依据", "method.direct_match", "优先选择与题干场景、责任主体和控制目标直接匹配的选项。"
    if re.search(r"根本|根因|病因|症状|后果|直接源于|不是直接", text):
        return "选项排除依据", "method.root_cause_over_symptom", "区分根因、直接义务与后果，避免把风险症状或间接后果当成题目所问的根本答案。"
    if re.search(r"旨在|关键目标|核心目标|主要目标|监管目标|目标是|目的在于", text) and not re.search(r"应|必须|不得", text):
        return "目的与机制", "method.goal_vs_means", "区分监管目标与实现手段，题目问目标时优先选择直接目标。"
    if re.search(r"危险信号|可疑|异常|风险|红旗|不一致|缺乏|突然|频繁|重复|不符合|无合理|高风险", text):
        return "风险触发或危险信号", "control.risk_trigger", "将异常、不一致、缺乏合理业务背景或与历史模式不符的行为作为风险触发信号，结合整体情境判断。"
    if re.search(r"应当|应该|必须|不得|需要|采取|提交|报告|识别|核实|进一步调查|监测|保存|记录|审批|暂停|退出|拒绝|获取|评估|共享|合作|尽职调查|KYC|CDD|EDD|SAR|STR|CTR", text):
        if re.search(r"报告|SAR|STR|CTR|提交", text):
            return "合规义务/动作", "control.monitor_report", "发现相关风险或异常信号时，应按适用程序调查、监测、报告或升级，并保留依据。"
        if re.search(r"KYC|CDD|EDD|尽职调查|客户|受益所有人|身份|所有者", text):
            return "合规义务/动作", "control.kyc_edd", "建立或维持业务关系前，应识别客户、受益所有人及关联风险，并按风险程度采取尽调或强化尽调。"
        if re.search(r"保存|记录|期限|批准|授权|独立", text):
            return "合规义务/动作", "control.record_governance", "合规动作应由相应责任主体按授权和留痕要求执行，满足记录、审批或独立性要求。"
        return "合规义务/动作", "control.risk_based_action", "当触发条件或风险特征出现时，责任主体应采取与风险相称的识别、调查、监测或控制措施。"
    if re.search(r"\d+(?:\.\d+)?\s*(?:年|天|小时|美元|欧元|元|万|千|%|次|笔)|金额|门槛|阈值|期限|至少|超过|低于", text):
        return "阈值、期限或例外", "control.threshold_exception", "涉及金额、期限、比例或法定门槛时，按明确阈值及适用例外判断，避免绝对化推断。"
    if re.search(r"FATF|AMLD|集团|组织|指令|法案|备忘录|委员会|金融情报机构|政治公众人物", text) and len(text) <= 80:
        return "仅属专有名词或单题事实", "fact.local", "该片段优先保留为术语或局部事实，不能仅凭一次出现上升为跨题库一般规律。"
    if section == "option_analysis":
        return "选项排除依据", "method.context_match", "根据题干限定、责任主体和风险控制目标核对选项，不脱离场景作绝对判断。"
    return "仅属专有名词或单题事实", "fact.local", "暂按单题事实保留，待跨题证据支持后再提升为一般规律。"


def chapter_from_filename(name: str) -> str:
    match = re.match(r"(\d+(?:\.\d+)?)", name)
    return match.group(1) if match else "unknown"


def quality_flags(text: str, role: str) -> list[str]:
    """Flag historical formatting patterns that should not be copied blindly."""
    flags: list[str] = []
    if len(text) > 120:
        flags.append("historical_overbold")
    if len(text) <= 8 and role in {"合规义务/动作", "风险触发或危险信号", "阈值、期限或例外"}:
        flags.append("historical_underbold")
    if role == "风险触发或危险信号" and re.search(r"联系执法|提交.*报告|保存|审查.*传票|遵守|批准|调查", text):
        flags.append("role_confusion")
    if role == "合规义务/动作" and re.search(r"风险信号|红旗标志|声誉风险", text):
        flags.append("role_confusion")
    if re.search(r"FATF|FinCEN|AMLD|OFAC|31\s*CFR|第\s*\d+\s*条|建议\s*\d+|透明国际|排名|报告指出", text):
        flags.append("needs_verification")
    return sorted(set(flags))


def make_evidence(path: Path, paragraphs: list[Paragraph]) -> tuple[list[dict], list[dict]]:
    questions = segment_questions(paragraphs)
    evidence: list[dict] = []
    for question in questions:
        fields = question["fields"]
        for index, field in enumerate(fields):
            para: Paragraph = field["paragraph"]
            for span in bold_spans(para):
                role, rule_id, hint = role_and_rule(span["text"], field["section"])
                flags = quality_flags(span["text"], role)
                context_parts = [x["text"] for x in fields[max(0, index - 1): min(len(fields), index + 2)] if x["text"]]
                evidence.append({
                    "source_file": path.name,
                    "source_path": str(path),
                    "chapter": chapter_from_filename(path.name),
                    "question_id": question["question_id"],
                    "question_type": question["question_type"],
                    "section": field["section"],
                    "bold_text": span["text"],
                    "context": " ".join(context_parts),
                    "paragraph_index": para.paragraph_index,
                    "paragraph_location": para.location,
                    "run_start": span["run_start"],
                    "run_end": span["run_end"],
                    "bold_role": role,
                    "normalized_rule_id": rule_id,
                    "normalized_rule": hint,
                    "evidence_count": 0,
                    "confidence": "high" if rule_id != "fact.local" else "medium",
                    "quality_flags": flags,
                    "exception_note": "v6历史材料；进入v7前需独立核验。",
                })
    return evidence, questions


def aggregate_rules(evidence: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for item in evidence:
        groups[item["normalized_rule_id"]].append(item)
    summaries: list[dict] = []
    for rule_id, items in sorted(groups.items()):
        questions = sorted({f"{x['source_file']}#{x['question_id']}" for x in items})
        chapters = sorted({x["chapter"] for x in items})
        if rule_id == "label":
            status = "结构标签"
        elif rule_id == "fact.local":
            # A local fact must never become a general rule merely because
            # the same boilerplate definition appears in many questions.
            status = "局部规律或单题事实"
        elif len(questions) >= 3 and len(chapters) >= 2:
            status = "跨题库一般规律"
        else:
            status = "局部规律或单题事实"
        summary = {
            "normalized_rule_id": rule_id,
            "status": status,
            "normalized_rule": items[0]["normalized_rule"],
            "evidence_count": len(questions),
            "chapter_count": len(chapters),
            "source_questions": questions,
            "sample_bold_text": [x["bold_text"] for x in items[:8]],
            "roles": sorted({x["bold_role"] for x in items}),
            "exception_note": "单题或单章节内容不提升为一般规律；全部材料均须按v6历史来源另行核验。",
        }
        summaries.append(summary)
        for item in items:
            item["evidence_count"] = len(questions)
    return summaries


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_handbook(path: Path, manifest: dict, summaries: list[dict], evidence: list[dict]) -> None:
    general = [x for x in summaries if x["status"] == "跨题库一般规律"]
    local = [x for x in summaries if x["status"] == "局部规律或单题事实"]
    by_role = Counter(x["bold_role"] for x in evidence)
    lines = [
        "# V6 加粗方法归纳手册",
        "",
        "> 本手册由 v6 归档题库自动提取和归纳生成，仅用于历史研究。任何进入 v7 的内容都必须重新核对教材、法规和当前适用性。",
        "",
        "## 1. 数据范围与证据方法",
        "",
        f"- 文档数：{manifest['document_count']}；题目数：{manifest['question_count']}；加粗证据片段：{manifest['evidence_count']}。",
        "- 来源：原始 DOCX 的 OOXML；保留段落、表格单元格、run 范围和上下文。",
        "- 归纳门槛：至少 3 道题且覆盖至少 2 个章节，才标记为“跨题库一般规律”。",
        "",
        "## 2. 加粗内容分布",
        "",
    ]
    for role, count in by_role.most_common():
        lines.append(f"- {role}：{count} 条")
    lines.extend(["", "## 3. 跨题库一般规律", ""])
    if not general:
        lines.append("当前自动分类没有达到门槛的规律；请先查看证据表并进行人工复核。")
    for index, item in enumerate(general, 1):
        lines.extend([
            f"### 3.{index} {item['normalized_rule_id']}",
            "",
            f"**归纳**：{item['normalized_rule']}",
            f"**证据**：{item['evidence_count']} 道题，覆盖 {item['chapter_count']} 个章节。",
            f"**原文样例**：{'；'.join(item['sample_bold_text'][:5])}",
            "",
        ])
    lines.extend(["## 4. 通用做题判断框架", "", "1. 先判断题目是在问目标、主体、程序、风险、后果还是定义。", "2. 核对选项是否与题干场景、责任主体和控制目标直接匹配。", "3. 区分根因、直接义务、风险症状和后果，避免把间接后果当成答案。", "4. 区分监管目标与实现手段；题目问目标时不以协作平台、技术措施等手段替代目标。", "5. 遇到金额、期限、比例或法定门槛，按明确阈值和例外判断，警惕绝对化表述。", "6. 出现异常、不一致、缺乏合理业务背景或偏离历史模式的情形，应结合整体情境判断风险，并考虑调查、监测、报告或升级。", "", "## 5. 局部规律、单题事实与待核验项", ""])
    lines.append(f"共有 {len(local)} 个局部或单题规则簇，详见 `rule_summary.json` 和 `review_queue.md`；这些内容不应直接泛化。")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_review_queue(path: Path, summaries: list[dict], evidence: list[dict]) -> None:
    local = [x for x in summaries if x["status"] in {"局部规律或单题事实", "结构标签"}]
    lines = [
        "# V6 待核验清单",
        "",
        "> 这是历史材料的审阅队列，不代表事实错误；在任何 v7 使用前应重新核对当前教材、法规和原始出处。",
        "",
        f"- 待复核规则簇：{len(local)}",
        f"- 全部证据片段：{len(evidence)}",
        "",
        "## 规则簇",
        "",
    ]
    for item in local:
        samples = "；".join(item["sample_bold_text"][:3])
        lines.append(f"- `{item['normalized_rule_id']}`：{item['normalized_rule']}（{item['evidence_count']} 道题，{item['chapter_count']} 章；样例：{samples}）")
    lines.extend(["", "## 人工核查重点", "", "- 检查加粗是否为直接格式、字符样式或段落样式继承。", "- 检查题号、答案和解析标签是否被误切分。", "- 对绝对化、金额门槛、期限、法规名称和跨法域内容核对原始依据。", "- 对同一规则在不同题目中的责任主体、触发条件和例外进行对照。", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


ROLE_IDS = {
    "解析标签": "boilerplate_label",
    "选项排除依据": "answer_option_reasoning",
    "合规义务/动作": "control_obligation",
    "风险触发或危险信号": "risk_signal",
    "目的与机制": "goal_or_mechanism",
    "阈值、期限或例外": "threshold_or_exception",
    "仅属专有名词或单题事实": "local_fact",
}


def nonbold_spans(paragraph: Paragraph) -> list[dict]:
    spans: list[dict] = []
    current: list[Run] = []
    for run in paragraph.runs + [Run("", True, -1)]:
        if not run.bold and run.text:
            current.append(run)
        elif current:
            text = clean_text("".join(x.text for x in current))
            if text and len(text) >= 4 and re.search(r"[\w\u3400-\u9fff]", text):
                spans.append({
                    "text": text,
                    "run_start": current[0].run_index,
                    "run_end": current[-1].run_index,
                })
            current = []
    return spans


def make_training_examples(path: Path, paragraphs: list[Paragraph], questions: list[dict], evidence: list[dict]) -> list[dict]:
    """Create observed positive spans and same-paragraph hard negatives for an LLM annotator."""
    examples: list[dict] = []
    for item in evidence:
        if item["normalized_rule_id"] == "label":
            continue
        examples.append({
            "label": "bold",
            "example_type": "observed_positive",
            "annotation_role_id": ROLE_IDS.get(item["bold_role"], "local_fact"),
            "annotation_role": item["bold_role"],
            "text": item["bold_text"],
            "context": item["context"],
            "source_file": item["source_file"],
            "question_id": item["question_id"],
            "section": item["section"],
            "paragraph_index": item["paragraph_index"],
            "run_start": item["run_start"],
            "run_end": item["run_end"],
            "normalized_rule_id": item["normalized_rule_id"],
            "quality_flags": item.get("quality_flags", []),
            "training_tier": "observed_only" if item.get("quality_flags") else "gold_candidate",
        })
    for question in questions:
        fields = question["fields"]
        for index, field in enumerate(fields):
            if field["section"] not in {"explanation", "knowledge", "option_analysis"}:
                continue
            para: Paragraph = field["paragraph"]
            text = clean_text(para.text)
            if not text or text in {"具体知识点:", "具体知识点：", "选项分析:", "选项分析："}:
                continue
            spans = nonbold_spans(para)
            if not spans:
                continue
            context_parts = [x["text"] for x in fields[max(0, index - 1): min(len(fields), index + 2)] if x["text"]]
            for span in spans[:3]:
                examples.append({
                    "label": "do_not_bold",
                    "example_type": "same_paragraph_hard_negative",
                    "annotation_role_id": "none",
                    "annotation_role": "普通连接、背景或非答案承载内容",
                    "text": span["text"],
                    "context": " ".join(context_parts),
                    "source_file": path.name,
                    "question_id": question["question_id"],
                    "section": field["section"],
                    "paragraph_index": para.paragraph_index,
                    "run_start": span["run_start"],
                    "run_end": span["run_end"],
                    "normalized_rule_id": "none",
                    "quality_flags": [],
                    "training_tier": "gold_candidate",
                })
    return examples


def write_annotation_taxonomy(path: Path) -> None:
    taxonomy = {
        "purpose": "让LLM对已有反洗钱题目解析进行最小必要加粗，不改写原文、不把整段解析装饰化。",
        "decision_order": [
            "先排除结构标签、题号、选项字母、引用元数据和纯背景连接句。",
            "再寻找直接支撑正确选项的最小完整命题。",
            "如果包含责任主体、义务模态词和控制动作，标为control_obligation。",
            "如果包含可观察异常、红旗或风险触发条件，标为risk_signal。",
            "如果题干直接考定义、职责、阶段、组成或答案区分属性，标注最小必要命题；名称本身不自动加粗。",
            "如果包含定义的必要属性、监管目标、机制链条或因果关键点，标为goal_or_mechanism或local_fact。",
            "如果包含金额、比例、期限、门槛或例外条件，连同必要限定词一起标为threshold_or_exception。",
            "程序动作（审查、联系执法、提交报告、保存记录）归control_obligation，不归risk_signal。",
            "法规、年份、排名、金额或外部报告先标needs_verification，核验后才能进入gold。",
            "若解释在比较根因、症状和后果，标出决定答案的根因或直接义务，而不是所有后果。",
        ],
        "roles": [
            {"id": "answer_option_reasoning", "include": "直接解释为什么正确选项匹配题干，或为什么干扰项不匹配。", "exclude": "只加粗“ A选项正确/错误”这种标签，不单独加粗。"},
            {"id": "control_obligation", "include": "责任主体 + 应/必须/不得/需要 + 动作；保留动作的必要对象或触发条件。", "exclude": "不把泛泛的合规口号或动作后的长篇例子全部加粗。"},
            {"id": "risk_signal", "include": "异常、不一致、无合理业务背景、突然变化、重复、频繁、红旗等可观察信号。", "exclude": "没有情境支撑的抽象“风险”二字。"},
            {"id": "goal_or_mechanism", "include": "题目所问的直接目标、定义的核心属性或解释答案所需的因果机制。", "exclude": "把实现手段、平台名称或普通连接词当成目标。"},
            {"id": "threshold_or_exception", "include": "金额、比例、期限、频率、法定门槛和例外，连同必要单位和限定词。", "exclude": "孤立的法规编号、年份或与判断无关的数字。"},
            {"id": "local_fact", "include": "只有单题或单一法域成立的术语、机构名称、法条和事实。", "exclude": "不能仅因反复出现就提升为通用标注规则。"},
        ],
        "format_rules": [
            "保持原文字符、顺序和标点不变，只在原文外包裹Markdown加粗标记。",
            "以最小完整语义单元为边界；优先加粗短语或单句，不默认整段加粗。",
            "条件和动作不可拆开：例如“发现异常交易”与“应调查/报告”若共同构成答案依据，应整体加粗。",
            "数字必须与单位、比较关系和必要限定词绑定，例如“至少90天”“低于报告门槛”。",
            "同一解析中重复出现的同一事实只保留最能支撑答案的一处。",
            "专有名词、机构名和局部事实默认不加粗；若题干直接考其定义、职责、阶段或组成，只加粗最小必要命题，不加粗名称本身。",
            "条件—主体—动作—目的/后果是可选绑定链：优先保留条件、主体、义务模态、动作和必要阈值；目的与后果只有在改变答案判断时才追加。",
            "程序动作与风险信号分离：‘联系执法部门’是动作，‘缺乏完整付款人信息’才是风险信号。",
            "历史过标、历史漏标、角色混淆和未核验引用只作为纠错样本，不直接作为gold正例。",
            "不得加粗解析标签“具体知识点”“选项分析”、答案字母、纯引用、普通过渡语和无答案贡献的例子。",
            "不确定时宁可少加粗；每个加粗片段都必须能回答“它为什么帮助判定答案”。",
        ],
        "output_contract": {
            "input": "包含题干、选项、答案和解析的原文。",
            "output": "原文的最小改动版本，仅新增成对的**加粗标记**。",
            "optional_audit": "同时返回每个加粗片段的role、触发理由和置信度，供人工复核。",
        },
    }
    path.write_text(json.dumps(taxonomy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_annotation_spec(path: Path, manifest: dict, training_examples: list[dict]) -> None:
    positives = sum(x["label"] == "bold" for x in training_examples)
    negatives = sum(x["label"] == "do_not_bold" for x in training_examples)
    lines = [
        "# LLM 解析加粗标注规范",
        "",
        "> 目标：让模型对已有解析做最小必要加粗，而不是重写解析或把所有知识点装饰成粗体。本文档是从 V6 原始 DOCX 的加粗实例归纳出的标注政策；V6 内容本身仍需独立核验。",
        "",
        "## 一、标注任务定义",
        "",
        "输入是已有题目解析，输出必须保留原文，只新增 `**...**`。每一个加粗片段都必须承担至少一个功能：直接支撑答案、表达合规义务、指出风险信号、给出核心定义/机制，或锁定阈值和例外。",
        "",
        "## 二、决策树",
        "",
        "1. 先排除 `具体知识点`、`选项分析`、答案字母、题号、引用元数据、普通过渡语和无答案贡献的例子。",
        "2. 找出直接回答题干的最小完整命题；优先标注“为什么正确/错误”，不要只标注“ A选项正确”。",
        "3. 若文本是“主体 + 应/必须/不得 + 动作”，标注完整义务单元；必要时把触发条件和动作一起保留。",
        "4. 若文本描述异常、不一致、重复、频繁、突然变化或缺乏合理业务背景，标注风险信号及其必要限定。",
        "5. 若题干直接考定义、职责、阶段或组成，标注最小必要的定义/职责命题，不自动标注术语名称本身。",
        "6. 若文本给出监管目标或因果机制，标注能区分该概念并直接支撑答案的核心部分。",
        "7. 若文本出现金额、比例、期限、频率、门槛或例外，连同数字、单位、比较关系和限定词一起标注。",
        "8. 程序动作（审查、联系执法、提交报告、保存记录）归为控制动作，不归为风险信号。",
        "9. 若文本比较根因、症状和后果，只标注决定选项的根因或直接义务，不把整条后果链全部标粗。",
        "10. 每个片段都用“它是否改变答案判断？”复核；不能改变判断的内容不加粗。",
        "",
        "## 三、边界规则",
        "",
        "- 最小语义单元优先：不跨越无关例子、重复解释或整段背景。",
        "- 条件与动作绑定：不能只加粗“应当报告”而漏掉题干中的触发条件，也不能只加粗风险现象而漏掉决定性的控制动作。",
        "- 数字与限定绑定：例如 `至少90天`、`低于报告门槛`、`超过1万美元`不能拆散。",
        "- 专有名词、机构名和局部事实默认不加粗；定义题、职责题、阶段题允许标注其最小必要命题，但不单独标注名称。",
        "- 完整单元优先采用 `[适用条件] + [责任主体] + [义务模态] + [控制动作] + [必要阈值/期限]`；目的和后果只有改变答案判断时才追加。",
        "- 法规、年份、排名、金额和外部报告先进入 `needs_verification`，核验后才能进入 gold。",
        "- 历史过标、历史漏标和角色混淆只作为纠错样本，不直接复制。",
        "- 不确定时少加粗；宁可漏掉边缘背景，也不要把普通叙述误标为答案依据。",
        "",
        "## 四、从 V6 得到的标注类别",
        "",
        "| 类别 | 何时加粗 | 典型排除项 |",
        "|---|---|---|",
        "| `answer_option_reasoning` | 直接说明正确项匹配或干扰项不匹配的命题 | 只有“ A项正确/错误” |",
        "| `control_obligation` | 主体、义务模态词和控制动作 | 泛泛口号、无关例子 |",
        "| `risk_signal` | 可观察异常或红旗及必要情境 | 孤立的“风险”二字 |",
        "| `goal_or_mechanism` | 直接目标、定义核心属性、关键因果机制 | 仅实现手段或平台名称 |",
        "| `threshold_or_exception` | 金额、期限、比例、门槛和例外 | 无判断作用的年份/编号 |",
        "| `local_fact` | 单题或单法域事实，在审计时可标注 | 不得自动泛化为通用规则 |",
        "",
        "## 五、训练材料统计",
        "",
        f"- 源文档：{manifest['document_count']} 份；题目：{manifest['question_count']} 道。",
        f"- 观察到的正例：{positives} 条；同段落非加粗难负例：{negatives} 条。",
        f"- 未被历史噪声标记的候选 gold 正例：{sum(x['label'] == 'bold' and x.get('training_tier') == 'gold_candidate' for x in training_examples)} 条。",
        "- 正例保留原始文件、题号、段落和 run 范围；负例来自同一解析段落的非加粗文本，用于学习边界。",
        "- 数据分三层使用：历史观察层（全量）、纠错层（过标/漏标/角色混淆/待核验）和人工 gold 层（复核后）。",
        "",
        "机器可读的类别和决策顺序见 `annotation_taxonomy.json`；训练样本见 `llm_bold_training_examples.jsonl`。",
        "",
        "## 六、建议的模型输出格式",
        "",
        "默认只返回原文加粗后的文本；内部审计模式可额外返回 `span`、`role`、`reason`、`confidence`。不要改变原文，不要新增解释，不要使用整段粗体替代片段选择。",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_prompt_template(path: Path) -> None:
    lines = [
        "# LLM 解析加粗提示词模板",
        "",
        "## System",
        "",
        "你是反洗钱考试解析的加粗标注器。你的任务是对已有解析做最小必要加粗，不改写、不补充事实、不删除原文。输出必须保留原文顺序和字符，只新增成对的 Markdown `**` 标记。",
        "",
        "加粗的唯一标准是：该片段是否直接帮助读者判断题目答案。优先加粗最小完整语义单元，包括正确项的关键依据、责任主体的义务动作、可观察风险信号、定义核心属性、关键因果机制、金额/期限/门槛/例外。",
        "",
        "必须遵守：",
        "- 不加粗题号、选项字母、`具体知识点`、`选项分析`、普通连接语、纯引用和无答案贡献的例子。",
        "- 不只加粗“ A选项正确/错误”；要加粗其后真正说明原因的命题。",
        "- 条件和动作必须绑定；数字必须和单位、比较关系及限定词绑定。",
        "- 区分根因、症状和后果；只标出决定答案的根因或直接义务。",
        "- 专有名词默认不加粗；定义题、职责题、阶段题可以标注其最小必要命题，但不单独标注名称。",
        "- 程序动作（审查、联系执法、提交报告、保存记录）是控制动作，不是风险信号。",
        "- 法规、年份、排名、金额和外部报告先视为 needs_verification，未经核验不得作为 gold 正例。",
        "- 不确定时少加粗；禁止整段粗体替代片段选择。",
        "",
        "## Runtime Procedure",
        "",
        "1. 从解析中定位答案、具体知识点和选项分析区域。",
        "2. 生成候选片段：答案依据、义务动作、风险信号、定义/机制、阈值/例外。",
        "3. 删除结构标签和普通叙述；把条件、主体、动作、数字与单位合并为最小完整片段。定义题、职责题和阶段题只保留必要命题。",
        "4. 对候选片段逐一询问：删除该片段后，读者是否更难判断正确选项？若否，不加粗。",
        "5. 合并重叠片段，去掉同一解析中的重复标注；长段拆成多个判分单元。",
        "6. 将片段按原始字符位置回写为 `**片段**`，最后检查原文去除 `**` 后完全一致。",
        "",
        "## User Input",
        "",
        "题干：{{question_stem}}",
        "选项：{{options}}",
        "答案：{{answer}}",
        "解析：{{explanation}}",
        "",
        "## Output",
        "",
        "只输出加粗后的完整解析文本，不要输出解释、标签或代码围栏。审计模式下可额外返回 JSON：",
        "```json",
        '{"text":"...", "spans":[{"text":"...", "role":"risk_signal|control_obligation|answer_option_reasoning|goal_or_mechanism|threshold_or_exception|local_fact", "reason":"...", "confidence":0.0}]}',
        "```",
        "",
        "## Validation",
        "",
        "- 去除所有 `**` 后，输出必须与输入解析逐字符一致。",
        "- 不允许嵌套或未闭合的 `**`。",
        "- 每个 span 必须能在原文中找到，且不包含结构标签。",
        "- 同一段落不应把背景、例子和结论全部标粗。",
        "",
        "可用 `llm_bold_training_examples.jsonl` 中的 observed_positive 和 same_paragraph_hard_negative 作为检索式示例。",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def count_structured_questions(structured_dir: Path) -> int | None:
    """Count the existing Markdown question headings when the derived archive is present."""
    if not structured_dir.exists():
        return None
    pattern = re.compile(r"^##\s+第\d+题", re.MULTILINE)
    return sum(len(pattern.findall(path.read_text(encoding="utf-8"))) for path in structured_dir.glob("*.md"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("v6_归档/习题/v6/习题docx"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/v6_加粗方法归纳"))
    parser.add_argument("--structured-dir", type=Path, default=Path("v6_归档/习题/v6/习题结构化"))
    args = parser.parse_args()
    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()
    files = sorted(input_dir.glob("*.docx"))
    if not files:
        raise SystemExit(f"No DOCX files found: {input_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    evidence: list[dict] = []
    training_examples: list[dict] = []
    question_count = 0
    manifest_files: list[dict] = []
    for path in files:
        paragraphs = parse_docx(path)
        file_evidence, questions = make_evidence(path, paragraphs)
        evidence.extend(file_evidence)
        training_examples.extend(make_training_examples(path, paragraphs, questions, file_evidence))
        question_count += len(questions)
        manifest_files.append({
            "source_file": path.name,
            "chapter": chapter_from_filename(path.name),
            "paragraph_count": len(paragraphs),
            "question_count": len(questions),
            "bold_evidence_count": len(file_evidence),
        })
    summaries = aggregate_rules(evidence)
    structured_question_count = count_structured_questions(args.structured_dir.resolve())
    positive_count = sum(x["label"] == "bold" for x in training_examples)
    negative_count = sum(x["label"] == "do_not_bold" for x in training_examples)
    gold_positive_count = sum(x["label"] == "bold" and x.get("training_tier") == "gold_candidate" for x in training_examples)
    flag_counts = Counter(flag for item in evidence for flag in item.get("quality_flags", []))
    manifest = {
        "source_dir": str(input_dir),
        "output_dir": str(output_dir),
        "document_count": len(files),
        "question_count": question_count,
        "evidence_count": len(evidence),
        "training_example_count": len(training_examples),
        "training_positive_count": positive_count,
        "training_negative_count": negative_count,
        "training_gold_positive_count": gold_positive_count,
        "quality_flag_counts": dict(sorted(flag_counts.items())),
        "rule_cluster_count": len(summaries),
        "general_rule_count": sum(x["status"] == "跨题库一般规律" for x in summaries),
        "local_rule_count": sum(x["status"] == "局部规律或单题事实" for x in summaries),
        "structured_question_count": structured_question_count,
        "structured_question_count_match": structured_question_count == question_count if structured_question_count is not None else None,
        "source_note": "V6 archive only; validate independently before any V7 use.",
        "files": manifest_files,
    }
    write_jsonl(output_dir / "bold_evidence.jsonl", evidence)
    write_jsonl(output_dir / "llm_bold_training_examples.jsonl", training_examples)
    (output_dir / "rule_summary.json").write_text(json.dumps(summaries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sample_files = manifest_files[:10]
    validation = {
        "document_count": len(files),
        "question_count": question_count,
        "structured_question_count": structured_question_count,
        "question_count_match": manifest["structured_question_count_match"],
        "evidence_count": len(evidence),
        "training_example_count": len(training_examples),
        "training_positive_count": positive_count,
        "training_negative_count": negative_count,
        "training_gold_positive_count": gold_positive_count,
        "quality_flag_counts": dict(sorted(flag_counts.items())),
        "empty_bold_text_count": sum(not x["bold_text"] for x in evidence),
        "sample_documents": sample_files,
        "sample_document_count": len(sample_files),
        "checks": {
            "all_source_documents_indexed": len(files) == 35,
            "question_segmentation_matches_structured_markdown": manifest["structured_question_count_match"] is True,
            "all_evidence_has_location": all(x["source_file"] and x["paragraph_location"] for x in evidence),
            "all_evidence_has_rule": all(x["normalized_rule_id"] for x in evidence),
            "no_boilerplate_positive_examples": all(x["annotation_role_id"] != "boilerplate_label" for x in training_examples if x["label"] == "bold"),
            "training_examples_have_labels": all(x["label"] in {"bold", "do_not_bold"} for x in training_examples),
            "gold_examples_have_no_quality_flags": all(not x.get("quality_flags") for x in training_examples if x.get("training_tier") == "gold_candidate"),
        },
    }
    (output_dir / "validation_report.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_handbook(output_dir / "method_handbook.md", manifest, summaries, evidence)
    write_review_queue(output_dir / "review_queue.md", summaries, evidence)
    write_annotation_taxonomy(output_dir / "annotation_taxonomy.json")
    write_annotation_spec(output_dir / "llm_bold_annotation_spec.md", manifest, training_examples)
    write_prompt_template(output_dir / "llm_bold_prompt.md")
    print(json.dumps({k: manifest[k] for k in ["document_count", "question_count", "evidence_count", "rule_cluster_count", "general_rule_count", "local_rule_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
