import Phaser from 'phaser';
import * as Blockly from 'blockly';
import { api } from './services/api.js';
import { roomSocket } from './services/ws.js';
import { soundManager } from './services/audio.js';
import { GameScene } from './game/GameScene.js';
import { compileAndSimulate } from './game/Interpreter.js';
import { ActionCardEditor } from './editor/ActionCardEditor.js';
import { registerNovaBlocks, buildToolboxConfig, workspaceToAst, astToWorkspace } from './editor/BlocklySetup.js';
import { generatePythonPreview } from './editor/PythonGenerator.js';
import { TeacherPanel } from './ui/TeacherPanel.js';
import { UIManager } from './ui/UIManager.js';
import {
  ROBOT_SKINS, HEAD_ACCESSORIES, BASE_DECORS, ZONE_THEMES,
  QUICK_MESSAGES_LIST, EMOJI_REACTIONS,
} from './data/levelsData.js';

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const CARD_ONLY = new Set(['move_forward', 'move_backward', 'turn_left', 'turn_right', 'pickup', 'repair_device', 'activate_switch', 'open_door']);
const TIER_LABEL = { guided: '基礎', core: '標準', challenge: '挑戰' };

const state = {
  player: null,
  levels: [],
  level: null,         // level object from API
  tier: 'guided',
  mode: 'cards',       // cards | blockly
  showPython: false,
  room: null,
  hintsShown: 0,
  hintsUsedTotal: 0,
  attempts: 0,
  levelStartedAt: Date.now(),
  run: { running: false, paused: false, trace: [], idx: 0, simResult: null, isRemote: false, token: 0 },
  hadError: false,
};

let phaserGame = null;
let scene = null;
let cardEditor = null;
let workspace = null;
let teacherPanel = null;
let saveTimer = null;
let suppressSync = false;

/* ---------------- helpers ---------------- */
function toast(msg) {
  const feed = $('coop-toast-feed');
  feed.textContent = msg;
  clearTimeout(toast._t);
  toast._t = setTimeout(() => { if (feed.textContent === msg) feed.textContent = ''; }, 6000);
}
function setConsole(msg, kind = '') {
  const el = $('console-status-banner');
  el.textContent = msg;
  el.className = `console-status-banner ${kind}`;
}
function logStep(text, current = false) {
  const log = $('console-step-log');
  log.querySelectorAll('.current').forEach((n) => n.classList.remove('current'));
  const d = document.createElement('div');
  d.textContent = text;
  if (current) d.classList.add('current');
  log.appendChild(d);
  log.scrollTop = log.scrollHeight;
}
function openModal(id) { $(id).classList.remove('hidden'); }
function closeModal(id) { $(id).classList.add('hidden'); }
function levelData() { return state.level?.variants?.[state.tier] || state.level?.variants?.guided || {}; }
function me() { return state.player?.player_code; }
function roomMembers() { return state.room?.members || []; }
function isMulti() { return roomMembers().length > 1; }
function isEditor() { return !isMulti() || state.room?.editor_player_code === me(); }

function currentAst() {
  if (state.mode === 'blockly' && workspace) return workspaceToAst(workspace);
  return cardEditor.getAst();
}
function isFlatCards(ast) { return ast.every((n) => CARD_ONLY.has(n.type)); }

/* ---------------- editor management ---------------- */
function ensureBlockly() {
  if (workspace) return;
  registerNovaBlocks();
  workspace = Blockly.inject('blockly-div', {
    toolbox: buildToolboxConfig(levelData().allowed_blocks),
    trashcan: true,
    zoom: { controls: true, wheel: true, startScale: 0.9 },
    grid: { spacing: 24, length: 3, colour: '#1e293b', snap: true },
    move: { scrollbars: true, drag: true, wheel: false },
    theme: Blockly.Themes.Classic,
  });
  workspace.addChangeListener((e) => {
    if (e.isUiEvent || suppressSync) return;
    onEditorChanged();
  });
}

function setMode(mode) {
  if (mode === 'cards') {
    if (state.mode === 'blockly' && workspace) {
      const ast = workspaceToAst(workspace);
      if (!isFlatCards(ast)) {
        toast('⚠️ 目前積木包含迴圈／條件／函式，指令卡無法表示，請留在 Blockly 積木模式。');
        return;
      }
      cardEditor.loadAst(ast);
    }
  } else if (mode === 'blockly') {
    ensureBlockly();
    if (state.mode === 'cards') {
      suppressSync = true;
      astToWorkspace(workspace, cardEditor.getAst());
      suppressSync = false;
    }
    workspace.updateToolbox(buildToolboxConfig(levelData().allowed_blocks));
  }
  state.mode = mode;
  $('action-card-container').classList.toggle('hidden', mode !== 'cards');
  $('blockly-wrapper').classList.toggle('hidden', mode !== 'blockly');
  $('tab-mode-cards').classList.toggle('active', mode === 'cards');
  $('tab-mode-blockly').classList.toggle('active', mode === 'blockly');
  if (mode === 'blockly') setTimeout(() => Blockly.svgResize(workspace), 30);
  refreshPython();
}

function refreshPython() {
  $('python-preview-pane').classList.toggle('hidden', !state.showPython);
  $('tab-mode-split').classList.toggle('active', state.showPython);
  if (state.showPython) $('python-code-content').textContent = generatePythonPreview(currentAst());
}

function onEditorChanged() {
  refreshPython();
  scheduleSave();
  if (isMulti() && isEditor() && !suppressSync) {
    roomSocket.sendWorkspaceUpdate({ version: 1, mode: state.mode, ast: currentAst() });
  }
}

