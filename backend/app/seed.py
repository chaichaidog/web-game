import hashlib
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from .models import Level, LevelVariant, Achievement, Teacher
from .config import settings


ACHIEVEMENTS_SEED = [
    {
        "achievement_code": "first_boot",
        "name": "初次啟動",
        "description": "完成第一個關卡，成功喚醒第一台 NOVA 維修機器人。",
        "category": "milestone",
        "reward_type": "title",
        "reward_value": "序列領航員",
        "xp_reward": 50,
    },
    {
        "achievement_code": "junior_engineer",
        "name": "小小工程師",
        "description": "第一次使用「迴圈」積木簡化重複的機器人指令。",
        "category": "concept",
        "reward_type": "skin",
        "reward_value": "crimson_mech",
        "xp_reward": 80,
    },
    {
        "achievement_code": "logic_master",
        "name": "邏輯高手",
        "description": "成功使用條件判斷 (if/else) 讓機器人避開障礙或判斷狀態。",
        "category": "concept",
        "reward_type": "accessory",
        "reward_value": "holo_visor",
        "xp_reward": 100,
    },
    {
        "achievement_code": "resource_commander",
        "name": "資源調度官",
        "description": "成功運用變數追蹤與比較能源數量並開啟安全閘門。",
        "category": "concept",
        "reward_type": "decor",
        "reward_value": "energy_fountain",
        "xp_reward": 100,
    },
    {
        "achievement_code": "dual_core_sync",
        "name": "雙核協同師",
        "description": "運用邏輯運算 (AND/OR/NOT) 解決多重安全鎖控制任務。",
        "category": "concept",
        "reward_type": "skin",
        "reward_value": "emerald_guardian",
        "xp_reward": 120,
    },
    {
        "achievement_code": "automation_expert",
        "name": "自動化專家",
        "description": "建立並呼叫自訂函式，將重複工作模組化。",
        "category": "concept",
        "reward_type": "accessory",
        "reward_value": "radar_dish",
        "xp_reward": 120,
    },
    {
        "achievement_code": "debug_specialist",
        "name": "除錯專家",
        "description": "在觀察錯誤提示後自行修正程式錯誤並成功完成任務。",
        "category": "resilience",
        "reward_type": "decor",
        "reward_value": "mini_drone",
        "xp_reward": 90,
    },
    {
        "achievement_code": "best_teammate",
        "name": "最佳隊友",
        "description": "在多人合作房間中與隊友協同完成基地修復任務或積極參與討論。",
        "category": "coop",
        "reward_type": "title",
        "reward_value": "王牌協同工程師",
        "xp_reward": 100,
    },
    {
        "achievement_code": "challenge_explorer",
        "name": "深層探索者",
        "description": "完成任一關卡的「挑戰（Challenge）」難度版本。",
        "category": "exploration",
        "reward_type": "skin",
        "reward_value": "quantum_gold",
        "xp_reward": 150,
    },
    {
        "achievement_code": "secret_finder",
        "name": "秘密探索者",
        "description": "在基地隱藏支線或廢棄研究區發現額外的隱藏能源晶片。",
        "category": "exploration",
        "reward_type": "skin",
        "reward_value": "void_stealth",
        "xp_reward": 120,
    },
    {
        "achievement_code": "nova_savior",
        "name": "NOVA 傳奇守護者",
        "description": "完成最終章「重啟 NOVA 核心」，恢復整座研究基地運作！",
        "category": "milestone",
        "reward_type": "decor",
        "reward_value": "core_trophy",
        "xp_reward": 250,
    },
]


