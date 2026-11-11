export class RoomSocketClient {
  constructor() {
    this.ws = null;
    this.roomCode = null;
    this.playerCode = null;
    this.listeners = new Set();
    this.reconnectTimer = null;
    this.manualClose = false;
  }

  onMessage(callback) {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  connect(roomCode, playerCode) {
    this.disconnect();
    this.manualClose = false;
    this.roomCode = roomCode;
    this.playerCode = playerCode;
    this._openSocket();
  }

  _openSocket() {
    if (!this.roomCode || !this.playerCode) return;

    let wsBase = import.meta.env.VITE_WS_URL || '';
    if (!wsBase && typeof window !== 'undefined') {
      const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      wsBase = `${proto}//${window.location.host}`;
    }
    wsBase = wsBase.replace(/\/$/, '');

    const url = `${wsBase}/ws/rooms/${encodeURIComponent(this.roomCode)}?player_code=${encodeURIComponent(this.playerCode)}`;
    try {
      this.ws = new WebSocket(url);
      this.ws.onopen = () => {
        this._emit({ type: 'ws_connected', room_code: this.roomCode });
      };
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this._emit(data);
        } catch {
          // ignore malformed frame
        }
      };
      this.ws.onclose = () => {
        if (!this.manualClose && this.roomCode) {
          this.reconnectTimer = setTimeout(() => this._openSocket(), 2500);
        }
      };
      this.ws.onerror = () => {
        // handled by onclose
      };
    } catch {
      // ignore offline socket error
    }
  }

  send(payload) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(payload));
    }
  }

  sendWorkspaceUpdate(workspaceState) {
    this.send({
      type: 'editor_state_updated',
      workspace_state: workspaceState,
    });
  }

  sendEditorLock(locked) {
    this.send({
      type: 'editor_lock_changed',
      locked: Boolean(locked),
    });
  }

  sendRobotAction(actionData) {
    this.send({
      type: 'robot_action',
      action_data: actionData,
    });
  }

  sendQuickMessage(messageKey = null, emoji = null) {
    this.send({
      type: 'quick_message',
      message_key: messageKey,
      emoji,
    });
  }

  disconnect() {
    this.manualClose = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      try {
        this.ws.close();
      } catch {
        // ignore
      }
      this.ws = null;
    }
    this.roomCode = null;
  }

  _emit(data) {
    for (const cb of this.listeners) {
      try {
        cb(data);
      } catch (err) {
        console.error('WS listener error:', err);
      }
    }
  }
}

export const roomSocket = new RoomSocketClient();

