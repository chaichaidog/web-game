import { BLOCK_CATALOG } from '../data/levelsData.js';

export class UIManager {
  static renderBlockGuideCatalog(allowedBlocks = []) {
    const allowedSet = new Set(allowedBlocks || []);
    const entries = Object.entries(BLOCK_CATALOG);

    const unlockedHtml = entries
      .filter(([key]) => allowedSet.has(key))
      .map(
        ([, info]) => `
        <div class="skin-card" style="border-left: 4px solid ${info.color}">
          <strong>${info.label}</strong> <span class="badge-pill">${info.category}</span>
          <p style="margin:4px 0;font-size:0.85em;">${info.desc}</p>
          <small class="muted-note">🎬 小示範：${info.demo}</small>
        </div>
      `
      )
      .join('');

    const lockedHtml = entries
      .filter(([key]) => !allowedSet.has(key))
      .map(
        ([, info]) => `
        <div class="skin-card ach-card locked">
          <strong>🔒 ${info.label}</strong> <span class="badge-pill">${info.category}</span>
          <p style="margin:4px 0;font-size:0.85em;">${info.desc}</p>
          <small class="muted-note">（後續章節解鎖預覽，目前關卡無須使用）</small>
        </div>
      `
      )
      .join('');

    return `
      <h3>✅ 本關已解鎖積木與指令說明</h3>
      <div class="skin-grid">${unlockedHtml || '<p class="muted-note">基本移動積木</p>'}</div>
      <h3 style="margin-top:12px;">🔒 後續章節概念預覽（現在無須理解）</h3>
      <div class="skin-grid">${lockedHtml}</div>
    `;
  }
}

