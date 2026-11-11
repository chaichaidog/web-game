import { api } from '../services/api.js';
import { soundManager } from '../services/audio.js';

export class TeacherPanel {
  constructor(modalEl, levelsList = []) {
    this.modalEl = modalEl;
    this.levelsList = levelsList;
    this.token = localStorage.getItem('nova_teacher_token') || null;
    this.teacherName = localStorage.getItem('nova_teacher_name') || 'NOVA 指導教師';
    this.sessions = [];
    this.selectedSessionCode = null;
    this.overviewData = null;
    this.selectedStudentDetail = null;
    this.activeTab = 'overview'; // overview | students | trajectory | assign | coop
    this.statusMessage = '';
  }

  setLevels(levelsList) {
    this.levelsList = levelsList || [];
  }

  async open() {
    this.modalEl.classList.remove('hidden');
    if (this.token) {
      try {
        const res = await api.teacherListSessions(this.token);
        this.sessions = res.sessions || [];
        if (this.sessions.length > 0 && !this.selectedSessionCode) {
          this.selectedSessionCode = this.sessions[0].session_code;
        }
        if (this.selectedSessionCode) {
          await this.loadSessionOverview(this.selectedSessionCode);
        }
      } catch {
        this.token = null;
        localStorage.removeItem('nova_teacher_token');
      }
    }
    this.render();
  }

  close() {
    this.modalEl.classList.add('hidden');
  }

  async loadSessionOverview(sessionCode) {
    if (!this.token || !sessionCode) return;
    try {
      this.selectedSessionCode = sessionCode;
      this.overviewData = await api.teacherGetOverview(this.token, sessionCode);
      this.render();
    } catch (err) {
      this.statusMessage = `⚠️ 讀取場次失敗：${err.message}`;
      this.render();
    }
  }

  async loadStudentTrajectory(playerCode) {
    if (!this.token || !this.selectedSessionCode || !playerCode) return;
    try {
      this.selectedStudentDetail = await api.teacherGetStudentDetail(
        this.token,
        this.selectedSessionCode,
        playerCode
      );
      this.activeTab = 'trajectory';
      this.render();
    } catch (err) {
      this.statusMessage = `⚠️ 讀取學習歷程失敗：${err.message}`;
      this.render();
    }
  }

