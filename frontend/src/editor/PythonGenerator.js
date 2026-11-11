// Translates NOVA Protocol AST into clean, educational Python code for side-by-side preview

function condToPython(cond) {
  if (!cond) return 'False';
  const c = typeof cond === 'string' ? { type: cond } : cond;
  switch (c.type) {
    case 'obstacle_ahead':
      return 'obstacle_ahead()';
    case 'path_clear_ahead':
      return 'path_clear_ahead()';
    case 'energy_on_tile':
      return 'energy_on_tile()';
    case 'has_energy':
      return 'has_energy()';
    case 'all_switches_active':
      return 'all_switches_active()';
    case 'var_compare':
      return `${c.var || 'energy'} ${c.op || '>='} ${Number(c.value ?? 0)}`;
    case 'logic_and':
      return `(${condToPython(c.left)} and ${condToPython(c.right)})`;
    case 'logic_or':
      return `(${condToPython(c.left)} or ${condToPython(c.right)})`;
    case 'logic_not':
      return `not (${condToPython(c.operand)})`;
    default:
      return 'True';
  }
}

function nodesToPythonLines(nodes, indentLevel = 0) {
  const pad = '    '.repeat(indentLevel);
  const lines = [];
  if (!Array.isArray(nodes) || nodes.length === 0) {
    if (indentLevel > 0) lines.push(`${pad}pass`);
    return lines;
  }

  nodes.forEach((node, idx) => {
    if (!node || typeof node !== 'object') return;
    const t = node.type;
    if (t === 'move_forward') {
      lines.push(`${pad}move_forward()      # 前進一步`);
    } else if (t === 'move_backward') {
      lines.push(`${pad}move_backward()     # 後退一步`);
    } else if (t === 'turn_left') {
      lines.push(`${pad}turn_left()         # 向左轉 90 度`);
    } else if (t === 'turn_right') {
      lines.push(`${pad}turn_right()        # 向右轉 90 度`);
    } else if (t === 'pickup') {
      lines.push(`${pad}pickup_energy()     # 撿取能源 (energy += 1)`);
    } else if (t === 'activate_switch') {
      lines.push(`${pad}activate_switch()   # 啟動控制開關`);
    } else if (t === 'open_door') {
      lines.push(`${pad}open_door()         # 開啟安全閘門`);
    } else if (t === 'repair_device') {
      lines.push(`${pad}repair_device()     # 修復發電設備`);
    } else if (t === 'scan_ahead') {
      lines.push(`${pad}scan_ahead()        # 雷達掃描前方`);
    } else if (t === 'var_set') {
      lines.push(`${pad}${node.var || 'energy'} = ${Number(node.value ?? 0)}`);
    } else if (t === 'var_change') {
      const d = Number(node.delta ?? 1);
      const sign = d >= 0 ? '+' : '-';
      lines.push(`${pad}${node.var || 'energy'} = ${node.var || 'energy'} ${sign} ${Math.abs(d)}`);
    } else if (t === 'repeat_n') {
      const count = Number(node.count ?? 3);
      lines.push(`${pad}for i_${indentLevel}_${idx} in range(${count}):`);
      lines.push(...nodesToPythonLines(node.body || [], indentLevel + 1));
    } else if (t === 'repeat_until_goal') {
      lines.push(`${pad}while not at_goal():`);
      lines.push(...nodesToPythonLines(node.body || [], indentLevel + 1));
    } else if (t === 'if') {
      lines.push(`${pad}if ${condToPython(node.condition)}:`);
      lines.push(...nodesToPythonLines(node.then_body || node.body || [], indentLevel + 1));
    } else if (t === 'if_else') {
      lines.push(`${pad}if ${condToPython(node.condition)}:`);
      lines.push(...nodesToPythonLines(node.then_body || [], indentLevel + 1));
      lines.push(`${pad}else:`);
      lines.push(...nodesToPythonLines(node.else_body || [], indentLevel + 1));
    } else if (t === 'func_def') {
      const fname = String(node.name || 'collect_step').replace(/[^a-zA-Z0-9_]/g, '_') || 'collect_step';
      lines.push(`${pad}def ${fname}():`);
      lines.push(...nodesToPythonLines(node.body || [], indentLevel + 1));
      lines.push('');
    } else if (t === 'func_call') {
      const fname = String(node.name || 'collect_step').replace(/[^a-zA-Z0-9_]/g, '_') || 'collect_step';
      lines.push(`${pad}${fname}()  # 呼叫自訂函式`);
    }
  });

  return lines;
}

export function generatePythonPreview(programAst) {
  const header = [
    '# NOVA 基地機器人控制程式 (Python 對照預覽)',
    '# ※ 系統採安全虛擬機逐步執行，下方為對應之 Python 語法結構：',
    '',
  ];
  if (!Array.isArray(programAst) || programAst.length === 0) {
    return [...header, '# (請在左側排列指令卡或 Blockly 積木)'].join('\n');
  }
  const bodyLines = nodesToPythonLines(programAst, 0);
  return [...header, ...bodyLines].join('\n');
}