function applyAst(ast, mode) {
  suppressSync = true;
  if (mode === 'blockly' || !isFlatCards(ast)) {
    if (state.mode !== 'blockly') setMode('blockly');
    astToWorkspace(workspace, ast);
  } else {
    if (state.mode !== 'cards') setMode('cards');
    cardEditor.loadAst(ast);
  }
  suppressSync = false;
  refreshPython();
}

function scheduleSave() {
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {
    if (!state.player || !state.level) return;
    api.saveWorkspace(me(), state.level.level_code, state.tier, { version: 1, mode: state.mode, ast: currentAst() }).catch(() => {});
  }, 700);
}

function highlight(blockId) {
  if (state.mode === 'cards') cardEditor.highlightBlock(blockId);
  else if (workspace) workspace.highlightBlock(blockId || null);
}

function applyEditorLock() {
  const locked = state.run.running || !isEditor();
  $('editor-primary-lock')?.remove();
  document.querySelector('.editor-primary-pane').classList.toggle('locked', locked);
  cardEditor.setReadOnly(locked);
  const banner = $('editor-lock-banner');
  if (isMulti() && !isEditor()) {
    const owner = roomMembers().find((m) => m.player_code === state.room.editor_player_code);
    $('lock-owner-name').textContent = owner?.nickname || '隊友';
    banner.classList.remove('hidden');
  } else banner.classList.add('hidden');
  $('btn-run-program').disabled = !isEditor() || state.run.running;
  $('btn-step-program')?.setAttribute('disabled', !isEditor() ? 'true' : '');
  $('btn-step-program').disabled = !isEditor() || (state.run.running && !state.run.paused);
}

/* ---------------- level loading ---------------- */
async function loadLevel(levelCode, tier, { fromRoom = false } = {}) {
  const lv = state.levels.find((l) => l.level_code === levelCode) || state.levels[0];
  state.level = lv;
  state.tier = lv.variants[tier] ? tier : 'guided';
  state.hintsShown = 0;
  state.attempts = 0;
  state.hadError = false;
  state.levelStartedAt = Date.now();
  resetRun(true);
  const ld = levelData();

  document.querySelectorAll('.diff-btn').forEach((b) => b.classList.toggle('active', b.dataset.diff === state.tier));
  $('current-level-title').textContent = lv.level_name;
  $('current-zone-subtitle').textContent = ZONE_THEMES[ld.zone]?.name || 'NOVA 基地';
  $('brief-chapter-tag').textContent = lv.chapter_name;
  $('mission-desc-text').textContent = lv.description;
  $('mission-learning-obj').textContent = lv.learning_objective;
  const g = ld.four_step_guide || {};
  $('guide-step-1').textContent = g.step1_concrete || '-';
  $('guide-step-2').textContent = g.step2_visual || '-';
  $('guide-step-3').textContent = g.step3_logic || '-';
  $('guide-step-4').textContent = g.step4_code || '-';
  $('hint-tier-count').textContent = '0/3';
  $('hint-drawer').classList.add('hidden');
  updateRecommendTag();
  updateHud({ energy: 0 });

  cardEditor.setAllowedBlocks((ld.allowed_blocks || []).filter((b) => CARD_ONLY.has(b)));
  if (workspace) workspace.updateToolbox(buildToolboxConfig(ld.allowed_blocks));

  scene.loadLevelData(ld);
  scene.setPlayerAppearance(state.player.character_skin, state.player.head_accessory, state.player.settings.animation_level);

  // restore saved workspace for this level+tier
  let saved = null;
  try { saved = (await api.loadWorkspace(me(), lv.level_code, state.tier)).workspace_data; } catch { /* offline */ }
  const defaultMode = lv.editor_mode === 'cards' ? 'cards' : 'blockly';
  suppressSync = true;
  if (saved && Array.isArray(saved.ast)) {
    applyAst(saved.ast, saved.mode);
  } else {
    if (defaultMode === 'blockly') { setMode('blockly'); astToWorkspace(workspace, []); }
    else { setMode('cards'); cardEditor.loadAst([]); }
  }
  suppressSync = false;
  refreshPython();
  applyEditorLock();
  setConsole('🤖 準備就緒：排列好指令後，按下「▶️ 執行程式」或「⏭️ 單步執行」觀察機器人行動！');
  $('console-step-log').innerHTML = '';

  if (state.room && !fromRoom && isEditor()) {
    api.startOrChangeRoomLevel(state.room.room_code, me(), lv.level_code, state.tier).catch(() => {});
  }
  closeModal('level-select-modal');
}

function updateRecommendTag() {
  const tag = $('brief-recommend-tag');
  tag.classList.add('hidden');
  const assigned = state.player.active_session?.assigned_difficulty;
  const rec = state.player.learning_summary?.recommendations?.[state.level.concept_code];
  if (assigned) {
    tag.textContent = `🎓 教師指定：${TIER_LABEL[assigned]}`;
    tag.classList.remove('hidden');
  } else if (rec && rec.recommended_tier !== state.tier) {
    tag.textContent = `✨ 推薦：${TIER_LABEL[rec.recommended_tier]}（可忽略）`;
    tag.title = rec.reason;
    tag.classList.remove('hidden');
  }
}

function updateHud(vars) {
  const req = levelData().required_energy || 0;
  $('hud-energy-val').textContent = `${vars.energy ?? 0} / ${req}`;
}

