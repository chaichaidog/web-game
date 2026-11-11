// Web Audio API Sci-Fi Sound Synthesizer for NOVA Protocol
class SoundManager {
  constructor() {
    this.ctx = null;
    this.enabled = true;
  }

  init() {
    if (!this.ctx && typeof window !== 'undefined') {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume().catch(() => {});
    }
  }

  setEnabled(val) {
    this.enabled = Boolean(val);
  }

  playTone(freq, type = 'sine', duration = 0.12, volume = 0.12, slideFreq = null) {
    if (!this.enabled) return;
    try {
      this.init();
      if (!this.ctx) return;
      const now = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(freq, now);
      if (slideFreq) {
        osc.frequency.exponentialRampToValueAtTime(slideFreq, now + duration);
      }
      gain.gain.setValueAtTime(volume, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + duration);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start(now);
      osc.stop(now + duration);
    } catch {
      // Ignore audio errors on restricted autoplay
    }
  }

  playMove() {
    this.playTone(260, 'triangle', 0.09, 0.1, 320);
  }

  playTurn() {
    this.playTone(380, 'sine', 0.08, 0.09, 440);
  }

  playPickup() {
    this.playTone(523.25, 'sine', 0.1, 0.14, 783.99);
    setTimeout(() => this.playTone(1046.5, 'triangle', 0.16, 0.12), 70);
  }

  playSwitch() {
    this.playTone(440, 'square', 0.1, 0.08, 660);
  }

  playDoorOpen() {
    this.playTone(180, 'sawtooth', 0.22, 0.09, 420);
  }

  playRepair() {
    [440, 554.37, 659.25].forEach((f, idx) => {
      setTimeout(() => this.playTone(f, 'triangle', 0.14, 0.12), idx * 70);
    });
  }

  playSuccess() {
    [523.25, 659.25, 783.99, 1046.5].forEach((f, idx) => {
      setTimeout(() => this.playTone(f, 'triangle', 0.18, 0.15), idx * 90);
    });
  }

  playError() {
    this.playTone(220, 'sawtooth', 0.18, 0.12, 130);
    setTimeout(() => this.playTone(150, 'sawtooth', 0.22, 0.12, 110), 140);
  }

  playClick() {
    this.playTone(600, 'sine', 0.04, 0.06, 750);
  }

  playJoin() {
    this.playTone(480, 'sine', 0.1, 0.1, 720);
  }
}

export const soundManager = new SoundManager();

