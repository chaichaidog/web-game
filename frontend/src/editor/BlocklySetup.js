import * as Blockly from 'blockly';

let blocksRegistered = false;

export function registerNovaBlocks() {
  if (blocksRegistered) return;
  blocksRegistered = true;

  Blockly.defineBlocksWithJsonArray([
    // 1. 移動類 (Movement)
    {
      type: 'nova_move_forward',
      message0: '⬆️ 前進一步',
      previousStatement: null,
      nextStatement: null,
      colour: 199,
      tooltip: '讓機器人往目前面向的方向前進 1 格',
    },
    {
      type: 'nova_move_backward',
      message0: '⬇️ 後退一步',
      previousStatement: null,
      nextStatement: null,
      colour: 199,
      tooltip: '讓機器人往背對方向後退 1 格',
    },
    {
      type: 'nova_turn_left',
      message0: '↩️ 向左轉 (逆時針 90°)',
      previousStatement: null,
      nextStatement: null,
      colour: 199,
      tooltip: '在原地逆時針向左轉向 90 度（不會移動格子）',
    },
    {
      type: 'nova_turn_right',
      message0: '↪️ 向右轉 (順時針 90°)',
      previousStatement: null,
      nextStatement: null,
      colour: 199,
      tooltip: '在原地順時針向右轉向 90 度（不會移動格子）',
    },

    // 2. 互動類 (Interaction)
    {
      type: 'nova_pickup',
      message0: '⚡ 撿取能源晶片 (energy + 1)',
      previousStatement: null,
      nextStatement: null,
      colour: 38,
      tooltip: '撿取腳下格子上的藍色能源晶片',
    },
    {
      type: 'nova_activate_switch',
      message0: '🔘 啟動地板控制開關',
      previousStatement: null,
      nextStatement: null,
      colour: 38,
      tooltip: '啟動腳下的控制開關（單人時自動啟動脈衝保持）',
    },
    {
      type: 'nova_open_door',
      message0: '🚪 開啟安全閘門',
      previousStatement: null,
      nextStatement: null,
      colour: 38,
      tooltip: '當能源或開關條件滿足時，開啟相鄰的安全閘門',
    },
    {
      type: 'nova_repair_device',
      message0: '🔧 修復受損發電設備',
      previousStatement: null,
      nextStatement: null,
      colour: 38,
      tooltip: '在受損設備格子上執行修復',
    },
    {
      type: 'nova_scan_ahead',
      message0: '📡 掃描前方環境',
      previousStatement: null,
      nextStatement: null,
      colour: 38,
      tooltip: '使用雷達掃描前方一格狀態',
    },

    // 3. 迴圈類 (Loops)
    {
      type: 'nova_repeat_n',
      message0: '🔁 重複 %1 次',
      args0: [
        {
          type: 'field_number',
          name: 'COUNT',
          value: 3,
          min: 1,
          max: 25,
          precision: 1,
        },
      ],
      message1: '執行 %1',
      args1: [
        {
          type: 'input_statement',
          name: 'DO',
        },
      ],
      previousStatement: null,
      nextStatement: null,
      colour: 265,
      tooltip: '將內部的積木重複執行指定的次數',
    },
    {
      type: 'nova_repeat_until_goal',
      message0: '🔄 持續執行直到抵達終點',
      message1: '執行 %1',
      args1: [
        {
          type: 'input_statement',
          name: 'DO',
        },
      ],
      previousStatement: null,
      nextStatement: null,
      colour: 265,
      tooltip: '反覆執行內部積木，直到機器人站在綠色終點為止',
    },

    // 4. 條件類 (Conditions & Sensors)
    {
      type: 'nova_if',
      message0: '❓ 如果 %1 成立',
      args0: [
        {
          type: 'input_value',
          name: 'COND',
          check: 'Boolean',
        },
      ],
      message1: '那麼執行 %1',
      args1: [
        {
          type: 'input_statement',
          name: 'THEN',
        },
      ],
      previousStatement: null,
      nextStatement: null,
      colour: 155,
      tooltip: '當條件為真時，才執行內部的動作',
    },
    {
      type: 'nova_if_else',
      message0: '⚖️ 如果 %1 成立',
      args0: [
        {
          type: 'input_value',
          name: 'COND',
          check: 'Boolean',
        },
      ],
      message1: '那麼執行 %1',
      args1: [
        {
          type: 'input_statement',
          name: 'THEN',
        },
      ],
      message2: '否則執行 %1',
      args2: [
        {
          type: 'input_statement',
          name: 'ELSE',
        },
      ],
      previousStatement: null,
      nextStatement: null,
      colour: 155,
      tooltip: '條件成立時執行第一段，否則執行第二段',
    },
    {
      type: 'nova_sensor_obstacle',
      message0: '⚠️ 前方有障礙物',
      output: 'Boolean',
      colour: 155,
      tooltip: '偵測機器人正前方一格是否有障礙物、牆壁或未開的門',
    },
    {
      type: 'nova_sensor_energy_tile',
      message0: '⚡ 腳下有能源晶片',
      output: 'Boolean',
      colour: 155,
      tooltip: '偵測機器人目前站的格子上是否有尚未撿取的能源晶片',
    },
    {
      type: 'nova_sensor_has_energy',
      message0: '🔋 已持有能源 (energy > 0)',
      output: 'Boolean',
      colour: 155,
      tooltip: '檢查目前是否已收集至少 1 顆能源晶片',
    },
    {
      type: 'nova_sensor_all_switches',
      message0: '🔘 所有開關皆已啟動',
      output: 'Boolean',
      colour: 155,
      tooltip: '檢查地圖上的所有控制開關是否都已啟動',
    },

    // 5. 變數類 (Variables)
    {
      type: 'nova_var_compare',
      message0: '🔢 變數 %1 %2 %3',
      args0: [
        {
          type: 'field_dropdown',
          name: 'VAR',
          options: [
            ['能源 (energy)', 'energy'],
            ['電力 (power)', 'power'],
            ['鑰匙 (keys)', 'keys'],
          ],
        },
        {
          type: 'field_dropdown',
          name: 'OP',
          options: [
            ['>= (大於或等於)', '>='],
            ['== (等於)', '=='],
            ['> (大於)', '>'],
            ['<= (小於或等於)', '<='],
          ],
        },
        {
          type: 'field_number',
          name: 'VAL',
          value: 3,
          min: 0,
          max: 50,
          precision: 1,
        },
      ],
      output: 'Boolean',
      colour: 330,
      tooltip: '比較變數目前的數值是否符合條件',
    },
    {
      type: 'nova_var_set',
      message0: '🔢 設定變數 %1 為 %2',
      args0: [
        {
          type: 'field_dropdown',
          name: 'VAR',
          options: [
            ['能源 (energy)', 'energy'],
            ['電力 (power)', 'power'],
          ],
        },
        {
          type: 'field_number',
          name: 'VAL',
          value: 0,
        },
      ],
      previousStatement: null,
      nextStatement: null,
      colour: 330,
      tooltip: '設定指定變數的數值',
    },
    {
      type: 'nova_var_change',
      message0: '🔢 變數 %1 增加 %2',
      args0: [
        {
          type: 'field_dropdown',
          name: 'VAR',
          options: [
            ['能源 (energy)', 'energy'],
            ['電力 (power)', 'power'],
          ],
        },
        {
          type: 'field_number',
          name: 'DELTA',
          value: 1,
        },
      ],
      previousStatement: null,
      nextStatement: null,
      colour: 330,
      tooltip: '增加或減少變數的數值',
    },

    // 6. 邏輯類 (Logic)
    {
      type: 'nova_logic_and',
      message0: '🔗 %1 %2 %3',
      args0: [
        {
          type: 'input_value',
          name: 'LEFT',
          check: 'Boolean',
        },
        {
          type: 'field_dropdown',
          name: 'OP',
          options: [
            ['且 (AND — 兩者皆成立)', 'logic_and'],
            ['或 (OR — 任一成立)', 'logic_or'],
          ],
        },
        {
          type: 'input_value',
          name: 'RIGHT',
          check: 'Boolean',
        },
      ],
      inputsInline: true,
      output: 'Boolean',
      colour: 230,
      tooltip: '組合兩個布林條件判斷',
    },
    {
      type: 'nova_logic_not',
      message0: '🚫 非 (NOT) %1',
      args0: [
        {
          type: 'input_value',
          name: 'OPERAND',
          check: 'Boolean',
        },
      ],
      output: 'Boolean',
      colour: 230,
      tooltip: '將條件結果反轉（原本不成立變成成立）',
    },

    // 7. 函式類 (Functions)
    {
      type: 'nova_func_def',
      message0: '📦 建立自訂函式 %1',
      args0: [
        {
          type: 'field_input',
          name: 'NAME',
          text: 'collect_step',
        },
      ],
      message1: '函式內容 %1',
      args1: [
        {
          type: 'input_statement',
          name: 'BODY',
        },
      ],
      colour: 350,
      tooltip: '將常用的一組動作打包成自訂函式（記得搭配「呼叫函式」執行！）',
    },
    {
      type: 'nova_func_call',
      message0: '▶️ 呼叫自訂函式 %1',
      args0: [
        {
          type: 'field_input',
          name: 'NAME',
          text: 'collect_step',
        },
      ],
      previousStatement: null,
      nextStatement: null,
      colour: 350,
      tooltip: '執行已建立的自訂函式',
    },
  ]);
}