/* ---------------- execution ---------------- */
function resetRun(silent = false) {
  state.run.token++;
  state.run = { running: false, paused: false, trace: [], idx: 0, simResult: null, isRemote: false, token: state.run.token };
  highlight(null);
  if (scene && state.level) scene.resetMapState();
  $('hud-steps-val').textContent = '0';
  updateHud({ energy: 0 });
  $('btn-pause-program').disabled = true;
  $('btn-pause-program').textContent = '⏸️ 暫停';
  if (!silent) {
    setConsole('🔄 已重新開始，地圖與機器人已還原。');
    $('console-step-log').innerHTML = '';
  }
  if (isMulti() && isEditor() && !silent) roomSocket.sendEditorLock(false);
  applyEditorLock();
}

function prepareRun(ast, remote = false) {
  const sim = compileAndSimulate(ast, levelData());
  state.run = { running: true, paused: false, trace: sim.trace, idx: 0, simResult: sim, isRemote: remote, token: state.run.token + 1 };
  scene.resetMapState();
  scene.setPlayerAppearance(state.player.character_skin, state.player.head_accessory, state.player.settings.animation_level);
  $('console-step-log').innerHTML = '';
  $('hud-steps-val').textContent = '0';
  updateHud({ energy: 0 });
  return sim;
}

async function playOneStep() {
  const r = state.run;
  const ev = r.trace[r.idx];
  if (!ev) return false;
  highlight(ev.block_id);
  r.idx++;
  logStep(`第 ${ev.step} 步：${ev.label || ev.action}`, true);
  $('hud-steps-val').textContent = String(ev.step);
  updateHud(ev.variables);
  const dur = Number($('exec-speed-select').value);
  await scene.animateStep(ev, dur);
  return true;
}

async function finishRun() {
  const r = state.run;
  const sim = r.simResult;
  r.running = false;
  highlight(null);
  $('btn-pause-program').disabled = true;
  if (isMulti() && isEditor() && !r.isRemote) roomSocket.sendEditorLock(false);
  applyEditorLock();

  if (sim.success) {
    setConsole(sim.message, 'success');
    scene.playVictoryEffect();
  } else {
    highlight(sim.error_block_id);
    setConsole(`❌ ${sim.message}`, 'error');
    scene.playErrorEffect();
    logStep(`⚠️ 錯誤位置：第 ${sim.error_step ?? '-'} 步（${sim.error_type}）`);
  }
  if (r.isRemote) return;

  // server-authoritative verification & learning events
  state.attempts++;
  try {
    const res = await api.submitLevelProgram(state.level.level_code, {
      player_code: me(),
      room_code: state.room?.room_code || null,
      difficulty_tier: state.tier,
      program_ast: currentAst(),
      workspace_data: { version: 1, mode: state.mode, ast: currentAst() },
      hints_used: state.hintsShown,
      attempts: state.attempts,
      completion_time: Math.round((Date.now() - state.levelStartedAt) / 1000),
    });
    if (!sim.success) { state.hadError = true; return; }
    if (res.verified) {
      state.player = await api.getPlayer(me());
      refreshPlayerUi();
      if (res.room_state) { state.room = res.room_state; refreshRoomUi(); applyEditorLock(); }
      showVictory(res);
    } else {
      setConsole(`⚠️ 伺服器驗證未通過：${res.simulation.message}`, 'error');
    }
  } catch (err) {
    setConsole(`⚠️ 無法連線到伺服器驗證：${err.message}（進度未保存）`, 'error');
  }
}

async function runLoop(token) {
  while (state.run.token === token && state.run.running && !state.run.paused) {
    const more = await playOneStep();
    if (!more) break;
  }
  if (state.run.token === token && state.run.running && !state.run.paused && state.run.idx >= state.run.trace.length) {
    await finishRun();
  }
}

function startRun(remoteAst = null) {
  if (state.run.running && !remoteAst) return;
  const ast = remoteAst || currentAst();
  const sim = prepareRun(ast, Boolean(remoteAst));
  if (!remoteAst) {
    if (!sim.success && sim.trace.length === 0) {
      state.run.running = false;
      setConsole(`❌ ${sim.message}`, 'error');
      scene.playErrorEffect();
      finishRunNoTrace(sim);
      return;
    }
    if (isMulti()) {
      roomSocket.sendEditorLock(true);
      roomSocket.sendRobotAction({ phase: 'run', ast, tier: state.tier, level_code: state.level.level_code });
    }
  }
  $('btn-pause-program').disabled = false;
  setConsole('▶️ 程式執行中…觀察機器人一步一步照指令行動。');
  applyEditorLock();
  runLoop(state.run.token);
}

async function finishRunNoTrace(sim) {
  state.attempts++;
  if (state.hadError === false) state.hadError = true;
  try {
    await api.submitLevelProgram(state.level.level_code, {
      player_code: me(), room_code: state.room?.room_code || null, difficulty_tier: state.tier,
      program_ast: currentAst(), hints_used: state.hintsShown, attempts: state.attempts,
    });
  } catch { /* ignore */ }
  applyEditorLock();
}

async function stepRun() {
  if (!isEditor()) return;
  if (!state.run.running) {
    const ast = currentAst();
    const sim = prepareRun(ast, false);
    if (!sim.success && sim.trace.length === 0) {
      state.run.running = false;
      setConsole(`❌ ${sim.message}`, 'error');
      finishRunNoTrace(sim);
      return;
    }
    state.run.paused = true;
    $('btn-pause-program').disabled = false;
    $('btn-pause-program').textContent = '▶️ 繼續';
    if (isMulti()) roomSocket.sendEditorLock(true);
    applyEditorLock();
  }
  if (!state.run.paused) return;
  const token = state.run.token;
  if (state.run.idx < state.run.trace.length) {
    await playOneStep();
  }
  if (state.run.token === token && state.run.idx >= state.run.trace.length) {
    await finishRun();
    $('btn-pause-program').textContent = '⏸️ 暫停';
  }
}

