(function () {
  'use strict';

  const STAGES = ['intake', 'duplicate_check', 'evidence_research', 'evidence_confirmation', 'analysis', 'final_verification', 'human_approval', 'release'];
  const STAGE_LABELS = {
    intake: '接收整理', duplicate_check: '重复检查', evidence_research: '证据研究',
    evidence_confirmation: '证据确认', analysis_drafting: '等待正式解析', analysis_revision: '解析润色',
    final_verification: '最终核验', human_approval: '待教研批准', release_ready: '可发布', released: '已发布'
  };
  const ROLE_LABELS = {support_answer: '支持答案', exclude_option: '排除选项', background: '背景补充'};
  const METHOD_LABELS = {question_rag: '题目 RAG', general_rag: '一般 RAG', kg_expand: 'KG 扩展', grep_keyword: 'grep', direct_page_review: '直接翻页', external_search: '外部搜索', legacy_import: '旧记录迁移'};
  const TASK_LABELS = {intake: '题源整理', duplicate_check: '重复检查', evidence_research: '证据研究', evidence_confirmation: '证据确认', analysis_drafting: '生成正式解析', analysis_revision: '解析润色', final_verification: '最终核验', human_approval: '教研批准', ds_opinion: 'DS 辅助研判', grep_keyword: '关键词查找'};
  const TASK_STATUS_LABELS = {idle: '未开始', running: '进行中', waiting: '等待中', completed: '已完成', failed: '失败'};
  const ACTOR_LABELS = {'workflow-migration': '系统迁移', codex: 'Codex', educator: '教研', 'web-user': '教研'};
  const $ = (id) => document.getElementById(id);
  const state = {selected: null, detail: null, rows: [], activeView: 'question', dirty: false,
    polling: false, drawerScope: 'curated', evidenceOffset: 0, evidenceLimit: 20, evidenceTotal: 0};
  const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
  const textValue = (value) => typeof value === 'string' ? value : JSON.stringify(value ?? '', null, 2);
  const say = (message, kind = '') => {$('message').textContent = message; $('message').className = `message-bar ${kind}`.trim();};

  async function request(url, options = {}) {
    const response = await fetch(url, options); let body = {};
    try { body = await response.json(); } catch (_) { /* non-json */ }
    if (!response.ok) throw new Error(body.error || `请求失败（${response.status}）`);
    return body;
  }
  function bodyFor(payload = {}) {
    const q = state.detail.question;
    return {actor: 'web-user', expected_question_version: q.version,
      expected_archive_revision: q.archive_revision || 0, ...payload};
  }
  function jsonOptions(payload) { return {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)}; }
  function dirty(value) { state.dirty = Boolean(value); }
  function showError(error) { say(error.message || String(error), 'error'); }

  function visibleRows() {
    const filter = $('status-filter').value, query = $('question-filter').value.trim().toLowerCase();
    return state.rows.filter((row) => {
      const active = row.disposition === 'active' && row.workflow_stage !== 'released';
      const statusMatches = filter === 'all' || (filter === 'active' ? active : row.workflow_stage === filter);
      return statusMatches && (!query || `${row.question_id} ${row.stem || ''}`.toLowerCase().includes(query));
    });
  }
  function renderList() {
    const rows = visibleRows(); $('count').textContent = String(rows.length);
    $('question-list').innerHTML = rows.length ? rows.map((row) => `<button class="question-row ${row.question_id === state.selected ? 'active' : ''}" data-qid="${escapeHtml(row.question_id)}"><strong>${escapeHtml(row.question_id)}</strong><em>${escapeHtml(STAGE_LABELS[row.workflow_stage] || row.workflow_stage)}</em><span>${escapeHtml(row.stem || '未提取题干')}</span></button>`).join('') : '<div class="queue-empty">当前范围没有题目。</div>';
    document.querySelectorAll('.question-row').forEach((button) => button.addEventListener('click', () => loadQuestion(button.dataset.qid).catch(showError)));
  }
  async function loadList() {
    const data = await request('/api/questions?limit=500'); state.rows = data.items || []; renderList();
    $('health').textContent = '已连接'; $('health-dot').className = 'online'; return state.rows;
  }

  function normalizedStage(stage) {
    if (['analysis_drafting', 'analysis_revision'].includes(stage)) return 'analysis';
    if (['release_ready', 'released'].includes(stage)) return 'release';
    return stage;
  }
  function renderProcess(workflow) {
    const active = normalizedStage(workflow.stage), index = STAGES.indexOf(active);
    document.querySelectorAll('[data-process]').forEach((node) => {
      const nodeIndex = STAGES.indexOf(node.dataset.process);
      node.classList.toggle('complete', nodeIndex >= 0 && nodeIndex < index);
      node.classList.toggle('active', node.dataset.process === active);
    });
  }
  function renderTask(task = {}) {
    const strip = $('task-strip'); strip.className = `task-strip ${task.status || 'idle'}`;
    const taskLabel = task.task_type === 'evidence_research' && task.status === 'completed'
      ? '本轮检索' : (TASK_LABELS[task.task_type] || task.task_type);
    $('task-title').textContent = task.task_type ? `${taskLabel} · ${TASK_STATUS_LABELS[task.status] || task.status || '未开始'}` : '当前无运行任务';
    $('task-summary').textContent = task.error || task.next_step || task.summary || '等待开始处理';
    $('task-owner').textContent = [task.actor && `执行：${ACTOR_LABELS[task.actor] || task.actor}`, task.waiting_for && `等待：${ACTOR_LABELS[task.waiting_for] || task.waiting_for}`].filter(Boolean).join(' · ');
  }

  function renderQuestion(detail) {
    const content = detail.question.content || {}, options = content.options || {};
    $('question-type').textContent = content.question_type === 'multiple' ? '多选题' : '单选题';
    $('question-read').innerHTML = `<div class="question-stem">${escapeHtml(content.stem || content.stem_cn || '题干缺失')}</div>${Object.entries(options).map(([key, value]) => `<div class="option-row"><span class="option-key">${escapeHtml(key)}</span><span>${escapeHtml(value)}</span></div>`).join('')}<div class="answer-line">当前答案：${escapeHtml((content.answer || []).join('、') || '待核定')}</div>`;
    $('edit-stem').value = content.stem || content.stem_cn || ''; $('edit-answer').value = (content.answer || []).join('、');
    $('edit-options').innerHTML = Object.entries(options).map(([key, value]) => `<label>${escapeHtml(key)}<input data-option="${escapeHtml(key)}" value="${escapeHtml(value)}"></label>`).join('');
  }
  async function renderArchive(detail) {
    const intake = detail.intake || {}, duplicate = detail.duplicate_check || {}, audit = await request(`/api/questions/${encodeURIComponent(state.selected)}/audit`);
    $('archive-details').innerHTML = `<div class="archive-block"><strong>题源</strong><p>${escapeHtml(intake.source_description || '迁移题目')}</p></div><div class="archive-block"><strong>重复检查</strong><p>${escapeHtml(duplicate.decision || detail.workflow.duplicate_check || '未完成')}</p></div><div class="archive-block"><strong>最近操作</strong><ul>${(audit.items || []).slice(-5).reverse().map((item) => `<li>${escapeHtml(item.operation)} · ${escapeHtml(item.actor || '')}</li>`).join('') || '<li>暂无记录</li>'}</ul></div>`;
  }

  function evidenceQuote(item) { return item.quote || item.knowledge_zh || item.knowledge_en || ''; }
  function evidenceMeta(item) {
    const discoveries = item.discoveries || [], methods = [...new Set(discoveries.map((hit) => METHOD_LABELS[hit.method] || hit.method).filter(Boolean))];
    return [item.source_kind === 'external' ? '外部资料' : '冻结教材', item.heading_context instanceof Array ? item.heading_context.join(' / ') : item.heading_context,
      item.printed_page && `书内 ${item.printed_page}`, item.pdf_page && `PDF ${item.pdf_page}`, methods.join(' + ')].filter(Boolean).join(' · ');
  }
  function renderCandidate(detail) {
    const candidate = detail.evidence_candidate, selected = detail.evidence_summary?.items || [], byId = Object.fromEntries(selected.map((item) => [item.evidence_id, item]));
    $('candidate-version').textContent = candidate ? `候选 v${candidate.version}` : '';
    if (!candidate) {$('candidate-content').innerHTML = '<div class="conclusion-empty">Codex 尚未提交最终证据候选。</div>';}
    else {
      const groups = {support_answer: [], exclude_option: [], background: []};
      (candidate.entries || []).forEach((entry) => groups[entry.role]?.push({...byId[entry.evidence_id], ...entry}));
      $('candidate-content').innerHTML = Object.entries(groups).filter(([, rows]) => rows.length).map(([role, rows]) => `<section class="evidence-group ${role === 'exclude_option' ? 'exclude' : role === 'background' ? 'background' : ''}"><h3>${ROLE_LABELS[role]}${role === 'exclude_option' ? ` · ${escapeHtml([...new Set(rows.map((r) => r.target_option).filter(Boolean))].join('、'))}` : ''}</h3>${rows.map((item) => `<div class="conclusion-item" data-evidence-id="${escapeHtml(item.evidence_id)}"><p>${escapeHtml(evidenceQuote(item) || item.evidence_id)}</p><small>${escapeHtml(evidenceMeta(item))}</small></div>`).join('')}</section>`).join('') || '<div class="conclusion-empty">候选版本中没有有效条目。</div>';
    }
    $('evidence-decision-panel').hidden = detail.workflow.stage !== 'evidence_confirmation';
  }

  function renderAnalysis(detail) {
    const record = detail.analysis, analysis = record?.analysis || {};
    $('analysis-version').textContent = record ? `解析 v${record.version}` : '';
    const sections = [['exam_point', '考点'], ['core_analysis', '核心解析'], ['option_analysis', '错误项分析'], ['pitfall', '易错提醒'], ['evidence', '教材依据']];
    $('analysis-content').innerHTML = record ? sections.map(([key, label]) => {
      const value = analysis[key];
      if (Array.isArray(value)) return `<section class="analysis-section"><h3>${label}</h3><ul>${value.map((item) => `<li>${escapeHtml(textValue(item))}</li>`).join('')}</ul></section>`;
      if (value && typeof value === 'object') return `<section class="analysis-section"><h3>${label}</h3><ul>${Object.entries(value).map(([name, text]) => `<li><strong>${escapeHtml(name)}</strong> ${escapeHtml(textValue(text))}</li>`).join('')}</ul></section>`;
      return `<section class="analysis-section"><h3>${label}</h3><p>${escapeHtml(value || '未填写')}</p></section>`;
    }).join('') : '<div class="conclusion-empty">等待 Codex 基于已确认依据生成正式解析。</div>';
    const feedback = detail.analysis_feedback || [];
    if (feedback.length) $('analysis-content').insertAdjacentHTML('beforeend', `<section class="analysis-section feedback-list"><h3>教研批注</h3>${feedback.map((item) => `<div class="feedback-item"><strong>${escapeHtml(item.feedback_id)} · ${escapeHtml(item.section)}</strong><p>${escapeHtml(item.comment)}</p></div>`).join('')}</section>`);
    $('feedback-panel').hidden = !(record && detail.workflow.stage === 'analysis_revision');
    const check = detail.final_check;
    $('final-check-panel').className = `final-check ${check?.status === 'passed' ? 'passed' : ''}`;
    $('final-check-panel').innerHTML = check ? `<strong>最终核验：${escapeHtml(check.status)}</strong><p>${escapeHtml(check.summary || '')}</p>` : '';
    $('decision-panel').hidden = detail.workflow.stage !== 'human_approval';
  }

  async function loadQuestion(qid, refreshQueue = true) {
    const previous = state.selected === qid ? state.detail : null, detail = await request(`/api/questions/${encodeURIComponent(qid)}`);
    if (state.selected !== qid) window.pdfReader?.clearHighlight();
    state.selected = qid; state.detail = detail; dirty(false); $('empty').hidden = true; $('detail').hidden = false; $('sync-notice').hidden = true;
    localStorage.setItem('cams-active-question', qid); $('qid').textContent = qid;
    await request('/api/active-context', jsonOptions({question_id: qid}));
    $('stage').textContent = STAGE_LABELS[detail.workflow.stage] || detail.workflow.stage; $('version').textContent = `题面 v${detail.question.version} · 档案 r${detail.question.archive_revision || 0}`;
    renderProcess(detail.workflow); renderTask(detail.task); renderQuestion(detail); renderCandidate(detail); renderAnalysis(detail); await renderArchive(detail);
    const counts = detail.evidence_summary?.counts || {}; $('curated-count').textContent = `${counts.curated || 0} 精选`; $('raw-count').textContent = `${counts.all || 0} 原始`;
    if (previous?.evidence_candidate?.version !== detail.evidence_candidate?.version && detail.evidence_candidate && state.activeView !== 'evidence') $('evidence-dot').hidden = false;
    if (previous?.analysis?.version !== detail.analysis?.version && detail.analysis && state.activeView !== 'analysis') $('analysis-dot').hidden = false;
    $('queue').classList.add('is-collapsed'); if (refreshQueue) await loadList(); else renderList(); setView(state.activeView);
    if (!$('evidence-drawer').hidden) await loadEvidence();
  }
  function setView(view) {
    state.activeView = view;
    document.querySelectorAll('.pane-tab').forEach((tab) => tab.classList.toggle('active', tab.dataset.view === view));
    document.querySelectorAll('.pane-view').forEach((pane) => { const active = pane.dataset.pane === view; pane.hidden = !active; pane.classList.toggle('active', active); });
    if (view === 'evidence') $('evidence-dot').hidden = true; if (view === 'analysis') $('analysis-dot').hidden = true;
  }

  async function saveQuestion(event) {
    event.preventDefault(); const reason = $('edit-reason').value.trim(); if (!reason) throw new Error('修改题目必须填写理由');
    if (!confirm('题面变化会使旧证据、解析、核验和批准失效。确认继续？')) return;
    const content = {...(state.detail.question.content || {})}; content.stem = $('edit-stem').value.trim(); content.options = {};
    document.querySelectorAll('[data-option]').forEach((input) => {content.options[input.dataset.option] = input.value.trim();});
    content.answer = $('edit-answer').value.split(/[、，,\s]+/).filter(Boolean);
    const payload = bodyFor({confirmed: true, reason, content});
    await request(`/api/questions/${encodeURIComponent(state.selected)}`, {method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)});
    $('question-edit').hidden = true; $('question-read').hidden = false; dirty(false); say('题面已修改，后续版本已失效。', 'success'); await loadQuestion(state.selected);
  }
  async function evidenceDecision(action) {
    const reason = $('evidence-decision-reason').value.trim(); if (action === 'return' && !reason) throw new Error('退回补证必须填写理由');
    if (!confirm(action === 'confirm' ? '确认冻结当前证据版本？' : '确认退回 Codex 继续补证？')) return;
    await request(`/api/questions/${encodeURIComponent(state.selected)}/evidence-decision`, jsonOptions(bodyFor({confirmed: true, action, reason: reason || '教研确认最终证据'})));
    dirty(false); say(action === 'confirm' ? '最终证据已确认。' : '已退回 Codex 补证。', 'success'); await loadQuestion(state.selected);
  }
  async function addFeedback() {
    const comment = $('feedback-comment').value.trim(); if (!comment) throw new Error('批注不能为空');
    await request(`/api/questions/${encodeURIComponent(state.selected)}/analysis-feedback`, jsonOptions(bodyFor({section: $('feedback-section').value, comment, reason: '教研提交正式解析批注'})));
    $('feedback-comment').value = ''; dirty(false); say('批注已提交，等待 Codex 生成新版本。', 'success'); await loadQuestion(state.selected);
  }
  async function polishingComplete() {
    if (!confirm('确认当前解析已完成润色，交由 Codex 做最终核验？')) return;
    await request(`/api/questions/${encodeURIComponent(state.selected)}/polishing-complete`, jsonOptions(bodyFor({confirmed: true, reason: '教研确认解析润色完成'})));
    dirty(false); say('已进入最终核验。', 'success'); await loadQuestion(state.selected);
  }
  async function saveDecision() {
    const decision = document.querySelector('input[name="decision"]:checked')?.value || 'approved', reason = $('decision-notes').value.trim();
    if (decision !== 'approved' && !reason) throw new Error('退回、暂缓或不收录必须填写理由');
    if (!confirm(`确认提交“${decision}”决定？`)) return;
    await request(`/api/questions/${encodeURIComponent(state.selected)}/workflow-decision`, jsonOptions(bodyFor({confirmed: true, decision, reason: reason || '教研批准当前固定版本组合'})));
    dirty(false); say('教研决定已记录。', 'success'); await loadQuestion(state.selected);
  }

  async function loadEvidence() {
    if (!state.selected) return;
    const params = new URLSearchParams({scope: state.drawerScope, offset: String(state.evidenceOffset), limit: String(state.evidenceLimit)});
    if (state.drawerScope === 'all') { if ($('run-filter').value) params.set('run_id', $('run-filter').value); if ($('method-filter').value) params.set('method', $('method-filter').value); if ($('source-filter').value) params.set('source_kind', $('source-filter').value); if ($('option-filter').value) params.set('option', $('option-filter').value); }
    const data = await request(`/api/questions/${encodeURIComponent(state.selected)}/evidence?${params}`); state.evidenceTotal = data.total || 0;
    $('curated-count').textContent = `${data.counts?.curated || 0} 精选`; $('raw-count').textContent = `${data.counts?.all || 0} 原始`;
    const runValue = $('run-filter').value;
    $('run-filter').innerHTML = '<option value="">全部轮次</option>' + (data.available_runs || []).map((runId) => `<option value="${escapeHtml(runId)}" ${runId === runValue ? 'selected' : ''}>${escapeHtml(runId)}</option>`).join('');
    const renderRow = (item) => {
      const selected = Boolean(item.curation?.selected), role = item.curation?.role || 'support_answer';
      return `<div class="evidence-row ${selected ? 'curated' : ''}"><div class="evidence-main" data-focus-id="${escapeHtml(item.evidence_id)}"><div class="evidence-meta">${escapeHtml(evidenceMeta(item))}</div><div class="evidence-quote">${escapeHtml(evidenceQuote(item))}</div></div>${state.drawerScope === 'all' ? `<div class="evidence-actions"><select data-role-id="${escapeHtml(item.evidence_id)}"><option value="support_answer" ${role === 'support_answer' ? 'selected' : ''}>支持答案</option><option value="exclude_option" ${role === 'exclude_option' ? 'selected' : ''}>排除选项</option><option value="background" ${role === 'background' ? 'selected' : ''}>背景补充</option></select><button data-suggest-id="${escapeHtml(item.evidence_id)}" type="button">建议纳入</button></div>` : `<div class="evidence-actions"><span class="subtle">${escapeHtml(ROLE_LABELS[role] || role)}</span></div>`}</div>`;
    };
    if (!data.items.length) $('evidence-list').innerHTML = '<div class="evidence-empty">当前范围没有证据。</div>';
    else if (state.drawerScope === 'curated') {
      const groups = {support_answer: [], exclude_option: [], background: []}; data.items.forEach((item) => (groups[item.curation?.role] || groups.background).push(item));
      $('evidence-list').innerHTML = Object.entries(groups).filter(([, items]) => items.length).map(([role, items]) => `<div class="evidence-group-label">${ROLE_LABELS[role]}</div>${items.map(renderRow).join('')}`).join('');
    } else $('evidence-list').innerHTML = data.items.map(renderRow).join('');
    document.querySelectorAll('[data-focus-id]').forEach((node) => node.addEventListener('click', () => focusEvidence(data.items.find((item) => item.evidence_id === node.dataset.focusId)).catch(showError)));
    document.querySelectorAll('[data-suggest-id]').forEach((button) => button.addEventListener('click', () => suggestEvidence(button.dataset.suggestId).catch(showError)));
    const page = Math.floor(state.evidenceOffset / state.evidenceLimit) + 1, pages = Math.max(1, Math.ceil(state.evidenceTotal / state.evidenceLimit));
    $('evidence-pagination').hidden = state.drawerScope !== 'all' || pages <= 1; $('evidence-page').textContent = `${page} / ${pages}`;
    $('evidence-prev').disabled = state.evidenceOffset <= 0; $('evidence-next').disabled = state.evidenceOffset + state.evidenceLimit >= state.evidenceTotal;
  }
  async function suggestEvidence(evidenceId) {
    const role = document.querySelector(`[data-role-id="${CSS.escape(evidenceId)}"]`).value;
    const targetOption = role === 'exclude_option' ? (prompt('要排除哪个选项？例如 A') || '').trim().toUpperCase() : null;
    if (role === 'exclude_option' && !targetOption) return;
    await request(`/api/questions/${encodeURIComponent(state.selected)}/evidence-suggestion`, jsonOptions(bodyFor({reason: '教研从原始候选中建议纳入', updates: [{evidence_id: evidenceId, selected: true, role, target_option: targetOption}]})));
    say('已记录为教研建议，等待 Codex 整理正式候选。', 'success'); await loadQuestion(state.selected, false);
  }
  async function focusEvidence(item) {
    if (!item?.pdf_page) { say(item?.url ? `外部资料：${item.url}` : '该证据没有可定位的 PDF 页码。'); return; }
    const query = item.quote || item.knowledge_zh || item.knowledge_en || '';
    const language = /[\u3400-\u9fff]/.test(query) ? 'zh' : 'en';
    document.querySelectorAll('.language-button').forEach((button) => button.classList.toggle('active', button.dataset.language === language));
    await window.pdfReader.setLanguage(language); const result = await window.pdfReader.highlight(Number(item.pdf_page), query, language);
    if (result.stale) return;
    $('evidence-drawer').hidden = true; $('evidence-toggle').setAttribute('aria-expanded', 'false');
    say(result.matched ? `已定位 PDF 第 ${item.pdf_page} 页并高亮原文。` : `已跳到 PDF 第 ${item.pdf_page} 页，原文未自动匹配。`, result.matched ? 'success' : '');
  }

  function setCommandHelper(open) {
    const helper = $('command-helper');
    helper.classList.toggle('is-open', open);
    $('command-helper-trigger').setAttribute('aria-expanded', String(open));
    if (!open) $('command-copy-fallback').hidden = true;
  }
  async function copyCommand(command) {
    let copied = false;
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(command);
        copied = true;
      }
    } catch (_) { /* use the local fallback below */ }
    const fallback = $('command-copy-fallback');
    if (!copied) {
      fallback.hidden = false; fallback.value = command; fallback.focus(); fallback.select();
      try { copied = document.execCommand('copy'); } catch (_) { copied = false; }
    }
    if (copied) {
      setCommandHelper(false);
      $('command-helper-trigger').focus();
      say(`已复制“${command}”，可粘贴到 Codex。`, 'success');
    } else {
      setCommandHelper(true); fallback.hidden = false; fallback.focus(); fallback.select();
      say('浏览器未允许自动复制，请复制浮层中已选中的文字。');
    }
  }

  async function openSettings() {
    const settings = await request('/api/settings/deepseek'); $('ds-enabled').checked = settings.enabled; $('ds-base-url').value = settings.base_url; $('ds-model').value = settings.model;
    $('ds-api-key').value = ''; $('ds-configured').textContent = settings.configured ? '本机已保存 API Key。' : '尚未配置 API Key；可保持关闭。'; $('settings-dialog').showModal();
  }
  async function saveSettings(event) {
    event.preventDefault(); const payload = {enabled: $('ds-enabled').checked, base_url: $('ds-base-url').value.trim(), model: $('ds-model').value.trim(), api_key: $('ds-api-key').value.trim()};
    const result = await request('/api/settings/deepseek', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)});
    localStorage.setItem('cams-settings-seen-v2', '1'); $('settings-dialog').close(); say(result.enabled ? 'DS 辅助研判已启用。' : 'DS 辅助研判保持关闭。', 'success');
  }
  function closeSettings() { localStorage.setItem('cams-settings-seen-v2', '1'); $('settings-dialog').close(); }

  async function poll() {
    if (document.hidden || state.polling) return; state.polling = true;
    try { const rows = await loadList(); if (!state.selected || !state.detail) return; const row = rows.find((item) => item.question_id === state.selected);
      if (row && Number(row.archive_revision || 0) !== Number(state.detail.question.archive_revision || 0)) { if (state.dirty) $('sync-notice').hidden = false; else {await loadQuestion(state.selected, false); say('已同步后台最新版本。', 'success');} }
    } catch (error) {$('health').textContent = '连接失败'; $('health-dot').className = 'offline'; showError(error);} finally {state.polling = false;}
  }
  function setupSplitter() {
    const splitter = $('splitter'), workspace = $('split-workspace'); let dragging = false;
    splitter.addEventListener('pointerdown', (event) => {dragging = true; splitter.setPointerCapture(event.pointerId);});
    splitter.addEventListener('pointermove', (event) => {if (!dragging) return; const rect = workspace.getBoundingClientRect(), value = Math.max(30, Math.min(70, ((event.clientX - rect.left) / rect.width) * 100)); workspace.style.setProperty('--question-width', `${value}%`); splitter.setAttribute('aria-valuenow', String(Math.round(value)));});
    splitter.addEventListener('pointerup', () => {dragging = false;});
    splitter.addEventListener('keydown', (event) => {if (!['ArrowLeft','ArrowRight'].includes(event.key)) return; event.preventDefault(); const value = Math.max(30, Math.min(70, Number(splitter.getAttribute('aria-valuenow') || 40) + (event.key === 'ArrowRight' ? 5 : -5))); workspace.style.setProperty('--question-width', `${value}%`); splitter.setAttribute('aria-valuenow', String(value));});
  }

  $('status-filter').addEventListener('change', renderList); $('question-filter').addEventListener('input', renderList);
  $('open-queue').addEventListener('click', () => $('queue').classList.toggle('is-collapsed'));
  $('refresh').addEventListener('click', () => {if (state.dirty && !confirm('刷新会清除未保存内容，继续？')) return; Promise.all([loadList(), state.selected ? loadQuestion(state.selected, false) : Promise.resolve()]).catch(showError);});
  document.querySelectorAll('.pane-tab').forEach((tab) => tab.addEventListener('click', () => setView(tab.dataset.view)));
  $('edit-question').addEventListener('click', () => {$('question-edit').hidden = false; $('question-read').hidden = true; dirty(true);}); $('cancel-edit').addEventListener('click', () => {$('question-edit').hidden = true; $('question-read').hidden = false; dirty(false);}); $('question-edit').addEventListener('submit', (event) => saveQuestion(event).catch(showError));
  $('evidence-decision-reason').addEventListener('input', () => dirty(true)); $('confirm-evidence').addEventListener('click', () => evidenceDecision('confirm').catch(showError)); $('return-evidence').addEventListener('click', () => evidenceDecision('return').catch(showError));
  $('feedback-comment').addEventListener('input', () => dirty(true)); $('add-feedback').addEventListener('click', () => addFeedback().catch(showError)); $('polishing-complete').addEventListener('click', () => polishingComplete().catch(showError));
  $('decision-notes').addEventListener('input', () => dirty(true)); $('save-decision').addEventListener('click', () => saveDecision().catch(showError));
  $('sync-refresh').addEventListener('click', () => loadQuestion(state.selected).catch(showError)); $('sync-keep').addEventListener('click', () => {$('sync-notice').hidden = true;});
  $('evidence-toggle').addEventListener('click', () => {const drawer = $('evidence-drawer'), open = drawer.hidden; drawer.hidden = !open; $('evidence-toggle').setAttribute('aria-expanded', String(open)); $('evidence-toggle').firstElementChild.textContent = open ? '⌄' : '⌃'; if (open) loadEvidence().catch(showError);});
  $('command-helper').addEventListener('mouseenter', () => setCommandHelper(true));
  $('command-helper').addEventListener('mouseleave', () => {if (!$('command-helper').matches(':focus-within')) setCommandHelper(false);});
  $('command-helper').addEventListener('focusin', () => setCommandHelper(true));
  $('command-helper').addEventListener('focusout', () => setTimeout(() => {if (!$('command-helper').matches(':focus-within')) setCommandHelper(false);}, 0));
  $('command-helper-trigger').addEventListener('click', () => setCommandHelper(!$('command-helper').classList.contains('is-open')));
  document.querySelectorAll('[data-copy-command]').forEach((button) => button.addEventListener('click', () => copyCommand(button.dataset.copyCommand).catch(showError)));
  $('command-helper').addEventListener('keydown', (event) => {if (event.key === 'Escape') {setCommandHelper(false); $('command-helper-trigger').focus();}});
  document.querySelectorAll('.drawer-tab').forEach((tab) => tab.addEventListener('click', () => {state.drawerScope = tab.dataset.scope; state.evidenceOffset = 0; document.querySelectorAll('.drawer-tab').forEach((node) => node.classList.toggle('active', node === tab)); $('raw-filters').hidden = state.drawerScope !== 'all'; loadEvidence().catch(showError);}));
  ['run-filter','method-filter','source-filter','option-filter'].forEach((id) => $(id).addEventListener('change', () => {state.evidenceOffset = 0; loadEvidence().catch(showError);})); $('evidence-prev').addEventListener('click', () => {state.evidenceOffset = Math.max(0, state.evidenceOffset - state.evidenceLimit); loadEvidence().catch(showError);}); $('evidence-next').addEventListener('click', () => {state.evidenceOffset += state.evidenceLimit; loadEvidence().catch(showError);});
  document.querySelectorAll('.language-button').forEach((button) => button.addEventListener('click', () => {document.querySelectorAll('.language-button').forEach((node) => node.classList.toggle('active', node === button)); window.pdfReader.setLanguage(button.dataset.language).catch(showError);}));
  $('page-input').addEventListener('change', () => window.pdfReader.setPage($('page-input').value).catch(showError)); $('zoom-out').addEventListener('click', () => window.pdfReader.setZoom(-10).catch(showError)); $('zoom-in').addEventListener('click', () => window.pdfReader.setZoom(10).catch(showError)); $('pdf-maximize').addEventListener('click', () => window.pdfReader.maximize());
  $('settings-open').addEventListener('click', () => openSettings().catch(showError)); $('settings-form').addEventListener('submit', (event) => saveSettings(event).catch(showError)); $('settings-close').addEventListener('click', closeSettings); $('settings-cancel').addEventListener('click', closeSettings);
  document.addEventListener('visibilitychange', () => {if (!document.hidden) poll();}); setupSplitter();
  window.pdfReader = new window.PdfReader({scroll: $('pdf-scroll'), pageInput: $('page-input'), pageCount: $('page-count'), zoomLabel: $('zoom-label'), root: $('pdf-pane')}); window.pdfReader.init().catch(showError);
  loadList().then(() => {const params = new URLSearchParams(location.search), requested = params.get('question') || localStorage.getItem('cams-active-question'); return requested ? loadQuestion(requested) : undefined;}).then(() => {if (!localStorage.getItem('cams-settings-seen-v2')) return openSettings();}).catch(showError); setInterval(poll, 5000);
})();