const KEY_TO_BLOCK_TYPE = {
  move_forward: 'nova_move_forward',
  move_backward: 'nova_move_backward',
  turn_left: 'nova_turn_left',
  turn_right: 'nova_turn_right',
  pickup: 'nova_pickup',
  activate_switch: 'nova_activate_switch',
  open_door: 'nova_open_door',
  repair_device: 'nova_repair_device',
  scan_ahead: 'nova_scan_ahead',
  repeat_n: 'nova_repeat_n',
  repeat_until_goal: 'nova_repeat_until_goal',
  if: 'nova_if',
  if_else: 'nova_if_else',
  obstacle_ahead: 'nova_sensor_obstacle',
  energy_on_tile: 'nova_sensor_energy_tile',
  has_energy: 'nova_sensor_has_energy',
  all_switches_active: 'nova_sensor_all_switches',
  var_compare: 'nova_var_compare',
  var_set: 'nova_var_set',
  var_change: 'nova_var_change',
  logic_and: 'nova_logic_and',
  logic_or: 'nova_logic_and',
  logic_not: 'nova_logic_not',
  func_def: 'nova_func_def',
  func_call: 'nova_func_call',
};

export function buildToolboxConfig(allowedKeys = []) {
  const allowedSet = new Set(
    allowedKeys && allowedKeys.length > 0
      ? allowedKeys
      : ['move_forward', 'turn_left', 'turn_right', 'pickup']
  );

  const contents = [
    {
      kind: 'label',
      text: '✅ 本關可用積木',
    },
  ];
  const addedTypes = new Set();

  for (const key of allowedSet) {
    const bType = KEY_TO_BLOCK_TYPE[key];
    if (bType && !addedTypes.has(bType)) {
      contents.push({ kind: 'block', type: bType });
      addedTypes.add(bType);
    }
  }

  // Show locked upcoming blocks as disabled preview (Section 6.2)
  const lockedBlocks = [];
  for (const [key, bType] of Object.entries(KEY_TO_BLOCK_TYPE)) {
    if (!allowedSet.has(key) && !addedTypes.has(bType)) {
      lockedBlocks.push({ kind: 'block', type: bType, disabled: 'true' });
      addedTypes.add(bType);
    }
  }

  if (lockedBlocks.length > 0) {
    contents.push({
      kind: 'label',
      text: '🔒 後續章節解鎖預覽（現在無須理解）',
    });
    contents.push(...lockedBlocks);
  }

  return {
    kind: 'flyoutToolbox',
    contents,
  };
}