function togglePause() {
  const r = state.run;
  if (!r.running) return;
  if (r.paused) {
    r.paused = false;
    $('btn-pause-program').textContent = '⏸️ 暫停';
    setConsole('▶️ 繼續執行。');
    runLoop(r.token);
  } else {
    r.paused = true;
    $('btn-pause-program').textContent = '▶️ 繼續';
    setConsole('⏸️ 已暫停，可按「單步執行」逐步檢查或「繼續」。');
  }
  applyEditorLock();
}

/* ---------------- hints ---------------- */
function renderHints() {
  const hints = levelData().hints || [];
  $('hint-tier-list').innerHTML = hints.slice(0, state.hintsShown).map((h) => `<p>${esc(h)}</p>`).join('');
  $('hint-tier-count').textContent = `${state.hintsShown}/${Math.min(3, hints.length)}`;
  const canExample = state.tier === 'guided' && (levelData().example_ast || []).length > 0 && state.hintsShown >= 3;
  $('btn-load-guided-example').classList.toggle('hidden', !canExample);
  $('btn-next-hint-tier').disabled = state.hintsShown >= Math.min(3, hints.length);
}
function requestHint() {
  const hints = levelData().hints || [];
  $('hint-drawer').classList.remove('hidden');
  if (state.hintsShown < Math.min(3, hints.length)) {
    state.hintsShown++;
    state.hintsUsedTotal++;
    api.recordLearningEvent({
      player_code: me(), room_code: state.room?.room_code || null, level_code: state.level.level_code,
      difficulty_tier: state.tier, concept_code: state.level.concept_code, event_type: 'hint_used',
      event_data: { hint_tier: state.hintsShown },
    }).catch(() => {});
  }
  renderHints();
}
function loadExample() {
  const ex = levelData().example_ast || [];
  if (state.tier !== 'guided' || ex.length === 0) {
    toast('此難度不預先提供完整範例，試試使用提示吧！');
    return;
  }
  applyAst(JSON.parse(JSON.stringify(ex)), isFlatCards(ex) ? 'cards' : 'blockly');
  onEditorChanged();
}

/* ---------------- victory ---------------- */
function showVictory(res) {
  const lv = state.level;
  const ld = levelData();
  const rq = ld.reflection_question;
  const sim = res.simulation || {};
  const idx = state.levels.findIndex((l) => l.level_code === lv.level_code);
  const next = state.levels[idx + 1];
  const concepts = (sim.concepts_used || []).join('、') || lv.concept_code;
  const ach = (res.newly_unlocked_achievements || [])
    .map((a) => `<li>🏅 <strong>${esc(a.name)}</strong>（+${a.xp_reward} XP，獎勵：${esc(a.reward_value || '徽章')}）</li>`).join('');
  const coop = res.room_state && res.room_state.player_count > 1
    ? `<p>🤝 合作紀錄：${res.room_state.player_count} 位隊友完成任務，操作權已輪替給 <strong>${esc(res.room_state.members.find((m) => m.is_editor)?.nickname || '')}</strong>。</p>` : '';
  $('victory-modal-body').innerHTML = `
    <p>${esc(lv.level_name)}（${TIER_LABEL[state.tier]}）</p>
    <p>⭐ 星等：${res.stars} ・ ✨ 獲得 <strong>${res.xp_gained} XP</strong>${res.self_corrected_bonus ? '（含成功除錯獎勵！）' : ''}</p>
    <p>📘 本關運用的程式概念：<strong>${esc(concepts)}</strong></p>
    ${ach ? `<ul>${ach}</ul>` : ''}
    ${coop}
    ${rq ? `<div class="lobby-section"><h3>🤔 小小反思（不計分）</h3><p>${esc(rq.question)}</p>
      ${rq.options.map((o, i) => `<button type="button" class="reflection-opt" data-ref="${i}">${esc(o)}</button>`).join('')}</div>` : ''}
    <div class="modal-footer-btns">
      <button type="button" class="btn-secondary" id="btn-victory-retry">換個難度／再玩一次</button>
      ${next ? '<button type="button" class="btn-primary" id="btn-victory-next">下一關 ➔</button>' : ''}
    </div>`;
  openModal('victory-modal');
  document.querySelectorAll('.reflection-opt').forEach((b) => b.addEventListener('click', () => {
    document.querySelectorAll('.reflection-opt').forEach((x) => x.classList.remove('picked'));
    b.classList.add('picked');
    api.recordLearningEvent({
      player_code: me(), room_code: state.room?.room_code || null, level_code: lv.level_code,
      difficulty_tier: state.tier, concept_code: lv.concept_code, event_type: 'reflection_answered',
      event_data: { option_index: Number(b.dataset.ref) },
    }).catch(() => {});
  }));
  $('btn-victory-retry')?.addEventListener('click', () => { closeModal('victory-modal'); resetRun(); });
  $('btn-victory-next')?.addEventListener('click', () => {
    closeModal('victory-modal');
    const tier = state.player.active_session?.assigned_difficulty || state.tier;
    loadLevel(next.level_code, tier);
  });
}

