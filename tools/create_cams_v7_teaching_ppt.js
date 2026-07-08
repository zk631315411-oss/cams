const pptxgen = require("pptxgenjs");
const path = require("path");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "CAMS project";
pptx.company = "Shouzheng";
pptx.subject = "CAMS V7 teaching research workflow";
pptx.title = "CAMS V7 教研工作台沟通版";
pptx.lang = "zh-CN";
pptx.theme = {
  headFontFace: "Microsoft YaHei",
  bodyFontFace: "Microsoft YaHei",
  lang: "zh-CN",
};
pptx.defineLayout({ name: "WIDE", width: 13.333, height: 7.5 });
pptx.layout = "WIDE";
pptx.margin = 0;

const C = {
  ink: "1F2933",
  muted: "64748B",
  slate: "334155",
  line: "CBD5E1",
  pale: "F7FAFC",
  panel: "FFFFFF",
  green: "0F766E",
  green2: "14B8A6",
  tealPale: "D9F3F0",
  amber: "F59E0B",
  amberPale: "FEF3C7",
  red: "DC2626",
  redPale: "FEE2E2",
  blue: "2563EB",
  bluePale: "DBEAFE",
  purple: "7C3AED",
  purplePale: "EDE9FE",
  dark: "102A43",
  dark2: "16324F",
  white: "FFFFFF",
};

function addBg(slide, color = C.pale) {
  slide.background = { color };
}

function addFooter(slide, page) {
  slide.addText("依据：技术路线总图.md / CAMSV7 260630 材料", {
    x: 0.55,
    y: 7.12,
    w: 9.7,
    h: 0.18,
    fontFace: "Microsoft YaHei",
    fontSize: 8.5,
    color: "94A3B8",
    margin: 0,
  });
  slide.addText(String(page).padStart(2, "0"), {
    x: 12.25,
    y: 7.02,
    w: 0.55,
    h: 0.22,
    fontSize: 9,
    bold: true,
    color: "94A3B8",
    align: "right",
    margin: 0,
  });
}

function title(slide, text, sub) {
  slide.addText(text, {
    x: 0.55,
    y: 0.36,
    w: 8.9,
    h: 0.45,
    fontSize: 24,
    bold: true,
    color: C.ink,
    margin: 0,
  });
  if (sub) {
    slide.addText(sub, {
      x: 0.56,
      y: 0.86,
      w: 9.6,
      h: 0.28,
      fontSize: 10.5,
      color: C.muted,
      margin: 0,
    });
  }
}

function card(slide, x, y, w, h, opts = {}) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.08,
    fill: { color: opts.fill || C.panel },
    line: { color: opts.line || "E2E8F0", width: 0.8 },
    shadow: opts.shadow
      ? { type: "outer", color: "000000", opacity: 0.08, blur: 1, angle: 45, distance: 1 }
      : undefined,
  });
}

function pill(slide, text, x, y, w, color, fill) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h: 0.32,
    rectRadius: 0.06,
    fill: { color: fill || "FFFFFF" },
    line: { color, width: 0.8 },
  });
  slide.addText(text, {
    x,
    y: y + 0.075,
    w,
    h: 0.12,
    fontSize: 8.8,
    bold: true,
    color,
    align: "center",
    margin: 0,
  });
}

function iconCircle(slide, label, x, y, color, fill) {
  slide.addShape(pptx.ShapeType.ellipse, {
    x,
    y,
    w: 0.42,
    h: 0.42,
    fill: { color: fill },
    line: { color: fill },
  });
  slide.addText(label, {
    x,
    y: y + 0.1,
    w: 0.42,
    h: 0.12,
    fontSize: 9,
    bold: true,
    color,
    align: "center",
    margin: 0,
  });
}

function smallBox(slide, x, y, w, h, header, body, color, fill) {
  card(slide, x, y, w, h, { fill, line: color });
  slide.addText(header, {
    x: x + 0.2,
    y: y + 0.15,
    w: w - 0.4,
    h: 0.25,
    fontSize: 12.5,
    bold: true,
    color,
    margin: 0,
  });
  slide.addText(body, {
    x: x + 0.2,
    y: y + 0.5,
    w: w - 0.4,
    h: h - 0.65,
    fontSize: 9.2,
    color: C.slate,
    breakLine: false,
    valign: "top",
    fit: "shrink",
    margin: 0.02,
  });
}

