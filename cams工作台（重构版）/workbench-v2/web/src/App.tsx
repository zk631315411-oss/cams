import { FormEvent, type ReactNode, useEffect, useState } from "react";
import {
  Archive,
  ArrowDown,
  ArrowUp,
  BookOpen,
  Check,
  ChevronLeft,
  ClipboardCheck,
  Code2,
  Diff,
  ExternalLink,
  FileOutput,
  Filter,
  History,
  ListChecks,
  LoaderCircle,
  LockKeyhole,
  LogOut,
  Menu,
  PanelRightOpen,
  Play,
  Plus,
  RotateCcw,
  Save,
  Search,
  Send,
  ShieldCheck,
  SquarePen,
  X,
} from "lucide-react";
import { api, login, openApiResource, type User } from "./api";

type Option = { label: string; zh: string; en: string };
type Parsed = {
  question_type: string;
  stem_zh: string;
  stem_en: string;
  options: Option[];
  answer_letters: string[];
  exam_point: string;
  core_analysis: string;
  wrong_analysis: string;
  reminder: string;
  evidence_unit_ids: string[];
};
type Version = {
  id: string;
  sequence: number;
  task_id?: string;
  content: Parsed;
  markdown?: string;
  note: string;
  created_at: string;
  structured_changes: Record<string, unknown>;
};
type Position = { section_code: string; ordinal: number; paper_title: string };
type Question = {
  question_id: string;
  status: string;
  needs_attention: boolean;
  stem_zh: string;
  stem_en: string;
  position?: Position;
  current_version_id: string;
  published_version_id?: string;
  primary_cp_id?: string;
  supporting_cp_ids: string[];
  evidence_unit_ids: string[];
  current_version?: Version;
  versions?: Version[];
  active_task?: EditTask;
};
type EditTask = { id: string; owner_id: number; purpose: string; state: string };
type Dashboard = {
  total: number;
  needs_attention: number;
  statuses: Record<string, number>;
  open_locks: number;
  pending_reviews: number;
};

const STATUS_LABELS: Record<string, string> = {
  editing: "编辑中",
  pending_review: "待提交审核",
  in_review: "审核中",
  returned: "退回",
  approved: "已批准",
  published: "已发布",
};

function statusLabel(status: string) {
  return STATUS_LABELS[status] || status;
}

function useHashRoute() {
  const [route, setRoute] = useState(location.hash.slice(1) || "/questions");
  useEffect(() => {
    const listener = () => setRoute(location.hash.slice(1) || "/questions");
    window.addEventListener("hashchange", listener);
    return () => window.removeEventListener("hashchange", listener);
  }, []);
  return route;
}

function IconButton({ label, children, onClick, disabled = false }: { label: string; children: ReactNode; onClick?: () => void; disabled?: boolean }) {
  return (
    <button className="icon-button" title={label} aria-label={label} onClick={onClick} disabled={disabled}>
      {children}
    </button>
  );
}

function Login({ onLogin }: { onLogin: (user: User) => void }) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin-local-only");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      onLogin(await login(username, password));
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="login-shell">
      <form className="login-panel" onSubmit={submit}>
        <div className="brand-mark">C</div>
        <h1>CAMS 教研工作台</h1>
        <p>内容、证据、版本与交付</p>
        <label>账号<input value={username} onChange={(event) => setUsername(event.target.value)} autoFocus /></label>
        <label>密码<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} /></label>
        {error && <div className="error-banner">{error}</div>}
        <button className="primary-button" disabled={busy}>{busy && <LoaderCircle className="spin" size={16} />}登录</button>
      </form>
    </main>
  );
}

function Shell({ user, children, onLogout }: { user: User; children: ReactNode; onLogout: () => void }) {
  const route = useHashRoute();
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigation = [
    ["/questions", "题目工作台", ListChecks],
    ["/reviews", "审核队列", ClipboardCheck],
    ["/releases", "发布批次", FileOutput],
  ] as const;
  return (
    <div className="app-shell">
      <aside className={mobileOpen ? "sidebar open" : "sidebar"}>
        <div className="brand"><div className="brand-mark small">C</div><span>CAMS 工作台</span></div>
        <nav>
          {navigation.map(([href, label, Icon]) => (
            <a key={href} href={`#${href}`} className={route.startsWith(href) ? "active" : ""} onClick={() => setMobileOpen(false)}>
              <Icon size={18} />{label}
            </a>
          ))}
        </nav>
        <div className="user-block">
          <div><strong>{user.username}</strong><span>{user.role}</span></div>
          <IconButton label="退出登录" onClick={onLogout}><LogOut size={17} /></IconButton>
        </div>
      </aside>
      <section className="workspace">
        <header className="mobile-header"><IconButton label="打开导航" onClick={() => setMobileOpen(!mobileOpen)}><Menu size={19} /></IconButton><span>CAMS 工作台</span></header>
        {children}
      </section>
    </div>
  );
}

