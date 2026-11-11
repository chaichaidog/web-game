const DIR_VECTORS = {
  0: [1, 0],
  1: [0, 1],
  2: [-1, 0],
  3: [0, -1],
};

const DIR_NAMES = {
  0: '右方(東)',
  1: '下方(南)',
  2: '左方(西)',
  3: '上方(北)',
};

const ACTION_LABELS = {
  move_forward: '⬆️ 前進一步',
  move_backward: '⬇️ 後退一步',
  turn_left: '↩️ 向左轉',
  turn_right: '↪️ 向右轉',
  pickup: '⚡ 撿取能源',
  activate_switch: '🔘 啟動開關',
  open_door: '🚪 開啟閘門',
  repair_device: '🔧 修復設備',
  scan_ahead: '📡 掃描前方',
  var_set: '🔢 設定變數',
  var_change: '🔢 修改變數',
};

export function compileAndSimulate(programAst, levelData, limits = {}) {
  const MAX_INSTRUCTIONS = limits.maxInstructions || 200;
  const MAX_LOOP = limits.maxLoop || 100;
  const MAX_STEPS = limits.maxSteps || 500;
  const MAX_DEPTH = limits.maxDepth || 6;

  function countAst(nodes, depth = 1) {
    if (!Array.isArray(nodes)) return { count: 0, maxDepth: depth };
    let count = 0;
    let maxD = depth;
    for (const n of nodes) {
      if (!n || typeof n !== 'object') continue;
      count += 1;
      for (const k of ['body', 'then_body', 'else_body']) {
        if (Array.isArray(n[k])) {
          const sub = countAst(n[k], depth + 1);
          count += sub.count;
          if (sub.maxDepth > maxD) maxD = sub.maxDepth;
        }
      }
    }
    return { count, maxDepth: maxD };
  }

  const { count: nodeCount, maxDepth } = countAst(programAst);
  if (nodeCount === 0) {
    return {
      success: false,
      error_type: 'empty_program',
      error_step: 0,
      error_block_id: null,
      message: '工作區目前還沒有放入任何指令喔！請先加入指令卡或積木再按執行。',
      trace: [],
      concepts_used: [],
    };
  }
  if (nodeCount > MAX_INSTRUCTIONS) {
    return {
      success: false,
      error_type: 'instruction_limit_exceeded',
      error_step: 0,
      error_block_id: null,
      message: `積木數量 (${nodeCount}) 超過上限 (${MAX_INSTRUCTIONS})，試著使用迴圈或函式簡化吧！`,
      trace: [],
      concepts_used: [],
    };
  }
  if (maxDepth > MAX_DEPTH) {
    return {
      success: false,
      error_type: 'nesting_depth_exceeded',
      error_step: 0,
      error_block_id: null,
      message: `積木巢狀層數 (${maxDepth}) 超過安全上限 (${MAX_DEPTH})！`,
      trace: [],
      concepts_used: [],
    };
  }

  const start = levelData.start || { x: 1, y: 1, dir: 0 };
  const state = {
    x: Number(start.x ?? 1),
    y: Number(start.y ?? 1),
    dir: Number(start.dir ?? 0),
    items: (levelData.items || []).map((it) => ({ ...it, collected: false })),
    switches: (levelData.switches || []).map((sw) => ({ ...sw, active: false })),
    doors: (levelData.doors || []).map((dr) => ({ ...dr, open: Boolean(dr.open) })),
    devices: (levelData.devices || []).map((dv) => ({ ...dv, repaired: false })),
    variables: {
      energy: Number(levelData.initial_variables?.energy || 0),
      keys: Number(levelData.initial_variables?.keys || 0),
      power: Number(levelData.initial_variables?.power || 0),
    },
    functions: {},
    steps: 0,
    trace: [],
    concepts_used: new Set(),
    error: null,
  };

  const mainNodes = [];
  for (const node of programAst) {
    if (node && node.type === 'func_def') {
      const fname = String(node.name || 'collect_step').trim() || 'collect_step';
      state.functions[fname] = node.body || [];
      state.concepts_used.add('functions');
    } else if (node) {
      mainNodes.push(node);
    }
  }

  const width = Number(levelData.width || 7);
  const height = Number(levelData.height || 6);
  const obstacleSet = new Set((levelData.obstacles || []).map((o) => `${o.x},${o.y}`));

  function evalCond(cond) {
    if (!cond) return false;
    const c = typeof cond === 'string' ? { type: cond } : cond;
    const [dx, dy] = DIR_VECTORS[state.dir] || [1, 0];
    const nx = state.x + dx;
    const ny = state.y + dy;
    const inBounds = nx >= 0 && nx < width && ny >= 0 && ny < height;
    const closedDoorAhead = state.doors.some((d) => !d.open && d.x === nx && d.y === ny);

    if (c.type === 'obstacle_ahead') {
      return !inBounds || obstacleSet.has(`${nx},${ny}`) || closedDoorAhead;
    }
    if (c.type === 'path_clear_ahead') {
      return inBounds && !obstacleSet.has(`${nx},${ny}`) && !closedDoorAhead;
    }
    if (c.type === 'energy_on_tile') {
      return state.items.some((it) => !it.collected && it.x === state.x && it.y === state.y);
    }
    if (c.type === 'has_energy') {
      return (state.variables.energy || 0) > 0;
    }
    if (c.type === 'all_switches_active') {
      return state.switches.length > 0 ? state.switches.every((s) => s.active) : true;
    }
    if (c.type === 'var_compare') {
      const curr = Number(state.variables[c.var || 'energy'] || 0);
      const target = Number(c.value ?? 0);
      const op = c.op || '>=';
      if (op === '>=') return curr >= target;
      if (op === '<=') return curr <= target;
      if (op === '>') return curr > target;
      if (op === '<') return curr < target;
      if (op === '==' || op === '=') return curr === target;
      if (op === '!=') return curr !== target;
      return false;
    }
    if (c.type === 'logic_and') {
      return evalCond(c.left) && evalCond(c.right);
    }
    if (c.type === 'logic_or') {
      return evalCond(c.left) || evalCond(c.right);
    }
    if (c.type === 'logic_not') {
      return !evalCond(c.operand);
    }
    return false;
  }

  function updateAutoDoors() {
    const allSw = state.switches.length > 0 && state.switches.every((s) => s.active);
    for (const door of state.doors) {
      if (door.requires_switches && allSw && state.variables.energy >= Number(door.requires_energy || 0)) {
        door.open = true;
      }
    }
  }

  function execNodes(nodes, callDepth = 0) {
    if (callDepth > MAX_DEPTH) {
      state.error = {
        type: 'recursion_limit',
        step: state.steps,
        block_id: null,
        message: '函式呼叫層數太深，請檢查是否有無限遞迴呼叫。',
      };
      return;
    }

    for (const node of nodes) {
      if (state.error) return;
      if (state.steps >= MAX_STEPS) {
        state.error = {
          type: 'step_limit_exceeded',
          step: state.steps,
          block_id: node.id || null,
          message: `程式執行超過 ${MAX_STEPS} 步上限，請檢查迴圈是否會正常結束！`,
        };
        return;
      }

      const ntype = node.type;
      const blockId = node.id || null;

      if (
        ['move_forward', 'move_backward', 'turn_left', 'turn_right', 'pickup', 'activate_switch', 'open_door', 'repair_device'].includes(
          ntype
        )
      ) {
        state.concepts_used.add('sequence');
      }

      if (ntype === 'move_forward' || ntype === 'move_backward') {
        state.steps += 1;
        let [dx, dy] = DIR_VECTORS[state.dir] || [1, 0];
        if (ntype === 'move_backward') {
          dx = -dx;
          dy = -dy;
        }
        const nx = state.x + dx;
        const ny = state.y + dy;

        if (nx < 0 || nx >= width || ny < 0 || ny >= height) {
          state.error = {
            type: 'out_of_bounds',
            step: state.steps,
            block_id: blockId,
            message: `第 ${state.steps} 步：機器人面向${DIR_NAMES[state.dir]}走出了基地平台邊界！要不要檢查一下前進的步數或轉彎時機？`,
          };
          return;
        }
        if (obstacleSet.has(`${nx},${ny}`)) {
          state.error = {
            type: 'obstacle_collision',
            step: state.steps,
            block_id: blockId,
            message: `第 ${state.steps} 步：機器人前方 (${nx}, ${ny}) 有障礙物，但是你讓它繼續往前走了。要不要檢查一下這段指令？`,
          };
          return;
        }
        const closedDoor = state.doors.find((d) => !d.open && d.x === nx && d.y === ny);
        if (closedDoor) {
          state.error = {
            type: 'door_locked',
            step: state.steps,
            block_id: blockId,
            message: `第 ${state.steps} 步：前方 (${nx}, ${ny}) 的安全閘門還沒開啟喔！請確認已收集足夠能源或啟動開關並執行「開啟閘門」。`,
          };
          return;
        }

        state.x = nx;
        state.y = ny;
        updateAutoDoors();
        state.trace.push({
          step: state.steps,
          action: ntype,
          label: ACTION_LABELS[ntype],
          block_id: blockId,
          x: state.x,
          y: state.y,
          dir: state.dir,
          variables: { ...state.variables },
        });
      } else if (ntype === 'turn_left') {
        state.steps += 1;
        state.dir = (state.dir + 3) % 4;
        state.trace.push({
          step: state.steps,
          action: 'turn_left',
          label: `${ACTION_LABELS.turn_left} → 面向${DIR_NAMES[state.dir]}`,
          block_id: blockId,
          x: state.x,
          y: state.y,
          dir: state.dir,
          variables: { ...state.variables },
        });
      } else if (ntype === 'turn_right') {
        state.steps += 1;
        state.dir = (state.dir + 1) % 4;
        state.trace.push({
          step: state.steps,
          action: 'turn_right',
          label: `${ACTION_LABELS.turn_right} → 面向${DIR_NAMES[state.dir]}`,
          block_id: blockId,
          x: state.x,
          y: state.y,
          dir: state.dir,
          variables: { ...state.variables },
        });
      } else if (ntype === 'pickup') {
        state.steps += 1;
        const item = state.items.find((it) => !it.collected && it.x === state.x && it.y === state.y);
        if (item) {
          item.collected = true;
          const vType = item.type || 'energy';
          state.variables[vType] = (state.variables[vType] || 0) + Number(item.value || 1);
        }
        updateAutoDoors();
        state.trace.push({
          step: state.steps,
          action: 'pickup',
          label: item ? `⚡ 撿取能源 (energy = ${state.variables.energy})` : '⚡ 嘗試撿取（腳下無晶片）',
          block_id: blockId,
          x: state.x,
          y: state.y,
          dir: state.dir,
          variables: { ...state.variables },
        });
      } else if (ntype === 'activate_switch' || ntype === 'pulse_lock') {
        state.steps += 1;
        const sw = state.switches.find((s) => s.x === state.x && s.y === state.y);
        if (sw) {
          sw.active = true;
          state.variables.power = (state.variables.power || 0) + 10;
        }
        updateAutoDoors();
        state.trace.push({
          step: state.steps,
          action: ntype,
          label: sw ? '🔘 啟動控制開關（脈衝鎖定）' : '🔘 嘗試啟動開關（腳下無開關）',
          block_id: blockId,
          x: state.x,
          y: state.y,
          dir: state.dir,
          variables: { ...state.variables },
        });
      } else if (ntype === 'open_door') {
        state.steps += 1;
        for (const door of state.doors) {
          if (Math.abs(door.x - state.x) + Math.abs(door.y - state.y) <= 1) {
            const reqEn = Number(door.requires_energy || 0);
            const reqSw = Boolean(door.requires_switches);
            const allSw = state.switches.length > 0 ? state.switches.every((s) => s.active) : true;
            if (state.variables.energy < reqEn) {
              state.error = {
                type: 'insufficient_energy_for_door',
                step: state.steps,
                block_id: blockId,
                message: `第 ${state.steps} 步：開啟這道閘門需要至少 ${reqEn} 個能源，但目前只有 ${state.variables.energy} 個喔！`,
              };
              return;
            }
            if (reqSw && !allSw) {
              state.error = {
                type: 'switches_not_active',
                step: state.steps,
                block_id: blockId,
                message: `第 ${state.steps} 步：開啟中央閘門前，必須先啟動所有控制開關！`,
              };
              return;
            }
            door.open = true;
          }
        }
        state.trace.push({
          step: state.steps,
          action: 'open_door',
          label: '🚪 開啟安全閘門',
          block_id: blockId,
          x: state.x,
          y: state.y,
          dir: state.dir,
          variables: { ...state.variables },
        });
      } else if (ntype === 'repair_device') {
        state.steps += 1;
        const dev = state.devices.find((d) => d.x === state.x && d.y === state.y);
        if (dev) {
          const reqEn = Number(dev.requires_energy || 0);
          if (state.variables.energy < reqEn) {
            state.error = {
              type: 'insufficient_energy',
              step: state.steps,
              block_id: blockId,
              message: `第 ${state.steps} 步：修復這台設備需要 ${reqEn} 個能源晶片，但目前只有 ${state.variables.energy} 個！`,
            };
            return;
          }
          dev.repaired = true;
        }
        state.trace.push({
          step: state.steps,
          action: 'repair_device',
          label: dev ? '🔧 成功修復供電設備' : '🔧 嘗試修復（此格無設備）',
          block_id: blockId,
          x: state.x,
          y: state.y,
          dir: state.dir,
          variables: { ...state.variables },
        });
      } else if (ntype === 'var_set') {
        state.concepts_used.add('variables');
        state.steps += 1;
        const vn = node.var || 'energy';
        state.variables[vn] = Number(node.value || 0);
        state.trace.push({
          step: state.steps,
          action: 'var_set',
          label: `🔢 設定變數 ${vn} = ${state.variables[vn]}`,
          block_id: blockId,
          x: state.x,
          y: state.y,
          dir: state.dir,
          variables: { ...state.variables },
        });
      } else if (ntype === 'var_change') {
        state.concepts_used.add('variables');
        state.steps += 1;
        const vn = node.var || 'energy';
        state.variables[vn] = (state.variables[vn] || 0) + Number(node.delta || 1);
        state.trace.push({
          step: state.steps,
          action: 'var_change',
          label: `🔢 變數 ${vn} 變更為 ${state.variables[vn]}`,
          block_id: blockId,
          x: state.x,
          y: state.y,
          dir: state.dir,
          variables: { ...state.variables },
        });
      } else if (ntype === 'repeat_n') {
        state.concepts_used.add('loops');
        const count = Number(node.count ?? 1);
        if (count < 0 || count > MAX_LOOP) {
          state.error = {
            type: 'loop_limit_exceeded',
            step: state.steps,
            block_id: blockId,
            message: `迴圈次數 (${count}) 超過安全上限 (${MAX_LOOP})！請調整重複次數。`,
          };
          return;
        }
        for (let i = 0; i < count; i++) {
          execNodes(node.body || [], callDepth);
          if (state.error) return;
        }
      } else if (ntype === 'repeat_until_goal') {
        state.concepts_used.add('loops');
        const goal = levelData.goal || { x: -1, y: -1 };
        let iters = 0;
        while (!(state.x === goal.x && state.y === goal.y)) {
          iters += 1;
          if (iters > MAX_LOOP || !(node.body && node.body.length)) {
            state.error = {
              type: 'loop_limit_exceeded',
              step: state.steps,
              block_id: blockId,
              message: '「持續執行直到終點」超過循環上限，請確認迴圈內的指令是否能引導機器人走向終點！',
            };
            return;
          }
          execNodes(node.body || [], callDepth);
          if (state.error) return;
        }
      } else if (ntype === 'if' || ntype === 'if_else') {
        state.concepts_used.add('conditions');
        const cond = node.condition || {};
        if (cond.type && cond.type.startsWith('logic_')) state.concepts_used.add('logic');
        if (cond.type === 'var_compare') state.concepts_used.add('variables');
        if (evalCond(cond)) {
          execNodes(node.then_body || node.body || [], callDepth);
        } else if (ntype === 'if_else') {
          execNodes(node.else_body || [], callDepth);
        }
      } else if (ntype === 'func_call') {
        state.concepts_used.add('functions');
        const fname = String(node.name || 'collect_step').trim() || 'collect_step';
        const fbody = state.functions[fname];
        if (!fbody) {
          state.error = {
            type: 'undefined_function',
            step: state.steps,
            block_id: blockId,
            message: `找不到名為「${fname}」的自訂函式！請確認已先放置「建立函式 ${fname}」積木。`,
          };
          return;
        }
        execNodes(fbody, callDepth + 1);
      }
    }
  }

  execNodes(mainNodes);

  if (state.error) {
    return {
      success: false,
      error_type: state.error.type,
      error_step: state.error.step,
      error_block_id: state.error.block_id,
      message: state.error.message,
      trace: state.trace,
      concepts_used: Array.from(state.concepts_used),
    };
  }

  const goal = levelData.goal || { x: -1, y: -1 };
  const atGoal = state.x === goal.x && state.y === goal.y;
  const reqEnergy = Number(levelData.required_energy || 0);
  const reqSwitches = Boolean(levelData.require_all_switches);
  const reqDevices = Boolean(levelData.require_all_devices);

  if (!atGoal) {
    return {
      success: false,
      error_type: 'not_at_goal',
      error_step: state.steps,
      error_block_id: null,
      message: `機器人執行完指令後停在 (${state.x}, ${state.y})，還沒抵達綠色終點 (${goal.x}, ${goal.y}) 喔！檢查看看步數或轉彎方向吧。`,
      trace: state.trace,
      concepts_used: Array.from(state.concepts_used),
    };
  }
  if (state.variables.energy < reqEnergy) {
    return {
      success: false,
      error_type: 'missing_energy',
      error_step: state.steps,
      error_block_id: null,
      message: `機器人到達終點了，但能源晶片只收集到 ${state.variables.energy} / ${reqEnergy} 個！記得在能源晶片位置放「撿取能源」指令。`,
      trace: state.trace,
      concepts_used: Array.from(state.concepts_used),
    };
  }
  if (reqSwitches && !state.switches.every((s) => s.active)) {
    return {
      success: false,
      error_type: 'missing_switches',
      error_step: state.steps,
      error_block_id: null,
      message: '還有控制開關尚未啟動喔！請確認所有地板開關都已啟動。',
      trace: state.trace,
      concepts_used: Array.from(state.concepts_used),
    };
  }
  if (reqDevices && !state.devices.every((d) => d.repaired)) {
    return {
      success: false,
      error_type: 'missing_devices',
      error_step: state.steps,
      error_block_id: null,
      message: '還有受損的發電設備尚未修復！請走到設備位置並執行「修復設備」指令。',
      trace: state.trace,
      concepts_used: Array.from(state.concepts_used),
    };
  }

  return {
    success: true,
    error_type: null,
    error_step: null,
    error_block_id: null,
    message: '🎉 任務目標全部達成！機器人順利完成修復程序！',
    trace: state.trace,
    concepts_used: Array.from(state.concepts_used),
  };
}