function conditionBlockToAst(condBlock) {
  if (!condBlock) return { type: 'obstacle_ahead' };
  const btype = condBlock.type;
  if (btype === 'nova_sensor_obstacle') return { type: 'obstacle_ahead' };
  if (btype === 'nova_sensor_energy_tile') return { type: 'energy_on_tile' };
  if (btype === 'nova_sensor_has_energy') return { type: 'has_energy' };
  if (btype === 'nova_sensor_all_switches') return { type: 'all_switches_active' };
  if (btype === 'nova_var_compare') {
    return {
      type: 'var_compare',
      var: condBlock.getFieldValue('VAR') || 'energy',
      op: condBlock.getFieldValue('OP') || '>=',
      value: Number(condBlock.getFieldValue('VAL') ?? 3),
    };
  }
  if (btype === 'nova_logic_and') {
    return {
      type: condBlock.getFieldValue('OP') || 'logic_and',
      left: conditionBlockToAst(condBlock.getInputTargetBlock('LEFT')),
      right: conditionBlockToAst(condBlock.getInputTargetBlock('RIGHT')),
    };
  }
  if (btype === 'nova_logic_not') {
    return {
      type: 'logic_not',
      operand: conditionBlockToAst(condBlock.getInputTargetBlock('OPERAND')),
    };
  }
  return { type: 'obstacle_ahead' };
}