function arrow(slide, x1, y1, x2, y2, color = C.line) {
  slide.addShape(pptx.ShapeType.line, {
    x: x1,
    y: y1,
    w: x2 - x1,
    h: y2 - y1,
    line: { color, width: 1.3, beginArrowType: "none", endArrowType: "triangle" },
  });
}

function stepBox(slide, x, y, w, h, num, header, body, color, fill) {
  card(slide, x, y, w, h, { fill, line: color });
  iconCircle(slide, num, x + 0.18, y + 0.18, color, "FFFFFF");
  slide.addText(header, {
    x: x + 0.7,
    y: y + 0.2,
    w: w - 0.85,
    h: 0.22,
    fontSize: 11.2,
    bold: true,
    color,
    margin: 0,
  });
  slide.addText(body, {
    x: x + 0.7,
    y: y + 0.52,
    w: w - 0.85,
    h: h - 0.62,
    fontSize: 8.7,
    color: C.slate,
    fit: "shrink",
    margin: 0,
  });
}

// Slide 1
{
  const slide = pptx.addSlide();
  addBg(slide, C.dark);
  slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.333, h: 7.5, fill: { color: C.dark }, line: { color: C.dark } });
  slide.addShape(pptx.ShapeType.rect, { x: 8.65, y: 0, w: 4.7, h: 7.5, fill: { color: C.green }, line: { color: C.green } });
  slide.addText("CAMS V7\n教研工作台沟通版", {
    x: 0.8,
    y: 1.15,
    w: 6.8,
    h: 1.35,
    fontSize: 34,
    bold: true,
    color: C.white,
    breakLine: false,
    fit: "shrink",
    margin: 0,
  });
  slide.addText("以教材为底座，把官方题、解析、答疑都挂回知识点", {
    x: 0.84,
    y: 2.85,
    w: 7.05,
    h: 0.32,
    fontSize: 16,
    color: "D9F3F0",
    margin: 0,
  });
  slide.addText("明天沟通重点：先讲全流程与最终产物，工程细节一笔带过。", {
    x: 0.86,
    y: 3.45,
    w: 6.7,
    h: 0.42,
    fontSize: 13,
    color: "B6E6DF",
    margin: 0,
  });
  const mini = [
    ["教材", "句卡"],
    ["V7题", "绑定"],
    ["解析", "复核"],
    ["答疑", "沉淀"],
  ];
  mini.forEach((r, i) => {
    const y = 1.15 + i * 1.08;
    card(slide, 9.15, y, 1.3, 0.56, { fill: "FFFFFF", line: "FFFFFF" });
    slide.addText(r[0], { x: 9.15, y: y + 0.17, w: 1.3, h: 0.14, fontSize: 10, bold: true, color: C.green, align: "center", margin: 0 });
    arrow(slide, 10.55, y + 0.28, 11.18, y + 0.28, "B6E6DF");
    card(slide, 11.35, y, 1.3, 0.56, { fill: C.amberPale, line: C.amberPale });
    slide.addText(r[1], { x: 11.35, y: y + 0.17, w: 1.3, h: 0.14, fontSize: 10, bold: true, color: "92400E", align: "center", margin: 0 });
  });
  slide.addText("260630", { x: 0.86, y: 6.6, w: 1.3, h: 0.18, fontSize: 10, color: "94A3B8", margin: 0 });
}

// Slide 2
{
  const slide = pptx.addSlide();
  addBg(slide);
  title(slide, "先把口径对齐", "教研需要先理解“系统如何产生价值”，不是先听脚本和字段。");
  smallBox(slide, 0.65, 1.55, 3.75, 3.7, "一句话定位", "这不是单纯让 AI 写解析，而是以教材为中心，把 V7 官方题、解析、学生答疑都关联回教材知识点的教研工作台。", C.green, C.tealPale);
  smallBox(slide, 4.8, 1.55, 3.75, 3.7, "第一阶段目标", "先服务 V7 官方题库：题目整理、证据绑定、候选解析、教研复核、上架。标准是短、准、能回到知识点。", C.blue, C.bluePale);
  smallBox(slide, 8.95, 1.55, 3.75, 3.7, "AI 的边界", "AI 负责证据寻找和候选答案/解析生成；教研负责判断证据是否合适、解析是否准确、内容是否值得沉淀。", C.amber, C.amberPale);
  pill(slide, "明天讲法：先全流程，再看最终产物，最后确认教研拍板点", 3.0, 6.05, 7.35, C.green, "FFFFFF");
  addFooter(slide, 2);
}