/* ---------------- player / UI refresh ---------------- */
function refreshPlayerUi() {
  const p = state.player;
  $('topbar-player-name').textContent = p.nickname;
  $('topbar-xp-badge').textContent = `${p.experience} XP`;
  $('menu-player-code-display').textContent = p.player_code;
  $('menu-title-display').textContent = p.title_badge;
  $('menu-nickname-input').value = p.nickname;
  const decor = BASE_DECORS.find((d) => d.id === p.base_decor);
  if (decor) { $('base-decor-icon').textContent = decor.icon; $('base-decor-name').textContent = decor.name; }
  document.body.classList.toggle('text-size-large', p.settings.text_size === 'large');
  document.body.classList.toggle('text-size-medium', p.settings.text_size !== 'large');
  soundManager.setEnabled(p.settings.sound_enabled);
  if (scene) scene.setPlayerAppearance(p.character_skin, p.head_accessory, p.settings.animation_level);
  if (p.active_session) {
    $('menu-session-status-text').textContent = `✅ 已加入課堂：${p.active_session.display_name}（${p.active_session.session_code}）`;
  }
}

function refreshRoomUi() {
  const r = state.room;
  const members = r?.members || [];
  $('topbar-room-badge').textContent = r ? `${r.room_code}・${members.length}人` : '單人';
  const multi = members.length > 1;
  const mine = members.find((m) => m.player_code === me());
  $('coop-mode-title').textContent = !r || !multi
    ? '單人修復模式（1 人完整流程）' : `${members.length} 人合作模式（代碼 ${r.room_code}）`;
  $('coop-role-desc').textContent = !multi
    ? '全能修復員：分析地圖 → 排列指令 → 執行測試 → 觀察除錯'
    : `你的角色：${mine?.role_label || '-'}${mine?.is_editor ? '（目前主操作者）' : '（觀察與提出想法）'}`;
  $('btn-pass-turn').classList.toggle('hidden', !(multi && isEditor()));
  $('coop-members-row').innerHTML = members.map((m) =>
    `<span class="member-chip ${m.is_editor ? 'is-editor' : ''} ${m.is_online ? '' : 'offline'}">${m.is_editor ? '✏️' : '👀'} ${esc(m.nickname)}${m.is_host ? ' 👑' : ''}・${esc(m.role_label)}${m.is_online ? '' : '（離線）'}</span>`).join('');
  applyEditorLock();
  if (!$('lobby-modal').classList.contains('hidden')) renderLobby();
}

/* ---------------- websocket ---------------- */
function connectRoom(room) {
  state.room = room;
  roomSocket.connect(room.room_code, me());
  refreshRoomUi();
}
roomSocket.onMessage(async (msg) => {
  if (msg.room_state) { state.room = msg.room_state; refreshRoomUi(); }
  switch (msg.type) {
    case 'player_joined': soundManager.playJoin(); toast(`🤖 ${msg.nickname} 加入了小隊！`); break;
    case 'player_left': toast(msg.disconnected ? '📴 有隊友暫時離線，操作權已自動處理。' : '👋 有隊友離開了房間。'); break;
    case 'turn_changed': {
      const ed = state.room.members.find((m) => m.is_editor);
      toast(`🔄 目前主操作者：${ed?.nickname}`);
      break;
    }
    case 'editor_state_updated':
      if (msg.updated_by !== me() && msg.workspace_state?.ast) applyAst(msg.workspace_state.ast, msg.workspace_state.mode);
      break;
    case 'editor_lock_changed':
      if (msg.editor_player_code !== me() && !msg.locked && state.run.isRemote) resetRunRemoteEnd();
      break;
    case 'robot_action':
      if (msg.triggered_by !== me() && msg.action_data?.phase === 'run') {
        if (msg.action_data.level_code !== state.level.level_code || msg.action_data.tier !== state.tier) {
          await loadLevel(msg.action_data.level_code, msg.action_data.tier, { fromRoom: true });
        }
        resetRun(true);
        startRun(msg.action_data.ast);
      }
      break;
    case 'quick_message': toast(`💬 ${msg.nickname}：${msg.text}`); break;
    case 'game_started':
      if (msg.level_code !== state.level?.level_code || msg.difficulty_tier !== state.tier) {
        await loadLevel(msg.level_code, msg.difficulty_tier, { fromRoom: true });
      }
      break;
    case 'mission_completed':
      if (msg.submitted_by !== state.player.nickname) {
        toast(`🎉 ${msg.submitted_by} 提交的程式通過了「${msg.level_code}」！操作權已輪替。`);
        state.player = await api.getPlayer(me()); refreshPlayerUi();
      }
      break;
    default: break;
  }
});
function resetRunRemoteEnd() { /* remote run ends on its own when trace finishes */ }

/* ---------------- modals ---------------- */
function renderLevelSelect() {
  const done = new Set((state.player.progress || []).filter((p) => p.completed).map((p) => `${p.level_code}:${p.difficulty_tier}`));
  const byChapter = {};
  state.levels.forEach((l) => { (byChapter[l.chapter_id] ||= { name: l.chapter_name, items: [] }).items.push(l); });
  $('level-select-body').innerHTML = Object.values(byChapter).map((c) => `
    <div class="chapter-block"><h3>${esc(c.name)}</h3>
    ${c.items.map((l) => `<div class="level-row"><div><strong>${esc(l.level_name)}</strong><br/><small class="muted-note">${esc(l.learning_objective)}</small></div>
      <div class="tier-btns">${['guided', 'core', 'challenge'].map((t) =>
        `<button type="button" class="tier-btn ${done.has(`${l.level_code}:${t}`) ? 'done' : ''}" data-lv="${l.level_code}" data-tier="${t}">${done.has(`${l.level_code}:${t}`) ? '✔ ' : ''}${TIER_LABEL[t]}</button>`).join('')}</div></div>`).join('')}
    </div>`).join('');
  document.querySelectorAll('#level-select-body .tier-btn').forEach((b) => b.addEventListener('click', () => {
    closeModal('main-menu-modal');
    loadLevel(b.dataset.lv, b.dataset.tier);
  }));
}

