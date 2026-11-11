function resolveApiBase() {
  const explicit = (import.meta.env.VITE_API_URL || '').trim().replace(/\/$/, '');
  if (explicit) return explicit;
  const host = (import.meta.env.VITE_BACKEND_HOST || '').trim();
  if (host) {
    const fullHost = host.includes('.') ? host : `${host}.onrender.com`;
    return `https://${fullHost}`;
  }
  return '';
}

const API_BASE = resolveApiBase();

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };
  const res = await fetch(url, {
    ...options,
    headers,
  });
  if (!res.ok) {
    let errMsg = `HTTP ${res.status}`;
    try {
      const errJson = await res.json();
      errMsg = errJson.detail || errJson.message || errMsg;
    } catch {
      // ignore
    }
    throw new Error(errMsg);
  }
  return res.json();
}

export const api = {
  // Players
  createOrGetPlayer(nickname, playerCode = null, characterSkin = 'nova_scout') {
    return request('/api/players', {
      method: 'POST',
      body: JSON.stringify({
        nickname,
        player_code: playerCode,
        character_skin: characterSkin,
      }),
    });
  },

  getPlayer(playerCode) {
    return request(`/api/players/${encodeURIComponent(playerCode)}`);
  },

  updatePlayer(playerCode, updates) {
    return request(`/api/players/${encodeURIComponent(playerCode)}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  },

  updateSettings(playerCode, settings) {
    return request(`/api/players/${encodeURIComponent(playerCode)}/settings`, {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  },

  saveWorkspace(playerCode, levelCode, difficultyTier, workspaceData) {
    return request('/api/players/workspace/save', {
      method: 'POST',
      body: JSON.stringify({
        player_code: playerCode,
        level_code: levelCode,
        difficulty_tier: difficultyTier,
        workspace_data: workspaceData,
      }),
    });
  },

  loadWorkspace(playerCode, levelCode, difficultyTier = 'guided') {
    return request(
      `/api/players/${encodeURIComponent(playerCode)}/workspace/${encodeURIComponent(levelCode)}?difficulty_tier=${encodeURIComponent(difficultyTier)}`
    );
  },

  recordLearningEvent(eventPayload) {
    return request('/api/players/events', {
      method: 'POST',
      body: JSON.stringify(eventPayload),
    });
  },

  // Levels
  getLevels() {
    return request('/api/levels');
  },

  getLevelDetail(levelCode, difficultyTier = 'guided') {
    return request(
      `/api/levels/${encodeURIComponent(levelCode)}?difficulty_tier=${encodeURIComponent(difficultyTier)}`
    );
  },

  submitLevelProgram(levelCode, payload) {
    return request(`/api/levels/${encodeURIComponent(levelCode)}/submit`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // Rooms (1~4 Players)
  createRoom(playerCode, levelCode = 'ch1_lv1', difficultyTier = 'guided', sessionCode = null) {
    return request('/api/rooms', {
      method: 'POST',
      body: JSON.stringify({
        player_code: playerCode,
        level_code: levelCode,
        difficulty_tier: difficultyTier,
        session_code: sessionCode,
      }),
    });
  },

  joinRoom(playerCode, roomCode) {
    return request('/api/rooms/join', {
      method: 'POST',
      body: JSON.stringify({
        player_code: playerCode,
        room_code: roomCode,
      }),
    });
  },

  leaveRoom(playerCode, roomCode) {
    return request('/api/rooms/leave', {
      method: 'POST',
      body: JSON.stringify({
        player_code: playerCode,
        room_code: roomCode,
      }),
    });
  },

  getRoomInfo(roomCode) {
    return request(`/api/rooms/${encodeURIComponent(roomCode)}`);
  },

  startOrChangeRoomLevel(roomCode, playerCode, levelCode, difficultyTier) {
    return request(`/api/rooms/${encodeURIComponent(roomCode)}/start`, {
      method: 'POST',
      body: JSON.stringify({
        player_code: playerCode,
        level_code: levelCode,
        difficulty_tier: difficultyTier,
      }),
    });
  },

  rotateRoomTurn(roomCode, playerCode) {
    return request(`/api/rooms/${encodeURIComponent(roomCode)}/rotate`, {
      method: 'POST',
      body: JSON.stringify({
        player_code: playerCode,
      }),
    });
  },

  // Classroom Sessions (Student join)
  joinTeachingSession(playerCode, sessionCode) {
    return request('/api/sessions/join', {
      method: 'POST',
      body: JSON.stringify({
        player_code: playerCode,
        session_code: sessionCode,
      }),
    });
  },

  // Teacher Dashboard APIs
  teacherLogin(passkey, displayName = '資訊科技教師') {
    return request('/api/teacher/login', {
      method: 'POST',
      body: JSON.stringify({
        passkey,
        display_name: displayName,
      }),
    });
  },

  teacherCreateSession(token, displayName, expiresHours = 24) {
    return request('/api/teacher/sessions', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({
        display_name: displayName,
        expires_hours: expiresHours,
      }),
    });
  },

  teacherListSessions(token) {
    return request('/api/teacher/sessions', {
      headers: { Authorization: `Bearer ${token}` },
    });
  },

  teacherUpdateSession(token, sessionCode, status = 'closed', extendHours = 0) {
    return request(
      `/api/teacher/sessions/${encodeURIComponent(sessionCode)}?status=${encodeURIComponent(status)}&extend_hours=${extendHours}`,
      {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${token}` },
      }
    );
  },

  teacherGetOverview(token, sessionCode) {
    return request(`/api/teacher/sessions/${encodeURIComponent(sessionCode)}/overview`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  },

  teacherGetStudentDetail(token, sessionCode, playerCode) {
    return request(
      `/api/teacher/sessions/${encodeURIComponent(sessionCode)}/students/${encodeURIComponent(playerCode)}`,
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );
  },

  teacherAssignTask(token, sessionCode, payload) {
    return request(`/api/teacher/sessions/${encodeURIComponent(sessionCode)}/assign`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify(payload),
    });
  },

  teacherOverrideDifficulty(token, sessionCode, payload) {
    return request(`/api/teacher/sessions/${encodeURIComponent(sessionCode)}/difficulty`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify(payload),
    });
  },

  teacherExportSummary(token, sessionCode) {
    return request(`/api/teacher/sessions/${encodeURIComponent(sessionCode)}/export`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  },
};