LEVELS_SEED = [
    # ==================== 第一章：新手維修區 (Stage 1: 指令與執行順序) ====================
    {
        "level_code": "ch1_lv1",
        "chapter_id": 1,
        "chapter_name": "第一章：新手維修區",
        "level_order": 1,
        "level_name": "1-1 喚醒維修機器人：序列啟動",
        "description": "NOVA 中央控制室的備用機器人已啟動！基礎版跟著地面引導箭頭前進；標準版挑戰轉彎與撿取能源；挑戰版則需在雙岔路障礙中規劃最佳維修路線！",
        "difficulty": "guided",
        "learning_objective": "認識什麼是電腦指令，理解機器人會由上而下、一步一步按照順序執行移動、轉向與互動指令。",
        "concept_code": "sequence",
        "editor_mode": "cards",
        "variants": {
            "guided": {
                "zone": "zone_control",
                "width": 7,
                "height": 6,
                "start": {"x": 1, "y": 3, "dir": 0},
                "goal": {"x": 4, "y": 3},
                "obstacles": [{"x": 1, "y": 1}, {"x": 2, "y": 1}, {"x": 3, "y": 1}, {"x": 4, "y": 1}, {"x": 1, "y": 5}, {"x": 2, "y": 5}, {"x": 3, "y": 5}, {"x": 4, "y": 5}],
                "items": [],
                "switches": [],
                "doors": [],
                "devices": [],
                "floor_arrows": [{"x": 1, "y": 3, "dir": 0}, {"x": 2, "y": 3, "dir": 0}, {"x": 3, "y": 3, "dir": 0}],
                "required_energy": 0,
                "allowed_blocks": ["move_forward"],
                "four_step_guide": {
                    "step1_concrete": "點擊或拖曳「前進一步」指令卡到右側序列區，按「執行」觀察機器人移動。",
                    "step2_visual": "注意地面上的藍色發光箭頭，每一張「前進」指令卡會讓機器人往前走一格。",
                    "step3_logic": "起點到終點共有 3 格距離，因此需要依序執行 3 次「前進一步」。",
                    "step4_code": "你可以隨時切換右上角「積木 / Python 對照」，看看指令卡如何變成 Blockly 積木！"
                },
                "hints": [
                    "提示一（注意觀察）：數一數機器人前方到綠色終點總共有幾個格子？",
                    "提示二（概念提醒）：每放入一張「前進一步」指令卡，機器人就會往前移動 1 格。",
                    "提示三（局部示範）：試著連續放入 3 張「前進一步」指令卡，再按下「執行程式」！"
                ],
                "example_ast": [{"type": "move_forward"}, {"type": "move_forward"}, {"type": "move_forward"}],
                "reflection_question": {
                    "question": "如果我們只放 2 張「前進一步」指令卡，機器人會發生什麼事？",
                    "options": ["會在終點前一格停下來", "會自動跳到終點", "會往後退"]
                }
            },
            "core": {
                "zone": "zone_control",
                "width": 7,
                "height": 6,
                "start": {"x": 1, "y": 2, "dir": 0},
                "goal": {"x": 3, "y": 4},
                "obstacles": [
                    {"x": 4, "y": 2},
                    {"x": 1, "y": 3},
                    {"x": 2, "y": 3},
                    {"x": 2, "y": 4},
                    {"x": 4, "y": 4}
                ],
                "items": [{"x": 3, "y": 2, "type": "energy", "value": 1}],
                "switches": [],
                "doors": [],
                "devices": [],
                "floor_arrows": [],
                "required_energy": 1,
                "allowed_blocks": ["move_forward", "turn_left", "turn_right", "pickup"],
                "four_step_guide": {
                    "step1_concrete": "標準版出現了 L 型轉角與能源晶片！請自行排列前進、撿取能源與右轉的順序。",
                    "step2_visual": "機器人走到轉角 (3, 2) 時，必須先「撿取能源」並「向右轉」，才能往南走到終點 (3, 4)。",
                    "step3_logic": "注意：「向右轉」只會原地改變面向角度，轉完後還要繼續放「前進一步」才會移動！",
                    "step4_code": "觀察 move_forward()、pickup() 與 turn_right() 的組合順序。"
                },
                "hints": [
                    "提示一（注意觀察）：能源晶片位於轉角 (3, 2)，終點位於下方的 (3, 4)。",
                    "提示二（概念提醒）：從 (1, 2) 前進 2 次到達 (3, 2) 後，執行「撿取能源」與「向右轉」，再前進 2 次抵達 (3, 4)。",
                    "提示三（局部示範）：前進一步 → 前進一步 → 撿取能源 → 向右轉 → 前進一步 → 前進一步。"
                ],
                "example_ast": [],
                "reflection_question": {
                    "question": "為什麼在轉角 (3, 2) 執行「向右轉」之後，還需要再放 2 張「前進一步」？",
                    "options": ["因為轉彎指令只會原地改變方向，不會自動往前走", "因為機器人走太慢", "純粹為了湊字數"]
                }
            },
            "challenge": {
                "zone": "zone_control",
                "width": 8,
                "height": 7,
                "start": {"x": 1, "y": 3, "dir": 0},
                "goal": {"x": 6, "y": 3},
                "obstacles": [
                    {"x": 3, "y": 3},
                    {"x": 4, "y": 3},
                    {"x": 2, "y": 1},
                    {"x": 4, "y": 1},
                    {"x": 2, "y": 5},
                    {"x": 4, "y": 5}
                ],
                "items": [
                    {"x": 3, "y": 2, "type": "energy", "value": 1},
                    {"x": 3, "y": 4, "type": "energy", "value": 1}
                ],
                "switches": [],
                "doors": [],
                "devices": [{"x": 5, "y": 3, "id": "dev_boot", "requires_energy": 1}],
                "floor_arrows": [],
                "required_energy": 1,
                "require_all_devices": True,
                "allowed_blocks": ["move_forward", "turn_left", "turn_right", "pickup", "repair_device"],
                "four_step_guide": {
                    "step1_concrete": "挑戰版中央通道被障礙物封鎖了！上下兩條岔路各有 1 顆能源晶片，任選一條繞行收集能源，並到 (5, 3) 修復設備後抵達 (6, 3)。",
                    "step2_visual": "比較看看：從 (2, 3) 走北側岔路 (y=2) 或南側岔路 (y=4) 都能拿到能源並匯合到 (5, 3) 的發電機！",
                    "step3_logic": "分析多岔路與先後依賴：必須先在岔路「撿取能源」，回到 (5, 3) 才能成功「修復設備」。",
                    "step4_code": "體會同一任務目標可以有不同的路徑規劃與選擇理由！"
                },
                "hints": [
                    "提示一（注意觀察）：正前方 (3, 3) 與 (4, 3) 被障礙擋住了！你可以在 (2, 3) 左轉走上方 (y=2) 或右轉走下方 (y=4)。",
                    "提示二（概念提醒）：若選上方路線：前進到 (2,3) → 左轉 → 前進到 (2,2) → 右轉 → 前進到 (3,2) 撿取能源 → 前進2次到 (5,2) → 右轉 → 前進到 (5,3) 修復設備 → 左轉 → 前進到 (6,3)。",
                    "提示三（局部示範）：記得在 (5, 3) 的橘色設備格執行「修復設備」，再往東走 1 格到綠色終點 (6, 3)！"
                ],
                "example_ast": [],
                "reflection_question": {
                    "question": "在這個雙岔路挑戰中，走上方路線 (y=2) 與走下方路線 (y=4) 步數相同且都能過關，這說明了什麼？",
                    "options": ["面對有多條岔路的問題時，只要能避開干擾物並滿足任務條件，不同路徑都是好解法", "只有走上方才算正確", "電腦不允許走下方路線"]
                }
            }
        }
    },
    {
        "level_code": "ch1_lv2",
        "chapter_id": 1,
        "chapter_name": "第一章：新手維修區",
        "level_order": 2,
        "level_name": "1-2 轉向校準：轉彎與方向感",
        "description": "維修通道出現了轉角！注意「左轉」與「右轉」只會改變機器人面向的方向，不會往前移動格子喔。",
        "difficulty": "guided",
        "learning_objective": "理解「原地轉向」與「前進移動」的差別，建立以機器人視角為主的左右方向感。",
        "concept_code": "sequence",
        "editor_mode": "cards",
        "variants": {
            "guided": {
                "zone": "zone_factory",
                "width": 7,
                "height": 6,
                "start": {"x": 1, "y": 2, "dir": 0},
                "goal": {"x": 3, "y": 4},
                "obstacles": [{"x": 4, "y": 2}, {"x": 2, "y": 3}, {"x": 2, "y": 4}],
                "items": [],
                "switches": [],
                "doors": [],
                "devices": [],
                "floor_arrows": [{"x": 1, "y": 2, "dir": 0}, {"x": 2, "y": 2, "dir": 0}, {"x": 3, "y": 2, "dir": 1}, {"x": 3, "y": 3, "dir": 1}],
                "required_energy": 0,
                "allowed_blocks": ["move_forward", "turn_left", "turn_right"],
                "four_step_guide": {
                    "step1_concrete": "先讓機器人前進到轉角，放入「向右轉」，再繼續「前進」。",
                    "step2_visual": "觀察機器人轉彎時的旋轉動畫：它站在原本的格子上轉向，沒有離開該格。",
                    "step3_logic": "為什麼轉彎後還要再放「前進」？因為轉彎指令只負責改變面向角度。",
                    "step4_code": "turn_right() 與 move_forward() 的先後順序會決定機器人走去哪裡。"
                },
                "hints": [
                    "提示一（注意觀察）：機器人一開始面向右方(東)，走到 (3, 2) 時終點在它的下方(南)。",
                    "提示二（概念提醒）：面向右方時，往下方轉是「向右轉」還是「向左轉」？答案是「向右轉」！",
                    "提示三（局部示範）：前進 → 前進 → 向右轉 → 前進 → 前進。"
                ],
                "example_ast": [
                    {"type": "move_forward"},
                    {"type": "move_forward"},
                    {"type": "turn_right"},
                    {"type": "move_forward"},
                    {"type": "move_forward"}
                ],
                "reflection_question": {
                    "question": "執行「向右轉」指令時，機器人會移動到下一個格子嗎？",
                    "options": ["不會，它只會在原地改變面向的方向", "會自動往右走一格", "會跳過障礙物"]
                }
            },
            "core": {
                "zone": "zone_factory",
                "width": 7,
                "height": 7,
                "start": {"x": 1, "y": 5, "dir": 0},
                "goal": {"x": 4, "y": 2},
                "obstacles": [{"x": 5, "y": 5}, {"x": 3, "y": 4}, {"x": 3, "y": 3}, {"x": 3, "y": 2}],
                "items": [],
                "switches": [],
                "doors": [],
                "devices": [],
                "floor_arrows": [],
                "required_energy": 0,
                "allowed_blocks": ["move_forward", "turn_left", "turn_right"],
                "four_step_guide": {
                    "step1_concrete": "規劃從左下角 (1, 5) 走到右上角 (4, 2) 的轉彎路徑。",
                    "step2_visual": "想像自己就是機器人：當你面向右方時，上方是你的左邊還是右邊？",
                    "step3_logic": "先向右走 3 格到 (4, 5)，再向左轉面向北方，接著前進 3 格。",
                    "step4_code": "對照積木與 Python 預覽中的 turn_left()。"
                },
                "hints": [
                    "提示一（注意觀察）：機器人需要先從 (1, 5) 走到轉角 (4, 5)。",
                    "提示二（概念提醒）：當機器人面向右方時，要轉向畫面「上方」，應該使用「向左轉」。",
                    "提示三（局部示範）：前進 3 次 → 向左轉 → 前進 3 次。"
                ],
                "example_ast": [],
                "reflection_question": {
                    "question": "如果把「向左轉」不小心提早放在第一個「前進」後面，會發生什麼事？",
                    "options": ["機器人會太早轉彎並撞上左側障礙物", "結果完全一樣", "機器人會自動修正"]
                }
            },
            "challenge": {
                "zone": "zone_factory",
                "width": 8,
                "height": 6,
                "start": {"x": 1, "y": 2, "dir": 0},
                "goal": {"x": 5, "y": 4},
                "obstacles": [{"x": 4, "y": 2}, {"x": 2, "y": 3}, {"x": 2, "y": 4}, {"x": 4, "y": 3}, {"x": 3, "y": 5}],
                "items": [],
                "switches": [],
                "doors": [],
                "devices": [],
                "floor_arrows": [],
                "required_energy": 0,
                "allowed_blocks": ["move_forward", "turn_left", "turn_right"],
                "four_step_guide": {
                    "step1_concrete": "通過 S 型連續兩個轉彎的維修通道。",
                    "step2_visual": "注意第二次轉彎時機器人正面向下方(南)，此時往右邊走是機器人的「左方」！",
                    "step3_logic": "將問題拆解成三段直線與兩次轉向。",
                    "step4_code": "比較兩次轉彎分別使用 turn_right() 與 turn_left() 的原因。"
                },
                "hints": [
                    "提示一（注意觀察）：第一段從 (1,2) 到 (3,2)，第二段從 (3,2) 到 (3,4)，第三段從 (3,4) 到 (5,4)。",
                    "提示二（概念提醒）：當機器人面向下方(南)時，要轉向東邊(畫面右方)，對機器人來說是「向左轉」喔！",
                    "提示三（局部示範）：前進2次 → 右轉 → 前進2次 → 左轉 → 前進2次。"
                ],
                "example_ast": [],
                "reflection_question": {
                    "question": "當機器人面向下方時，為什麼要往畫面右邊走卻是用「向左轉」？",
                    "options": ["因為左右轉是以機器人自己面向的方向為準", "因為地圖顛倒了", "這是隨便定的規則"]
                }
            }
        }
    },
    {
        "level_code": "ch1_lv3",
        "chapter_id": 1,
        "chapter_name": "第一章：新手維修區",
        "level_order": 3,
        "level_name": "1-3 繞過殘骸：問題拆解與路線規劃",
        "description": "通道中央有掉落的基地殘骸（紅色警戒障礙物）！你現在可以自由使用「指令卡」或切換成「Blockly 積木」來繞過障礙物。",
        "difficulty": "guided",
        "learning_objective": "學會把「繞過障礙物」拆解成數個轉向與移動步驟，並認識 Blockly 積木與指令卡的對應關係。",
        "concept_code": "sequence",
        "editor_mode": "hybrid",
        "variants": {
            "guided": {
                "zone": "zone_factory",
                "width": 7,
                "height": 6,
                "start": {"x": 1, "y": 3, "dir": 0},
                "goal": {"x": 4, "y": 2},
                "obstacles": [{"x": 3, "y": 3}, {"x": 3, "y": 4}],
                "items": [],
                "switches": [],
                "doors": [],
                "devices": [],
                "floor_arrows": [{"x": 1, "y": 3, "dir": 0}, {"x": 2, "y": 3, "dir": 3}, {"x": 2, "y": 2, "dir": 0}, {"x": 3, "y": 2, "dir": 0}],
                "required_energy": 0,
                "allowed_blocks": ["move_forward", "turn_left", "turn_right"],
                "four_step_guide": {
                    "step1_concrete": "試著點擊上方「切換為 Blockly 積木模式」，把積木像拼圖一樣扣在一起！",
                    "step2_visual": "如果直接往前走 2 格會撞上 (3, 3) 的障礙物，所以要在 (2, 3) 提早轉彎。",
                    "step3_logic": "先走 1 格到 (2,3) → 左轉往上走 1 格到 (2,2) → 右轉往右走 2 格到 (4,2)。",
                    "step4_code": "你會發現 Blockly 積木和剛才排的指令卡順序完全一樣！"
                },
                "hints": [
                    "提示一（注意觀察）：障礙物在 (3, 3)，所以機器人走到 (2, 3) 時就必須轉彎繞開。",
                    "提示二（概念提醒）：從上方繞過障礙物：先左轉向上走一格，再右轉繼續往東走。",
                    "提示三（局部示範）：前進 → 左轉 → 前進 → 右轉 → 前進 → 前進。"
                ],
                "example_ast": [
                    {"type": "move_forward"},
                    {"type": "turn_left"},
                    {"type": "move_forward"},
                    {"type": "turn_right"},
                    {"type": "move_forward"},
                    {"type": "move_forward"}
                ],
                "reflection_question": {
                    "question": "指令卡和 Blockly 積木有什麼共同點？",
                    "options": ["都是按照由上到下的排列順序，一步一步控制機器人", "完全沒有關係", "積木只能用來畫圖"]
                }
            },
            "core": {
                "zone": "zone_factory",
                "width": 7,
                "height": 6,
                "start": {"x": 1, "y": 3, "dir": 0},
                "goal": {"x": 5, "y": 3},
                "obstacles": [{"x": 3, "y": 3}],
                "items": [],
                "switches": [],
                "doors": [],
                "devices": [],
                "floor_arrows": [],
                "required_energy": 0,
                "allowed_blocks": ["move_forward", "turn_left", "turn_right"],
                "four_step_guide": {
                    "step1_concrete": "繞過正中央 (3, 3) 的障礙物，並回到同一條水平線上的終點 (5, 3)。",
                    "step2_visual": "你可以走上方路線 (y=2) 或下方路線 (y=4)，兩條路線都能通關！",
                    "step3_logic": "繞過障礙物後，記得轉彎回到 y=3 的通道。",
                    "step4_code": "同一個問題可以有不同的正確程式解法。"
                },
                "hints": [
                    "提示一（注意觀察）：起點在 (1,3)，障礙在 (3,3)，終點在 (5,3)。上下兩側都沒有障礙物！",
                    "提示二（概念提醒）：走上方或走下方都可以，注意繞過去之後要再轉彎回到 y=3。",
                    "提示三（局部示範）：前進 → 左轉 → 前進 → 右轉 → 前進 → 前進 → 右轉 → 前進 → 左轉 → 前進。"
                ],
                "example_ast": [],
                "reflection_question": {
                    "question": "這關從上方繞過或從下方繞過都能抵達終點，這代表什麼？",
                    "options": ["解決同一個問題可以有不只一種正確的演算法與路線", "其中一條一定算錯", "電腦只接受一種答案"]
                }
            },
            "challenge": {
                "zone": "zone_factory",
                "width": 8,
                "height": 6,
                "start": {"x": 1, "y": 3, "dir": 0},
                "goal": {"x": 6, "y": 3},
                "obstacles": [{"x": 3, "y": 3}, {"x": 4, "y": 2}],
                "items": [],
                "switches": [],
                "doors": [],
                "devices": [],
                "floor_arrows": [],
                "required_energy": 0,
                "allowed_blocks": ["move_forward", "turn_left", "turn_right"],
                "four_step_guide": {
                    "step1_concrete": "觀察地圖上的兩處障礙物 (3,3) 與 (4,2)，比較上方與下方路線哪一條比較順暢！",
                    "step2_visual": "上方路線在 (4,2) 被擋住了，而下方 (y=4) 路線是暢通的。",
                    "step3_logic": "先分析整體地圖再動手排積木，可以減少走冤枉路。",
                    "step4_code": "規劃下方繞行路徑抵達 (6, 3)。"
                },
                "hints": [
                    "提示一（注意觀察）：看看上方 (4, 2) 也有一個障礙物，走下方 (y=4) 通道會不會比較順？",
                    "提示二（概念提醒）：在 (2, 3) 向右轉進入 y=4 通道，直走繞過障礙後再左轉回 y=3。",
                    "提示三（局部示範）：前進 → 右轉 → 前進 → 左轉 → 前進3次 → 左轉 → 前進 → 右轉 → 前進。"
                ],
                "example_ast": [],
                "reflection_question": {
                    "question": "在有多條岔路的地圖中，寫程式前先做什麼最有幫助？",
                    "options": ["先觀察地圖障礙並規劃好完整路線再開始排列積木", "隨便亂放積木碰運氣", "只看起點不看終點"]
                }
            }
        }
    },
    {
        "level_code": "ch1_lv4",
        "chapter_id": 1,
        "chapter_name": "第一章：新手維修區",
        "level_order": 4,
        "level_name": "1-4 收集首顆能源晶片",
        "description": "基地系統需要能源晶片才能重新供電！請讓機器人走到發光的藍色能源晶片位置，執行「撿取能源」，再前往終點。",
        "difficulty": "guided",
        "learning_objective": "學會結合移動與互動指令（撿取能源），注意互動指令必須在機器人站在物品格子上時執行。",
        "concept_code": "sequence",
        "editor_mode": "hybrid",
        "variants": {
            "guided": {
                "zone": "zone_factory",
                "width": 7,
                "height": 6,
                "start": {"x": 1, "y": 3, "dir": 0},
                "goal": {"x": 5, "y": 3},
                "obstacles": [],
                "items": [{"x": 3, "y": 3, "type": "energy", "value": 1}],
                "switches": [],
                "doors": [],
                "devices": [],
                "floor_arrows": [{"x": 1, "y": 3, "dir": 0}, {"x": 2, "y": 3, "dir": 0}, {"x": 3, "y": 3, "dir": 0}, {"x": 4, "y": 3, "dir": 0}],
                "required_energy": 1,
                "allowed_blocks": ["move_forward", "turn_left", "turn_right", "pickup"],
                "four_step_guide": {
                    "step1_concrete": "當機器人走到能源晶片所在的 (3, 3) 時，必須放入「撿取能源」積木。",
                    "step2_visual": "如果只是走過去而沒有放「撿取能源」，能源晶片不會自己進到背包喔！",
                    "step3_logic": "順序是：走到晶片格 → 撿取能源 → 繼續走到終點。",
                    "step4_code": "pickup() 代表在目前所在位置執行撿取動作。"
                },
                "hints": [
                    "提示一（注意觀察）：能源晶片在 (3, 3)，距離起點 (1, 3) 是 2 格。",
                    "提示二（概念提醒）：前進 2 次抵達 (3, 3) 後，要立刻執行「撿取能源」，再前進 2 次到終點 (5, 3)。",
                    "提示三（局部示範）：前進 → 前進 → 撿取能源 → 前進 → 前進。"
                ],
                "example_ast": [
                    {"type": "move_forward"},
                    {"type": "move_forward"},
                    {"type": "pickup"},
                    {"type": "move_forward"},
                    {"type": "move_forward"}
                ],
                "reflection_question": {
                    "question": "如果在一開始起點 (1, 3) 就先執行「撿取能源」，再往前走到終點，能收集到位於 (3, 3) 的能源嗎？",
                    "options": ["不能，必須先走到有能源晶片的格子上再執行撿取", "可以，機器人會隔空吸取", "能源會自己跑到終點"]
                }
            },
            "core": {
                "zone": "zone_factory",
                "width": 7,
                "height": 7,
                "start": {"x": 1, "y": 2, "dir": 0},
                "goal": {"x": 4, "y": 5},
                "obstacles": [{"x": 2, "y": 4}, {"x": 3, "y": 4}],
                "items": [{"x": 4, "y": 2, "type": "energy", "value": 1}],
                "switches": [],
                "doors": [],
                "devices": [],
                "floor_arrows": [],
                "required_energy": 1,
                "allowed_blocks": ["move_forward", "turn_left", "turn_right", "pickup"],
                "four_step_guide": {
                    "step1_concrete": "先前往轉角 (4, 2) 撿取能源，再轉彎前往下方終點 (4, 5)。",
                    "step2_visual": "觀察右上角「能源：0 / 1」在撿取瞬間變成「1 / 1」！",
                    "step3_logic": "確認撿取與轉彎放在正確的步數位置。",
                    "step4_code": "檢視 pickup() 與 turn_right() 的組合。"
                },
                "hints": [
                    "提示一（注意觀察）：能源晶片剛好在轉角 (4, 2) 上！",
                    "提示二（概念提醒）：前進 3 格到 (4, 2) 後，可以「撿取能源」並「向右轉」，再前進 3 格到 (4, 5)。",
                    "提示三（局部示範）：前進3次 → 撿取能源 → 右轉 → 前進3次。"
                ],
                "example_ast": [],
                "reflection_question": {
                    "question": "站在 (4, 2) 格子上時，「先撿取再右轉」和「先右轉再撿取」結果一樣嗎？",
                    "options": ["一樣，因為右轉只是原地轉向，機器人還站在 (4, 2) 格子上", "不一樣，右轉後能源會消失", "會發生錯誤"]
                }
            },
            "challenge": {
                "zone": "zone_factory",
                "width": 8,
                "height": 7,
                "start": {"x": 1, "y": 2, "dir": 0},
                "goal": {"x": 6, "y": 5},
                "obstacles": [{"x": 4, "y": 2}, {"x": 2, "y": 4}],
                "items": [
                    {"x": 3, "y": 2, "type": "energy", "value": 1},
                    {"x": 3, "y": 5, "type": "energy", "value": 1}
                ],
                "switches": [],
                "doors": [],
                "devices": [],
                "floor_arrows": [],
                "required_energy": 2,
                "allowed_blocks": ["move_forward", "turn_left", "turn_right", "pickup"],
                "four_step_guide": {
                    "step1_concrete": "依序收集兩顆能源晶片 (3, 2) 與 (3, 5)，最後抵達 (6, 5)。",
                    "step2_visual": "分段檢查：第一顆能源拿到後，往哪裡轉才能拿到第二顆？",
                    "step3_logic": "將長路徑切分成「起點→能源1」、「能源1→能源2」、「能源2→終點」三個小任務。",
                    "step4_code": "體會問題拆解（Decomposition）在程式設計中的威力。"
                },
                "hints": [
                    "提示一（注意觀察）：兩顆能源分別在 (3, 2) 與 (3, 5)，終點在 (6, 5)。",
                    "提示二（概念提醒）：在 (3, 2) 撿取第一顆後向右轉走 3 格到 (3, 5) 撿取第二顆，再向左轉走 3 格到 (6, 5)。",
                    "提示三（局部示範）：前進2次 → 撿取 → 右轉 → 前進3次 → 撿取 → 左轉 → 前進3次。"
                ],
                "example_ast": [],
                "reflection_question": {
                    "question": "面對比較複雜的任務時，怎麼做最不容易出錯？",
                    "options": ["把大任務拆成幾個小段落，一段一段測試確認", "一口氣排完 20 個積木都不測試", "跳過收集直接去終點"]
                }
            }
        }
    },
    {
        "level_code": "ch1_lv5",
        "chapter_id": 1,
        "chapter_name": "第一章：新手維修區",
        "level_order": 5,
        "level_name": "1-5 第一章整合：修復第一台供電設備",
        "description": "恭喜完成基礎訓練！現在請正式使用 Blockly 積木：先撿取能源晶片，走到受損的橘色發電機設備上執行「修復設備」，最後抵達終點。",
        "difficulty": "core",
        "learning_objective": "整合移動、轉向、撿取能源與修復設備指令，完成具備先後依賴關係的完整任務（必須先有能源才能修復設備）。",
        "concept_code": "sequence",
        "editor_mode": "blockly",
        "variants": {
            "guided": {
                "zone": "zone_factory",
                "width": 7,
                "height": 6,
                "start": {"x": 1, "y": 3, "dir": 0},
                "goal": {"x": 5, "y": 3},
                "obstacles": [],
                "items": [{"x": 2, "y": 3, "type": "energy", "value": 1}],
                "switches": [],
                "doors": [],
                "devices": [{"x": 4, "y": 3, "id": "dev_1", "requires_energy": 1}],
                "floor_arrows": [{"x": 1, "y": 3, "dir": 0}, {"x": 2, "y": 3, "dir": 0}, {"x": 3, "y": 3, "dir": 0}, {"x": 4, "y": 3, "dir": 0}],
                "required_energy": 1,
                "require_all_devices": True,
                "allowed_blocks": ["move_forward", "turn_left", "turn_right", "pickup", "repair_device"],
                "four_step_guide": {
                    "step1_concrete": "從左側工具箱拖曳 Blockly 積木，組合成完整修復流程。",
                    "step2_visual": "機器人需要先在 (2, 3) 撿取能源，走到 (4, 3) 才能成功「修復設備」。",
                    "step3_logic": "如果還沒撿取能源就執行修復設備，系統會提示能源不足！這就是程式的「先後依賴順序」。",
                    "step4_code": "查看右側 Python 預覽視窗，認識結構化的函式呼叫順序。"
                },
                "hints": [
                    "提示一（注意觀察）：(2, 3) 有能源晶片，(4, 3) 有受損設備，(5, 3) 是終點。",
                    "提示二（概念提醒）：前進 1 格 → 撿取能源 → 前進 2 格 → 修復設備 → 前進 1 格。",
                    "提示三（局部示範）：可點擊「載入範例」觀察積木如何拼接！"
                ],
                "example_ast": [
                    {"type": "move_forward"},
                    {"type": "pickup"},
                    {"type": "move_forward"},
                    {"type": "move_forward"},
                    {"type": "repair_device"},
                    {"type": "move_forward"}
                ],
                "reflection_question": {
                    "question": "為什麼必須先執行「撿取能源」，後面才能執行「修復設備」？",
                    "options": ["因為修復設備需要消耗或驗證已收集的能源，順序顛倒會失敗", "純粹因為積木比較好看", "其實順序可以隨便調換"]
                }
            },
            "core": {
                "zone": "zone_factory",
                "width": 7,
                "height": 7,
                "start": {"x": 1, "y": 2, "dir": 0},
                "goal": {"x": 5, "y": 4},
                "obstacles": [{"x": 4, "y": 2}, {"x": 2, "y": 4}],
                "items": [{"x": 3, "y": 2, "type": "energy", "value": 1}],
                "switches": [],
                "doors": [],
                "devices": [{"x": 3, "y": 4, "id": "dev_1", "requires_energy": 1}],
                "floor_arrows": [],
                "required_energy": 1,
                "require_all_devices": True,
                "allowed_blocks": ["move_forward", "turn_left", "turn_right", "pickup", "repair_device"],
                "four_step_guide": {
                    "step1_concrete": "獨立規劃從 (1,2) 撿取能源、到 (3,4) 修復設備、再到 (5,4) 終點的積木程式。",
                    "step2_visual": "善用「單步執行」檢查轉彎與互動的位置是否精確。",
                    "step3_logic": "確認每個互動積木（撿取、修復）都放在對應座標抵達之後。",
                    "step4_code": "完成第一章所有基礎指令訓練！"
                },
                "hints": [
                    "提示一（注意觀察）：能源在 (3, 2)，設備在 (3, 4)，終點在 (5, 4)。",
                    "提示二（概念提醒）：到 (3, 2) 撿取能源並右轉 → 走 2 格到 (3, 4) 修復設備並左轉 → 走 2 格到 (5, 4)。",
                    "提示三（局部示範）：前進2次 → 撿取 → 右轉 → 前進2次 → 修復設備 → 左轉 → 前進2次。"
                ],
                "example_ast": [],
                "reflection_question": {
                    "question": "當程式出現錯誤時，哪一個工具最能幫我們找出是哪一步出錯？",
                    "options": ["單步執行與積木步驟高亮提示", "把整個網頁關掉重開", "隨便刪掉最後一個積木"]
                }
            },
            "challenge": {
                "zone": "zone_factory",
                "width": 8,
                "height": 7,
                "start": {"x": 1, "y": 2, "dir": 0},
                "goal": {"x": 5, "y": 5},
                "obstacles": [{"x": 4, "y": 3}],
                "items": [
                    {"x": 3, "y": 2, "type": "energy", "value": 1},
                    {"x": 5, "y": 2, "type": "energy", "value": 1}
                ],
                "switches": [],
                "doors": [],
                "devices": [{"x": 5, "y": 4, "id": "dev_1", "requires_energy": 2}],
                "floor_arrows": [],
                "required_energy": 2,
                "require_all_devices": True,
                "allowed_blocks": ["move_forward", "turn_left", "turn_right", "pickup", "repair_device"],
                "four_step_guide": {
                    "step1_concrete": "這台大型發電機需要 2 顆能源晶片才能修復！",
                    "step2_visual": "先沿著上方通道收集 (3,2) 與 (5,2) 兩顆能源，再南下至 (5,4) 修復設備。",
                    "step3_logic": "分析前置條件：能源 >= 2 才能修復 (5,4) 的設備。",
                    "step4_code": "挑戰成功後即可進入第二章學習「迴圈」！"
                },
                "hints": [
                    "提示一（注意觀察）：設備需要 2 顆能源，剛好在 (3, 2) 和 (5, 2) 各有一顆。",
                    "提示二（概念提醒）：直走收集兩顆能源後，在 (5, 2) 向右轉往下走 2 格到 (5, 4) 修復設備，再走 1 格到 (5, 5)。",
                    "提示三（局部示範）：前進2次 → 撿取 → 前進2次 → 撿取 → 右轉 → 前進2次 → 修復設備 → 前進1次。"
                ],
                "example_ast": [],
                "reflection_question": {
                    "question": "如果只撿了 1 顆能源就去修需要 2 顆能源的設備，會發生什麼事？",
                    "options": ["機器人會回報能源不足並停在該步驟提醒我們", "設備會修好一半", "系統會當機"]
                }
            }
        }
    },

    # ==================== 第二章：能源研究區 (Stage 2: 迴圈) ====================
    {
        "level_code": "ch2_lv1",
        "chapter_id": 2,
        "chapter_name": "第二章：能源研究區",
        "level_order": 6,
        "level_name": "2-1 能源長廊：認識重複迴圈",
        "description": "能源研究區的長廊上排列著多顆能源晶片！與其重複放好幾次相同的積木，試試看使用「重複 N 次」迴圈積木吧！",
        "difficulty": "guided",
        "learning_objective": "發現重複出現的動作規律，使用固定次數迴圈（Repeat N times）簡化程式結構。",
        "concept_code": "loops",
        "editor_mode": "blockly",
        "variants": {
            "guided": {
                "zone": "zone_energy",
                "width": 7,
                "height": 6,
                "start": {"x": 1, "y": 3, "dir": 0},
                "goal": {"x": 4, "y": 3},
                "obstacles": [],
                "items": [
                    {"x": 2, "y": 3, "type": "energy", "value": 1},
                    {"x": 3, "y": 3, "type": "energy", "value": 1},
                    {"x": 4, "y": 3, "type": "energy", "value": 1}
                ],
                "switches": [],
                "doors": [],
                "devices": [],
                "floor_arrows": [{"x": 1, "y": 3, "dir": 0}, {"x": 2, "y": 3, "dir": 0}, {"x": 3, "y": 3, "dir": 0}],
                "required_energy": 3,
                "allowed_blocks": ["move_forward", "turn_left", "turn_right", "pickup", "repeat_n"],
                "four_step_guide": {
                    "step1_concrete": "把「前進一步」和「撿取能源」放進紫色的「重複 3 次」迴圈積木肚子裡！",
                    "step2_visual": "執行時觀察迴圈積木如何反覆高亮，帶動機器人連續完成 3 次「前進＋撿取」。",
                    "step3_logic": "原本需要 6 個積木（前進、撿取 × 3），用迴圈只需要 3 個積木！",
                    "step4_code": "在 Python 中，這對應到 `for i in range(3):` 迴圈語法。"
                },
                "hints": [
                    "提示一（注意觀察）：每一格都有一顆能源晶片，連續 3 格都是「前進一步 → 撿取能源」。",
                    "提示二（概念提醒）：拖出「重複 3 次」積木，把「前進一步」與「撿取能源」放進它的內部插槽。",
                    "提示三（局部示範）：重複 3 次 { 前進一步, 撿取能源 }。"
                ],
                "example_ast": [
                    {
                        "type": "repeat_n",
                        "count": 3,
                        "body": [
                            {"type": "move_forward"},
                            {"type": "pickup"}
                        ]
                    }
                ],
                "reflection_question": {
                    "question": "「重複 3 次 { 前進一步、撿取能源 }」總共會讓機器人前進幾格、撿取幾次？",
                    "options": ["前進 3 格、撿取 3 次", "前進 3 格、只撿取 1 次", "前進 1 格、撿取 3 次"]
                }
            },
            "core": {
                "zone": "zone_energy",
                "width": 8,
                "height": 6,
                "start": {"x": 1, "y": 2, "dir": 0},
                "goal": {"x": 5, "y": 4},
                "obstacles": [
                    {"x": 6, "y": 2},
                    {"x": 2, "y": 3},
                    {"x": 3, "y": 3},
                    {"x": 4, "y": 3},
                    {"x": 6, "y": 3}
                ],
                "items": [
                    {"x": 2, "y": 2, "type": "energy", "value": 1},
                    {"x": 3, "y": 2, "type": "energy", "value": 1},
                    {"x": 4, "y": 2, "type": "energy", "value": 1},
                    {"x": 5, "y": 2, "type": "energy", "value": 1}
                ],
                "switches": [],
                "doors": [],
                "devices": [],
                "floor_arrows": [],
                "required_energy": 4,
                "allowed_blocks": ["move_forward", "turn_left", "turn_right", "pickup", "repeat_n"],
                "four_step_guide": {
                    "step1_concrete": "長廊上有 4 顆能源晶片，但終點位於轉角下方的 (5, 4)！",
                    "step2_visual": "先用「重複 4 次 { 前進一步, 撿取能源 }」走完橫向長廊，再在迴圈外加上「向右轉」與 2 次「前進一步」。",
                    "step3_logic": "分辨「重複發生的動作（放迴圈內）」與「只做一次的收尾動作（放迴圈外）」。",
                    "step4_code": "觀察 Python 預覽中縮排在 `for` 迴圈內與迴圈外的差別。"
                },
                "hints": [
                    "提示一（注意觀察）：(2,2) 到 (5,2) 有連續 4 顆能源晶片，走到 (5,2) 後需要向右轉往南走到 (5,4)。",
                    "提示二（概念提醒）：將「重複 4 次 { 前進一步, 撿取能源 }」排好後，在迴圈下方接上「向右轉 → 前進一步 → 前進一步」。",
                    "提示三（局部示範）：重複 4 次 { 前進一步, 撿取能源 } → 向右轉 → 前進一步 → 前進一步。"
                ],
                "example_ast": [],
                "reflection_question": {
                    "question": "為什麼「向右轉」要放在「重複 4 次」迴圈的外面（下方），而不是放在迴圈裡面？",
                    "options": ["因為我們只需要在收集完 4 顆能源後轉彎一次，放裡面會每走一格就轉彎", "因為迴圈裡面不能放轉彎積木", "放裡面或外面結果完全一樣"]
                }
            },
            "challenge": {
                "zone": "zone_energy",
                "width": 7,
                "height": 7,
                "start": {"x": 1, "y": 2, "dir": 0},
                "goal": {"x": 4, "y": 5},
                "obstacles": [{"x": 2, "y": 4}, {"x": 3, "y": 4}],
                "items": [
                    {"x": 2, "y": 2, "type": "energy", "value": 1},
                    {"x": 3, "y": 2, "type": "energy", "value": 1},
                    {"x": 4, "y": 2, "type": "energy", "value": 1},
                    {"x": 4, "y": 3, "type": "energy", "value": 1},
                    {"x": 4, "y": 4, "type": "energy", "value": 1},
                    {"x": 4, "y": 5, "type": "energy", "value": 1}
                ],
                "switches": [],
                "doors": [],
                "devices": [],
                "floor_arrows": [],
                "required_energy": 6,
                "allowed_blocks": ["move_forward", "turn_left", "turn_right", "pickup", "repeat_n"],
                "four_step_guide": {
                    "step1_concrete": "這條 L 型能源走廊分成橫向與縱向兩段，試著組合兩段迴圈（或巢狀迴圈）完成任務！",
                    "step2_visual": "注意「向右轉」應該放在第一個迴圈結束之後，還是放在迴圈裡面？",
                    "step3_logic": "比較兩種寫法：① 兩個重複 3 次迴圈中間放右轉；② 外層重複 2 次包住內層重複 3 次！",
                    "step4_code": "能分辨「迴圈內」與「迴圈外」的差異是掌握迴圈的關鍵。"
                },
                "hints": [
                    "提示一（注意觀察）：橫向有 3 顆能源，轉角右轉後縱向又有 3 顆能源。",
                    "提示二（概念提醒）：先「重複 3 次 { 前進, 撿取 }」，接著在迴圈外「向右轉」，再「重複 3 次 { 前進, 撿取 }」。",
                    "提示三（局部示範）：你也可以用巢狀迴圈：重複 2 次 { 重複 3 次 { 前進, 撿取 }, 向右轉 }！"
                ],
                "example_ast": [],
                "reflection_question": {
                    "question": "如果把「向右轉」不小心放進「重複 3 次 { 前進, 撿取, 右轉 }」裡面，機器人會怎麼走？",
                    "options": ["每走一格就右轉一次，變成在原地繞小圈圈", "會先走完 3 格才右轉", "會直接飛到終點"]
                }
            }
        }
    },
    {
        "level_code": "ch2_lv2",
        "chapter_id": 2,
        "chapter_name": "第二章：能源研究區",
        "level_order": 7,
        "level_name": "2-2 階梯充能陣列：多動作迴圈整合",
        "description": "研究區的充能開關與能源呈規律排列！找出每一組重複的動作模式，用迴圈一次啟動所有裝置。",
        "difficulty": "core",
        "learning_objective": "能從較複雜的地圖中找出規律（Pattern Recognition），將多個動作封裝在同一個迴圈中重複執行。",
        "concept_code": "loops",
        "editor_mode": "blockly",
        "variants": {
            "guided": {
                "zone": "zone_energy",
                "width": 7,
                "height": 6,
                "start": {"x": 1, "y": 3, "dir": 0},
                "goal": {"x": 5, "y": 3},
                "obstacles": [],
                "items": [],
                "switches": [
                    {"x": 2, "y": 3, "id": "sw1"},
                    {"x": 3, "y": 3, "id": "sw2"},
                    {"x": 4, "y": 3, "id": "sw3"}
                ],
                "doors": [],
                "devices": [],
                "floor_arrows": [{"x": 1, "y": 3, "dir": 0}, {"x": 2, "y": 3, "dir": 0}, {"x": 3, "y": 3, "dir": 0}],
                "required_energy": 0,
                "require_all_switches": True,
                "allowed_blocks": ["move_forward", "turn_left", "turn_right", "activate_switch", "repeat_n"],
                "four_step_guide": {
                    "step1_concrete": "連續啟動 3 個地板控制開關後，再往前走 1 格到終點。",
                    "step2_visual": "啟動開關時地板會由暗紫色亮起為青綠色！",
                    "step3_logic": "前 3 格是規律的「前進＋啟動開關」，最後 1 格只需要「前進」放在迴圈外。",
                    "step4_code": "練習迴圈結束後接續一般指令的結構。"
                },
                "hints": [
                    "提示一（注意觀察）：開關位於 (2,3)、(3,3)、(4,3)，終點在 (5,3)。",
                    "提示二（概念提醒）：用「重複 3 次 { 前進一步, 啟動開關 }」啟動三個開關，最後在迴圈下方再加一個「前進一步」。",
                    "提示三（局部示範）：重複 3 次 { 前進一步, 啟動開關 } → 前進一步。"
                ],
                "example_ast": [
                    {
                        "type": "repeat_n",
                        "count": 3,
                        "body": [
                            {"type": "move_forward"},
                            {"type": "activate_switch"}
                        ]
                    },
                    {"type": "move_forward"}
                ],
                "reflection_question": {
                    "question": "為什麼最後一個「前進一步」要放在迴圈外面？",
                    "options": ["因為只有最後走到終點那一步不需要再啟動開關", "因為迴圈裡面只能放兩個積木", "放在裡面外面沒差別"]
                }
            },
            "core": {
                "zone": "zone_energy",
                "width": 7,
                "height": 7,
                "start": {"x": 1, "y": 2, "dir": 0},
                "goal": {"x": 4, "y": 5},
                "obstacles": [{"x": 1, "y": 3}, {"x": 2, "y": 4}, {"x": 3, "y": 5}],
                "items": [
                    {"x": 2, "y": 3, "type": "energy", "value": 1},
                    {"x": 3, "y": 4, "type": "energy", "value": 1},
                    {"x": 4, "y": 5, "type": "energy", "value": 1}
                ],
                "switches": [],
                "doors": [],
                "devices": [],
                "floor_arrows": [],
                "required_energy": 3,
                "allowed_blocks": ["move_forward", "turn_left", "turn_right", "pickup", "repeat_n"],
                "four_step_guide": {
                    "step1_concrete": "觀察階梯狀排列的 3 顆能源晶片，找出每一階的重複動作！",
                    "step2_visual": "每一階都是：往右走 1 格 → 右轉 → 往下走 1 格 → 撿取能源 → 左轉（恢復面向右方）。",
                    "step3_logic": "關鍵技巧：在迴圈最後加上「向左轉」，就能讓機器人恢復初始面向，順利接下一輪迴圈！",
                    "step4_code": "這是演算法中非常重要的「迴圈不變量（保持方向一致）」概念。"
                },
                "hints": [
                    "提示一（注意觀察）：從 (1,2) 到 (2,3)、從 (2,3) 到 (3,4)、從 (3,4) 到 (4,5) 都是往右下走一階！",
                    "提示二（概念提醒）：每一階做完「前進 → 右轉 → 前進 → 撿取」後，記得「左轉」讓機器人重新面向右方。",
                    "提示三（局部示範）：重複 3 次 { 前進, 右轉, 前進, 撿取能源, 左轉 }。"
                ],
                "example_ast": [],
                "reflection_question": {
                    "question": "在階梯迴圈的最後加上「向左轉」有什麼重要作用？",
                    "options": ["讓機器人恢復面向右方，這樣下一輪迴圈開始時方向才會一致", "只是為了跳支舞", "沒有作用"]
                }
            },
            "challenge": {
                "zone": "zone_energy",
                "width": 7,
                "height": 7,
                "start": {"x": 2, "y": 2, "dir": 0},
                "goal": {"x": 2, "y": 2},
                "obstacles": [{"x": 3, "y": 3}, {"x": 4, "y": 3}, {"x": 3, "y": 4}, {"x": 4, "y": 4}],
                "items": [
                    {"x": 5, "y": 2, "type": "energy", "value": 1},
                    {"x": 5, "y": 5, "type": "energy", "value": 1},
                    {"x": 2, "y": 5, "type": "energy", "value": 1}
                ],
                "switches": [],
                "doors": [],
                "devices": [],
                "floor_arrows": [],
                "required_energy": 3,
                "allowed_blocks": ["move_forward", "turn_left", "turn_right", "pickup", "repeat_n"],
                "four_step_guide": {
                    "step1_concrete": "環繞中央反應爐一圈收集三個角落的能源，並回到起點/終點 (2, 2)！",
                    "step2_visual": "正方形的四個邊長都是 3 格！",
                    "step3_logic": "試著用巢狀迴圈：外層重複 4 次（四條邊），內層重複 3 次（每邊走 3 格）！",
                    "step4_code": "比較看看：使用巢狀迴圈與不使用迴圈，積木數量相差多少？"
                },
                "hints": [
                    "提示一（注意觀察）：這是一個 3×3 邊長的正方形環形步道，起點與終點都在 (2, 2)。",
                    "提示二（概念提醒）：每條邊走 3 格後「撿取能源」並「向右轉」，重複 4 條邊就會剛好回到 (2, 2)！",
                    "提示三（局部示範）：重複 4 次 { 重複 3 次 { 前進一步 }, 撿取能源, 向右轉 }。"
                ],
                "example_ast": [],
                "reflection_question": {
                    "question": "使用「重複 4 次 { 重複 3 次 { 前進 }, 撿取, 右轉 }」解決正方形路線，展現了什麼概念？",
                    "options": ["巢狀迴圈（迴圈裡面包著另一個迴圈）能優雅解決二維規律問題", "程式越長越好", "只能用在直線"]
                }
            }
        }
    },

    # ==================== 第三章：故障迷宮 (Stage 3: 條件判斷) ====================
    {
        "level_code": "ch3_lv1",
        "chapter_id": 3,
        "chapter_name": "第三章：故障迷宮",
        "level_order": 8,
        "level_name": "3-1 障礙掃描儀：如果…否則…",
        "description": "地下迷宮的通道需要自動導航！使用「如果前方有障礙物 → 向右轉，否則 → 前進一步」，讓機器人學會自己判斷路況。",
        "difficulty": "guided",
        "learning_objective": "理解條件判斷（if / else），讓機器人能根據前方是否有障礙物自動選擇不同行動。",
        "concept_code": "conditions",
        "editor_mode": "blockly",
        "variants": {
            "guided": {
                "zone": "zone_maze",
                "width": 7,
                "height": 7,
                "start": {"x": 1, "y": 2, "dir": 0},
                "goal": {"x": 3, "y": 5},
                "obstacles": [{"x": 4, "y": 2}, {"x": 2, "y": 3}, {"x": 2, "y": 4}, {"x": 2, "y": 5}],
                "items": [],
                "switches": [],
                "doors": [],
                "devices": [],
                "floor_arrows": [{"x": 1, "y": 2, "dir": 0}, {"x": 2, "y": 2, "dir": 0}, {"x": 3, "y": 2, "dir": 1}, {"x": 3, "y": 3, "dir": 1}, {"x": 3, "y": 4, "dir": 1}],
                "required_energy": 0,
                "allowed_blocks": ["move_forward", "turn_left", "turn_right", "repeat_n", "repeat_until_goal", "if", "if_else", "obstacle_ahead"],
                "four_step_guide": {
                    "step1_concrete": "在迴圈內放入「如果 (前方有障礙物) 執行 { 向右轉 } 否則 { 前進一步 }」。",
                    "step2_visual": "觀察機器人每一步都會先發射雷達掃描前方：沒障礙就前進，遇到 (4, 2) 障礙就自動右轉！",
                    "step3_logic": "同一段條件判斷程式，在不同格子上會因為環境不同而做出不同決定。",
                    "step4_code": "對照 Python 的 `if obstacle_ahead(): turn_right() else: move_forward()`。"
                },
                "hints": [
                    "提示一（注意觀察）：機器人往右走 2 格到 (3, 2) 時，正前方 (4, 2) 有一顆障礙物！",
                    "提示二（概念提醒）：把「如果前方有障礙物 → 右轉，否則 → 前進」放進「持續執行直到終點」（或重複 6 次）裡。",
                    "提示三（局部示範）：持續執行直到終點 { 如果 (前方有障礙物) { 向右轉 } 否則 { 前進一步 } }。"
                ],
                "example_ast": [
                    {
                        "type": "repeat_until_goal",
                        "body": [
                            {
                                "type": "if_else",
                                "condition": {"type": "obstacle_ahead"},
                                "then_body": [{"type": "turn_right"}],
                                "else_body": [{"type": "move_forward"}]
                            }
                        ]
                    }
                ],
                "reflection_question": {
                    "question": "在「如果前方有障礙物就右轉，否則前進」中，當前方「沒有」障礙物時，機器人會做什麼？",
                    "options": ["執行「否則」裡面的「前進一步」", "什麼都不做", "同時右轉又前進"]
                }
            },
            "core": {
                "zone": "zone_maze",
                "width": 7,
                "height": 7,
                "start": {"x": 1, "y": 1, "dir": 0},
                "goal": {"x": 1, "y": 4},
                "obstacles": [{"x": 5, "y": 1}, {"x": 4, "y": 5}],
                "items": [],
                "switches": [],
                "doors": [],
                "devices": [],
                "floor_arrows": [],
                "required_energy": 0,
                "allowed_blocks": ["move_forward", "turn_left", "turn_right", "repeat_n", "repeat_until_goal", "if", "if_else", "obstacle_ahead"],
                "four_step_guide": {
                    "step1_concrete": "設計一段自動導航迴圈，讓機器人連續遇到兩處障礙物時都能自動右轉抵達 (1, 4)！",
                    "step2_visual": "機器人會在 (4, 1) 遇到第一個障礙右轉，在 (4, 4) 遇到第二個障礙再次右轉。",
                    "step3_logic": "不需要自己算每段有幾格，交給「持續執行直到終點」＋「if/else」自動判斷！",
                    "step4_code": "感受條件判斷如何讓機器人具備初步的「智慧反應」能力。"
                },
                "hints": [
                    "提示一（注意觀察）：轉角 (4, 1) 和 (4, 4) 的正前方都有障礙物，而且兩次轉彎都是向右轉！",
                    "提示二（概念提醒）：使用「持續執行直到終點」包住「如果 (前方有障礙物) → 向右轉，否則 → 前進一步」。",
                    "提示三（局部示範）：持續執行直到終點 { 如果 (前方有障礙物) { 向右轉 } 否則 { 前進一步 } }。"
                ],
                "example_ast": [],
                "reflection_question": {
                    "question": "為什麼這關不用算每條邊要走幾步，也能走完兩個轉彎？",
                    "options": ["因為機器人每一步都透過條件判斷檢查前方是否有障礙物", "因為地圖會自己移動", "因為機器人記住了答案"]
                }
            },
            "challenge": {
                "zone": "zone_maze",
                "width": 7,
                "height": 7,
                "start": {"x": 1, "y": 1, "dir": 0},
                "goal": {"x": 1, "y": 4},
                "obstacles": [{"x": 5, "y": 1}, {"x": 4, "y": 5}],
                "items": [
                    {"x": 3, "y": 1, "type": "energy", "value": 1},
                    {"x": 4, "y": 3, "type": "energy", "value": 1}
                ],
                "switches": [],
                "doors": [],
                "devices": [],
                "floor_arrows": [],
                "required_energy": 2,
                "allowed_blocks": ["move_forward", "turn_left", "turn_right", "pickup", "repeat_n", "repeat_until_goal", "if", "if_else", "obstacle_ahead", "energy_on_tile"],
                "four_step_guide": {
                    "step1_concrete": "在自動導航迷宮的同時，還要偵測「如果腳下有能源晶片 → 撿取能源」！",
                    "step2_visual": "結合兩個獨立的條件判斷：① 檢查腳下能源；② 檢查前方障礙物。",
                    "step3_logic": "思考兩個判斷的順序：每走一步後，先檢查腳下有沒有能源，再決定下一步要前進還是轉彎。",
                    "step4_code": "多個 if 判斷並排時，電腦會依序檢查每一個條件。"
                },
                "hints": [
                    "提示一（注意觀察）：路線跟標準版一樣，但途中 (3, 1) 與 (4, 3) 多了兩顆必收的能源晶片！",
                    "提示二（概念提醒）：在迴圈中加入「如果 (腳下有能源) { 撿取能源 }」，再接原本的障礙物判斷。",
                    "提示三（局部示範）：持續執行直到終點 { 如果 (腳下有能源) { 撿取能源 }; 如果 (前方有障礙物) { 向右轉 } 否則 { 前進一步 } }。"
                ],
                "example_ast": [],
                "reflection_question": {
                    "question": "為什麼「檢查腳下是否有能源」要用獨立的「如果」，而不是放進障礙物判斷的「否則」之後？",
                    "options": ["因為站在轉角格時可能同時腳下有能源且前方有障礙物，兩個條件都需要被檢查", "因為積木顏色不同", "沒有原因"]
                }
            }
        }
    },

    # ==================== 第四章：資源管理中心 (Stage 4: 變數) ====================
    {
        "level_code": "ch4_lv1",
        "chapter_id": 4,
        "chapter_name": "第四章：資源管理中心",
        "level_order": 9,
        "level_name": "4-1 能源計數器：變數與比較判斷",
        "description": "中央能源閘門需要累積足夠的能源數值才能解鎖！觀察右上角即時變化的「energy（能源）」變數，當 energy >= 指定數值時開啟閘門。",
        "difficulty": "guided",
        "learning_objective": "理解變數（Variables）是用來記錄與更新狀態（如能源數量）的容器，並學會使用比較運算（>=）作為條件。",
        "concept_code": "variables",
        "editor_mode": "blockly",
        "variants": {
            "guided": {
                "zone": "zone_eco",
                "width": 8,
                "height": 6,
                "start": {"x": 1, "y": 3, "dir": 0},
                "goal": {"x": 6, "y": 3},
                "obstacles": [{"x": 5, "y": 2}, {"x": 5, "y": 4}],
                "items": [
                    {"x": 2, "y": 3, "type": "energy", "value": 1},
                    {"x": 3, "y": 3, "type": "energy", "value": 1},
                    {"x": 4, "y": 3, "type": "energy", "value": 1}
                ],
                "switches": [],
                "doors": [{"x": 5, "y": 3, "id": "door_main", "open": False, "requires_energy": 3}],
                "devices": [],
                "floor_arrows": [{"x": 1, "y": 3, "dir": 0}, {"x": 2, "y": 3, "dir": 0}, {"x": 3, "y": 3, "dir": 0}, {"x": 4, "y": 3, "dir": 0}],
                "required_energy": 3,
                "allowed_blocks": ["move_forward", "turn_left", "turn_right", "pickup", "open_door", "repeat_n", "if", "var_compare", "var_set", "var_change"],
                "four_step_guide": {
                    "step1_concrete": "每撿取一顆能源，變數 `energy` 就會 +1。當 `energy >= 3` 時執行「開啟閘門」！",
                    "step2_visual": "注意畫面頂部狀態列的「能源變數 energy：0 / 3」會隨著每次撿取即時跳動更新。",
                    "step3_logic": "變數就像一個貼著標籤的計分盒，隨時記住目前累積了多少能源。",
                    "step4_code": "在 Python 中，`energy = energy + 1` 與 `if energy >= 3: open_door()` 就是變數的經典用法。"
                },
                "hints": [
                    "提示一（注意觀察）：(2,3)、(3,3)、(4,3) 有三顆能源，(5,3) 是需要 3 顆能源的閘門，(6,3) 是終點。",
                    "提示二（概念提醒）：先用「重複 3 次 { 前進一步, 撿取能源 }」收集 3 顆能源，接著「如果 (energy >= 3) { 開啟閘門 }」，最後前進 2 次到 (6, 3)。",
                    "提示三（局部示範）：重複 3 次 { 前進, 撿取 } → 如果 (energy >= 3) { 開啟閘門 } → 前進 → 前進。"
                ],
                "example_ast": [
                    {
                        "type": "repeat_n",
                        "count": 3,
                        "body": [{"type": "move_forward"}, {"type": "pickup"}]
                    },
                    {
                        "type": "if",
                        "condition": {"type": "var_compare", "var": "energy", "op": ">=", "value": 3},
                        "then_body": [{"type": "open_door"}]
                    },
                    {"type": "move_forward"},
                    {"type": "move_forward"}
                ],
                "reflection_question": {
                    "question": "程式中的「變數 energy」扮演什麼角色？",
                    "options": ["用來儲存並隨時更新目前收集到的能源數量", "用來改變地圖背景顏色", "這是一個固定的常數不能改變"]
                }
            },
            "core": {
                "zone": "zone_eco",
                "width": 8,
                "height": 6,
                "start": {"x": 1, "y": 2, "dir": 0},
                "goal": {"x": 5, "y": 4},
                "obstacles": [
                    {"x": 6, "y": 2},
                    {"x": 2, "y": 3},
                    {"x": 3, "y": 3},
                    {"x": 4, "y": 3},
                    {"x": 6, "y": 3}
                ],
                "items": [
                    {"x": 2, "y": 2, "type": "energy", "value": 1},
                    {"x": 3, "y": 2, "type": "energy", "value": 1},
                    {"x": 4, "y": 2, "type": "energy", "value": 1},
                    {"x": 5, "y": 2, "type": "energy", "value": 1}
                ],
                "switches": [],
                "doors": [{"x": 5, "y": 3, "id": "door_main", "open": False, "requires_energy": 4}],
                "devices": [],
                "floor_arrows": [],
                "required_energy": 4,
                "allowed_blocks": ["move_forward", "turn_left", "turn_right", "pickup", "open_door", "repeat_n", "if", "var_compare", "var_set", "var_change"],
                "four_step_guide": {
                    "step1_concrete": "沿著北側長廊收集 4 顆能源晶片，在 (5, 2) 向右轉面對南側閘門 (5, 3)，並用 `energy >= 4` 判斷開門！",
                    "step2_visual": "觀察每次撿取時狀態面板的數值變化，確認轉彎面向閘門時 `energy` 已達到 4。",
                    "step3_logic": "注意：開啟閘門指令必須在機器人「面向閘門 (5, 3)」時執行，因此要先「向右轉」再判斷開門！",
                    "step4_code": "練習結合迴圈、轉向與變數比較條件。"
                },
                "hints": [
                    "提示一（注意觀察）：(2,2)~(5,2) 有 4 顆能源，強化閘門在 (5,2) 正下方的 (5,3)，終點在 (5,4)。",
                    "提示二（概念提醒）：重複 4 次 { 前進, 撿取 } → 向右轉 → 如果 (energy >= 4) { 開啟閘門 } → 前進 2 次。",
                    "提示三（局部示範）：別忘了在 (5, 2) 先「向右轉」面向 (5, 3) 閘門，再開門並前進 2 格到 (5, 4) 喔！"
                ],
                "example_ast": [],
                "reflection_question": {
                    "question": "當 energy 的值是 4 時，條件「energy >= 4」成立嗎？",
                    "options": ["成立，因為 >= 代表「大於或等於」", "不成立，一定要 5 以上才成立", "電腦無法比較"]
                }
            },
            "challenge": {
                "zone": "zone_eco",
                "width": 8,
                "height": 7,
                "start": {"x": 1, "y": 2, "dir": 0},
                "goal": {"x": 6, "y": 5},
                "obstacles": [{"x": 5, "y": 4}, {"x": 5, "y": 6}],
                "items": [
                    {"x": 2, "y": 2, "type": "energy", "value": 1},
                    {"x": 3, "y": 2, "type": "energy", "value": 1},
                    {"x": 4, "y": 2, "type": "energy", "value": 1},
                    {"x": 4, "y": 4, "type": "energy", "value": 1}
                ],
                "switches": [],
                "doors": [{"x": 5, "y": 5, "id": "door_main", "open": False, "requires_energy": 4}],
                "devices": [],
                "floor_arrows": [],
                "required_energy": 4,
                "allowed_blocks": ["move_forward", "turn_left", "turn_right", "pickup", "open_door", "repeat_n", "if", "var_compare", "var_set", "var_change"],
                "four_step_guide": {
                    "step1_concrete": "橫向收集 3 顆能源後，南下收集第 4 顆能源，並在 (4, 5) 轉向東邊判斷 `energy >= 4` 開門過關！",
                    "step2_visual": "追蹤變數在不同路段累積的過程。",
                    "step3_logic": "結合迴圈、轉彎、條件比較與開門動作。",
                    "step4_code": "檢查你的 Python 程式碼預覽，結構是否清晰易讀？"
                },
                "hints": [
                    "提示一（注意觀察）：前三顆能源在 (2,2)~(4,2)，第四顆在 (4,4)，閘門在 (5,5)，終點在 (6,5)。",
                    "提示二（概念提醒）：重複 3 次 { 前進, 撿取 } → 右轉 → 前進 2 次 → 撿取 → 前進 1 次 → 左轉 → 如果(energy>=4) 開門 → 前進 2 次。",
                    "提示三（局部示範）：確認在站在 (4, 5) 面向右方 (5, 5) 閘門時執行「開啟閘門」！"
                ],
                "example_ast": [],
                "reflection_question": {
                    "question": "在遊戲或日常軟體中，還有哪些東西也適合用「變數」來記錄？",
                    "options": ["經驗值、鑰匙數量、電力值、完成關卡數等會變動的狀態", "完全固定不變的網站標題圖片", "以上皆非"]
                }
            }
        }
    },

    # ==================== 第五章：雙人控制實驗室 (Stage 5: 邏輯運算與 1~4 人合作) ====================
    {
        "level_code": "ch5_lv1",
        "chapter_id": 5,
        "chapter_name": "第五章：雙人控制實驗室",
        "level_order": 10,
        "level_name": "5-1 雙重安全鎖：AND / OR 邏輯與協同排程",
        "description": "雙人控制實驗室的中央閘門需要多重條件同時成立（邏輯 AND）才能開啟！支援 2～4 人分工規劃，單人遊玩時也可透過「脈衝鎖定／依序啟動開關」完成等價邏輯挑戰！",
        "difficulty": "core",
        "learning_objective": "理解布林邏輯運算（AND、OR、NOT），學會組合多重條件判斷（例如：已收集足夠能源 AND 所有開關皆已啟動）。",
        "concept_code": "logic",
        "editor_mode": "blockly",
        "variants": {
            "guided": {
                "zone": "zone_control",
                "width": 8,
                "height": 6,
                "start": {"x": 1, "y": 3, "dir": 0},
                "goal": {"x": 6, "y": 3},
                "obstacles": [{"x": 5, "y": 2}, {"x": 5, "y": 4}],
                "items": [{"x": 2, "y": 3, "type": "energy", "value": 1}],
                "switches": [
                    {"x": 3, "y": 3, "id": "sw_a"},
                    {"x": 4, "y": 3, "id": "sw_b"}
                ],
                "doors": [{"x": 5, "y": 3, "id": "door_logic", "open": False, "requires_energy": 1, "requires_switches": True}],
                "devices": [],
                "floor_arrows": [{"x": 1, "y": 3, "dir": 0}, {"x": 2, "y": 3, "dir": 0}, {"x": 3, "y": 3, "dir": 0}, {"x": 4, "y": 3, "dir": 0}],
                "required_energy": 1,
                "require_all_switches": True,
                "allowed_blocks": ["move_forward", "turn_left", "turn_right", "pickup", "activate_switch", "open_door", "repeat_n", "if", "logic_and", "logic_or", "logic_not", "has_energy", "all_switches_active"],
                "four_step_guide": {
                    "step1_concrete": "依序撿取 (2,3) 能源、啟動 (3,3) 左開關與 (4,3) 右開關，再用 `持有能源 AND 所有開關已啟動` 判斷開門！",
                    "step2_visual": "單人模式中，啟動開關會啟動暫存脈衝鎖定，讓你一人也能依序啟動 A、B 兩側開關！多人模式中可由隊友共同分析與組裝。",
                    "step3_logic": "AND（且）代表左右兩個條件都必須為真（True），整體條件才會成立。",
                    "step4_code": "對應 Python 的 `if has_energy() and all_switches_active(): open_door()`。"
                },
                "hints": [
                    "提示一（注意觀察）：(2,3) 是能源，(3,3) 和 (4,3) 是兩個控制開關，(5,3) 是雙重安全門。",
                    "提示二（概念提醒）：前進 → 撿取能源 → 前進 → 啟動開關 → 前進 → 啟動開關 → 如果 (持有能源 AND 所有開關已啟動) { 開啟閘門 } → 前進 2 次。",
                    "提示三（局部示範）：在「如果」積木中放入「且 (AND)」邏輯積木，左邊放「持有能源」，右邊放「所有開關已啟動」。"
                ],
                "example_ast": [
                    {"type": "move_forward"},
                    {"type": "pickup"},
                    {"type": "move_forward"},
                    {"type": "activate_switch"},
                    {"type": "move_forward"},
                    {"type": "activate_switch"},
                    {
                        "type": "if",
                        "condition": {
                            "type": "logic_and",
                            "left": {"type": "has_energy"},
                            "right": {"type": "all_switches_active"}
                        },
                        "then_body": [{"type": "open_door"}]
                    },
                    {"type": "move_forward"},
                    {"type": "move_forward"}
                ],
                "reflection_question": {
                    "question": "在「條件 A AND（且）條件 B」中，如果只收集了能源但沒有啟動開關，條件會成立嗎？",
                    "options": ["不會成立，AND 需要兩個條件同時滿足才會成立", "會成立，只要其中一個滿足就好", "看運氣"]
                }
            },
            "core": {
                "zone": "zone_control",
                "width": 8,
                "height": 7,
                "start": {"x": 1, "y": 3, "dir": 0},
                "goal": {"x": 6, "y": 3},
                "obstacles": [{"x": 5, "y": 2}, {"x": 5, "y": 4}],
                "items": [{"x": 2, "y": 3, "type": "energy", "value": 1}],
                "switches": [
                    {"x": 3, "y": 2, "id": "sw_top"},
                    {"x": 3, "y": 4, "id": "sw_bottom"}
                ],
                "doors": [{"x": 5, "y": 3, "id": "door_logic", "open": False, "requires_energy": 1, "requires_switches": True}],
                "devices": [],
                "floor_arrows": [],
                "required_energy": 1,
                "require_all_switches": True,
                "allowed_blocks": ["move_forward", "turn_left", "turn_right", "pickup", "activate_switch", "open_door", "repeat_n", "if", "logic_and", "logic_or", "logic_not", "has_energy", "all_switches_active"],
                "four_step_guide": {
                    "step1_concrete": "兩個開關分別在通道上方 (3, 2) 與下方 (3, 4)！規劃路線啟動兩側開關後前往 (5, 3) 閘門。",
                    "step2_visual": "單人時機器人可先北上啟動 (3,2) 開關（啟動脈衝保持），再南下啟動 (3,4) 開關！多人時可與隊友輪流規劃。",
                    "step3_logic": "當 `持有能源 AND 所有開關已啟動` 時，中央閘門即可開啟。",
                    "step4_code": "驗證複合邏輯條件在分支路線上的應用。"
                },
                "hints": [
                    "提示一（注意觀察）：在 (2,3) 撿取能源並前進到 (3,3) 後，上方 (3,2) 與下方 (3,4) 各有一個開關。",
                    "提示二（概念提醒）：在 (3,3) 左轉走 1 格到 (3,2) 啟動上開關 → 左轉兩次(向南)走 2 格到 (3,4) 啟動下開關 → 左轉走 1 格右轉回 (4,3)。",
                    "提示三（局部示範）：抵達 (4, 3) 面向閘門時，使用「如果 (持有能源 AND 所有開關已啟動) { 開啟閘門 }」，再前進 2 格到 (6, 3)。"
                ],
                "example_ast": [],
                "reflection_question": {
                    "question": "「AND（且）」與「OR（或）」最大的差別是什麼？",
                    "options": ["AND 需要兩邊都成立；OR 只要其中一邊成立就成立", "AND 比較快，OR 比較慢", "兩者完全相同"]
                }
            },
            "challenge": {
                "zone": "zone_control",
                "width": 8,
                "height": 7,
                "start": {"x": 1, "y": 3, "dir": 0},
                "goal": {"x": 6, "y": 3},
                "obstacles": [{"x": 5, "y": 2}, {"x": 5, "y": 4}],
                "items": [
                    {"x": 2, "y": 3, "type": "energy", "value": 1},
                    {"x": 4, "y": 3, "type": "energy", "value": 1}
                ],
                "switches": [
                    {"x": 3, "y": 2, "id": "sw_top"},
                    {"x": 3, "y": 4, "id": "sw_bottom"}
                ],
                "doors": [{"x": 5, "y": 3, "id": "door_logic", "open": False, "requires_energy": 2, "requires_switches": True}],
                "devices": [],
                "floor_arrows": [],
                "required_energy": 2,
                "require_all_switches": True,
                "allowed_blocks": ["move_forward", "turn_left", "turn_right", "pickup", "activate_switch", "open_door", "repeat_n", "if", "logic_and", "logic_or", "logic_not", "has_energy", "all_switches_active", "var_compare"],
                "four_step_guide": {
                    "step1_concrete": "同時滿足三個條件：收集 2 顆能源、啟動北側開關、啟動南側開關！",
                    "step2_visual": "比較先走北側還是先走南側路徑，兩者都是正確的替代路線。",
                    "step3_logic": "使用 `(energy >= 2) AND (所有開關已啟動)` 驗證複合邏輯。",
                    "step4_code": "挑戰完成後，你已掌握複合布林邏輯判斷！"
                },
                "hints": [
                    "提示一（注意觀察）：除了上下兩個開關，(2,3) 與 (4,3) 各有一顆能源晶片。",
                    "提示二（概念提醒）：回到 (4, 3) 時記得撿取第二顆能源，再判斷條件開啟 (5, 3) 閘門。",
                    "提示三（局部示範）：如果 ((energy >= 2) AND 所有開關已啟動) { 開啟閘門 } → 前進 2 次。"
                ],
                "example_ast": [],
                "reflection_question": {
                    "question": "「NOT（非）前方有障礙物」代表什麼意思？",
                    "options": ["代表前方「沒有」障礙物（道路暢通）", "代表前方有兩個障礙物", "代表機器人不能動"]
                }
            }
        }
    },

    # ==================== 第六章：自動化工廠 (Stage 6: 函式與程式碼) ====================
    {
        "level_code": "ch6_lv1",
        "chapter_id": 6,
        "chapter_name": "第六章：自動化工廠",
        "level_order": 11,
        "level_name": "6-1 模組化採集程序：建立與呼叫自訂函式",
        "description": "在自動化工廠中，我們可以把常用的一組動作打包成一個「自訂函式（Function）」！定義好之後，只要呼叫函式名稱就能重複使用。",
        "difficulty": "guided",
        "learning_objective": "理解函式定義（def）與函式呼叫（call）的概念，學會將重複的子任務模組化並對照 Python 程式碼。",
        "concept_code": "functions",
        "editor_mode": "blockly",
        "variants": {
            "guided": {
                "zone": "zone_ai",
                "width": 7,
                "height": 6,
                "start": {"x": 1, "y": 3, "dir": 0},
                "goal": {"x": 4, "y": 3},
                "obstacles": [],
                "items": [
                    {"x": 2, "y": 3, "type": "energy", "value": 1},
                    {"x": 3, "y": 3, "type": "energy", "value": 1},
                    {"x": 4, "y": 3, "type": "energy", "value": 1}
                ],
                "switches": [],
                "doors": [],
                "devices": [],
                "floor_arrows": [{"x": 1, "y": 3, "dir": 0}, {"x": 2, "y": 3, "dir": 0}, {"x": 3, "y": 3, "dir": 0}],
                "required_energy": 3,
                "allowed_blocks": ["move_forward", "turn_left", "turn_right", "pickup", "repeat_n", "func_def", "func_call"],
                "four_step_guide": {
                    "step1_concrete": "先用「建立函式 collect_step」把「前進一步＋撿取能源」包起來，再連續呼叫 3 次「呼叫函式 collect_step」！",
                    "step2_visual": "注意只「建立函式」是不會自己執行的，必須在主程式中放「呼叫函式」積木才會動作喔！",
                    "step3_logic": "函式就像替一整組動作取一個新名字，讓主程式變得超乾淨。",
                    "step4_code": "觀察右側 Python 預覽：`def collect_step():` 就是標準的 Python 函式定義！"
                },
                "hints": [
                    "提示一（注意觀察）：我們需要執行 3 次「前進一步＋撿取能源」。",
                    "提示二（概念提醒）：先放一個「建立函式 collect_step { 前進一步, 撿取能源 }」，再放 3 個「呼叫函式 collect_step」。",
                    "提示三（局部示範）：也可以把「呼叫函式 collect_step」放進「重複 3 次」迴圈裡！"
                ],
                "example_ast": [
                    {
                        "type": "func_def",
                        "name": "collect_step",
                        "body": [{"type": "move_forward"}, {"type": "pickup"}]
                    },
                    {"type": "func_call", "name": "collect_step"},
                    {"type": "func_call", "name": "collect_step"},
                    {"type": "func_call", "name": "collect_step"}
                ],
                "reflection_question": {
                    "question": "如果只在工作區放了「建立函式 collect_step」，卻沒有放「呼叫函式 collect_step」，機器人會動嗎？",
                    "options": ["不會動，因為建立函式只是教會機器人這個技能，必須「呼叫」它才會執行", "會自動執行 10 次", "會報錯當機"]
                }
            },
            "core": {
                "zone": "zone_ai",
                "width": 7,
                "height": 7,
                "start": {"x": 1, "y": 2, "dir": 0},
                "goal": {"x": 3, "y": 4},
                "obstacles": [{"x": 2, "y": 3}, {"x": 2, "y": 4}],
                "items": [
                    {"x": 2, "y": 2, "type": "energy", "value": 1},
                    {"x": 3, "y": 2, "type": "energy", "value": 1},
                    {"x": 3, "y": 3, "type": "energy", "value": 1},
                    {"x": 3, "y": 4, "type": "energy", "value": 1}
                ],
                "switches": [],
                "doors": [],
                "devices": [],
                "floor_arrows": [],
                "required_energy": 4,
                "allowed_blocks": ["move_forward", "turn_left", "turn_right", "pickup", "repeat_n", "func_def", "func_call"],
                "four_step_guide": {
                    "step1_concrete": "建立一個函式負責「往前收集 2 顆能源」，在轉彎前後各呼叫一次！",
                    "step2_visual": "第一段 (1,2)→(3,2) 與第二段 (3,2)→(3,4) 都是「前進＋撿取」重複 2 次。",
                    "step3_logic": "主程式只要寫：呼叫函式 → 向右轉 → 呼叫函式，一秒看懂整體流程！",
                    "step4_code": "對照 Python 的 `def collect_step():` 與兩次 `collect_step()` 呼叫。"
                },
                "hints": [
                    "提示一（注意觀察）：橫向有 2 顆能源，右轉後縱向也有 2 顆能源。",
                    "提示二（概念提醒）：在「建立函式 collect_step」裡面放「重複 2 次 { 前進, 撿取 }」。",
                    "提示三（局部示範）：主程式：呼叫 collect_step → 向右轉 → 呼叫 collect_step。"
                ],
                "example_ast": [],
                "reflection_question": {
                    "question": "把長程式拆成有意義的「函式」有什麼好處？",
                    "options": ["可以重複呼叫使用，而且主程式更容易閱讀與除錯", "沒有任何好處", "只為了讓程式跑比較慢"]
                }
            },
            "challenge": {
                "zone": "zone_ai",
                "width": 8,
                "height": 7,
                "start": {"x": 1, "y": 2, "dir": 0},
                "goal": {"x": 5, "y": 5},
                "obstacles": [{"x": 2, "y": 3}, {"x": 4, "y": 3}],
                "items": [
                    {"x": 2, "y": 2, "type": "energy", "value": 1},
                    {"x": 3, "y": 2, "type": "energy", "value": 1},
                    {"x": 3, "y": 4, "type": "energy", "value": 1},
                    {"x": 4, "y": 4, "type": "energy", "value": 1}
                ],
                "switches": [],
                "doors": [],
                "devices": [{"x": 5, "y": 4, "id": "dev_ai", "requires_energy": 4}],
                "floor_arrows": [],
                "required_energy": 4,
                "require_all_devices": True,
                "allowed_blocks": ["move_forward", "turn_left", "turn_right", "pickup", "repair_device", "repeat_n", "func_def", "func_call"],
                "four_step_guide": {
                    "step1_concrete": "運用自訂函式完成兩段能源採集，並在 (5, 4) 修復 AI 設備後前往 (5, 5) 終點！",
                    "step2_visual": "觀察函式與迴圈結合後的簡潔結構。",
                    "step3_logic": "檢視主程式是否能清楚表達「採集第一段 → 轉移陣地 → 採集第二段 → 修復設備 → 抵達終點」。",
                    "step4_code": "你已經具備模組化程式設計的核心思維了！"
                },
                "hints": [
                    "提示一（注意觀察）：(2,2)、(3,2) 是第一段能源；從 (3,2) 南下 2 格到 (3,4)，收集 (3,4) 與 (4,4) 後到 (5,4) 修復設備。",
                    "提示二（概念提醒）：定義函式 `collect_step` 為 `{ 前進, 撿取 }`，即可在各路段重複呼叫。",
                    "提示三（局部示範）：收集滿 4 顆能源後，在 (5, 4) 執行「修復設備」，再右轉前進 1 格到 (5, 5)。"
                ],
                "example_ast": [],
                "reflection_question": {
                    "question": "在 Python 程式碼中，定義函式使用的是哪一個關鍵字？",
                    "options": ["def", "for", "if"]
                }
            }
        }
    },

    # ==================== 最終章：NOVA 核心 (Final Chapter: 綜合任務) ====================
    {
        "level_code": "ch7_lv1",
        "chapter_id": 7,
        "chapter_name": "最終章：NOVA 核心",
        "level_order": 12,
        "level_name": "7-1 最終任務：重啟 NOVA 能源核心",
        "description": "我們抵達了 NOVA 基地的最深處——最終能源核心！請整合你學過的指令順序、迴圈、條件判斷、變數、邏輯運算與函式，收集能源、啟動核心開關、開啟安全閘門並修復主反應爐！本關具有多種可行解法。",
        "difficulty": "challenge",
        "learning_objective": "綜合應用所有已學程式概念，自主規劃、測試與除錯，完成具有多種解法的開放式基地修復任務。",
        "concept_code": "integration",
        "editor_mode": "blockly",
        "variants": {
            "guided": {
                "zone": "zone_core",
                "width": 9,
                "height": 6,
                "start": {"x": 1, "y": 3, "dir": 0},
                "goal": {"x": 7, "y": 3},
                "obstacles": [{"x": 5, "y": 2}, {"x": 5, "y": 4}],
                "items": [
                    {"x": 2, "y": 3, "type": "energy", "value": 1},
                    {"x": 3, "y": 3, "type": "energy", "value": 1}
                ],
                "switches": [{"x": 4, "y": 3, "id": "sw_core"}],
                "doors": [{"x": 5, "y": 3, "id": "door_core", "open": False, "requires_energy": 2, "requires_switches": True}],
                "devices": [{"x": 6, "y": 3, "id": "reactor_core", "requires_energy": 2}],
                "floor_arrows": [{"x": 1, "y": 3, "dir": 0}, {"x": 2, "y": 3, "dir": 0}, {"x": 3, "y": 3, "dir": 0}, {"x": 4, "y": 3, "dir": 0}],
                "required_energy": 2,
                "require_all_switches": True,
                "require_all_devices": True,
                "allowed_blocks": [
                    "move_forward", "turn_left", "turn_right", "pickup", "activate_switch",
                    "open_door", "repair_device", "repeat_n", "repeat_until_goal",
                    "if", "if_else", "obstacle_ahead", "energy_on_tile", "has_energy",
                    "all_switches_active", "var_compare", "logic_and", "logic_or",
                    "func_def", "func_call"
                ],
                "four_step_guide": {
                    "step1_concrete": "分段完成：① 用迴圈收集 2 顆能源 → ② 啟動 (4,3) 開關 → ③ 判斷條件開啟 (5,3) 閘門 → ④ 在 (6,3) 修復核心反應爐 → ⑤ 抵達 (7,3)！",
                    "step2_visual": "你可以自由選擇使用迴圈、條件判斷或自訂函式來組合你的解答。",
                    "step3_logic": "只要能達成所有任務目標，任何合理的程式結構都能成功通關！",
                    "step4_code": "檢視你親手完成的完整 Python 修復程式！"
                },
                "hints": [
                    "提示一（注意觀察）：從左到右依序是：2 顆能源 (2,3)(3,3) → 開關 (4,3) → 閘門 (5,3) → 核心設備 (6,3) → 終點 (7,3)。",
                    "提示二（概念提醒）：重複 2 次 { 前進, 撿取 } → 前進 → 啟動開關 → 開啟閘門 → 前進 → 修復設備 → 前進。",
                    "提示三（局部示範）：別忘了在 (6, 3) 執行「修復設備」後，再前進一步抵達 (7, 3) 終點！"
                ],
                "example_ast": [
                    {
                        "type": "repeat_n",
                        "count": 2,
                        "body": [{"type": "move_forward"}, {"type": "pickup"}]
                    },
                    {"type": "move_forward"},
                    {"type": "activate_switch"},
                    {
                        "type": "if",
                        "condition": {
                            "type": "logic_and",
                            "left": {"type": "var_compare", "var": "energy", "op": ">=", "value": 2},
                            "right": {"type": "all_switches_active"}
                        },
                        "then_body": [{"type": "open_door"}]
                    },
                    {"type": "move_forward"},
                    {"type": "move_forward"},
                    {"type": "repair_device"},
                    {"type": "move_forward"}
                ],
                "reflection_question": {
                    "question": "回顧從第一章到最終章的旅程，你覺得「寫程式」最核心的精神是什麼？",
                    "options": ["將問題拆解成清楚的邏輯步驟，讓電腦協助我們解決問題", "死背越多英文單字越好", "只能有一種標準答案"]
                }
            },
            "core": {
                "zone": "zone_core",
                "width": 9,
                "height": 7,
                "start": {"x": 1, "y": 2, "dir": 0},
                "goal": {"x": 7, "y": 4},
                "obstacles": [{"x": 5, "y": 2}, {"x": 5, "y": 3}, {"x": 5, "y": 5}],
                "items": [
                    {"x": 2, "y": 2, "type": "energy", "value": 1},
                    {"x": 3, "y": 2, "type": "energy", "value": 1},
                    {"x": 4, "y": 2, "type": "energy", "value": 1}
                ],
                "switches": [{"x": 4, "y": 4, "id": "sw_core"}],
                "doors": [{"x": 5, "y": 4, "id": "door_core", "open": False, "requires_energy": 3, "requires_switches": True}],
                "devices": [{"x": 6, "y": 4, "id": "reactor_core", "requires_energy": 3}],
                "floor_arrows": [],
                "required_energy": 3,
                "require_all_switches": True,
                "require_all_devices": True,
                "allowed_blocks": [
                    "move_forward", "turn_left", "turn_right", "pickup", "activate_switch",
                    "open_door", "repair_device", "repeat_n", "repeat_until_goal",
                    "if", "if_else", "obstacle_ahead", "energy_on_tile", "has_energy",
                    "all_switches_active", "var_compare", "logic_and", "logic_or",
                    "func_def", "func_call"
                ],
                "four_step_guide": {
                    "step1_concrete": "沿北側收集 3 顆能源 → 南下至 (4,4) 啟動開關並開啟 (5,4) 閘門 → 修復 (6,4) 核心 → 抵達 (7,4)！",
                    "step2_visual": "可用迴圈或自訂函式處理連續採集。",
                    "step3_logic": "檢查每個關鍵節點的狀態條件。",
                    "step4_code": "自由發揮你的程式設計技巧！"
                },
                "hints": [
                    "提示一（注意觀察）：(2,2)~(4,2) 有 3 顆能源，從 (4,2) 右轉往下走 2 格就是 (4,4) 的控制開關！",
                    "提示二（概念提醒）：在 (4,4) 啟動開關並左轉面向東邊 (5,4) 閘門，開啟閘門後前進 2 格到 (6,4) 修復核心，再前進 1 格到 (7,4)。",
                    "提示三（局部示範）：重複3次{前進,撿取} → 右轉 → 前進2次 → 啟動開關 → 左轉 → 開門 → 前進2次 → 修復設備 → 前進1次。"
                ],
                "example_ast": [],
                "reflection_question": {
                    "question": "在團隊合作修復 NOVA 核心時，當隊友的程式出現小錯誤，最好的做法是什麼？",
                    "options": ["一起觀察機器人停在哪個步驟，討論如何調整指令", "直接責怪隊友", "放棄不玩"]
                }
            },
            "challenge": {
                "zone": "zone_core",
                "width": 9,
                "height": 7,
                "start": {"x": 1, "y": 3, "dir": 0},
                "goal": {"x": 7, "y": 3},
                "obstacles": [{"x": 3, "y": 3}, {"x": 5, "y": 2}, {"x": 5, "y": 4}],
                "items": [
                    {"x": 2, "y": 1, "type": "energy", "value": 1},
                    {"x": 3, "y": 1, "type": "energy", "value": 1},
                    {"x": 2, "y": 5, "type": "energy", "value": 1},
                    {"x": 3, "y": 5, "type": "energy", "value": 1}
                ],
                "switches": [{"x": 4, "y": 3, "id": "sw_core"}],
                "doors": [{"x": 5, "y": 3, "id": "door_core", "open": False, "requires_energy": 2, "requires_switches": True}],
                "devices": [{"x": 6, "y": 3, "id": "reactor_core", "requires_energy": 2}],
                "floor_arrows": [],
                "required_energy": 2,
                "require_all_switches": True,
                "require_all_devices": True,
                "allowed_blocks": [
                    "move_forward", "turn_left", "turn_right", "pickup", "activate_switch",
                    "open_door", "repair_device", "repeat_n", "repeat_until_goal",
                    "if", "if_else", "obstacle_ahead", "energy_on_tile", "has_energy",
                    "all_switches_active", "var_compare", "logic_and", "logic_or",
                    "func_def", "func_call"
                ],
                "four_step_guide": {
                    "step1_concrete": "開放式多路徑挑戰！北側路線 (y=1) 與南側路線 (y=5) 各有 2 顆能源，任選一條（或兩條都收集）皆可滿足核心需求的 2 顆能源！",
                    "step2_visual": "和同學或隊友比較看看：誰走北側路線？誰走南側路線？誰使用了函式或迴圈？",
                    "step3_logic": "驗證「同一任務目標可以有多種不同演算法與路線解法」。",
                    "step4_code": "恭喜你完成 NOVA Protocol 全部挑戰，成功恢復整座基地運作！"
                },
                "hints": [
                    "提示一（注意觀察）：核心閘門與反應爐只需要 2 顆能源，你可以選擇走上方 (y=1) 收集 2 顆，或走下方 (y=5) 收集 2 顆！",
                    "提示二（概念提醒）：從 (1,3) 前進到 (2,3) 後，左轉走 2 格可到 (2,1) 北路線，右轉走 2 格可到 (2,5) 南路線。",
                    "提示三（局部示範）：收集完 2 顆能源後回到 (4, 3) 啟動開關並開啟 (5, 3) 閘門，接著到 (6, 3) 修復設備並走到 (7, 3)！"
                ],
                "example_ast": [],
                "reflection_question": {
                    "question": "在這個最終挑戰中，走北側路線或南側路線都能成功重啟核心，這說明了什麼？",
                    "options": ["程式設計沒有唯一死板的標準答案，能正確達成目標且邏輯清楚就是好程式", "只有北側路線才算對", "只有南側路線才算對"]
                }
            }
        }
    }
]