function renderLobby() {
  const r = state.room;
  const body = $('lobby-modal-body');
  const roster = r ? `
    <div class="lobby-section">
      <h3>目前房間</h3>
      <div class="room-code-big">${esc(r.room_code)}</div>
      <p class="muted-note">把代碼分享給同學（最多 4 人）。目前 ${r.player_count} 人${r.is_solo ? '・單人也能完整遊玩，不需等待隊友' : ''}。</p>
      <ul>${r.members.map((m) => `<li>${m.is_editor ? '✏️' : '👀'} ${esc(m.nickname)}${m.is_host ? ' 👑' : ''}（${esc(m.role_label)}）${m.is_online ? '' : ' — 離線'}</li>`).join('')}</ul>
      <div class="modal-footer-btns">
        <button type="button" class="btn-danger" id="btn-leave-room">離開房間</button>
        <button type="button" class="btn-primary" id="btn-start-room">開始／同步目前關卡</button>
      </div>
    </div>` : `
    <div class="lobby-section"><h3>建立新房間</h3>
      <p class="muted-note">1 人也可建立；其他人用代碼加入後會自動切換為合作分工。</p>
      <button type="button" class="btn-primary" id="btn-create-room">➕ 建立房間（${esc(state.level.level_name)}・${TIER_LABEL[state.tier]}）</button></div>
    <div class="lobby-section"><h3>輸入房間代碼加入</h3>
      <div class="inline-nickname-form"><input type="text" id="join-room-code" maxlength="8" placeholder="例如 K7M2QX" />
      <button type="button" class="btn-secondary" id="btn-join-room">加入</button></div></div>`;
  body.innerHTML = roster + `
    <div class="lobby-section"><h3>課堂場次</h3>
      <div class="inline-nickname-form"><input type="text" id="lobby-session-code" placeholder="老師提供的 CLS-XXXXX" />
      <button type="button" class="btn-secondary" id="btn-lobby-join-session">加入課堂</button></div>
      <p class="muted-note">場次代碼與房間代碼不同；不加入課堂也能遊玩。</p></div>`;
  $('btn-create-room')?.addEventListener('click', async () => {
    try { connectRoom(await api.createRoom(me(), state.level.level_code, state.tier, state.player.active_session?.session_code || null)); renderLobby(); }
    catch (e) { toast(`❌ ${e.message}`); }
  });
  $('btn-join-room')?.addEventListener('click', async () => {
    try {
      const code = $('join-room-code').value.trim().toUpperCase();
      const room = await api.joinRoom(me(), code);
      connectRoom(room);
      await loadLevel(room.current_level, room.difficulty_tier, { fromRoom: true });
      renderLobby();
    } catch (e) { toast(`❌ ${e.message}`); alert(e.message); }
  });
  $('btn-leave-room')?.addEventListener('click', async () => {
    await api.leaveRoom(me(), r.room_code).catch(() => {});
    roomSocket.disconnect(); state.room = null; refreshRoomUi(); renderLobby();
  });
  $('btn-start-room')?.addEventListener('click', async () => {
    try { await api.startOrChangeRoomLevel(r.room_code, me(), state.level.level_code, state.tier); closeModal('lobby-modal'); } catch (e) { toast(`❌ ${e.message}`); }
  });
  $('btn-lobby-join-session')?.addEventListener('click', () => joinSession($('lobby-session-code').value));
}

async function joinSession(code) {
  try {
    await api.joinTeachingSession(me(), String(code).trim());
    state.player = await api.getPlayer(me());
    refreshPlayerUi(); updateRecommendTag();
    toast('✅ 已加入課堂場次！');
  } catch (e) { alert(`加入課堂失敗：${e.message}`); }
}