  render() {
    if (!this.modalEl) return;

    if (!this.token) {
      this.modalEl.innerHTML = `
        <div class="modal-card teacher-modal-card">
          <div class="modal-header">
            <h2>🎓 教師端／課堂教學管理中心</h2>
            <button type="button" class="btn-close-modal" id="btn-close-teacher">✕</button>
          </div>
          <div class="modal-body">
            <p class="teacher-intro-note">
              教師端提供課堂場次建立、混齡三層難度指派、概念學習證據觀察與多人合作輪替紀錄。<br/>
              <strong>隱私保護原則</strong>：系統僅使用匿名學員代號，不收集學生真實姓名、電話或個資，且不設公開能力排行榜。
            </p>
            ${this.statusMessage ? `<div class="teacher-alert">${this.statusMessage}</div>` : ''}
            <div class="teacher-login-box">
              <label>教師顯示名稱（選填）：</label>
              <input type="text" id="teacher-name-input" value="${this.teacherName}" placeholder="例如：王老師" />
              <label>教師通行密鑰（預設測試密鑰：<code>NOVA-TEACHER-2026</code>）：</label>
              <input type="password" id="teacher-passkey-input" value="NOVA-TEACHER-2026" />
              <button type="button" class="btn-primary" id="btn-teacher-login">🔐 登入教師管理介面</button>
            </div>
          </div>
        </div>
      `;

      this.modalEl.querySelector('#btn-close-teacher')?.addEventListener('click', () => this.close());
      this.modalEl.querySelector('#btn-teacher-login')?.addEventListener('click', async () => {
        const nameVal = this.modalEl.querySelector('#teacher-name-input')?.value || '資訊科技教師';
        const keyVal = this.modalEl.querySelector('#teacher-passkey-input')?.value || '';
        try {
          const res = await api.teacherLogin(keyVal, nameVal);
          this.token = res.access_token;
          this.teacherName = res.display_name;
          localStorage.setItem('nova_teacher_token', this.token);
          localStorage.setItem('nova_teacher_name', this.teacherName);
          this.statusMessage = '';
          await this.open();
        } catch (err) {
          this.statusMessage = `❌ 登入失敗：${err.message}`;
          this.render();
        }
      });
      return;
    }

    const ov = this.overviewData;
    const students = ov?.students || [];
    const rooms = ov?.rooms || [];
    const coopRecords = ov?.coop_records || [];
    const assignments = ov?.assignments || [];

    this.modalEl.innerHTML = `
      <div class="modal-card teacher-modal-wide">
        <div class="modal-header">
          <div>
            <h2>🎓 教師教學管理中心 — ${this.teacherName}</h2>
            <small>支援小五至國二混齡教學・三層難度動態調整・無公開排名標籤</small>
          </div>
          <div class="header-right-btns">
            <button type="button" class="btn-secondary btn-sm" id="btn-teacher-logout">登出教師端</button>
            <button type="button" class="btn-close-modal" id="btn-close-teacher">✕</button>
          </div>
        </div>

        <div class="modal-body teacher-dashboard-body">
          ${this.statusMessage ? `<div class="teacher-alert">${this.statusMessage}</div>` : ''}

          <!-- Top Session Bar -->
          <div class="teacher-session-bar">
            <div class="session-selector-group">
              <label>目前教學場次：</label>
              <select id="teacher-session-select">
                ${
                  this.sessions.length === 0
                    ? '<option value="">（尚無場次，請先於右側建立）</option>'
                    : this.sessions
                        .map(
                          (s) => `
                      <option value="${s.session_code}" ${s.session_code === this.selectedSessionCode ? 'selected' : ''}>
                        [${s.session_code}] ${s.display_name} (${s.status === 'active' ? '進行中' : '已關閉'}・${s.student_count}人)
                      </option>
                    `
                        )
                        .join('')
                }
              </select>
              <button type="button" class="btn-secondary btn-sm" id="btn-refresh-session">🔄 重新整理</button>
            </div>

            <div class="session-create-group">
              <input type="text" id="new-session-name" placeholder="輸入新場次名稱 (例：週三混齡社團)" />
              <button type="button" class="btn-primary btn-sm" id="btn-create-session">➕ 建立教學場次</button>
            </div>
          </div>

          ${
            ov
              ? `
            <!-- 5 Teacher Navigation Tabs -->
            <div class="teacher-tabs">
              <button type="button" class="teacher-tab-btn ${this.activeTab === 'overview' ? 'active' : ''}" data-tab="overview">
                1. 場次總覽 (${ov.session.session_code})
              </button>
              <button type="button" class="teacher-tab-btn ${this.activeTab === 'students' ? 'active' : ''}" data-tab="students">
                2. 學生清單 (${students.length})
              </button>
              <button type="button" class="teacher-tab-btn ${this.activeTab === 'trajectory' ? 'active' : ''}" data-tab="trajectory">
                3. 個人學習歷程
              </button>
              <button type="button" class="teacher-tab-btn ${this.activeTab === 'assign' ? 'active' : ''}" data-tab="assign">
                4. 任務與難度指派 (${assignments.length})
              </button>
              <button type="button" class="teacher-tab-btn ${this.activeTab === 'coop' ? 'active' : ''}" data-tab="coop">
                5. 合作紀錄與匯出 (${rooms.length})
              </button>
            </div>

            <!-- Tab Content -->
            <div class="teacher-tab-content">
              ${this._renderTabContent(ov, students, rooms, coopRecords, assignments)}
            </div>
          `
              : `<div class="empty-session-prompt">請先在上方建立一個教學場次，即可取得場次代碼（例如 <code>CLS-XXXXX</code>）供學生加入！</div>`
          }
        </div>
      </div>
    `;

    // Bind events
    this.modalEl.querySelector('#btn-close-teacher')?.addEventListener('click', () => this.close());
    this.modalEl.querySelector('#btn-teacher-logout')?.addEventListener('click', () => {
      this.token = null;
      localStorage.removeItem('nova_teacher_token');
      this.render();
    });

    this.modalEl.querySelector('#teacher-session-select')?.addEventListener('change', (e) => {
      this.loadSessionOverview(e.target.value);
    });

    this.modalEl.querySelector('#btn-refresh-session')?.addEventListener('click', () => {
      if (this.selectedSessionCode) this.loadSessionOverview(this.selectedSessionCode);
    });

    this.modalEl.querySelector('#btn-create-session')?.addEventListener('click', async () => {
      const nameInput = this.modalEl.querySelector('#new-session-name')?.value?.trim() || 'NOVA 混齡資訊課堂';
      try {
        soundManager.playClick();
        const created = await api.teacherCreateSession(this.token, nameInput, 24);
        const listRes = await api.teacherListSessions(this.token);
        this.sessions = listRes.sessions || [];
        this.statusMessage = `✅ 已建立教學場次：${created.display_name}（場次代碼：${created.session_code}）`;
        await this.loadSessionOverview(created.session_code);
      } catch (err) {
        this.statusMessage = `❌ 建立場次失敗：${err.message}`;
        this.render();
      }
    });

    this.modalEl.querySelectorAll('[data-tab]').forEach((btn) => {
      btn.addEventListener('click', () => {
        soundManager.playClick();
        this.activeTab = btn.dataset.tab;
        this.render();
      });
    });

    this._bindTabInnerEvents();
  }