// Slide 3
{
  const slide = pptx.addSlide();
  addBg(slide, "FFFFFF");
  title(slide, "全流程总图", "三条输入流都回到同一个教材证据底座：教材句卡与知识点。");
  const y1 = 1.35, y2 = 3.0, y3 = 4.65;
  stepBox(slide, 0.55, y1, 2.1, 0.92, "1", "教材 PDF", "MinerU + 清洗\n结构化 Markdown", C.green, C.tealPale);
  stepBox(slide, 3.05, y1, 2.1, 0.92, "2", "教材句卡", "5199 张\n可追溯原文证据", C.green, "EFFCFB");
  stepBox(slide, 5.55, y1, 2.1, 0.92, "3", "教材知识图谱", "知识点 / 法规 / 风险\n关系与句卡挂载", C.green, C.tealPale);

  stepBox(slide, 0.55, y2, 2.1, 0.92, "A", "V7 官方题库", "题干 / 选项 / 答案\n结构化入库", C.blue, C.bluePale);
  stepBox(slide, 3.05, y2, 2.1, 0.92, "B", "题目-选项-句卡绑定", "检索教材证据\n输出 q_{id}.json", C.blue, "EFF6FF");
  stepBox(slide, 5.55, y2, 2.1, 0.92, "C", "AI 候选解析", "候选答案\n正确/错误项解释", C.blue, C.bluePale);
  stepBox(slide, 8.05, y2, 2.1, 0.92, "D", "教研复核", "证据、解析、易错点\n人工定稿", C.amber, C.amberPale);
  stepBox(slide, 10.55, y2, 2.1, 0.92, "E", "上架与反馈", "解析上线\n用户反馈再迭代", C.amber, "FFF7ED");

  stepBox(slide, 0.55, y3, 2.1, 0.92, "α", "学生答疑", "问题 / 对应题目\n结构化记录", C.purple, C.purplePale);
  stepBox(slide, 3.05, y3, 2.1, 0.92, "β", "候选答疑", "基于题目与教材证据\n生成初稿", C.purple, "F5F3FF");
  stepBox(slide, 5.55, y3, 2.1, 0.92, "γ", "是否沉淀", "有代表性才回挂\n避免知识库变乱", C.purple, C.purplePale);
  stepBox(slide, 8.05, y3, 2.1, 0.92, "δ", "反哺教研", "易错点 / FAQ\n解析优化", C.purple, "F5F3FF");

  [[2.65, y1+0.46, 3.04, y1+0.46], [5.15, y1+0.46, 5.54, y1+0.46], [2.65, y2+0.46, 3.04, y2+0.46], [5.15, y2+0.46, 5.54, y2+0.46], [7.65, y2+0.46, 8.04, y2+0.46], [10.15, y2+0.46, 10.54, y2+0.46], [2.65, y3+0.46, 3.04, y3+0.46], [5.15, y3+0.46, 5.54, y3+0.46], [7.65, y3+0.46, 8.04, y3+0.46]].forEach(a => arrow(slide, ...a, C.line));
  arrow(slide, 6.55, 2.25, 4.35, 2.95, C.green2);
  arrow(slide, 4.1, 3.94, 4.1, 4.62, C.purple);
  slide.addText("工程细节可以一句话带过：底层已把教材拆成可追溯句卡，并用检索 + 裁判生成每题绑定过程。", {
    x: 0.65,
    y: 6.22,
    w: 11.4,
    h: 0.26,
    fontSize: 10.8,
    color: C.muted,
    margin: 0,
  });
  addFooter(slide, 3);
}

