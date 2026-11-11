import Phaser from 'phaser';
import { registerPixelAssets } from './PixelAssets.js';
import { ZONE_THEMES, HEAD_ACCESSORIES } from '../data/levelsData.js';
import { soundManager } from '../services/audio.js';

export class GameScene extends Phaser.Scene {
  constructor() {
    super({ key: 'GameScene' });
    this.levelData = null;
    this.skinId = 'nova_scout';
    this.accessoryId = 'antenna_basic';
    this.animationLevel = 'normal'; // normal | fast | reduced
    this.tileSize = 58;
    this.offsetX = 48;
    this.offsetY = 48;

    this.robotSprite = null;
    this.accessoryText = null;
    this.trailGraphics = null;
    this.itemSprites = [];
    this.switchSprites = [];
    this.doorSprites = [];
    this.deviceSprites = [];
    this.frameTimer = null;
    this.currentFrame = 0;
  }

  create() {
    registerPixelAssets(this);
    this.rootContainer = this.add.container(0, 0);

    // Idle animation timer for robot & crystals
    this.frameTimer = this.time.addEvent({
      delay: 450,
      loop: true,
      callback: () => {
        if (this.animationLevel === 'reduced') return;
        this.currentFrame = this.currentFrame === 0 ? 1 : 0;
        if (this.robotSprite && this.robotSprite.active) {
          this.robotSprite.setTexture(`robot_${this.skinId}_${this.currentFrame}`);
        }
        this.itemSprites.forEach((sp) => {
          if (sp.sprite && sp.sprite.active && sp.sprite.visible) {
            sp.sprite.setTexture(`energy_${this.currentFrame}`);
          }
        });
      },
    });

    if (this.levelData) {
      this.renderLevel(this.levelData);
    }

    this.scale.on('resize', () => {
      if (this.levelData) {
        this.renderLevel(this.levelData);
      }
    });
  }

  setPlayerAppearance(skinId, accessoryId, animationLevel = 'normal') {
    this.skinId = skinId || 'nova_scout';
    this.accessoryId = accessoryId || 'antenna_basic';
    this.animationLevel = animationLevel || 'normal';
    if (this.robotSprite && this.scene.isActive()) {
      this.robotSprite.setTexture(`robot_${this.skinId}_0`);
    }
    if (this.accessoryText && this.scene.isActive()) {
      const acc = HEAD_ACCESSORIES.find((a) => a.id === this.accessoryId);
      this.accessoryText.setText(acc ? acc.icon : '📡');
    }
  }

  loadLevelData(levelData) {
    this.levelData = JSON.parse(JSON.stringify(levelData));
    if (this.scene && this.scene.isActive() && this.rootContainer) {
      this.renderLevel(this.levelData);
    }
  }

  gridToPixel(gx, gy) {
    return {
      x: this.offsetX + gx * this.tileSize + this.tileSize / 2,
      y: this.offsetY + gy * this.tileSize + this.tileSize / 2,
    };
  }