function renderProfile() {
  const p = state.player;
  $('profile-modal-body').innerHTML = `
    <h3>機器人塗裝</h3><div class="skin-grid">${ROBOT_SKINS.map((s) => {
      const owned = s.id === 'nova_scout' || p.achievements.some((a) => a.unlocked && a.reward_type === 'skin' && a.reward_value === s.id) || p.available_skins.includes(s.id) && p.achievements.some((a) => a.unlocked && a.reward_value === s.id);
      return `<div class="skin-card ${p.character_skin === s.id ? 'selected' : ''}"><span class="skin-swatch" style="background:${s.primary}"></span><strong>${esc(s.name)}</strong><br/><small>${esc(s.desc)}</small><br/>
        <button type="button" class="btn-xs" data-skin="${s.id}" ${owned ? '' : 'disabled'}>${owned ? '裝備' : '🔒 完成成就解鎖'}</button></div>`; }).join('')}</div>
    <h3>頭部配件</h3><div class="skin-grid">${HEAD_ACCESSORIES.map((a) => {
      const owned = a.id === 'antenna_basic' || p.achievements.some((x) => x.unlocked && x.reward_value === a.id);
      return `<div class="skin-card ${p.head_accessory === a.id ? 'selected' : ''}">${a.icon} <strong>${esc(a.name)}</strong><br/><button type="button" class="btn-xs" data-acc="${a.id}" ${owned ? '' : 'disabled'}>${owned ? '裝備' : '🔒'}</button></div>`; }).join('')}</div>
    <h3>基地裝飾</h3><div class="skin-grid">${BASE_DECORS.map((d) => {
      const owned = d.id === 'holo_plant' || p.achievements.some((x) => x.unlocked && x.reward_value === d.id);
      return `<div class="skin-card ${p.base_decor === d.id ? 'selected' : ''}">${d.icon} <strong>${esc(d.name)}</strong><br/><small>${esc(d.desc)}</small><br/><button type="button" class="btn-xs" data-decor="${d.id}" ${owned ? '' : 'disabled'}>${owned ? '擺放' : '🔒'}</button></div>`; }).join('')}</div>
    <h3>成就（${p.achievements.filter((a) => a.unlocked).length}/${p.achievements.length}）・稱號：${esc(p.title_badge)}</h3>
    <div class="ach-grid">${p.achievements.map((a) => `<div class="ach-card ${a.unlocked ? '' : 'locked'}">${a.unlocked ? '🏅' : '🔒'} <strong>${esc(a.name)}</strong><br/><small>${esc(a.description)}</small></div>`).join('')}</div>
    <p class="muted-note">經驗值 ${p.experience} XP・等級 ${p.level_rank}。外觀純裝飾，不影響能力；本遊戲沒有公開排行榜。</p>`;
  const upd = async (u) => { state.player = await api.updatePlayer(me(), u); refreshPlayerUi(); renderProfile(); };
  document.querySelectorAll('[data-skin]').forEach((b) => b.addEventListener('click', () => upd({ character_skin: b.dataset.skin })));
  document.querySelectorAll('[data-acc]').forEach((b) => b.addEventListener('click', () => upd({ head_accessory: b.dataset.acc })));
  document.querySelectorAll('[data-decor]').forEach((b) => b.addEventListener('click', () => upd({ base_decor: b.dataset.decor })));
}

function renderSettings() {
  const s = state.player.settings;
  $('settings-modal-body').innerHTML = `
    <div class="setting-row"><span>🔊 音效</span><button type="button" class="btn-secondary" id="set-sound">${s.sound_enabled ? '開啟中（點擊關閉）' : '已關閉（點擊開啟）'}</button></div>
    <div class="setting-row"><span>🎞️ 動畫</span><select id="set-anim">
      <option value="normal" ${s.animation_level === 'normal' ? 'selected' : ''}>標準</option>
      <option value="fast" ${s.animation_level === 'fast' ? 'selected' : ''}>快速播放</option>
      <option value="reduced" ${s.animation_level === 'reduced' ? 'selected' : ''}>減少動畫</option></select></div>
    <div class="setting-row"><span>🔠 文字大小</span><select id="set-text">
      <option value="medium" ${s.text_size === 'medium' ? 'selected' : ''}>標準</option>
      <option value="large" ${s.text_size === 'large' ? 'selected' : ''}>大字</option></select></div>
    <h3>怎麼玩？</h3>
    <ol><li>看地圖：藍色框是起點，綠色框是終點，紅黃方塊是障礙物。</li>
    <li>排指令：點指令卡（或拖 Blockly 積木），機器人會由上而下照順序做。</li>
    <li>按「執行」看機器人走；出錯時會告訴你卡在哪一步，改一改再試。</li>
    <li>卡關可按「💡 呼叫提示」，不會扣分。一個人或 2～4 人都能通關。</li></ol>
    ${UIManager.renderBlockGuideCatalog(levelData().allowed_blocks)}
    <p class="muted-note">資料僅使用暱稱與匿名代號，不收集真實姓名等個資。</p>`;
  const save = async (u) => { state.player = await api.updateSettings(me(), u); refreshPlayerUi(); renderSettings(); };
  $('set-sound').addEventListener('click', () => save({ sound_enabled: !s.sound_enabled }));
  $('set-anim').addEventListener('change', (e) => save({ animation_level: e.target.value }));
  $('set-text').addEventListener('change', (e) => save({ text_size: e.target.value }));
}