function statementChainToAst(startBlock) {
  const list = [];
  let curr = startBlock;
  while (curr) {
    const id = curr.id;
    const t = curr.type;
    if (t === 'nova_move_forward') {
      list.push({ id, type: 'move_forward' });
    } else if (t === 'nova_move_backward') {
      list.push({ id, type: 'move_backward' });
    } else if (t === 'nova_turn_left') {
      list.push({ id, type: 'turn_left' });
    } else if (t === 'nova_turn_right') {
      list.push({ id, type: 'turn_right' });
    } else if (t === 'nova_pickup') {
      list.push({ id, type: 'pickup' });
    } else if (t === 'nova_activate_switch') {
      list.push({ id, type: 'activate_switch' });
    } else if (t === 'nova_open_door') {
      list.push({ id, type: 'open_door' });
    } else if (t === 'nova_repair_device') {
      list.push({ id, type: 'repair_device' });
    } else if (t === 'nova_scan_ahead') {
      list.push({ id, type: 'scan_ahead' });
    } else if (t === 'nova_var_set') {
      list.push({
        id,
        type: 'var_set',
        var: curr.getFieldValue('VAR') || 'energy',
        value: Number(curr.getFieldValue('VAL') ?? 0),
      });
    } else if (t === 'nova_var_change') {
      list.push({
        id,
        type: 'var_change',
        var: curr.getFieldValue('VAR') || 'energy',
        delta: Number(curr.getFieldValue('DELTA') ?? 1),
      });
    } else if (t === 'nova_repeat_n') {
      list.push({
        id,
        type: 'repeat_n',
        count: Number(curr.getFieldValue('COUNT') ?? 3),
        body: statementChainToAst(curr.getInputTargetBlock('DO')),
      });
    } else if (t === 'nova_repeat_until_goal') {
      list.push({
        id,
        type: 'repeat_until_goal',
        body: statementChainToAst(curr.getInputTargetBlock('DO')),
      });
    } else if (t === 'nova_if') {
      list.push({
        id,
        type: 'if',
        condition: conditionBlockToAst(curr.getInputTargetBlock('COND')),
        then_body: statementChainToAst(curr.getInputTargetBlock('THEN')),
      });
    } else if (t === 'nova_if_else') {
      list.push({
        id,
        type: 'if_else',
        condition: conditionBlockToAst(curr.getInputTargetBlock('COND')),
        then_body: statementChainToAst(curr.getInputTargetBlock('THEN')),
        else_body: statementChainToAst(curr.getInputTargetBlock('ELSE')),
      });
    } else if (t === 'nova_func_call') {
      list.push({
        id,
        type: 'func_call',
        name: curr.getFieldValue('NAME') || 'collect_step',
      });
    }
    curr = curr.getNextBlock();
  }
  return list;
}

export function workspaceToAst(workspace) {
  if (!workspace) return [];
  const topBlocks = workspace.getTopBlocks(true);
  const ast = [];

  for (const top of topBlocks) {
    if (top.type === 'nova_func_def') {
      ast.push({
        id: top.id,
        type: 'func_def',
        name: top.getFieldValue('NAME') || 'collect_step',
        body: statementChainToAst(top.getInputTargetBlock('BODY')),
      });
    } else {
      ast.push(...statementChainToAst(top));
    }
  }
  return ast;
}

function buildConditionBlock(workspace, condAst) {
  if (!condAst) return null;
  const c = typeof condAst === 'string' ? { type: condAst } : condAst;
  let b = null;
  if (c.type === 'obstacle_ahead') {
    b = workspace.newBlock('nova_sensor_obstacle');
  } else if (c.type === 'energy_on_tile') {
    b = workspace.newBlock('nova_sensor_energy_tile');
  } else if (c.type === 'has_energy') {
    b = workspace.newBlock('nova_sensor_has_energy');
  } else if (c.type === 'all_switches_active') {
    b = workspace.newBlock('nova_sensor_all_switches');
  } else if (c.type === 'var_compare') {
    b = workspace.newBlock('nova_var_compare');
    b.setFieldValue(c.var || 'energy', 'VAR');
    b.setFieldValue(c.op || '>=', 'OP');
    b.setFieldValue(String(c.value ?? 3), 'VAL');
  } else if (c.type === 'logic_and' || c.type === 'logic_or') {
    b = workspace.newBlock('nova_logic_and');
    b.setFieldValue(c.type, 'OP');
    const leftB = buildConditionBlock(workspace, c.left);
    const rightB = buildConditionBlock(workspace, c.right);
    if (leftB && b.getInput('LEFT')) {
      b.getInput('LEFT').connection.connect(leftB.outputConnection);
    }
    if (rightB && b.getInput('RIGHT')) {
      b.getInput('RIGHT').connection.connect(rightB.outputConnection);
    }
  } else if (c.type === 'logic_not') {
    b = workspace.newBlock('nova_logic_not');
    const opB = buildConditionBlock(workspace, c.operand);
    if (opB && b.getInput('OPERAND')) {
      b.getInput('OPERAND').connection.connect(opB.outputConnection);
    }
  }
  if (b) {
    b.initSvg();
    b.render();
  }
  return b;
}

