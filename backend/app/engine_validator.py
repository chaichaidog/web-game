from typing import Any
from .config import settings

# Direction vectors: 0=East(+x), 1=South(+y), 2=West(-x), 3=North(-y)
DIR_VECTORS = {
    0: (1, 0),
    1: (0, 1),
    2: (-1, 0),
    3: (0, -1),
}

DIR_NAMES = {
    0: "右方(東)",
    1: "下方(南)",
    2: "左方(西)",
    3: "上方(北)",
}


def count_ast_nodes_and_depth(nodes: list[dict[str, Any]], depth: int = 1) -> tuple[int, int]:
    if not isinstance(nodes, list):
        return 0, depth
    total = 0
    max_d = depth
    for node in nodes:
        if not isinstance(node, dict):
            continue
        total += 1
        for child_key in ("body", "then_body", "else_body"):
            if child_key in node and isinstance(node[child_key], list):
                c_count, c_depth = count_ast_nodes_and_depth(node[child_key], depth + 1)
                total += c_count
                if c_depth > max_d:
                    max_d = c_depth
    return total, max_d


def evaluate_condition(cond: Any, state: dict[str, Any], level_data: dict[str, Any]) -> bool:
    if not cond:
        return False
    if isinstance(cond, str):
        cond = {"type": cond}
    if not isinstance(cond, dict):
        return False

    ctype = cond.get("type", "")
    rx, ry, rdir = state["x"], state["y"], state["dir"]
    dx, dy = DIR_VECTORS.get(rdir, (1, 0))
    nx, ny = rx + dx, ry + dy

    width = level_data.get("width", 8)
    height = level_data.get("height", 8)
    in_bounds = 0 <= nx < width and 0 <= ny < height

    obstacles = {(o["x"], o["y"]) for o in level_data.get("obstacles", [])}
    closed_doors = {
        (d["x"], d["y"])
        for d in state["doors"]
        if not d.get("open", False)
    }

    if ctype == "obstacle_ahead":
        return (not in_bounds) or ((nx, ny) in obstacles) or ((nx, ny) in closed_doors)
    if ctype == "path_clear_ahead":
        return in_bounds and ((nx, ny) not in obstacles) and ((nx, ny) not in closed_doors)
    if ctype == "door_ahead":
        return (nx, ny) in closed_doors
    if ctype == "energy_on_tile":
        return any(
            not item.get("collected", False) and item["x"] == rx and item["y"] == ry
            for item in state["items"]
        )
    if ctype == "has_energy":
        return state["variables"].get("energy", 0) > 0
    if ctype == "at_goal":
        goal = level_data.get("goal", {"x": -1, "y": -1})
        return rx == goal.get("x") and ry == goal.get("y")
    if ctype == "switch_active":
        sw_id = cond.get("switch_id")
        if sw_id:
            return any(s.get("id") == sw_id and s.get("active", False) for s in state["switches"])
        return all(s.get("active", False) for s in state["switches"]) if state["switches"] else False
    if ctype == "all_switches_active":
        return all(s.get("active", False) for s in state["switches"]) if state["switches"] else True
    if ctype == "var_compare":
        var_name = str(cond.get("var", "energy"))
        op = str(cond.get("op", ">="))
        target_val = int(cond.get("value", 0))
        curr_val = int(state["variables"].get(var_name, 0))
        if op == ">=":
            return curr_val >= target_val
        if op == "<=":
            return curr_val <= target_val
        if op == ">":
            return curr_val > target_val
        if op == "<":
            return curr_val < target_val
        if op in ("==", "="):
            return curr_val == target_val
        if op == "!=":
            return curr_val != target_val
        return False
    if ctype == "logic_and":
        return evaluate_condition(cond.get("left"), state, level_data) and evaluate_condition(
            cond.get("right"), state, level_data
        )
    if ctype == "logic_or":
        return evaluate_condition(cond.get("left"), state, level_data) or evaluate_condition(
            cond.get("right"), state, level_data
        )
    if ctype == "logic_not":
        return not evaluate_condition(cond.get("operand"), state, level_data)

    return False


