(function () {
  'use strict';

  class PdfReader {
    constructor(options) {
      this.scroll = options.scroll;
      this.pageInput = options.pageInput;
      this.pageCountEl = options.pageCount;
      this.zoomLabel = options.zoomLabel;
      this.root = options.root;
      this.language = 'zh';
      this.page = 1;
      this.pageCount = 1;
      this.zoom = 100;
      this.questionId = null;
      this.observer = null;
      this.renderToken = 0;
      this.loadingMore = false;
      this.highlightTimer = null;
      this.highlightRemovalTimer = null;
      this.highlightGeneration = 0;
    }

    async init() {
      const response = await fetch('/api/textbook/manifest');
      const body = await response.json();
      if (!response.ok) throw new Error(body.error || '无法读取冻结教材');
      this.pageCount = Number(body.textbook?.page_count || 1);
      this.pageCountEl.textContent = String(this.pageCount);
      this.pageInput.max = String(this.pageCount);
      this.zoomLabel.textContent = `${this.zoom}%`;
      this._observe();
      await this.render(this.page);
      return body.textbook;
    }

    async render(page, options = {}) {
      this.clearHighlight();
      const target = Math.max(1, Math.min(this.pageCount, Number(page) || 1));
      this.page = target;
      this.pageInput.value = String(target);
      const token = ++this.renderToken;
      const pages = options.single ? [target] : [target, target + 1].filter((value) => value <= this.pageCount);
      this.scroll.innerHTML = '<div class="pdf-loading">正在加载教材页面…</div>';
      const cards = pages.map((value) => this._card(value));
      this.scroll.replaceChildren(...cards);
      await Promise.all(cards.map((card) => this._loadCard(card)));
      if (token !== this.renderToken) return;
      this._observe();
      const selected = this.scroll.querySelector(`[data-page="${target}"]`);
      if (options.scroll !== false && selected) selected.scrollIntoView({block: 'start', behavior: 'smooth'});
    }

    _card(page) {
      const card = document.createElement('article');
      card.className = 'pdf-page';
      card.dataset.page = String(page);
      card.innerHTML = `<span class="pdf-page-label">PDF 第 ${page} 页</span><div class="pdf-page-spread"></div>`;
      return card;
    }

    async _loadCard(card) {
      const page = Number(card.dataset.page);
      const spread = card.querySelector('.pdf-page-spread');
      const languages = this.language === 'both' ? ['zh', 'en'] : [this.language];
      spread.classList.toggle('is-single', languages.length === 1);
      spread.replaceChildren();
      for (const language of languages) {
        const frame = document.createElement('div');
        frame.className = 'pdf-page-frame';
        const image = document.createElement('img');
        image.className = 'textbook-page';
        image.alt = `${language === 'zh' ? '中文' : '英文'}教材第 ${page} 页`;
        image.src = `/api/textbook/page?lang=${language}&page=${page}&scale=${(1.6 * this.zoom / 100).toFixed(2)}`;
        image.onerror = () => { frame.textContent = '教材页面加载失败，请检查运行环境。'; frame.classList.add('pdf-error'); };
        frame.appendChild(image);
        spread.appendChild(frame);
      }
      await Promise.all([...spread.querySelectorAll('img')].map((image) => new Promise((resolve) => {
        if (image.complete) resolve(); else { image.onload = resolve; image.onerror = resolve; }
      })));
    }

    _observe() {
      if (this.observer) this.observer.disconnect();
      this.observer = new IntersectionObserver((entries) => {
        const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (!visible) return;
        this.page = Number(visible.target.dataset.page);
        this.pageInput.value = String(this.page);
        const cards = [...this.scroll.querySelectorAll('.pdf-page')];
        const lastPage = cards.reduce((maximum, card) => Math.max(maximum, Number(card.dataset.page)), 0);
        if (this.page >= lastPage && lastPage < this.pageCount) this._appendMore(lastPage).catch(() => {});
      }, {root: this.scroll, threshold: [0.25, 0.6]});
      this.scroll.querySelectorAll('.pdf-page').forEach((card) => this.observer.observe(card));
    }

    async _appendMore(afterPage) {
      if (this.loadingMore) return;
      this.loadingMore = true;
      try {
        const pages = [afterPage + 1, afterPage + 2].filter((value) => value <= this.pageCount);
        const cards = pages.map((value) => this._card(value));
        cards.forEach((card) => this.scroll.appendChild(card));
        await Promise.all(cards.map((card) => this._loadCard(card)));
        cards.forEach((card) => this.observer?.observe(card));
      } finally { this.loadingMore = false; }
    }

    async setLanguage(language) {
      if (!['zh', 'en', 'both'].includes(language) || this.language === language) return;
      this.language = language;
      await this.render(this.page, {scroll: false});
    }

    async setPage(page) { await this.render(page); }

    async setZoom(delta) {
      this.zoom = Math.max(75, Math.min(180, this.zoom + delta));
      this.zoomLabel.textContent = `${this.zoom}%`;
      await this.render(this.page, {scroll: false});
    }

    maximize() { this.root.classList.toggle('is-maximized'); }

    clearHighlight() {
      this.highlightGeneration += 1;
      clearTimeout(this.highlightTimer);
      clearTimeout(this.highlightRemovalTimer);
      this.highlightTimer = null;
      this.highlightRemovalTimer = null;
      this.scroll.querySelectorAll('.pdf-highlight').forEach((node) => node.remove());
    }

    _scheduleHighlightRemoval(generation) {
      this.highlightTimer = setTimeout(() => {
        if (generation !== this.highlightGeneration) return;
        this.scroll.querySelectorAll('.pdf-highlight').forEach((node) => node.classList.add('is-fading'));
        this.highlightRemovalTimer = setTimeout(() => {
          if (generation === this.highlightGeneration) this.clearHighlight();
        }, 300);
      }, 5000);
    }

    async highlight(page, query, language = 'zh') {
      await this.render(page, {single: true});
      const generation = ++this.highlightGeneration;
      const card = this.scroll.querySelector(`[data-page="${page}"]`);
      if (!card || !query) return {matched: false};
      const response = await fetch('/api/textbook/match', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({language, page, query})});
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || '教材原文匹配失败');
      if (generation !== this.highlightGeneration) return {...result, matched: false, stale: true};
      const frames = [...card.querySelectorAll('.pdf-page-frame')];
      const frame = this.language === 'both' && language === 'en' ? frames[1] : frames[0];
      if (result.matched && frame) {
        result.boxes.forEach((box) => {
          const mark = document.createElement('span');
          mark.className = 'pdf-highlight';
          mark.style.left = `${box.x * 100}%`; mark.style.top = `${box.y * 100}%`;
          mark.style.width = `${box.width * 100}%`; mark.style.height = `${box.height * 100}%`;
          frame.appendChild(mark);
        });
        this._scheduleHighlightRemoval(generation);
      }
      return result;
    }
  }

  window.PdfReader = PdfReader;
})();
