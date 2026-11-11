import { BLOCK_CATALOG } from '../data/levelsData.js';
import { soundManager } from '../services/audio.js';

const CARD_TYPES = [
  { type: 'move_forward', icon: '⬆️', title: '前進一步', sub: '往前走 1 格', color: '#0284c7' },
  { type: 'turn_left', icon: '↩️', title: '向左轉', sub: '原地逆時針 90°', color: '#0369a1' },
  { type: 'turn_right', icon: '↪️', title: '向右轉', sub: '原地順時針 90°', color: '#0369a1' },
  { type: 'pickup', icon: '⚡', title: '撿取能源', sub: '收集腳下晶片', color: '#d97706' },
  { type: 'repair_device', icon: '🔧', title: '修復設備', sub: '啟動受損發電機', color: '#b45309' },
];

export class ActionCardEditor {
  constructor(containerEl, onChangeCallback, onSwitchToBlockly) {
    this.containerEl = containerEl;
    this.onChangeCallback = onChangeCallback;
    this.onSwitchToBlockly = onSwitchToBlockly;
    this.cards = [];
    this.history = [];
    this.redoStack = [];
    this.allowedTypes = ['move_forward', 'turn_left', 'turn_right', 'pickup', 'repair_device'];
    this.readOnly = false;
    this.highlightedCardId = null;
    this.dragSourceIndex = null;
    this._idCounter = 1;
    this.render();
  }

  setAllowedBlocks(allowedList) {
    if (Array.isArray(allowedList) && allowedList.length > 0) {
      this.allowedTypes = allowedList;
    } else {
      this.allowedTypes = ['move_forward', 'turn_left', 'turn_right', 'pickup', 'repair_device'];
    }
    this.render();
  }

  setReadOnly(readOnly) {
    this.readOnly = Boolean(readOnly);
    this.render();
  }

  _pushHistory() {
    this.history.push(JSON.parse(JSON.stringify(this.cards)));
    if (this.history.length > 30) this.history.shift();
    this.redoStack = [];
  }

  addCard(type) {
    if (this.readOnly) return;
    soundManager.playClick();
    this._pushHistory();
    this.cards.push({
      id: `card_${Date.now()}_${this._idCounter++}`,
      type,
    });
    this.render();
    this._notifyChange();
  }

  removeCard(index) {
    if (this.readOnly) return;
    soundManager.playClick();
    this._pushHistory();
    this.cards.splice(index, 1);
    this.render();
    this._notifyChange();
  }

  moveCard(fromIdx, toIdx) {
    if (this.readOnly || fromIdx === toIdx) return;
    if (toIdx < 0 || toIdx >= this.cards.length) return;
    this._pushHistory();
    const [moved] = this.cards.splice(fromIdx, 1);
    this.cards.splice(toIdx, 0, moved);
    this.render();
    this._notifyChange();
  }

  undo() {
    if (this.readOnly || this.history.length === 0) return;
    soundManager.playClick();
    this.redoStack.push(JSON.parse(JSON.stringify(this.cards)));
    this.cards = this.history.pop();
    this.render();
    this._notifyChange();
  }

  redo() {
    if (this.readOnly || this.redoStack.length === 0) return;
    soundManager.playClick();
    this.history.push(JSON.parse(JSON.stringify(this.cards)));
    this.cards = this.redoStack.pop();
    this.render();
    this._notifyChange();
  }

  clearAll() {
    if (this.readOnly || this.cards.length === 0) return;
    this._pushHistory();
    this.cards = [];
    this.highlightedCardId = null;
    this.render();
    this._notifyChange();
  }

  loadAst(astNodes) {
    const flat = [];
    (astNodes || []).forEach((n) => {
      if (n && ['move_forward', 'move_backward', 'turn_left', 'turn_right', 'pickup', 'repair_device', 'activate_switch', 'open_door'].includes(n.type)) {
        flat.push({
          id: n.id || `card_${Date.now()}_${this._idCounter++}`,
          type: n.type,
        });
      }
    });
    this.cards = flat;
    this.highlightedCardId = null;
    this.render();
  }

  getAst() {
    return this.cards.map((c) => ({
      id: c.id,
      type: c.type,
    }));
  }

  highlightBlock(cardId) {
    this.highlightedCardId = cardId;
    if (!this.containerEl) return;
    const items = this.containerEl.querySelectorAll('.seq-card-item');
    items.forEach((el) => {
      if (cardId && el.dataset.cardId === cardId) {
        el.classList.add('active-step-card');
        el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      } else {
        el.classList.remove('active-step-card');
      }
    });
  }

  _notifyChange() {
    if (this.onChangeCallback) {
      this.onChangeCallback(this.getAst());
    }
  }