def simulate_program(program_ast: list[dict[str, Any]], level_data: dict[str, Any]) -> dict[str, Any]:
    """
    Safely simulates a structured AST of robot instructions against level_data.
    Never uses eval() or exec().
    """
    node_count, max_depth = count_ast_nodes_and_depth(program_ast)
    if node_count > settings.MAX_INSTRUCTIONS:
        return {
            "success": False,
            "error_type": "instruction_limit_exceeded",
            "error_step": 0,
            "error_block_id": None,
            "message": f"積木總數量 ({node_count}) 超過安全上限 ({settings.MAX_INSTRUCTIONS})，試著使用迴圈或函式簡化程式吧！",
            "trace": [],
            "concepts_used": [],
        }

    if max_depth > settings.MAX_NESTING_DEPTH:
        return {
            "success": False,
            "error_type": "nesting_depth_exceeded",
            "error_step": 0,
            "error_block_id": None,
            "message": f"積木巢狀層數 ({max_depth}) 超過上限 ({settings.MAX_NESTING_DEPTH})，請減少過度複雜的巢狀結構。",
            "trace": [],
            "concepts_used": [],
        }

    start = level_data.get("start", {"x": 0, "y": 0, "dir": 0})
    state: dict[str, Any] = {
        "x": int(start.get("x", 0)),
        "y": int(start.get("y", 0)),
        "dir": int(start.get("dir", 0)),
        "items": [dict(item, collected=False) for item in level_data.get("items", [])],
        "switches": [dict(sw, active=False, pulse_steps=0) for sw in level_data.get("switches", [])],
        "doors": [dict(dr, open=bool(dr.get("open", False))) for dr in level_data.get("doors", [])],
        "devices": [dict(dv, repaired=False) for dv in level_data.get("devices", [])],
        "variables": {
            "energy": int(level_data.get("initial_variables", {}).get("energy", 0)),
            "keys": int(level_data.get("initial_variables", {}).get("keys", 0)),
            "power": int(level_data.get("initial_variables", {}).get("power", 0)),
        },
        "functions": {},
        "steps": 0,
        "trace": [],
        "concepts_used": set(),
        "error": None,
    }

    # Extract function definitions first
    main_nodes: list[dict[str, Any]] = []
    for node in program_ast:
        if isinstance(node, dict) and node.get("type") == "func_def":
            fname = str(node.get("name", "my_func")).strip() or "my_func"
            state["functions"][fname] = node.get("body", [])
            state["concepts_used"].add("functions")
        elif isinstance(node, dict):
            main_nodes.append(node)

    width = int(level_data.get("width", 8))
    height = int(level_data.get("height", 8))
    obstacles = {(o["x"], o["y"]) for o in level_data.get("obstacles", [])}

    def update_auto_doors():
        all_sw_active = bool(state["switches"]) and all(s.get("active", False) for s in state["switches"])
        for door in state["doors"]:
            req_sw = door.get("requires_switches", False)
            req_en = int(door.get("requires_energy", 0))
            if req_sw and all_sw_active and state["variables"].get("energy", 0) >= req_en:
                door["open"] = True

    def tick_pulse_switches():
        for sw in state["switches"]:
            if sw.get("pulse_steps", 0) > 0:
                sw["pulse_steps"] -= 1
                if sw["pulse_steps"] == 0 and not sw.get("permanent", True):
                    sw["active"] = False

    def execute_nodes(nodes: list[dict[str, Any]], call_depth: int = 0):
        if call_depth > settings.MAX_NESTING_DEPTH:
            state["error"] = {
                "type": "recursion_limit",
                "step": state["steps"],
                "block_id": None,
                "message": "函式呼叫層數太深，請確認是否有函式自己呼叫自己的情況。",
            }
            return

        for node in nodes:
            if state["error"] is not None:
                return
            if state["steps"] >= settings.MAX_EXECUTION_STEPS:
                state["error"] = {
                    "type": "step_limit_exceeded",
                    "step": state["steps"],
                    "block_id": node.get("id"),
                    "message": f"程式執行步數超過上限 ({settings.MAX_EXECUTION_STEPS} 步)，請檢查迴圈條件是否正確。",
                }
                return

            ntype = node.get("type", "")
            block_id = node.get("id")

            if ntype in ("move_forward", "move_backward", "turn_left", "turn_right", "pickup", "activate_switch", "open_door", "repair_device", "scan_ahead"):
                state["concepts_used"].add("sequence")

            if ntype in ("move_forward", "move_backward"):
                state["steps"] += 1
                dx, dy = DIR_VECTORS.get(state["dir"], (1, 0))
                if ntype == "move_backward":
                    dx, dy = -dx, -dy
                nx, ny = state["x"] + dx, state["y"] + dy

                if not (0 <= nx < width and 0 <= ny < height):
                    state["error"] = {
                        "type": "out_of_bounds",
                        "step": state["steps"],
                        "block_id": block_id,
                        "message": f"第 {state['steps']} 步：機器人面向{DIR_NAMES.get(state['dir'], '')}走出了基地邊界！要不要檢查前進的步數或轉彎時機？",
                    }
                    return

                if (nx, ny) in obstacles:
                    state["error"] = {
                        "type": "obstacle_collision",
                        "step": state["steps"],
                        "block_id": block_id,
                        "message": f"第 {state['steps']} 步：機器人前方 ({nx}, {ny}) 有障礙物，但是你讓它繼續往前走了。要不要檢查一下這段指令？",
                    }
                    return

                closed_door = next(
                    (d for d in state["doors"] if d["x"] == nx and d["y"] == ny and not d.get("open", False)),
                    None,
                )
                if closed_door is not None:
                    state["error"] = {
                        "type": "door_locked",
                        "step": state["steps"],
                        "block_id": block_id,
                        "message": f"第 {state['steps']} 步：前方的安全閘門尚未開啟！請先收集足夠能源或啟動開關並開啟閘門。",
                    }
                    return

                state["x"], state["y"] = nx, ny
                tick_pulse_switches()
                update_auto_doors()
                state["trace"].append({
                    "step": state["steps"],
                    "action": ntype,
                    "block_id": block_id,
                    "x": state["x"],
                    "y": state["y"],
                    "dir": state["dir"],
                    "variables": dict(state["variables"]),
                })

            elif ntype == "turn_left":
                state["steps"] += 1
                state["dir"] = (state["dir"] + 3) % 4
                state["trace"].append({
                    "step": state["steps"],
                    "action": "turn_left",
                    "block_id": block_id,
                    "x": state["x"],
                    "y": state["y"],
                    "dir": state["dir"],
                    "variables": dict(state["variables"]),
                })

            elif ntype == "turn_right":
                state["steps"] += 1
                state["dir"] = (state["dir"] + 1) % 4
                state["trace"].append({
                    "step": state["steps"],
                    "action": "turn_right",
                    "block_id": block_id,
                    "x": state["x"],
                    "y": state["y"],
                    "dir": state["dir"],
                    "variables": dict(state["variables"]),
                })

            elif ntype == "pickup":
                state["steps"] += 1
                found = False
                for item in state["items"]:
                    if not item.get("collected", False) and item["x"] == state["x"] and item["y"] == state["y"]:
                        item["collected"] = True
                        itype = item.get("type", "energy")
                        val = int(item.get("value", 1))
                        state["variables"][itype] = state["variables"].get(itype, 0) + val
                        found = True
                        break
                update_auto_doors()
                state["trace"].append({
                    "step": state["steps"],
                    "action": "pickup",
                    "success": found,
                    "block_id": block_id,
                    "x": state["x"],
                    "y": state["y"],
                    "dir": state["dir"],
                    "variables": dict(state["variables"]),
                })

            elif ntype in ("activate_switch", "pulse_lock"):
                state["steps"] += 1
                activated = False
                for sw in state["switches"]:
                    if sw["x"] == state["x"] and sw["y"] == state["y"]:
                        sw["active"] = True
                        sw["permanent"] = True
                        sw["pulse_steps"] = 20
                        state["variables"]["power"] = state["variables"].get("power", 0) + 10
                        activated = True
                update_auto_doors()
                state["trace"].append({
                    "step": state["steps"],
                    "action": ntype,
                    "success": activated,
                    "block_id": block_id,
                    "x": state["x"],
                    "y": state["y"],
                    "dir": state["dir"],
                    "variables": dict(state["variables"]),
                })

            elif ntype == "repair_device":
                state["steps"] += 1
                repaired = False
                for dv in state["devices"]:
                    if dv["x"] == state["x"] and dv["y"] == state["y"]:
                        req_en = int(dv.get("requires_energy", 0))
                        if state["variables"].get("energy", 0) >= req_en:
                            dv["repaired"] = True
                            repaired = True
                        else:
                            state["error"] = {
                                "type": "insufficient_energy",
                                "step": state["steps"],
                                "block_id": block_id,
                                "message": f"第 {state['steps']} 步：修復設備需要 {req_en} 個能源晶片，但目前只有 {state['variables'].get('energy', 0)} 個喔！",
                            }
                            return
                state["trace"].append({
                    "step": state["steps"],
                    "action": "repair_device",
                    "success": repaired,
                    "block_id": block_id,
                    "x": state["x"],
                    "y": state["y"],
                    "dir": state["dir"],
                    "variables": dict(state["variables"]),
                })

            elif ntype == "open_door":
                state["steps"] += 1
                dx, dy = DIR_VECTORS.get(state["dir"], (1, 0))
                nx, ny = state["x"] + dx, state["y"] + dy
                opened = False
                for door in state["doors"]:
                    if (door["x"] == nx and door["y"] == ny) or (abs(door["x"] - state["x"]) + abs(door["y"] - state["y"]) <= 1):
                        req_en = int(door.get("requires_energy", 0))
                        req_sw = bool(door.get("requires_switches", False))
                        all_sw = all(s.get("active", False) for s in state["switches"]) if state["switches"] else True
                        if state["variables"].get("energy", 0) < req_en:
                            state["error"] = {
                                "type": "insufficient_energy_for_door",
                                "step": state["steps"],
                                "block_id": block_id,
                                "message": f"第 {state['steps']} 步：開啟這道閘門需要至少 {req_en} 個能源，目前只有 {state['variables'].get('energy', 0)} 個！",
                            }
                            return
                        if req_sw and not all_sw:
                            state["error"] = {
                                "type": "switches_not_active",
                                "step": state["steps"],
                                "block_id": block_id,
                                "message": f"第 {state['steps']} 步：開啟中央閘門前，必須先啟動所有控制開關！",
                            }
                            return
                        door["open"] = True
                        opened = True
                state["trace"].append({
                    "step": state["steps"],
                    "action": "open_door",
                    "success": opened,
                    "block_id": block_id,
                    "x": state["x"],
                    "y": state["y"],
                    "dir": state["dir"],
                    "variables": dict(state["variables"]),
                })

            elif ntype == "scan_ahead":
                state["steps"] += 1
                state["trace"].append({
                    "step": state["steps"],
                    "action": "scan_ahead",
                    "block_id": block_id,
                    "x": state["x"],
                    "y": state["y"],
                    "dir": state["dir"],
                    "variables": dict(state["variables"]),
                })

            elif ntype == "var_set":
                state["concepts_used"].add("variables")
                state["steps"] += 1
                vname = str(node.get("var", "energy"))
                val = int(node.get("value", 0))
                state["variables"][vname] = val
                state["trace"].append({
                    "step": state["steps"],
                    "action": "var_set",
                    "block_id": block_id,
                    "x": state["x"],
                    "y": state["y"],
                    "dir": state["dir"],
                    "variables": dict(state["variables"]),
                })

            elif ntype == "var_change":
                state["concepts_used"].add("variables")
                state["steps"] += 1
                vname = str(node.get("var", "energy"))
                delta = int(node.get("delta", 1))
                state["variables"][vname] = state["variables"].get(vname, 0) + delta
                state["trace"].append({
                    "step": state["steps"],
                    "action": "var_change",
                    "block_id": block_id,
                    "x": state["x"],
                    "y": state["y"],
                    "dir": state["dir"],
                    "variables": dict(state["variables"]),
                })

            elif ntype == "repeat_n":
                state["concepts_used"].add("loops")
                count = int(node.get("count", 1))
                if count < 0 or count > settings.MAX_LOOP_ITERATIONS:
                    state["error"] = {
                        "type": "loop_limit_exceeded",
                        "step": state["steps"],
                        "block_id": block_id,
                        "message": f"迴圈次數 ({count}) 超過安全上限 ({settings.MAX_LOOP_ITERATIONS})！請調整重複次數。",
                    }
                    return
                body = node.get("body", [])
                for _ in range(count):
                    execute_nodes(body, call_depth)
                    if state["error"] is not None:
                        return

            elif ntype == "repeat_until_goal":
                state["concepts_used"].add("loops")
                body = node.get("body", [])
                goal = level_data.get("goal", {"x": -1, "y": -1})
                iters = 0
                while not (state["x"] == goal.get("x") and state["y"] == goal.get("y")):
                    iters += 1
                    if iters > settings.MAX_LOOP_ITERATIONS or not body:
                        state["error"] = {
                            "type": "loop_limit_exceeded",
                            "step": state["steps"],
                            "block_id": block_id,
                            "message": "「持續執行直到抵達終點」超過最大循環次數，請檢查迴圈內是否有讓機器人往終點移動的指令！",
                        }
                        return
                    execute_nodes(body, call_depth)
                    if state["error"] is not None:
                        return

            elif ntype in ("if", "if_else"):
                state["concepts_used"].add("conditions")
                cond = node.get("condition", {})
                if isinstance(cond, dict) and cond.get("type", "").startswith("logic_"):
                    state["concepts_used"].add("logic")
                if isinstance(cond, dict) and cond.get("type") == "var_compare":
                    state["concepts_used"].add("variables")
                if evaluate_condition(cond, state, level_data):
                    execute_nodes(node.get("then_body", node.get("body", [])), call_depth)
                elif ntype == "if_else":
                    execute_nodes(node.get("else_body", []), call_depth)

            elif ntype == "func_call":
                state["concepts_used"].add("functions")
                fname = str(node.get("name", "my_func")).strip() or "my_func"
                fbody = state["functions"].get(fname)
                if fbody is None:
                    state["error"] = {
                        "type": "undefined_function",
                        "step": state["steps"],
                        "block_id": block_id,
                        "message": f"找不到名為「{fname}」的自訂函式！請確認已先建立該函式積木。",
                    }
                    return
                execute_nodes(fbody, call_depth + 1)

    execute_nodes(main_nodes)

    if state["error"] is not None:
        return {
            "success": False,
            "error_type": state["error"]["type"],
            "error_step": state["error"]["step"],
            "error_block_id": state["error"]["block_id"],
            "message": state["error"]["message"],
            "trace": state["trace"],
            "concepts_used": sorted(list(state["concepts_used"])),
            "final_state": {
                "x": state["x"],
                "y": state["y"],
                "dir": state["dir"],
                "variables": state["variables"],
            },
        }

    # Check mission objectives
    goal = level_data.get("goal", {"x": -1, "y": -1})
    at_goal = (state["x"] == goal.get("x") and state["y"] == goal.get("y"))
    required_energy = int(level_data.get("required_energy", 0))
    collected_energy = state["variables"].get("energy", 0)
    require_all_switches = bool(level_data.get("require_all_switches", False))
    switches_ok = (not require_all_switches) or all(s.get("active", False) for s in state["switches"])
    require_all_devices = bool(level_data.get("require_all_devices", False))
    devices_ok = (not require_all_devices) or all(d.get("repaired", False) for d in state["devices"])

    if not at_goal:
        return {
            "success": False,
            "error_type": "not_at_goal",
            "error_step": state["steps"],
            "error_block_id": None,
            "message": f"機器人停在 ({state['x']}, {state['y']})，還沒抵達終點傳送站 ({goal.get('x')}, {goal.get('y')}) 喔！再檢查一下步數或方向吧。",
            "trace": state["trace"],
            "concepts_used": sorted(list(state["concepts_used"])),
        }

    if collected_energy < required_energy:
        return {
            "success": False,
            "error_type": "missing_energy",
            "error_step": state["steps"],
            "error_block_id": None,
            "message": f"機器人抵達終點了，但能源晶片只收集到 {collected_energy} / {required_energy} 個！記得在能源晶片的格子上使用「撿取能源」指令。",
            "trace": state["trace"],
            "concepts_used": sorted(list(state["concepts_used"])),
        }

    if not switches_ok:
        return {
            "success": False,
            "error_type": "missing_switches",
            "error_step": state["steps"],
            "error_block_id": None,
            "message": "還有控制開關尚未啟動喔！請確認所有指定開關都已啟動。",
            "trace": state["trace"],
            "concepts_used": sorted(list(state["concepts_used"])),
        }

    if not devices_ok:
        return {
            "success": False,
            "error_type": "missing_devices",
            "error_step": state["steps"],
            "error_block_id": None,
            "message": "還有受損設備尚未修復！請走到設備位置並執行「修復設備」指令。",
            "trace": state["trace"],
            "concepts_used": sorted(list(state["concepts_used"])),
        }

    return {
        "success": True,
        "error_type": None,
        "error_step": None,
        "error_block_id": None,
        "message": "任務成功！機器人已順利完成基地修復指令！",
        "trace": state["trace"],
        "concepts_used": sorted(list(state["concepts_used"])),
        "node_count": node_count,
        "steps_taken": state["steps"],
        "final_state": {
            "x": state["x"],
            "y": state["y"],
            "dir": state["dir"],
            "variables": state["variables"],
        },
    }