// Slide 4
{
  const slide = pptx.addSlide();
  addBg(slide);
  title(slide, "最终产物：一题一份可复核解析包", "技术主产物是 q_{id}.json；教研看到的应是可读的题目解析包。");
  card(slide, 0.7, 1.25, 5.25, 5.15, { fill: "FFFFFF", line: "CBD5E1", shadow: true });
  slide.addText("示例：第 N 题解析包", { x: 1.05, y: 1.55, w: 3.8, h: 0.25, fontSize: 17, bold: true, color: C.ink, margin: 0 });
  pill(slide, "主产物：output/questions/q_{id}.json", 1.05, 2.0, 3.1, C.green, C.tealPale);
  const rows = [
    ["题目与答案", "题干、选项、标准答案、题型"],
    ["教材证据", "每个选项对应的强证据 / 候选句卡"],
    ["AI 候选解析", "候选答案、正确项说明、错误项解释"],
    ["知识点位置", "教材章节、句卡、知识图谱节点"],
    ["复核标记", "证据不足、分歧、多 direct 冲突"],
  ];
  rows.forEach((r, i) => {
    const y = 2.55 + i * 0.62;
    slide.addShape(pptx.ShapeType.rect, { x: 1.05, y, w: 0.12, h: 0.36, fill: { color: i % 2 ? C.blue : C.green }, line: { color: i % 2 ? C.blue : C.green } });
    slide.addText(r[0], { x: 1.3, y: y + 0.04, w: 1.3, h: 0.16, fontSize: 10.8, bold: true, color: C.ink, margin: 0 });
    slide.addText(r[1], { x: 2.65, y: y + 0.04, w: 2.75, h: 0.16, fontSize: 9.6, color: C.slate, margin: 0 });
  });

  smallBox(slide, 6.45, 1.25, 2.85, 1.55, "解析标准", "短、准、能回到知识点；不写教材扩写，也不只写“答案是 A”。", C.green, C.tealPale);
  smallBox(slide, 9.65, 1.25, 2.85, 1.55, "证据标准", "每个关键判断尽量能回到教材句卡；弱证据和缺证据要显式标记。", C.blue, C.bluePale);
  smallBox(slide, 6.45, 3.1, 2.85, 1.55, "复核标准", "AI 候选答案只是候选；教研确认后才进入正式解析。", C.amber, C.amberPale);
  smallBox(slide, 9.65, 3.1, 2.85, 1.55, "沉淀标准", "有代表性的错误项、答疑、易错点沉淀回知识点。", C.purple, C.purplePale);
  slide.addText("教研最终不需要看 JSON 字段，而是看一份能审核、能改、能上架的题目解析包。", {
    x: 6.45,
    y: 5.42,
    w: 5.8,
    h: 0.38,
    fontSize: 14,
    bold: true,
    color: C.ink,
    margin: 0,
  });
  addFooter(slide, 4);
}

// Slide 5
{
  const slide = pptx.addSlide();
  addBg(slide, "FFFFFF");
  title(slide, "教研需要介入的地方", "系统越自动，越要把人工判断入口设计清楚。");
  const leftX = 0.8, rightX = 7.0;
  slide.addText("AI 先做", { x: leftX, y: 1.25, w: 2.0, h: 0.28, fontSize: 18, bold: true, color: C.green, margin: 0 });
  slide.addText("教研拍板", { x: rightX, y: 1.25, w: 2.0, h: 0.28, fontSize: 18, bold: true, color: C.amber, margin: 0 });
  const ai = [
    ["找教材证据", "从句卡和知识图谱中召回候选依据"],
    ["生成候选答案", "基于证据判断选项对错"],
    ["写候选解析", "解释正确项、错误项和疑似误区"],
    ["标记风险", "缺证据、答案分歧、证据冲突"],
  ];
  const human = [
    ["证据是否合适", "这张句卡能不能支撑这个选项"],
    ["解析是否准确", "是否短、准、讲到学生会错的点"],
    ["知识点怎么命名", "章节名、知识点名、考点名的口径"],
    ["是否值得沉淀", "答疑/易错点是否回挂教材"],
  ];
  ai.forEach((r, i) => stepBox(slide, leftX, 1.75 + i * 1.05, 4.65, 0.72, String(i + 1), r[0], r[1], C.green, C.tealPale));
  human.forEach((r, i) => stepBox(slide, rightX, 1.75 + i * 1.05, 4.65, 0.72, String(i + 1), r[0], r[1], C.amber, C.amberPale));
  arrow(slide, 5.62, 3.63, 6.82, 3.63, C.line);
  slide.addText("核心原则：AI 给候选，教研定结论。", {
    x: 3.55,
    y: 6.25,
    w: 6.1,
    h: 0.35,
    fontSize: 17,
    bold: true,
    color: C.ink,
    align: "center",
    margin: 0,
  });
  addFooter(slide, 5);
}