function buildBlockChain(workspace, nodes) {
  let firstBlock = null;
  let prevBlock = null;

  for (const node of nodes || []) {
    if (!node || typeof node !== 'object') continue;
    const bType = KEY_TO_BLOCK_TYPE[node.type];
    if (!bType || bType === 'nova_func_def') continue;

    const block = workspace.newBlock(bType);
    if (node.type === 'repeat_n') {
      block.setFieldValue(String(node.count ?? 3), 'COUNT');
      const innerFirst = buildBlockChain(workspace, node.body || []);
      if (innerFirst && block.getInput('DO')) {
        block.getInput('DO').connection.connect(innerFirst.previousConnection);
      }
    } else if (node.type === 'repeat_until_goal') {
      const innerFirst = buildBlockChain(workspace, node.body || []);
      if (innerFirst && block.getInput('DO')) {
        block.getInput('DO').connection.connect(innerFirst.previousConnection);
      }
    } else if (node.type === 'if') {
      const condB = buildConditionBlock(workspace, node.condition);
      if (condB && block.getInput('COND')) {
        block.getInput('COND').connection.connect(condB.outputConnection);
      }
      const thenFirst = buildBlockChain(workspace, node.then_body || node.body || []);
      if (thenFirst && block.getInput('THEN')) {
        block.getInput('THEN').connection.connect(thenFirst.previousConnection);
      }
    } else if (node.type === 'if_else') {
      const condB = buildConditionBlock(workspace, node.condition);
      if (condB && block.getInput('COND')) {
        block.getInput('COND').connection.connect(condB.outputConnection);
      }
      const thenFirst = buildBlockChain(workspace, node.then_body || []);
      if (thenFirst && block.getInput('THEN')) {
        block.getInput('THEN').connection.connect(thenFirst.previousConnection);
      }
      const elseFirst = buildBlockChain(workspace, node.else_body || []);
      if (elseFirst && block.getInput('ELSE')) {
        block.getInput('ELSE').connection.connect(elseFirst.previousConnection);
      }
    } else if (node.type === 'func_call') {
      block.setFieldValue(node.name || 'collect_step', 'NAME');
    } else if (node.type === 'var_set') {
      block.setFieldValue(node.var || 'energy', 'VAR');
      block.setFieldValue(String(node.value ?? 0), 'VAL');
    } else if (node.type === 'var_change') {
      block.setFieldValue(node.var || 'energy', 'VAR');
      block.setFieldValue(String(node.delta ?? 1), 'DELTA');
    }

    block.initSvg();
    block.render();

    if (!firstBlock) {
      firstBlock = block;
    }
    if (prevBlock && prevBlock.nextConnection && block.previousConnection) {
      prevBlock.nextConnection.connect(block.previousConnection);
    }
    prevBlock = block;
  }

  return firstBlock;
}

export function astToWorkspace(workspace, astNodes) {
  if (!workspace) return;
  Blockly.Events.disable();
  try {
    workspace.clear();
    const funcDefs = (astNodes || []).filter((n) => n && n.type === 'func_def');
    const mainNodes = (astNodes || []).filter((n) => n && n.type !== 'func_def');

    let yCursor = 24;
    for (const fdef of funcDefs) {
      const fb = workspace.newBlock('nova_func_def');
      fb.setFieldValue(fdef.name || 'collect_step', 'NAME');
      const bodyFirst = buildBlockChain(workspace, fdef.body || []);
      if (bodyFirst && fb.getInput('BODY')) {
        fb.getInput('BODY').connection.connect(bodyFirst.previousConnection);
      }
      fb.initSvg();
      fb.render();
      fb.moveBy(24, yCursor);
      yCursor += 140;
    }

    const mainFirst = buildBlockChain(workspace, mainNodes);
    if (mainFirst) {
      mainFirst.moveBy(24, yCursor);
    }
  } finally {
    Blockly.Events.enable();
  }
}