  render() {
    if (!this.containerEl) return;
    const availablePalette = CARD_TYPES.filter((c) => this.allowedTypes.includes(c.type));

    this.containerEl.innerHTML = `
      <div class="action-card-editor ${this.readOnly ? 'editor-readonly' : ''}">
        <div class="card-palette-section">
          <div class="card-section-header">
            <span>🃏 點擊或拖曳指令卡加入序列：</span>
            <button type="button" class="btn-switch-blockly" id="btn-card-to-blockly" title="將目前排列的指令卡轉換成 Google Blockly 程式積木！">
              🧩 轉換為 Blockly 積木檢視
            </button>
          </div>
          <div class="card-palette-grid">
            ${availablePalette
              .map(
                (c) => `
              <button type="button" class="palette-card-btn" data-add-type="${c.type}" style="--card-accent:${c.color}" ${this.readOnly ? 'disabled' : ''}>
                <span class="palette-card-icon">${c.icon}</span>
                <div class="palette-card-text">
                  <strong>${c.title}</strong>
                  <small>${c.sub}</small>
                </div>
                <span class="palette-plus">+</span>
              </button>
            `
              )
              .join('')}
          </div>
        </div>

        <div class="card-sequence-section">
          <div class="card-seq-header">
            <span>📋 機器人執行順序（由上而下依序執行，共 <strong>${this.cards.length}</strong> 步）：</span>
            <span class="card-seq-tip">可上下調整或刪除</span>
          </div>
          <div class="card-sequence-list" id="card-sequence-list">
            ${
              this.cards.length === 0
                ? `<div class="card-empty-hint">
                    <div class="empty-hint-icon">👆</div>
                    <p>點擊上方「指令卡」（例如：<strong>⬆️ 前進一步</strong>）<br/>排入機器人的行動順序吧！</p>
                  </div>`
                : this.cards
                    .map((item, idx) => {
                      const meta = CARD_TYPES.find((t) => t.type === item.type) || {
                        icon: '🔹',
                        title: BLOCK_CATALOG[item.type]?.label || item.type,
                        sub: '',
                        color: '#0284c7',
                      };
                      const isHi = this.highlightedCardId === item.id;
                      return `
                        <div class="seq-card-item ${isHi ? 'active-step-card' : ''}" data-card-id="${item.id}" data-index="${idx}" draggable="${!this.readOnly}">
                          <span class="seq-step-num">${idx + 1}</span>
                          <span class="seq-card-icon">${meta.icon}</span>
                          <div class="seq-card-info">
                            <strong>${meta.title}</strong>
                            <small>${meta.sub}</small>
                          </div>
                          <div class="seq-card-actions">
                            <button type="button" class="seq-move-btn" data-move-up="${idx}" ${idx === 0 || this.readOnly ? 'disabled' : ''} title="往上移">▲</button>
                            <button type="button" class="seq-move-btn" data-move-down="${idx}" ${idx === this.cards.length - 1 || this.readOnly ? 'disabled' : ''} title="往下移">▼</button>
                            <button type="button" class="seq-del-btn" data-del-idx="${idx}" ${this.readOnly ? 'disabled' : ''} title="刪除此指令卡">✕</button>
                          </div>
                        </div>
                      `;
                    })
                    .join('')
            }
          </div>
        </div>
      </div>
    `;

    this.containerEl.querySelectorAll('[data-add-type]').forEach((btn) => {
      btn.addEventListener('click', () => {
        this.addCard(btn.dataset.addType);
      });
    });

    this.containerEl.querySelectorAll('[data-move-up]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const idx = Number(btn.dataset.moveUp);
        this.moveCard(idx, idx - 1);
      });
    });

    this.containerEl.querySelectorAll('[data-move-down]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const idx = Number(btn.dataset.moveDown);
        this.moveCard(idx, idx + 1);
      });
    });

    this.containerEl.querySelectorAll('[data-del-idx]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const idx = Number(btn.dataset.delIdx);
        this.removeCard(idx);
      });
    });

    const switchBtn = this.containerEl.querySelector('#btn-card-to-blockly');
    if (switchBtn && this.onSwitchToBlockly) {
      switchBtn.addEventListener('click', () => {
        soundManager.playClick();
        this.onSwitchToBlockly(this.getAst());
      });
    }

    // Drag and drop reordering
    const seqItems = this.containerEl.querySelectorAll('.seq-card-item');
    seqItems.forEach((el) => {
      el.addEventListener('dragstart', (e) => {
        this.dragSourceIndex = Number(el.dataset.index);
        e.dataTransfer.effectAllowed = 'move';
      });
      el.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
      });
      el.addEventListener('drop', (e) => {
        e.preventDefault();
        const targetIndex = Number(el.dataset.index);
        if (this.dragSourceIndex !== null && !Number.isNaN(targetIndex)) {
          this.moveCard(this.dragSourceIndex, targetIndex);
        }
        this.dragSourceIndex = null;
      });
    });
  }
}