// Slide 6
{
  const slide = pptx.addSlide();
  addBg(slide);
  title(slide, "明天建议直接确认的 5 件事", "把沟通从“系统介绍”推进到“样板怎么跑、怎么验收”。");
  const items = [
    ["解析模板", "是否固定为：考什么 / 为什么正确 / 为什么错误 / 对应知识点 / 易错点"],
    ["长度标准", "每题解析控制在多少字；单选、多选、判断题是否不同"],
    ["知识点口径", "用教材章节、KG 节点，还是教研确认后的考点名"],
    ["复核方式", "全量逐题审核、低置信优先审核，还是先抽样校准"],
    ["样板范围", "先选 20-50 道 V7 官方题跑通样板，再批量展开"],
  ];
  items.forEach((it, i) => {
    const x = i < 3 ? 0.75 + i * 4.15 : 2.9 + (i - 3) * 4.15;
    const y = i < 3 ? 1.45 : 4.0;
    smallBox(slide, x, y, 3.55, 1.45, `${i + 1}. ${it[0]}`, it[1], i % 2 ? C.blue : C.green, i % 2 ? C.bluePale : C.tealPale);
  });
  slide.addText("建议收口：先出一批可审核样板，让教研校准模板和证据标准，再批量处理 V7 官方题。", {
    x: 1.35,
    y: 6.28,
    w: 10.7,
    h: 0.32,
    fontSize: 14,
    bold: true,
    color: C.ink,
    align: "center",
    margin: 0,
  });
  addFooter(slide, 6);
}

// Slide 7
{
  const slide = pptx.addSlide();
  addBg(slide, C.dark2);
  slide.addText("如果教研追问工程细节", {
    x: 0.75,
    y: 0.75,
    w: 5.5,
    h: 0.45,
    fontSize: 25,
    bold: true,
    color: C.white,
    margin: 0,
  });
  slide.addText("一笔带过即可，不要让沟通陷进字段和脚本。", {
    x: 0.78,
    y: 1.28,
    w: 5.9,
    h: 0.28,
    fontSize: 12.5,
    color: "B6E6DF",
    margin: 0,
  });
  const facts = [
    ["教材底座", "PDF -> 结构化 Markdown -> 5199 张句卡，句卡可回到教材原文和页码。"],
    ["知识图谱", "已完成教材 KG：节点、关系、句卡挂载，用于导航和辅助召回。"],
    ["题目绑定", "V7 题进来后，主产物是一题一份 q_{id}.json，记录证据寻找全过程。"],
    ["考点沉淀", "考点生成仍是 preview，等题目证据边稳定后再做归并和命名。"],
  ];
  facts.forEach((f, i) => {
    const y = 2.0 + i * 1.05;
    card(slide, 0.82, y, 11.7, 0.72, { fill: i % 2 ? "1E3A5F" : "173B57", line: "2B5876" });
    slide.addText(f[0], { x: 1.18, y: y + 0.22, w: 1.55, h: 0.16, fontSize: 11.5, bold: true, color: "FDE68A", margin: 0 });
    slide.addText(f[1], { x: 2.85, y: y + 0.22, w: 8.8, h: 0.18, fontSize: 10.8, color: "E2E8F0", margin: 0 });
  });
  slide.addText("推荐回应：底层能力已经在支撑“短、准、能回到知识点”的解析生产；明天先确认教研验收标准。", {
    x: 0.82,
    y: 6.45,
    w: 11.2,
    h: 0.3,
    fontSize: 13,
    bold: true,
    color: "FFFFFF",
    margin: 0,
  });
}

const out = path.join(process.cwd(), "CAMS_V7_教研沟通版_流程图.pptx");
pptx.writeFile({ fileName: out });