def seed_database(db: Session):
    # 1. Seed Achievements
    existing_ach = {a.achievement_code: a for a in db.query(Achievement).all()}
    for ach_data in ACHIEVEMENTS_SEED:
        if ach_data["achievement_code"] not in existing_ach:
            db.add(Achievement(**ach_data))
    db.commit()

    # 2. Seed Levels & LevelVariants
    existing_levels = {lv.level_code: lv for lv in db.query(Level).all()}
    for lv_seed in LEVELS_SEED:
        variants_map = lv_seed["variants"]
        default_data = variants_map.get("core") or variants_map.get("guided")
        lv_obj = existing_levels.get(lv_seed["level_code"])
        if not lv_obj:
            lv_obj = Level(
                level_code=lv_seed["level_code"],
                chapter_id=lv_seed["chapter_id"],
                chapter_name=lv_seed["chapter_name"],
                level_order=lv_seed["level_order"],
                level_name=lv_seed["level_name"],
                description=lv_seed["description"],
                difficulty=lv_seed["difficulty"],
                learning_objective=lv_seed["learning_objective"],
                concept_code=lv_seed["concept_code"],
                editor_mode=lv_seed["editor_mode"],
                level_data=default_data,
            )
            db.add(lv_obj)
            db.flush()
        else:
            lv_obj.level_name = lv_seed["level_name"]
            lv_obj.description = lv_seed["description"]
            lv_obj.learning_objective = lv_seed["learning_objective"]
            lv_obj.editor_mode = lv_seed["editor_mode"]
            lv_obj.level_data = default_data
            flag_modified(lv_obj, "level_data")
            db.flush()

        existing_vars = {
            v.difficulty_tier: v
            for v in db.query(LevelVariant).filter(LevelVariant.level_id == lv_obj.id).all()
        }
        for tier_key, tier_data in variants_map.items():
            if tier_key not in existing_vars:
                db.add(
                    LevelVariant(
                        level_id=lv_obj.id,
                        difficulty_tier=tier_key,
                        level_data=tier_data,
                        is_active=True,
                    )
                )
            else:
                existing_vars[tier_key].level_data = tier_data
                flag_modified(existing_vars[tier_key], "level_data")

    # 3. Seed Default Teacher Account
    default_teacher = db.query(Teacher).filter(Teacher.auth_subject == "teacher_default").first()
    token_hash = hashlib.sha256(settings.TEACHER_DEMO_PASSKEY.encode("utf-8")).hexdigest()
    if not default_teacher:
        db.add(
            Teacher(
                auth_subject="teacher_default",
                display_name="NOVA 基地指導教師",
                token_hash=token_hash,
            )
        )
    else:
        default_teacher.token_hash = token_hash

    db.commit()