/* ---------------- bootstrap ---------------- */
async function init() {
  soundManager.init();
  cardEditor = new ActionCardEditor($('action-card-container'), onEditorChanged, (ast) => { applyAst(ast, 'blockly'); onEditorChanged(); });

  phaserGame = new Phaser.Game({
    type: Phaser.AUTO,
    parent: 'phaser-game-container',
    width: $('phaser-game-container').clientWidth || 620,
    height: 440,
    pixelArt: true,
    backgroundColor: '#050912',
    scale: { mode: Phaser.Scale.RESIZE, parent: 'phaser-game-container', width: '100%', height: '100%' },
    scene: [GameScene],
  });
  await new Promise((resolve) => {
    const t = setInterval(() => {
      const sc = phaserGame.scene.getScene('GameScene');
      if (sc && sc.sys.isActive() && sc.rootContainer) { clearInterval(t); scene = sc; resolve(); }
    }, 50);
  });

  const savedCode = localStorage.getItem('nova_player_code');
  try {
    state.player = await api.createOrGetPlayer(null, savedCode);
    localStorage.setItem('nova_player_code', state.player.player_code);
    state.levels = (await api.getLevels()).levels;
  } catch (err) {
    document.body.insertAdjacentHTML('afterbegin', `<div class="teacher-alert">❌ 無法連線到後端 API（${esc(err.message)}）。請先啟動 FastAPI 後端，再重新整理。</div>`);
    return;
  }

  teacherPanel = new TeacherPanel($('teacher-modal'), state.levels);
  refreshPlayerUi();
  refreshRoomUi();

  $('quick-msg-btns').innerHTML = QUICK_MESSAGES_LIST.map((q) => `<button type="button" data-q="${q.key}">${q.label}</button>`).join('');
  $('quick-emoji-btns').innerHTML = EMOJI_REACTIONS.map((e) => `<button type="button" data-e="${e}">${e}</button>`).join('');
  document.querySelectorAll('[data-q]').forEach((b) => b.addEventListener('click', () => {
    if (!state.room) { toast('💡 單人模式：這是給自己的小提醒——' + b.textContent); return; }
    roomSocket.sendQuickMessage(b.dataset.q, null);
  }));
  document.querySelectorAll('[data-e]').forEach((b) => b.addEventListener('click', () => state.room && roomSocket.sendQuickMessage(null, b.dataset.e)));

  // default level: teacher assignment > first uncompleted guided
  const completed = new Set((state.player.progress || []).filter((p) => p.completed).map((p) => p.level_code));
  const assign = state.player.teacher_assignments?.[0];
  const firstOpen = state.levels.find((l) => !completed.has(l.level_code)) || state.levels[0];
  await loadLevel(assign?.level_code || firstOpen.level_code, assign?.difficulty_tier || state.player.active_session?.assigned_difficulty || 'guided');
  openModal('main-menu-modal');

  // events
  $('btn-run-program').addEventListener('click', () => { soundManager.playClick(); if (!isEditor()) return; resetRun(true); startRun(); });
  $('btn-pause-program').addEventListener('click', togglePause);
  $('btn-step-program').addEventListener('click', stepRun);
  $('btn-reset-program').addEventListener('click', () => resetRun(false));
  $('btn-request-hint').addEventListener('click', requestHint);
  $('btn-next-hint-tier').addEventListener('click', requestHint);
  $('btn-close-hint').addEventListener('click', () => $('hint-drawer').classList.add('hidden'));
  $('btn-load-guided-example').addEventListener('click', loadExample);
  $('btn-editor-example').addEventListener('click', loadExample);
  $('btn-toggle-4step').addEventListener('click', () => $('four-step-panel').classList.toggle('hidden'));
  $('tab-mode-cards').addEventListener('click', () => setMode('cards'));
  $('tab-mode-blockly').addEventListener('click', () => setMode('blockly'));
  $('tab-mode-split').addEventListener('click', () => { state.showPython = !state.showPython; refreshPython(); setTimeout(() => workspace && Blockly.svgResize(workspace), 30); });
  $('btn-editor-undo').addEventListener('click', () => { if (state.mode === 'cards') cardEditor.undo(); else workspace?.undo(false); });
  $('btn-editor-redo').addEventListener('click', () => { if (state.mode === 'cards') cardEditor.redo(); else workspace?.undo(true); });
  $('btn-editor-clear').addEventListener('click', () => openModal('clear-confirm-modal'));
  $('btn-cancel-clear').addEventListener('click', () => closeModal('clear-confirm-modal'));
  $('btn-confirm-clear').addEventListener('click', () => {
    if (state.mode === 'cards') cardEditor.clearAll(); else { workspace.clear(); onEditorChanged(); }
    closeModal('clear-confirm-modal');
  });
  $('btn-pass-turn').addEventListener('click', async () => {
    try { state.room = await api.rotateRoomTurn(state.room.room_code, me()); refreshRoomUi(); } catch (e) { toast(`❌ ${e.message}`); }
  });
  document.querySelectorAll('.diff-btn').forEach((b) => b.addEventListener('click', () => loadLevel(state.level.level_code, b.dataset.diff)));

  $('btn-open-main-menu').addEventListener('click', () => openModal('main-menu-modal'));
  $('btn-open-level-modal').addEventListener('click', () => { renderLevelSelect(); openModal('level-select-modal'); });
  $('btn-close-levels').addEventListener('click', () => closeModal('level-select-modal'));
  $('btn-open-lobby').addEventListener('click', () => { renderLobby(); openModal('lobby-modal'); });
  $('btn-close-lobby').addEventListener('click', () => closeModal('lobby-modal'));
  $('btn-open-profile').addEventListener('click', () => { renderProfile(); openModal('profile-modal'); });
  $('btn-close-profile').addEventListener('click', () => closeModal('profile-modal'));
  $('btn-open-settings').addEventListener('click', () => { renderSettings(); openModal('settings-modal'); });
  $('btn-close-settings').addEventListener('click', () => closeModal('settings-modal'));
  $('btn-close-victory').addEventListener('click', () => closeModal('victory-modal'));
  $('btn-open-teacher').addEventListener('click', () => teacherPanel.open());

  $('btn-menu-continue').addEventListener('click', () => closeModal('main-menu-modal'));
  $('btn-menu-coop').addEventListener('click', () => { closeModal('main-menu-modal'); renderLobby(); openModal('lobby-modal'); });
  $('btn-menu-levels').addEventListener('click', () => { renderLevelSelect(); openModal('level-select-modal'); });
  $('btn-menu-customize').addEventListener('click', () => { renderProfile(); openModal('profile-modal'); });
  $('btn-menu-teacher').addEventListener('click', () => teacherPanel.open());
  $('btn-menu-settings').addEventListener('click', () => { renderSettings(); openModal('settings-modal'); });
  $('btn-save-menu-nickname').addEventListener('click', async () => {
    state.player = await api.updatePlayer(me(), { nickname: $('menu-nickname-input').value });
    refreshPlayerUi();
  });
  $('btn-menu-join-session').addEventListener('click', () => joinSession($('menu-session-code-input').value));

  window.addEventListener('beforeunload', () => { if (state.room) roomSocket.disconnect(); });
  window.__nova = { state, loadLevel, startRun };
}

init();