  _renderTabContent(ov, students, rooms, coopRecords, assignments) {
    if (this.activeTab === 'overview') {
      return `
        <div class="teacher-overview-grid">
          <div class="overview-stat-card">
            <span class="stat-label">課堂場次代碼（供學生輸入加入）</span>
            <strong class="stat-big-code">${ov.session.session_code}</strong>
            <small>狀態：${ov.session.status === 'active' ? '🟢 開放加入中' : '🔴 已關閉'}</small>
            <div class="stat-actions">
              ${
                ov.session.status === 'active'
                  ? `<button type="button" class="btn-danger btn-xs" id="btn-close-session-status">關閉場次</button>`
                  : `<button type="button" class="btn-primary btn-xs" id="btn-reopen-session-status">重新開放 (+24h)</button>`
              }
            </div>
          </div>

          <div class="overview-stat-card">
            <span class="stat-label">場次內學生人數</span>
            <strong class="stat-big-num">${students.length} 位學生</strong>
            <small>全員使用匿名代號保護隱私</small>
          </div>

          <div class="overview-stat-card">
            <span class="stat-label">進行中合作房間</span>
            <strong class="stat-big-num">${rooms.length} 間房間</strong>
            <small>支援 1～4 人彈性角色輪替</small>
          </div>
        </div>

        <div class="teacher-section-block">
          <h3>📋 課堂學生即時摘要</h3>
          ${
            students.length === 0
              ? `<p class="muted-note">目前尚無學生加入此場次。請讓學生在主畫面點擊「加入課堂場次」並輸入代碼 <strong>${ov.session.session_code}</strong>。</p>`
              : `<table class="teacher-table">
                  <thead>
                    <tr>
                      <th>學生代號 / 暱稱</th>
                      <th>最高章節</th>
                      <th>完成關卡數</th>
                      <th>已接觸概念</th>
                      <th>自行除錯成功</th>
                      <th>學習證據觀察摘要</th>
                      <th>操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${students
                      .map(
                        (st) => `
                      <tr>
                        <td><strong>${st.nickname}</strong><br/><small><code>${st.player_code}</code></small></td>
                        <td>第 ${st.highest_chapter} 章</td>
                        <td>${st.completed_count} 關</td>
                        <td>${(st.concepts_seen || []).join(', ') || '初學中'}</td>
                        <td>${st.self_corrections} 次</td>
                        <td>${(st.descriptive_summary || [])[0] || ''}</td>
                        <td>
                          <button type="button" class="btn-secondary btn-xs" data-inspect-student="${st.player_code}">
                            查看完整歷程
                          </button>
                        </td>
                      </tr>
                    `
                      )
                      .join('')}
                  </tbody>
                </table>`
          }
        </div>
      `;
    }

    if (this.activeTab === 'students') {
      return `
        <div class="teacher-section-block">
          <h3>👥 學生清單與個別難度調整</h3>
          <p class="muted-note">教師可依課堂觀察手動指定學生的預設難度（基礎 Guided／標準 Core／挑戰 Challenge），系統不會公開比較學生成績。</p>
          ${
            students.length === 0
              ? '<p class="muted-note">尚無學生加入本場次。</p>'
              : `<table class="teacher-table">
                  <thead>
                    <tr>
                      <th>代號</th>
                      <th>暱稱</th>
                      <th>已完成關卡 (含難度)</th>
                      <th>嘗試 / 提示使用</th>
                      <th>目前指定難度</th>
                      <th>手動切換難度</th>
                      <th>歷程明細</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${students
                      .map(
                        (st) => `
                      <tr>
                        <td><code>${st.player_code}</code></td>
                        <td><strong>${st.nickname}</strong></td>
                        <td>${(st.completed_levels || []).join(', ') || '尚無'}</td>
                        <td>執行 ${st.total_runs} 次 / 提示 ${st.hints_used_total} 次</td>
                        <td><span class="tier-pill tier-${st.assigned_difficulty || 'guided'}">${st.assigned_difficulty || '系統自適應'}</span></td>
                        <td>
                          <div class="inline-btn-group">
                            <button type="button" class="btn-xs" data-set-student-tier="${st.player_code}" data-tier="guided">基礎</button>
                            <button type="button" class="btn-xs" data-set-student-tier="${st.player_code}" data-tier="core">標準</button>
                            <button type="button" class="btn-xs" data-set-student-tier="${st.player_code}" data-tier="challenge">挑戰</button>
                          </div>
                        </td>
                        <td>
                          <button type="button" class="btn-secondary btn-xs" data-inspect-student="${st.player_code}">查看歷程</button>
                        </td>
                      </tr>
                    `
                      )
                      .join('')}
                  </tbody>
                </table>`
          }
        </div>
      `;
    }

    if (this.activeTab === 'trajectory') {
      const det = this.selectedStudentDetail;
      return `
        <div class="teacher-section-block">
          <div class="trajectory-picker">
            <label>選擇要檢視的學生：</label>
            <select id="trajectory-student-select">
              <option value="">-- 請選擇學生 --</option>
              ${students
                .map(
                  (st) => `
                <option value="${st.player_code}" ${det && det.player_code === st.player_code ? 'selected' : ''}>
                  ${st.nickname} (${st.player_code})
                </option>
              `
                )
                .join('')}
            </select>
          </div>

          ${
            !det
              ? '<p class="muted-note">請從上方下拉選單或「學生清單」選擇一位學生，以檢視其概念理解證據、常見錯誤與自適應推薦。</p>'
              : `
              <div class="trajectory-detail-grid">
                <div class="traj-card">
                  <h4>📝 教師可讀學習證據描述（${det.nickname} <code>${det.player_code}</code>）</h4>
                  <ul class="traj-list">
                    ${(det.summary.descriptive_summary || []).map((line) => `<li>${line}</li>`).join('')}
                  </ul>
                  <div class="traj-stats-row">
                    <span>累計執行：<strong>${det.summary.total_runs}</strong> 次</span>
                    <span>自行修正錯誤通關：<strong>${det.summary.self_corrections}</strong> 次</span>
                    <span>策略性使用提示：<strong>${det.summary.hints_used_total}</strong> 次</span>
                  </div>
                </div>

                <div class="traj-card">
                  <h4>🧭 各概念保守型難度推薦</h4>
                  <ul class="traj-list">
                    ${Object.entries(det.summary.recommendations || {})
                      .map(
                        ([cKey, rec]) => `
                      <li>
                        <strong>${cKey}</strong> → 推薦 <span class="tier-pill tier-${rec.recommended_tier}">${rec.recommended_tier}</span><br/>
                        <small>${rec.reason}</small>
                      </li>
                    `
                      )
                      .join('')}
                  </ul>
                </div>
              </div>

              <h4>🕒 最近學習事件紀錄</h4>
              <div class="traj-events-scroll">
                <table class="teacher-table">
                  <thead>
                    <tr>
                      <th>時間</th>
                      <th>關卡 / 難度</th>
                      <th>概念</th>
                      <th>事件類型</th>
                      <th>結構化學習紀錄</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${(det.recent_events || [])
                      .map(
                        (ev) => `
                      <tr>
                        <td><small>${new Date(ev.created_at).toLocaleTimeString()}</small></td>
                        <td>${ev.level_code || '-'} (${ev.difficulty_tier})</td>
                        <td>${ev.concept_code}</td>
                        <td><code>${ev.event_type}</code></td>
                        <td><small>${JSON.stringify(ev.event_data)}</small></td>
                      </tr>
                    `
                      )
                      .join('')}
                  </tbody>
                </table>
              </div>
            `
          }
        </div>
      `;
    }

    if (this.activeTab === 'assign') {
      return `
        <div class="teacher-section-block">
          <h3>🎯 指派課堂任務與難度層級</h3>
          <div class="assign-form-card">
            <div class="assign-row">
              <label>指派對象類型：</label>
              <select id="assign-target-type">
                <option value="player">指定單一學生</option>
                <option value="room">指定多人合作房間</option>
              </select>

              <label>選擇學生 / 房間：</label>
              <select id="assign-target-code">
                ${students.map((st) => `<option value="P:${st.player_code}">[學生] ${st.nickname} (${st.player_code})</option>`).join('')}
                ${rooms.map((rm) => `<option value="R:${rm.room_code}">[房間] ${rm.room_code} (${rm.player_count}人)</option>`).join('')}
              </select>
            </div>

            <div class="assign-row">
              <label>指派章節關卡：</label>
              <select id="assign-level-code">
                ${this.levelsList
                  .map((lv) => `<option value="${lv.level_code}">${lv.level_name}</option>`)
                  .join('')}
              </select>

              <label>指定難度層級：</label>
              <select id="assign-tier-select">
                <option value="guided">基礎 (Guided — 路徑引導與範例)</option>
                <option value="core" selected>標準 (Core — 獨立規劃與測試)</option>
                <option value="challenge">挑戰 (Challenge — 多路徑與進階結構)</option>
              </select>

              <button type="button" class="btn-primary btn-sm" id="btn-submit-assignment">📌 發布任務指派</button>
            </div>
          </div>

          <h4>已發布的任務指派紀錄</h4>
          ${
            assignments.length === 0
              ? '<p class="muted-note">目前尚未發布任務指派。</p>'
              : `<table class="teacher-table">
                  <thead>
                    <tr>
                      <th>對象</th>
                      <th>指派關卡</th>
                      <th>指定難度</th>
                      <th>指派時間</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${assignments
                      .map(
                        (a) => `
                      <tr>
                        <td>${a.target_name} (<code>${a.target_code}</code>)</td>
                        <td>${a.level_name} (<code>${a.level_code}</code>)</td>
                        <td><span class="tier-pill tier-${a.difficulty_tier}">${a.difficulty_tier}</span></td>
                        <td><small>${new Date(a.created_at).toLocaleString()}</small></td>
                      </tr>
                    `
                      )
                      .join('')}
                  </tbody>
                </table>`
          }
        </div>
      `;
    }

    // Tab 5: Co-op & Export
    return `
      <div class="teacher-section-block">
        <div class="coop-header-row">
          <h3>🤝 多人房間編輯權輪替與合作參與紀錄</h3>
          <button type="button" class="btn-primary btn-sm" id="btn-export-session-json">📥 匯出匿名課堂摘要 (JSON)</button>
        </div>

        ${
          rooms.length === 0
            ? '<p class="muted-note">目前場次尚無多人合作房間紀錄。</p>'
            : rooms
                .map(
                  (r) => `
              <div class="room-coop-card">
                <div class="room-coop-top">
                  <strong>房間代碼：<code>${r.room_code}</code> (${r.player_count} 人)</strong>
                  <span>目前關卡：${r.current_level} (${r.difficulty_tier})</span>
                  <span>主操作者：<code>${r.editor_player_code || '-'}</code></span>
                </div>
                <div class="room-members-badges">
                  ${(r.members || [])
                    .map(
                      (m) => `
                    <span class="member-role-badge">
                      ${m.nickname} (<code>${m.player_code}</code>)：<strong>${m.role_label}</strong>
                    </span>
                  `
                    )
                    .join('')}
                </div>
                <div class="room-turn-history">
                  <small>操作權輪替紀錄：${(r.turn_history || [])
                    .map((th) => `${th.new_editor_nickname || th.new_editor_code}(${th.reason})`)
                    .join(' → ')}</small>
                </div>
              </div>
            `
                )
                .join('')
        }

        <h4>過關合作紀錄明細</h4>
        ${
          coopRecords.length === 0
            ? '<p class="muted-note">尚無多人房間過關提交紀錄。</p>'
            : `<table class="teacher-table">
                <thead>
                  <tr>
                    <th>房間</th>
                    <th>關卡</th>
                    <th>難度</th>
                    <th>嘗試 / 提示</th>
                    <th>完成時角色分工</th>
                  </tr>
                </thead>
                <tbody>
                  ${coopRecords
                    .map(
                      (cr) => `
                    <tr>
                      <td><code>${cr.room_code}</code></td>
                      <td>${cr.level_name}</td>
                      <td>${cr.difficulty_tier}</td>
                      <td>嘗試 ${cr.attempts} 次 / 提示 ${cr.hints_used} 次</td>
                      <td><small>${JSON.stringify(cr.role_distribution)}</small></td>
                    </tr>
                  `
                    )
                    .join('')}
                </tbody>
              </table>`
        }
      </div>
    `;
  }