  renderLevel(data) {
    if (!this.rootContainer) return;
    this.tweens.killAll();
    this.rootContainer.removeAll(true);
    this.itemSprites = [];
    this.switchSprites = [];
    this.doorSprites = [];
    this.deviceSprites = [];

    const width = data.width || 7;
    const height = data.height || 6;
    const canvasW = this.scale.width || 620;
    const canvasH = this.scale.height || 460;

    const maxTileW = Math.floor((canvasW - 72) / width);
    const maxTileH = Math.floor((canvasH - 72) / height);
    this.tileSize = Math.max(40, Math.min(64, maxTileW, maxTileH));

    const mapPixelW = width * this.tileSize;
    const mapPixelH = height * this.tileSize;
    this.offsetX = Math.floor((canvasW - mapPixelW) / 2);
    this.offsetY = Math.floor((canvasH - mapPixelH) / 2) + 8;

    const theme = ZONE_THEMES[data.zone] || ZONE_THEMES.zone_control;
    this.cameras.main.setBackgroundColor(theme.bg);

    // Outer ambient border frame
    const bgFrame = this.add.graphics();
    bgFrame.fillStyle(0x090d16, 0.75);
    bgFrame.fillRoundedRect(this.offsetX - 12, this.offsetY - 12, mapPixelW + 24, mapPixelH + 24, 10);
    bgFrame.lineStyle(2, Phaser.Display.Color.HexStringToColor(theme.accent).color, 0.45);
    bgFrame.strokeRoundedRect(this.offsetX - 12, this.offsetY - 12, mapPixelW + 24, mapPixelH + 24, 10);
    this.rootContainer.add(bgFrame);

    // Grid tiles & coordinate numbers
    const gridGfx = this.add.graphics();
    const colorA = Phaser.Display.Color.HexStringToColor(theme.floorA).color;
    const colorB = Phaser.Display.Color.HexStringToColor(theme.floorB).color;
    const wallColor = Phaser.Display.Color.HexStringToColor(theme.wall).color;

    for (let gx = 0; gx < width; gx++) {
      const topLabel = this.add
        .text(this.offsetX + gx * this.tileSize + this.tileSize / 2, this.offsetY - 22, `${gx}`, {
          fontFamily: 'monospace',
          fontSize: '12px',
          color: '#94a3b8',
        })
        .setOrigin(0.5);
      this.rootContainer.add(topLabel);
    }

    for (let gy = 0; gy < height; gy++) {
      const leftLabel = this.add
        .text(this.offsetX - 20, this.offsetY + gy * this.tileSize + this.tileSize / 2, `${gy}`, {
          fontFamily: 'monospace',
          fontSize: '12px',
          color: '#94a3b8',
        })
        .setOrigin(0.5);
      this.rootContainer.add(leftLabel);

      for (let gx = 0; gx < width; gx++) {
        const px = this.offsetX + gx * this.tileSize;
        const py = this.offsetY + gy * this.tileSize;
        const isEven = (gx + gy) % 2 === 0;
        gridGfx.fillStyle(isEven ? colorA : colorB, 1);
        gridGfx.fillRect(px + 1, py + 1, this.tileSize - 2, this.tileSize - 2);
        gridGfx.lineStyle(1, wallColor, 0.35);
        gridGfx.strokeRect(px, py, this.tileSize, this.tileSize);
      }
    }
    this.rootContainer.add(gridGfx);

    const scaleRatio = this.tileSize / 64;

    // Floor guidance arrows (Guided difficulty)
    (data.floor_arrows || []).forEach((arr) => {
      const pos = this.gridToPixel(arr.x, arr.y);
      const sp = this.add.image(pos.x, pos.y, 'floor_arrow').setScale(scaleRatio);
      sp.setAngle((arr.dir || 0) * 90);
      this.rootContainer.add(sp);
    });

    // Start & Goal Pads
    if (data.start) {
      const sPos = this.gridToPixel(data.start.x, data.start.y);
      const sPad = this.add.image(sPos.x, sPos.y, 'pad_start').setScale(scaleRatio);
      this.rootContainer.add(sPad);
    }
    if (data.goal) {
      const gPos = this.gridToPixel(data.goal.x, data.goal.y);
      const gPad = this.add.image(gPos.x, gPos.y, 'pad_goal').setScale(scaleRatio);
      const gLabel = this.add
        .text(gPos.x, gPos.y + this.tileSize * 0.32, '終點', {
          fontFamily: 'sans-serif',
          fontSize: '11px',
          fontStyle: 'bold',
          color: '#6ee7b7',
          backgroundColor: 'rgba(6,78,59,0.8)',
          padding: { x: 3, y: 1 },
        })
        .setOrigin(0.5);
      this.rootContainer.add([gPad, gLabel]);
    }

    // Obstacles
    (data.obstacles || []).forEach((ob) => {
      const pos = this.gridToPixel(ob.x, ob.y);
      const sp = this.add.image(pos.x, pos.y, 'tile_obstacle').setScale(scaleRatio);
      this.rootContainer.add(sp);
    });

    // Switches
    (data.switches || []).forEach((sw) => {
      const pos = this.gridToPixel(sw.x, sw.y);
      const sp = this.add.image(pos.x, pos.y, 'switch_off').setScale(scaleRatio);
      const lbl = this.add
        .text(pos.x, pos.y - this.tileSize * 0.32, '開關', {
          fontFamily: 'sans-serif',
          fontSize: '10px',
          color: '#e9d5ff',
          backgroundColor: 'rgba(59,7,100,0.75)',
          padding: { x: 2, y: 1 },
        })
        .setOrigin(0.5);
      this.rootContainer.add([sp, lbl]);
      this.switchSprites.push({ x: sw.x, y: sw.y, id: sw.id, sprite: sp, active: false });
    });

    // Doors
    (data.doors || []).forEach((dr) => {
      const pos = this.gridToPixel(dr.x, dr.y);
      const isOpen = Boolean(dr.open);
      const sp = this.add.image(pos.x, pos.y, isOpen ? 'door_open' : 'door_closed').setScale(scaleRatio);
      const lbl = this.add
        .text(pos.x, pos.y - this.tileSize * 0.34, isOpen ? '已開' : `閘門(${dr.requires_energy || 0}⚡)`, {
          fontFamily: 'sans-serif',
          fontSize: '10px',
          color: '#fef08a',
          backgroundColor: 'rgba(30,41,59,0.85)',
          padding: { x: 2, y: 1 },
        })
        .setOrigin(0.5);
      this.rootContainer.add([sp, lbl]);
      this.doorSprites.push({ x: dr.x, y: dr.y, sprite: sp, label: lbl, open: isOpen });
    });

    // Devices
    (data.devices || []).forEach((dv) => {
      const pos = this.gridToPixel(dv.x, dv.y);
      const sp = this.add.image(pos.x, pos.y, 'device_broken').setScale(scaleRatio);
      const lbl = this.add
        .text(pos.x, pos.y - this.tileSize * 0.34, `待修(${dv.requires_energy || 1}⚡)`, {
          fontFamily: 'sans-serif',
          fontSize: '10px',
          color: '#fed7aa',
          backgroundColor: 'rgba(124,45,18,0.85)',
          padding: { x: 2, y: 1 },
        })
        .setOrigin(0.5);
      this.rootContainer.add([sp, lbl]);
      this.deviceSprites.push({ x: dv.x, y: dv.y, sprite: sp, label: lbl, repaired: false });
    });

    // Items (Energy Crystals)
    (data.items || []).forEach((item) => {
      const pos = this.gridToPixel(item.x, item.y);
      const sp = this.add.image(pos.x, pos.y, 'energy_0').setScale(scaleRatio);
      this.rootContainer.add(sp);
      this.itemSprites.push({ x: item.x, y: item.y, sprite: sp, collected: false });
    });

    // Breadcrumb Path Trail Layer
    this.trailGraphics = this.add.graphics();
    this.rootContainer.add(this.trailGraphics);

    // Robot Sprite
    const start = data.start || { x: 1, y: 1, dir: 0 };
    const rPos = this.gridToPixel(start.x, start.y);
    this.robotSprite = this.add
      .image(rPos.x, rPos.y, `robot_${this.skinId}_0`)
      .setScale(scaleRatio * 0.96);
    this.robotSprite.setAngle((start.dir || 0) * 90);

    const acc = HEAD_ACCESSORIES.find((a) => a.id === this.accessoryId);
    this.accessoryText = this.add
      .text(rPos.x, rPos.y - this.tileSize * 0.34, acc ? acc.icon : '📡', {
        fontSize: `${Math.round(this.tileSize * 0.28)}px`,
      })
      .setOrigin(0.5);

    this.rootContainer.add([this.robotSprite, this.accessoryText]);
    this.lastRobotGrid = { x: start.x, y: start.y, dir: start.dir || 0 };
  }