function DashboardStrip() {
  const [data, setData] = useState<Dashboard | null>(null);
  useEffect(() => { api<Dashboard>("/api/dashboard").then(setData).catch(() => undefined); }, []);
  if (!data) return null;
  return (
    <div className="metric-strip">
      <div><span>题目总数</span><strong>{data.total}</strong></div>
      <div><span>待整理</span><strong className="attention">{data.needs_attention}</strong></div>
      <div><span>待审核</span><strong>{data.pending_reviews}</strong></div>
      <div><span>编辑锁</span><strong>{data.open_locks}</strong></div>
      <div><span>已发布</span><strong>{data.statuses.published || 0}</strong></div>
    </div>
  );
}

function QuestionList() {
  const [items, setItems] = useState<Question[]>([]);
  const [total, setTotal] = useState(0);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [sectionCode, setSectionCode] = useState("");
  const [ordinal, setOrdinal] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  async function load() {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams({ q: query, limit: "100" });
      if (status) params.set("status", status);
      if (sectionCode.trim()) params.set("section_code", sectionCode.trim());
      if (ordinal.trim()) params.set("ordinal", ordinal.trim());
      const result = await api<{ total: number; items: Question[] }>(`/api/questions?${params}`);
      setItems(result.items);
      setTotal(result.total);
    } catch (reason) { setError((reason as Error).message); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, [status]);
  return (
    <main className="page">
      <div className="page-title"><div><h1>题目工作台</h1><p>以永久 ID 管理正式 Markdown 与证据版本</p></div></div>
      <DashboardStrip />
      <div className="toolbar">
        <form className="search-box" onSubmit={(event) => { event.preventDefault(); void load(); }}><Search size={17} /><input placeholder="永久 ID、中文或英文题干" value={query} onChange={(event) => setQuery(event.target.value)} /></form>
        <input className="position-input" aria-label="小节编号" placeholder="小节，如 p3-ch8-h3" value={sectionCode} onChange={(event) => setSectionCode(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") void load(); }} />
        <input className="ordinal-input" aria-label="小节内题号" inputMode="numeric" placeholder="题号" value={ordinal} onChange={(event) => setOrdinal(event.target.value.replace(/\D/g, ""))} onKeyDown={(event) => { if (event.key === "Enter") void load(); }} />
        <div className="select-control"><Filter size={16} /><select value={status} onChange={(event) => setStatus(event.target.value)}><option value="">全部状态</option>{Object.entries(STATUS_LABELS).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></div>
        <span className="result-count">{total} 道</span>
      </div>
      {error && <div className="error-banner">{error}</div>}
      <div className="question-table-wrap">
        <table className="question-table">
          <thead><tr><th>位置</th><th>永久 ID / 题干</th><th>状态</th><th>证据</th><th></th></tr></thead>
          <tbody>
            {loading ? <tr><td colSpan={5} className="empty"><LoaderCircle className="spin" />读取中</td></tr> : items.map((item) => (
              <tr key={item.question_id}>
                <td className="position-cell">{item.position ? <><strong>{item.position.section_code}</strong><span>第 {item.position.ordinal} 题</span></> : <span>未匹配</span>}</td>
                <td><a className="question-link" href={`#/questions/${item.question_id}`}><code>{item.question_id}</code><strong>{item.stem_zh || item.stem_en}</strong><span>{item.stem_en}</span></a></td>
                <td><span className={`status status-${item.status}`}>{statusLabel(item.status)}</span>{item.needs_attention && <span className="warning-label">待整理</span>}</td>
                <td>{item.evidence_unit_ids.length}<span className="muted"> units</span></td>
                <td><a href={`#/questions/${item.question_id}`} className="row-action"><SquarePen size={17} /></a></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}

function Field({ label, value, onChange, rows = 2, disabled = false }: { label: string; value: string; onChange: (value: string) => void; rows?: number; disabled?: boolean }) {
  return <label className="field"><span>{label}</span><textarea rows={rows} value={value} disabled={disabled} onChange={(event) => onChange(event.target.value)} /></label>;
}

function QuestionDetail({ questionId, user }: { questionId: string; user: User }) {
  const [question, setQuestion] = useState<Question | null>(null);
  const [parsed, setParsed] = useState<Parsed | null>(null);
  const [markdown, setMarkdown] = useState("");
  const [advanced, setAdvanced] = useState(false);
  const [task, setTask] = useState<EditTask | null>(null);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [evidenceOpen, setEvidenceOpen] = useState(false);

  async function load() {
    const result = await api<Question>(`/api/questions/${questionId}`);
    setQuestion(result);
    setParsed(result.current_version!.content);
    setMarkdown(result.current_version!.markdown || "");
    setTask(result.active_task?.owner_id === user.id ? result.active_task : null);
  }
  useEffect(() => { load().catch((reason) => setError((reason as Error).message)); }, [questionId]);
  function updateField<K extends keyof Parsed>(key: K, value: Parsed[K]) { setParsed((current) => current ? { ...current, [key]: value } : current); }
  function moveOption(index: number, direction: -1 | 1) {
    if (!parsed) return;
    const target = index + direction;
    if (target < 0 || target >= parsed.options.length) return;
    const correct = new Set(parsed.answer_letters);
    const moved = parsed.options.map((item) => ({ ...item, originalLabel: item.label }));
    [moved[index], moved[target]] = [moved[target], moved[index]];
    const relabeled = moved.map((item, currentIndex) => ({
      label: String.fromCharCode(65 + currentIndex),
      zh: item.zh,
      en: item.en,
      originalLabel: item.originalLabel,
    }));
    updateField("options", relabeled.map(({ originalLabel: _, ...item }) => item));
    updateField("answer_letters", relabeled.filter((item) => correct.has(item.originalLabel)).map((item) => item.label));
  }
  function updateBindings(patch: Partial<Pick<Question, "primary_cp_id" | "supporting_cp_ids" | "evidence_unit_ids">>) {
    setQuestion((current) => current ? { ...current, ...patch } : current);
  }
  async function action(run: () => Promise<void>) {
    setBusy(true); setError(""); setNotice("");
    try { await run(); } catch (reason) { setError((reason as Error).message); } finally { setBusy(false); }
  }
  async function begin() {
    const purpose = window.prompt("本次修改目的", "人工核对与修订");
    if (!purpose) return;
    await action(async () => { const value = await api<EditTask>(`/api/questions/${questionId}/tasks`, { method: "POST", body: JSON.stringify({ purpose }) }); setTask(value); setNotice("已取得题目锁"); });
  }
  async function save() {
    if (!task || !parsed) return;
    await action(async () => {
      const content_patch = advanced ? { markdown } : { fields: parsed };
      await api(`/api/questions/${questionId}/save`, { method: "POST", body: JSON.stringify({ task_id: task.id, content_patch, bindings_patch: { primary_cp_id: question?.primary_cp_id || null, supporting_cp_ids: question?.supporting_cp_ids || [], evidence_unit_ids: question?.evidence_unit_ids || [] }, note: "工作台保存" }) });
      await load(); setNotice("已创建不可变版本");
    });
  }
  async function finish() {
    if (!task) return;
    await action(async () => { await api(`/api/tasks/${task.id}/finish`, { method: "POST", body: JSON.stringify({ summary: "工作台编辑完成" }) }); setTask(null); await load(); setNotice("编辑任务已结束，尚未提交审核"); });
  }
  async function submitReview() {
    await action(async () => { await api(`/api/questions/${questionId}/submit-review`, { method: "POST", body: JSON.stringify({ comment: "请审核当前版本" }) }); await load(); setNotice("已提交审核"); });
  }
  if (!question || !parsed) return <main className="page empty"><LoaderCircle className="spin" />读取题目</main>;
  return (
    <main className="detail-page">
      <div className="detail-header">
        <a href="#/questions" className="back-link"><ChevronLeft size={18} />题目列表</a>
        <div className="detail-title"><div><code>{question.question_id}</code><h1>{question.stem_zh}</h1></div><span className={`status status-${question.status}`}>{statusLabel(question.status)}</span></div>
        <div className="detail-actions">
          <div className="segmented"><button className={!advanced ? "active" : ""} onClick={() => setAdvanced(false)}><SquarePen size={15} />结构化</button><button className={advanced ? "active" : ""} onClick={() => setAdvanced(true)}><Code2 size={15} />Markdown</button></div>
          <IconButton label="查看差异" onClick={() => { location.hash = `#/diff/${questionId}`; }}><Diff size={18} /></IconButton>
          <IconButton label="版本历史" onClick={() => { location.hash = `#/history/${questionId}`; }}><History size={18} /></IconButton>
          <IconButton label="打开证据面板" onClick={() => setEvidenceOpen(!evidenceOpen)}><PanelRightOpen size={18} /></IconButton>
          {!task && question.status !== "pending_review" && question.status !== "in_review" && <button className="secondary-button" onClick={begin}><LockKeyhole size={16} />开始编辑</button>}
          {task && <><button className="secondary-button" onClick={save} disabled={busy}><Save size={16} />保存版本</button><button className="primary-button" onClick={finish} disabled={busy}><Check size={16} />结束任务</button></>}
          {!task && ["editing", "returned"].includes(question.status) && <button className="primary-button" onClick={submitReview}><Send size={16} />提交审核</button>}
        </div>
      </div>
      {(error || notice) && <div className={error ? "error-banner content-banner" : "success-banner content-banner"}>{error || notice}</div>}
      <div className={evidenceOpen ? "detail-layout evidence-visible" : "detail-layout"}>
        <section className="editor-surface">
          <div className="context-line"><span>{question.position ? `${question.position.section_code} · 第 ${question.position.ordinal} 题` : "暂无位置快照"}</span><span>版本 {question.current_version?.sequence}</span>{task && <span className="lock-indicator"><LockKeyhole size={13} />本题已锁定</span>}</div>
          {advanced ? <textarea className="markdown-editor" value={markdown} onChange={(event) => setMarkdown(event.target.value)} disabled={!task} spellCheck={false} /> : (
            <div className="structured-editor">
              <div className="language-grid"><Field label="中文题干" value={parsed.stem_zh} disabled={!task} onChange={(value) => updateField("stem_zh", value)} /><Field label="English stem" value={parsed.stem_en} disabled={!task} onChange={(value) => updateField("stem_en", value)} /></div>
              <div className="section-heading"><h2>选项与答案</h2><span>option_id 在底层保持稳定</span></div>
              <div className="options-editor">
                {parsed.options.map((option, index) => <div className="option-row" key={`${option.label}-${index}`}><span className="option-label">{option.label}</span><textarea rows={2} value={option.zh} disabled={!task} onChange={(event) => { const options = [...parsed.options]; options[index] = { ...option, zh: event.target.value }; updateField("options", options); }} /><textarea rows={2} value={option.en} disabled={!task} onChange={(event) => { const options = [...parsed.options]; options[index] = { ...option, en: event.target.value }; updateField("options", options); }} /><div className="option-tools"><IconButton label="上移选项" disabled={!task || index === 0} onClick={() => moveOption(index, -1)}><ArrowUp size={14} /></IconButton><IconButton label="下移选项" disabled={!task || index === parsed.options.length - 1} onClick={() => moveOption(index, 1)}><ArrowDown size={14} /></IconButton></div><label className="answer-check"><input type="checkbox" checked={parsed.answer_letters.includes(option.label)} disabled={!task} onChange={(event) => { const set = new Set(parsed.answer_letters); event.target.checked ? set.add(option.label) : set.delete(option.label); updateField("answer_letters", [...set].sort()); }} /><span>答案</span></label></div>)}
              </div>
              <div className="section-heading"><h2>解析</h2></div>
              <Field label="考点" value={parsed.exam_point} disabled={!task} onChange={(value) => updateField("exam_point", value)} />
              <Field label="核心解析" value={parsed.core_analysis} disabled={!task} onChange={(value) => updateField("core_analysis", value)} rows={8} />
              <Field label="错误项分析" value={parsed.wrong_analysis} disabled={!task} onChange={(value) => updateField("wrong_analysis", value)} rows={8} />
              <Field label="易错提醒" value={parsed.reminder} disabled={!task} onChange={(value) => updateField("reminder", value)} rows={4} />
            </div>
          )}
        </section>
        {evidenceOpen && <EvidencePanel question={question} canEdit={Boolean(task)} onBindingsChange={updateBindings} onClose={() => setEvidenceOpen(false)} />}
      </div>
    </main>
  );
}

type Unit = { unit_id: string; knowledge_zh: string; en_quote: string; pdf_page: number; printed_page: string; section_id: string };
type CorePoint = { core_point_id: string; title_zh: string; title_en: string };
function EvidencePanel({ question, canEdit, onBindingsChange, onClose }: { question: Question; canEdit: boolean; onBindingsChange: (patch: Partial<Question>) => void; onClose: () => void }) {
  const [query, setQuery] = useState("");
  const [units, setUnits] = useState<Unit[]>([]);
  const [corePoints, setCorePoints] = useState<CorePoint[]>([]);
  const [selected, setSelected] = useState<Unit | null>(null);
  async function search() { const result = await api<{ units: Unit[]; core_points: CorePoint[] }>(`/api/evidence/search?q=${encodeURIComponent(query)}`); setUnits(result.units); setCorePoints(result.core_points); }
  useEffect(() => { if (question.evidence_unit_ids[0]) api<Unit>(`/api/evidence/units/${question.evidence_unit_ids[0]}`).then(setSelected).catch(() => undefined); }, []);
  return (
    <aside className="evidence-panel">
      <div className="panel-header"><div><BookOpen size={18} /><strong>教材证据</strong></div><IconButton label="关闭证据面板" onClick={onClose}><X size={18} /></IconButton></div>
      <form className="search-box compact" onSubmit={(event) => { event.preventDefault(); void search(); }}><Search size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="unit、术语或原文" /></form>
      <div className="binding-summary"><span>主 CP</span><code>{question.primary_cp_id || "未绑定"}</code><span>辅助 CP</span><code>{question.supporting_cp_ids.join(", ") || "无"}</code></div>
      <div className="bound-units"><span>当前证据</span>{question.evidence_unit_ids.map((id) => <button key={id} onClick={() => api<Unit>(`/api/evidence/units/${id}`).then(setSelected)}>{id}{canEdit && <X size={10} onClick={(event) => { event.stopPropagation(); onBindingsChange({ evidence_unit_ids: question.evidence_unit_ids.filter((value) => value !== id) }); }} />}</button>)}</div>
      {corePoints.length > 0 && <div className="cp-results">{corePoints.map((cp) => <div key={cp.core_point_id}><button onClick={() => onBindingsChange({ primary_cp_id: cp.core_point_id })} disabled={!canEdit || question.primary_cp_id === cp.core_point_id}>设为主 CP</button><button onClick={() => onBindingsChange({ supporting_cp_ids: [...new Set([...question.supporting_cp_ids, cp.core_point_id])] })} disabled={!canEdit || question.supporting_cp_ids.includes(cp.core_point_id)}>辅助</button><code>{cp.core_point_id}</code><span>{cp.title_zh || cp.title_en}</span></div>)}</div>}
      {units.length > 0 && <div className="unit-results">{units.map((unit) => <button key={unit.unit_id} onClick={() => setSelected(unit)}><code>{unit.unit_id}</code><span>{unit.knowledge_zh}</span></button>)}</div>}
      {selected && <div className="unit-detail"><div className="unit-meta"><code>{selected.unit_id}</code><span>PDF {selected.pdf_page} / 书内 {selected.printed_page}</span></div><p>{selected.knowledge_zh}</p><blockquote>{selected.en_quote}</blockquote><div className="unit-actions"><button className="secondary-button" disabled={!canEdit || question.evidence_unit_ids.includes(selected.unit_id)} onClick={() => onBindingsChange({ evidence_unit_ids: [...question.evidence_unit_ids, selected.unit_id] })}><Plus size={14} />绑定证据</button><a href="#" onClick={(event) => { event.preventDefault(); void openApiResource(`/api/evidence/pages/${selected.pdf_page}.png?language=zh`); }}><ExternalLink size={15} />打开 PDF 原页</a></div></div>}
    </aside>
  );
}

function DiffView({ questionId }: { questionId: string }) {
  const [data, setData] = useState<{ from: Version; to: Version; diff: string } | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { api<{ from: Version; to: Version; diff: string }>(`/api/questions/${questionId}/diff`).then(setData).catch((reason) => setError(reason.message)); }, [questionId]);
  const lines = data?.diff.split("\n") || [];
  return <main className="page"><div className="page-title"><div><a href={`#/questions/${questionId}`} className="back-link"><ChevronLeft size={18} />返回题目</a><h1>版本差异</h1><p>{questionId} · 默认基线到当前版本</p></div></div>{error && <div className="error-banner">{error}</div>}{data && <><div className="compare-bar"><span>v{data.from.sequence}</span><span>→</span><span>v{data.to.sequence}</span></div><pre className="diff-view">{lines.map((line, index) => <span key={index} className={line.startsWith("+") ? "added" : line.startsWith("-") ? "removed" : line.startsWith("@@") ? "hunk" : ""}>{line || " "}</span>)}</pre></>}</main>;
}

function HistoryView({ questionId, user }: { questionId: string; user: User }) {
  const [question, setQuestion] = useState<Question | null>(null);
  useEffect(() => { api<Question>(`/api/questions/${questionId}`).then(setQuestion); }, [questionId]);
  return <main className="page"><div className="page-title"><div><a href={`#/questions/${questionId}`} className="back-link"><ChevronLeft size={18} />返回题目</a><h1>版本历史</h1><p>每次保存均为不可变快照，按任务可合并查看</p></div></div><div className="timeline">{question?.versions?.map((version) => <div className="timeline-item" key={version.id}><div className="timeline-dot" /><div><strong>版本 {version.sequence}</strong><span>{new Date(version.created_at).toLocaleString()} · {version.task_id || "首次导入"}</span><p>{version.note || "无说明"}</p><a href={`#/diff/${questionId}`}>查看差异</a></div></div>)}</div></main>;
}

type Review = { id: string; question_id: string; state: string; submitted_by: number; reviewer_id?: number; comment: string; submitted_at: string };
function ReviewQueue() {
  const [items, setItems] = useState<Review[]>([]);
  const [error, setError] = useState("");
  async function load() { try { setItems(await api<Review[]>("/api/reviews")); } catch (reason) { setError((reason as Error).message); } }
  useEffect(() => { void load(); }, []);
  async function claim(id: string) { try { await api(`/api/reviews/${id}/claim`, { method: "POST" }); await load(); } catch (reason) { setError((reason as Error).message); } }
  async function decide(id: string, decision: "approved" | "returned") { const comment = window.prompt(decision === "approved" ? "批准意见" : "退回原因", "") ?? ""; try { await api(`/api/reviews/${id}/decide`, { method: "POST", body: JSON.stringify({ decision, comment }) }); await load(); } catch (reason) { setError((reason as Error).message); } }
  return <main className="page"><div className="page-title"><div><h1>审核队列</h1><p>编辑人和批准人必须分离</p></div></div>{error && <div className="error-banner">{error}</div>}<div className="review-list">{items.length === 0 ? <div className="empty-state"><ShieldCheck size={28} /><strong>当前没有审核任务</strong></div> : items.map((item) => <article className="review-row" key={item.id}><div><span className={`status status-${item.state}`}>{statusLabel(item.state)}</span><a href={`#/questions/${item.question_id}`}>{item.question_id}</a><p>{item.comment || "未填写送审说明"}</p></div><div className="review-actions">{item.state === "submitted" && <button className="secondary-button" onClick={() => claim(item.id)}><Play size={15} />领取</button>}{item.state === "in_review" && <><button className="danger-button" onClick={() => decide(item.id, "returned")}><RotateCcw size={15} />退回</button><button className="primary-button" onClick={() => decide(item.id, "approved")}><Check size={15} />批准</button></>}</div></article>)}</div></main>;
}

type ReleaseItem = { id: number; question_id: string; publish_state: string; note: string };
type Release = { id: string; title: string; state: string; export_path: string; export_hash: string; created_at: string; items: ReleaseItem[] };
const RELEASE_LABELS: Record<string, string> = { pending_entry: "待录入", entered: "已录入", verified: "已核对", published: "已发布", needs_rework: "需返工" };
function Releases() {
  const [items, setItems] = useState<Release[]>([]);
  const [approved, setApproved] = useState<Question[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [title, setTitle] = useState("");
  const [error, setError] = useState("");
  async function load() { try { setItems(await api<Release[]>("/api/releases")); const q = await api<{ items: Question[] }>("/api/questions?status=approved&limit=200"); setApproved(q.items); } catch (reason) { setError((reason as Error).message); } }
  useEffect(() => { void load(); }, []);
  async function create() { try { await api("/api/releases", { method: "POST", body: JSON.stringify({ title, question_ids: selected }) }); setSelected([]); setTitle(""); await load(); } catch (reason) { setError((reason as Error).message); } }
  async function exportDocx(id: string) { try { await api(`/api/releases/${id}/export`, { method: "POST" }); await load(); } catch (reason) { setError((reason as Error).message); } }
  async function nextState(releaseId: string, item: ReleaseItem, state: string) { try { await api(`/api/releases/${releaseId}/items/${item.id}`, { method: "PATCH", body: JSON.stringify({ state, note: "" }) }); await load(); } catch (reason) { setError((reason as Error).message); } }
  return <main className="page"><div className="page-title"><div><h1>发布批次</h1><p>DOCX 交付与第三方后台人工录入进度</p></div></div>{error && <div className="error-banner">{error}</div>}<section className="release-builder"><div><h2>新建交付批次</h2><p>{approved.length} 道已批准题目可加入</p></div><input placeholder="批次名称" value={title} onChange={(event) => setTitle(event.target.value)} /><div className="approved-picker">{approved.map((question) => <label key={question.question_id}><input type="checkbox" checked={selected.includes(question.question_id)} onChange={(event) => setSelected(event.target.checked ? [...selected, question.question_id] : selected.filter((id) => id !== question.question_id))} /><code>{question.question_id}</code><span>{question.stem_zh}</span></label>)}</div><button className="primary-button" disabled={!title || selected.length === 0} onClick={create}><Plus size={16} />创建批次</button></section><div className="release-list">{items.map((release) => <article className="release-block" key={release.id}><header><div><code>{release.id}</code><h2>{release.title}</h2><span>{new Date(release.created_at).toLocaleString()}</span></div><div>{release.export_path ? <a className="secondary-button" href="#" onClick={(event) => { event.preventDefault(); void openApiResource(`/api/releases/${release.id}/download`, `${release.id}.docx`); }}><FileOutput size={16} />下载 DOCX</a> : <button className="secondary-button" onClick={() => exportDocx(release.id)}><FileOutput size={16} />生成 DOCX</button>}</div></header><div className="release-items">{release.items.map((item) => <div key={item.id}><a href={`#/questions/${item.question_id}`}>{item.question_id}</a><span className={`release-state state-${item.publish_state}`}>{RELEASE_LABELS[item.publish_state]}</span><div className="state-actions">{item.publish_state === "pending_entry" && <button onClick={() => nextState(release.id, item, "entered")}>标记已录入</button>}{item.publish_state === "entered" && <button onClick={() => nextState(release.id, item, "verified")}>标记已核对</button>}{item.publish_state === "verified" && <button onClick={() => nextState(release.id, item, "published")}>标记已发布</button>}{item.publish_state !== "published" && item.publish_state !== "needs_rework" && <button className="text-danger" onClick={() => nextState(release.id, item, "needs_rework")}>需返工</button>}</div></div>)}</div></article>)}</div></main>;
}

export default function App() {
  const route = useHashRoute();
  const [user, setUser] = useState<User | null>(null);
  const [checking, setChecking] = useState(true);
  useEffect(() => { api<User>("/api/auth/me").then(setUser).catch(() => localStorage.removeItem("cams_token")).finally(() => setChecking(false)); }, []);
  if (checking) return <div className="full-loader"><LoaderCircle className="spin" /></div>;
  if (!user) return <Login onLogin={setUser} />;
  let page: ReactNode = <QuestionList />;
  if (route === "/reviews") page = <ReviewQueue />;
  else if (route === "/releases") page = <Releases />;
  else if (route.startsWith("/questions/")) page = <QuestionDetail questionId={route.split("/")[2]} user={user} />;
  else if (route.startsWith("/diff/")) page = <DiffView questionId={route.split("/")[2]} />;
  else if (route.startsWith("/history/")) page = <HistoryView questionId={route.split("/")[2]} user={user} />;
  return <Shell user={user} onLogout={() => { localStorage.removeItem("cams_token"); setUser(null); }}>{page}</Shell>;
}