  _bindTabInnerEvents() {
    this.modalEl.querySelector('#btn-close-session-status')?.addEventListener('click', async () => {
      await api.teacherUpdateSession(this.token, this.selectedSessionCode, 'closed', 0);
      await this.loadSessionOverview(this.selectedSessionCode);
    });

    this.modalEl.querySelector('#btn-reopen-session-status')?.addEventListener('click', async () => {
      await api.teacherUpdateSession(this.token, this.selectedSessionCode, 'active', 24);
      await this.loadSessionOverview(this.selectedSessionCode);
    });

    this.modalEl.querySelectorAll('[data-inspect-student]').forEach((btn) => {
      btn.addEventListener('click', () => {
        this.loadStudentTrajectory(btn.dataset.inspectStudent);
      });
    });

    this.modalEl.querySelectorAll('[data-set-student-tier]').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const pCode = btn.dataset.setStudentTier;
        const tier = btn.dataset.tier;
        try {
          await api.teacherOverrideDifficulty(this.token, this.selectedSessionCode, {
            target_player_code: pCode,
            difficulty_tier: tier,
          });
          this.statusMessage = `✅ 已將學生 ${pCode} 的難度設為「${tier}」`;
          await this.loadSessionOverview(this.selectedSessionCode);
        } catch (err) {
          this.statusMessage = `❌ 調整難度失敗：${err.message}`;
          this.render();
        }
      });
    });

    this.modalEl.querySelector('#trajectory-student-select')?.addEventListener('change', (e) => {
      if (e.target.value) {
        this.loadStudentTrajectory(e.target.value);
      }
    });

    this.modalEl.querySelector('#btn-submit-assignment')?.addEventListener('click', async () => {
      const rawTarget = this.modalEl.querySelector('#assign-target-code')?.value || '';
      const lvCode = this.modalEl.querySelector('#assign-level-code')?.value || 'ch1_lv1';
      const tier = this.modalEl.querySelector('#assign-tier-select')?.value || 'core';
      if (!rawTarget) {
        this.statusMessage = '⚠️ 請先確認場次內已有學生或房間可指派！';
        this.render();
        return;
      }
      const payload = {
        level_code: lvCode,
        difficulty_tier: tier,
      };
      if (rawTarget.startsWith('P:')) {
        payload.target_player_code = rawTarget.slice(2);
      } else if (rawTarget.startsWith('R:')) {
        payload.target_room_code = rawTarget.slice(2);
      }
      try {
        await api.teacherAssignTask(this.token, this.selectedSessionCode, payload);
        this.statusMessage = `✅ 已成功指派關卡 ${lvCode} (${tier})！`;
        await this.loadSessionOverview(this.selectedSessionCode);
      } catch (err) {
        this.statusMessage = `❌ 指派失敗：${err.message}`;
        this.render();
      }
    });

    this.modalEl.querySelector('#btn-export-session-json')?.addEventListener('click', async () => {
      try {
        const data = await api.teacherExportSummary(this.token, this.selectedSessionCode);
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `nova_session_${this.selectedSessionCode}_summary.json`;
        a.click();
        URL.revokeObjectURL(url);
        this.statusMessage = '✅ 已匯出不含個資之匿名課堂學習摘要 JSON！';
        this.render();
      } catch (err) {
        this.statusMessage = `❌ 匯出失敗：${err.message}`;
        this.render();
      }
    });
  }
}