  resetMapState() {
    if (this.levelData) {
      this.renderLevel(this.levelData);
    }
  }

  showFloatingPopup(gx, gy, text, color = '#38bdf8') {
    if (!this.rootContainer) return;
    const pos = this.gridToPixel(gx, gy);
    const popup = this.add
      .text(pos.x, pos.y - 12, text, {
        fontFamily: 'sans-serif',
        fontSize: '13px',
        fontStyle: 'bold',
        color,
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        padding: { x: 6, y: 3 },
      })
      .setOrigin(0.5);
    this.rootContainer.add(popup);

    this.tweens.add({
      targets: popup,
      y: pos.y - 38,
      alpha: 0,
      duration: 850,
      onComplete: () => popup.destroy(),
    });
  }

  animateStep(stepEvent, durationMs = 360) {
    return new Promise((resolve) => {
      if (!this.robotSprite || !this.scene.isActive()) {
        resolve();
        return;
      }

      const effectiveDuration =
        this.animationLevel === 'reduced'
          ? 40
          : this.animationLevel === 'fast'
            ? Math.max(80, Math.floor(durationMs * 0.5))
            : durationMs;

      const prevPos = this.gridToPixel(this.lastRobotGrid.x, this.lastRobotGrid.y);
      const nextPos = this.gridToPixel(stepEvent.x, stepEvent.y);
      const action = stepEvent.action;

      if (action === 'move_forward' || action === 'move_backward') {
        soundManager.playMove();
        if (this.trailGraphics) {
          this.trailGraphics.lineStyle(3, 0x38bdf8, 0.55);
          this.trailGraphics.lineBetween(prevPos.x, prevPos.y, nextPos.x, nextPos.y);
          this.trailGraphics.fillStyle(0x38bdf8, 0.75);
          this.trailGraphics.fillCircle(nextPos.x, nextPos.y, 4);
        }
        this.tweens.add({
          targets: this.robotSprite,
          x: nextPos.x,
          y: nextPos.y,
          duration: effectiveDuration,
          ease: 'Sine.easeInOut',
          onUpdate: () => {
            if (this.accessoryText) {
              this.accessoryText.setPosition(this.robotSprite.x, this.robotSprite.y - this.tileSize * 0.34);
            }
          },
          onComplete: () => {
            this.lastRobotGrid = { x: stepEvent.x, y: stepEvent.y, dir: stepEvent.dir };
            resolve();
          },
        });
      } else if (action === 'turn_left' || action === 'turn_right') {
        soundManager.playTurn();
        const targetAngle = stepEvent.dir * 90;
        this.robotSprite.setAngle(targetAngle);
        this.lastRobotGrid.dir = stepEvent.dir;
        this.time.delayedCall(effectiveDuration * 0.7, () => resolve());
      } else if (action === 'pickup') {
        const itemObj = this.itemSprites.find(
          (it) => !it.collected && it.x === stepEvent.x && it.y === stepEvent.y
        );
        if (itemObj) {
          itemObj.collected = true;
          itemObj.sprite.setVisible(false);
          soundManager.playPickup();
          this.showFloatingPopup(stepEvent.x, stepEvent.y, '+1 ⚡能源晶片', '#22d3ee');
        } else {
          this.showFloatingPopup(stepEvent.x, stepEvent.y, '❓ 此處無能源', '#fbbf24');
        }
        this.time.delayedCall(effectiveDuration * 0.75, () => resolve());
      } else if (action === 'activate_switch' || action === 'pulse_lock') {
        const swObj = this.switchSprites.find((s) => s.x === stepEvent.x && s.y === stepEvent.y);
        if (swObj) {
          swObj.active = true;
          swObj.sprite.setTexture('switch_on');
          soundManager.playSwitch();
          this.showFloatingPopup(stepEvent.x, stepEvent.y, '🔘 開關已啟動！', '#34d399');
        }
        // Check if auto-door should open
        if (this.switchSprites.length > 0 && this.switchSprites.every((s) => s.active)) {
          this.doorSprites.forEach((d) => {
            if (!d.open) {
              d.open = true;
              d.sprite.setTexture('door_open');
              d.label.setText('已開');
            }
          });
        }
        this.time.delayedCall(effectiveDuration * 0.75, () => resolve());
      } else if (action === 'open_door') {
        soundManager.playDoorOpen();
        this.doorSprites.forEach((d) => {
          d.open = true;
          d.sprite.setTexture('door_open');
          d.label.setText('已開');
        });
        this.showFloatingPopup(stepEvent.x, stepEvent.y, '🚪 安全閘門已開啟！', '#34d399');
        this.time.delayedCall(effectiveDuration * 0.75, () => resolve());
      } else if (action === 'repair_device') {
        const devObj = this.deviceSprites.find((d) => d.x === stepEvent.x && d.y === stepEvent.y);
        if (devObj) {
          devObj.repaired = true;
          devObj.sprite.setTexture('device_repaired');
          devObj.label.setText('已修復✨');
          soundManager.playRepair();
          this.showFloatingPopup(stepEvent.x, stepEvent.y, '🔧 設備修復完成！', '#fde047');
        }
        this.time.delayedCall(effectiveDuration * 0.85, () => resolve());
      } else {
        this.time.delayedCall(effectiveDuration * 0.4, () => resolve());
      }
    });
  }

  playErrorEffect(message = '指令執行受阻！') {
    soundManager.playError();
    if (!this.robotSprite) return;
    this.showFloatingPopup(this.lastRobotGrid.x, this.lastRobotGrid.y, '⚠️ 執行受阻！', '#f43f5e');
    this.tweens.add({
      targets: this.robotSprite,
      x: this.robotSprite.x + 6,
      duration: 55,
      yoyo: true,
      repeat: 3,
    });
  }

  playVictoryEffect() {
    soundManager.playSuccess();
    if (!this.robotSprite) return;
    this.showFloatingPopup(this.lastRobotGrid.x, this.lastRobotGrid.y, '🎉 任務成功！', '#34d399');
    this.tweens.add({
      targets: this.robotSprite,
      scaleX: this.robotSprite.scaleX * 1.18,
      scaleY: this.robotSprite.scaleY * 1.18,
      duration: 180,
      yoyo: true,
      repeat: 1,
    });
  }
}

