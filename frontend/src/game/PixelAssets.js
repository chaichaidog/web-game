import { ROBOT_SKINS } from '../data/levelsData.js';

export function registerPixelAssets(scene) {
  // 1. Generate Robot Textures for each skin & frame
  ROBOT_SKINS.forEach((skin) => {
    [0, 1].forEach((frame) => {
      const key = `robot_${skin.id}_${frame}`;
      if (scene.textures.exists(key)) return;
      const canvas = scene.textures.createCanvas(key, 64, 64);
      const ctx = canvas.getContext();
      ctx.imageSmoothingEnabled = false;

      // Shadow
      ctx.fillStyle = 'rgba(0, 0, 0, 0.45)';
      ctx.fillRect(12, 48, 40, 10);

      // Treads / Wheels (facing Right / East = dir 0 by default so rotation works naturally)
      ctx.fillStyle = '#1e293b';
      const treadOffset = frame === 0 ? 0 : 2;
      ctx.fillRect(14 + treadOffset, 10, 34, 8);
      ctx.fillRect(14 - treadOffset, 46, 34, 8);
      ctx.fillStyle = '#64748b';
      ctx.fillRect(18 + treadOffset, 12, 6, 4);
      ctx.fillRect(32 + treadOffset, 12, 6, 4);
      ctx.fillRect(18 - treadOffset, 48, 6, 4);
      ctx.fillRect(32 - treadOffset, 48, 6, 4);

      // Chassis Body (Pixel Art)
      ctx.fillStyle = skin.primary;
      ctx.fillRect(12, 16, 38, 32);
      ctx.fillStyle = skin.secondary;
      ctx.fillRect(16, 20, 28, 24);

      // Core Emblem
      ctx.fillStyle = '#0f172a';
      ctx.fillRect(22, 26, 12, 12);
      ctx.fillStyle = skin.eye;
      ctx.fillRect(24, 28, 8, 8);

      // Front Visor & Direction Nose (Right side x=44..56 points Forward/East!)
      ctx.fillStyle = '#0f172a';
      ctx.fillRect(42, 20, 10, 24);
      ctx.fillStyle = skin.eye;
      ctx.fillRect(45, 22, 6, 7);
      ctx.fillRect(45, 35, 6, 7);

      // Front Directional Arrow Indicator on Chassis
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(52, 29, 6, 6);
      ctx.fillRect(49, 27, 3, 10);

      canvas.refresh();
    });
  });

  // 2. Energy Crystal (2 frames)
  [0, 1].forEach((f) => {
    const key = `energy_${f}`;
    if (scene.textures.exists(key)) return;
    const canvas = scene.textures.createCanvas(key, 64, 64);
    const ctx = canvas.getContext();
    const yOff = f === 0 ? 0 : -3;

    // Glow
    ctx.fillStyle = 'rgba(34, 211, 238, 0.25)';
    ctx.fillRect(14, 14 + yOff, 36, 36);

    // Diamond Crystal Pixel Art
    ctx.fillStyle = '#06b6d4';
    ctx.fillRect(28, 10 + yOff, 8, 44);
    ctx.fillRect(20, 18 + yOff, 24, 28);
    ctx.fillRect(14, 26 + yOff, 36, 12);

    ctx.fillStyle = '#67e8f9';
    ctx.fillRect(24, 20 + yOff, 16, 24);
    ctx.fillStyle = '#ecfeff';
    ctx.fillRect(28, 24 + yOff, 6, 12);

    canvas.refresh();
  });

  // 3. Obstacle (Sci-Fi Hazard Crate / Debris)
  if (!scene.textures.exists('tile_obstacle')) {
    const canvas = scene.textures.createCanvas('tile_obstacle', 64, 64);
    const ctx = canvas.getContext();
    ctx.fillStyle = '#334155';
    ctx.fillRect(6, 6, 52, 52);
    ctx.fillStyle = '#1e293b';
    ctx.fillRect(10, 10, 44, 44);
    // Hazard stripes
    ctx.fillStyle = '#f43f5e';
    ctx.fillRect(12, 12, 12, 8);
    ctx.fillRect(30, 12, 12, 8);
    ctx.fillRect(12, 44, 12, 8);
    ctx.fillRect(30, 44, 12, 8);
    // Cross brace
    ctx.fillStyle = '#64748b';
    ctx.fillRect(16, 28, 32, 8);
    ctx.fillRect(28, 16, 8, 32);
    ctx.fillStyle = '#fb7185';
    ctx.fillRect(28, 28, 8, 8);
    canvas.refresh();
  }

  // 4. Switch OFF & ON
  ['off', 'on'].forEach((st) => {
    const key = `switch_${st}`;
    if (scene.textures.exists(key)) return;
    const canvas = scene.textures.createCanvas(key, 64, 64);
    const ctx = canvas.getContext();
    ctx.fillStyle = '#1e293b';
    ctx.fillRect(10, 10, 44, 44);
    ctx.fillStyle = st === 'on' ? '#10b981' : '#a855f7';
    ctx.fillRect(16, 16, 32, 32);
    ctx.fillStyle = st === 'on' ? '#a7f3d0' : '#3b0764';
    ctx.fillRect(22, 22, 20, 20);
    canvas.refresh();
  });

  // 5. Door CLOSED & OPEN
  ['closed', 'open'].forEach((st) => {
    const key = `door_${st}`;
    if (scene.textures.exists(key)) return;
    const canvas = scene.textures.createCanvas(key, 64, 64);
    const ctx = canvas.getContext();
    if (st === 'closed') {
      ctx.fillStyle = '#475569';
      ctx.fillRect(4, 4, 56, 56);
      ctx.fillStyle = '#f59e0b';
      ctx.fillRect(8, 26, 48, 12);
      ctx.fillStyle = '#ef4444';
      ctx.fillRect(24, 22, 16, 20);
      ctx.fillStyle = '#fecaca';
      ctx.fillRect(28, 26, 8, 12);
    } else {
      ctx.fillStyle = 'rgba(16, 185, 129, 0.2)';
      ctx.fillRect(6, 6, 52, 52);
      ctx.fillStyle = '#10b981';
      ctx.fillRect(4, 4, 10, 56);
      ctx.fillRect(50, 4, 10, 56);
    }
    canvas.refresh();
  });

  // 6. Generator Device BROKEN & REPAIRED
  ['broken', 'repaired'].forEach((st) => {
    const key = `device_${st}`;
    if (scene.textures.exists(key)) return;
    const canvas = scene.textures.createCanvas(key, 64, 64);
    const ctx = canvas.getContext();
    ctx.fillStyle = '#334155';
    ctx.fillRect(8, 8, 48, 48);
    ctx.fillStyle = st === 'repaired' ? '#059669' : '#9a3412';
    ctx.fillRect(14, 14, 36, 36);
    ctx.fillStyle = st === 'repaired' ? '#34d399' : '#fb923c';
    ctx.fillRect(22, 22, 20, 20);
    if (st === 'repaired') {
      ctx.fillStyle = '#ecfdf5';
      ctx.fillRect(28, 28, 8, 8);
    }
    canvas.refresh();
  });

  // 7. Start & Goal Pads
  if (!scene.textures.exists('pad_start')) {
    const canvas = scene.textures.createCanvas('pad_start', 64, 64);
    const ctx = canvas.getContext();
    ctx.fillStyle = 'rgba(56, 189, 248, 0.22)';
    ctx.fillRect(6, 6, 52, 52);
    ctx.fillStyle = '#38bdf8';
    ctx.fillRect(6, 6, 14, 4);
    ctx.fillRect(6, 6, 4, 14);
    ctx.fillRect(44, 6, 14, 4);
    ctx.fillRect(54, 6, 4, 14);
    ctx.fillRect(6, 54, 14, 4);
    ctx.fillRect(6, 44, 4, 14);
    ctx.fillRect(44, 54, 14, 4);
    ctx.fillRect(54, 44, 4, 14);
    canvas.refresh();
  }

  if (!scene.textures.exists('pad_goal')) {
    const canvas = scene.textures.createCanvas('pad_goal', 64, 64);
    const ctx = canvas.getContext();
    ctx.fillStyle = 'rgba(16, 185, 129, 0.28)';
    ctx.fillRect(6, 6, 52, 52);
    ctx.fillStyle = '#10b981';
    ctx.fillRect(10, 10, 44, 4);
    ctx.fillRect(10, 50, 44, 4);
    ctx.fillRect(10, 10, 4, 44);
    ctx.fillRect(50, 10, 4, 44);
    ctx.fillStyle = '#6ee7b7';
    ctx.fillRect(22, 22, 20, 20);
    ctx.fillStyle = '#064e3b';
    ctx.fillRect(26, 26, 12, 12);
    canvas.refresh();
  }

  // 8. Floor Guidance Arrow (pointing Right/East by default)
  if (!scene.textures.exists('floor_arrow')) {
    const canvas = scene.textures.createCanvas('floor_arrow', 64, 64);
    const ctx = canvas.getContext();
    ctx.fillStyle = 'rgba(56, 189, 248, 0.45)';
    ctx.fillRect(14, 28, 22, 8);
    ctx.fillRect(32, 20, 6, 24);
    ctx.fillRect(38, 24, 6, 16);
    ctx.fillRect(44, 28, 6, 8);
    canvas.refresh();
  }
}

