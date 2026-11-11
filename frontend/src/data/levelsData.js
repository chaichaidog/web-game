export const ROBOT_SKINS = [
  {
    id: 'nova_scout',
    name: 'NOVA 藍白偵察型',
    primary: '#38bdf8',
    secondary: '#e0f2fe',
    eye: '#22d3ee',
    desc: '基地標準配發的全方位修復機器人，配備高感度光學鏡頭。',
  },
  {
    id: 'crimson_mech',
    name: '赤紅重裝工程型',
    primary: '#f43f5e',
    secondary: '#fecdd3',
    eye: '#fde047',
    desc: '專為能源研究區高溫環境設計的重裝修復機體。',
  },
  {
    id: 'emerald_guardian',
    name: '翡翠生態守護型',
    primary: '#10b981',
    secondary: '#d1fae5',
    eye: '#6ee7b7',
    desc: '負責生態實驗室與環境維持系統的特製機體。',
  },
  {
    id: 'quantum_gold',
    name: '量子黃金領航型',
    primary: '#f59e0b',
    secondary: '#fef3c7',
    eye: '#38bdf8',
    desc: '授予完成高階挑戰的王牌修復小隊榮譽塗裝。',
  },
];

export const HEAD_ACCESSORIES = [
  { id: 'antenna_basic', name: '標準通訊天線', icon: '📡' },
  { id: 'holo_visor', name: '全息雷達護目鏡', icon: '🥽' },
  { id: 'radar_dish', name: '深空掃描碟盤', icon: '🛰️' },
  { id: 'plasma_crown', name: '電漿核心光環', icon: '👑' },
];

export const BASE_DECORS = [
  { id: 'holo_plant', name: '全息生態盆栽', icon: '🌱', desc: '在控制室投影出充滿生機的太空植物。' },
  { id: 'energy_fountain', name: '微型能源噴泉', icon: '⛲', desc: '持續散發柔和藍光的超導能源柱。' },
  { id: 'mini_drone', name: '伴飛維修無人機', icon: '🛸', desc: '在基地大廳巡邏的可愛輔助小無人機。' },
  { id: 'core_trophy', name: 'NOVA 核心紀念碑', icon: '🏆', desc: '象徵成功重啟整座基地的最高榮譽結晶。' },
];

export const ZONE_THEMES = {
  zone_control: {
    name: 'NOVA 中央控制室',
    bg: '#0b132b',
    floorA: '#1c2541',
    floorB: '#16203a',
    wall: '#3a506b',
    accent: '#38bdf8',
  },
  zone_factory: {
    name: '機器人維修工廠',
    bg: '#141824',
    floorA: '#23293a',
    floorB: '#1d2231',
    wall: '#4f5d75',
    accent: '#f59e0b',
  },
  zone_energy: {
    name: '能源研究區',
    bg: '#091929',
    floorA: '#102a43',
    floorB: '#0d2238',
    wall: '#243b53',
    accent: '#22d3ee',
  },
  zone_maze: {
    name: '地下故障迷宮',
    bg: '#1a1423',
    floorA: '#2d233c',
    floorB: '#241b31',
    wall: '#5c4b7d',
    accent: '#c084fc',
  },
  zone_eco: {
    name: '資源與生態實驗室',
    bg: '#071f18',
    floorA: '#0f3328',
    floorB: '#0c2920',
    wall: '#205c48',
    accent: '#34d399',
  },
  zone_ai: {
    name: 'AI 自動化工廠',
    bg: '#1b112c',
    floorA: '#291b42',
    floorB: '#211536',
    wall: '#5a3d8a',
    accent: '#a855f7',
  },
  zone_core: {
    name: '最終能源核心',
    bg: '#190b1e',
    floorA: '#2d1436',
    floorB: '#220e2b',
    wall: '#702963',
    accent: '#f43f5e',
  },
};

export const BLOCK_CATALOG = {
  move_forward: {
    label: '⬆️ 前進一步',
    category: '移動類',
    color: '#0284c7',
    desc: '讓機器人往目前面向的方向前進 1 格。',
    demo: '機器人往前移動一格（若前方有牆壁或未開的門會發生碰撞）。',
  },
  move_backward: {
    label: '⬇️ 後退一步',
    category: '移動類',
    color: '#0284c7',
    desc: '讓機器人不改變面向、往後退 1 格。',
    demo: '機器人往背對方向退後一格。',
  },
  turn_left: {
    label: '↩️ 向左轉',
    category: '移動類',
    color: '#0284c7',
    desc: '讓機器人在原地逆時針左轉 90 度（不會移動格子）。',
    demo: '例如原本面向右方(東)，左轉後會變成面向構成上方(北)。',
  },
  turn_right: {
    label: '↪️ 向右轉',
    category: '移動類',
    color: '#0284c7',
    desc: '讓機器人在原地順時針右轉 90 度（不會移動格子）。',
    demo: '例如原本面向右方(東)，右轉後會變成面向下方(南)。',
  },
  pickup: {
    label: '⚡ 撿取能源',
    category: '互動類',
    color: '#d97706',
    desc: '撿取機器人目前腳下格子上的能源晶片，使 energy 變數 +1。',
    demo: '必須站在有藍色能源晶片的格子上執行才有效喔！',
  },
  activate_switch: {
    label: '🔘 啟動開關',
    category: '互動類',
    color: '#d97706',
    desc: '啟動機器人腳下的地板控制開關（單人時支援脈衝保持）。',
    demo: '啟動後開關會亮起青綠燈號。',
  },
  open_door: {
    label: '🚪 開啟閘門',
    category: '互動類',
    color: '#d97706',
    desc: '當能源或開關條件滿足時，開啟前方或相鄰的安全閘門。',
    demo: '開門後機器人才能穿過閘門所在的格子。',
  },
  repair_device: {
    label: '🔧 修復設備',
    category: '互動類',
    color: '#d97706',
    desc: '在受損發電機設備格上執行修復（需先收集足夠的能源晶片）。',
    demo: '修復成功後設備會發出金色運轉光芒！',
  },
  repeat_n: {
    label: '🔁 重複 N 次',
    category: '迴圈類',
    color: '#7c3aed',
    desc: '將包在裡面的指令重複執行指定的次數。',
    demo: '可避免重複排列大量相同的積木！',
  },
  repeat_until_goal: {
    label: '🔄 持續執行直到終點',
    category: '迴圈類',
    color: '#7c3aed',
    desc: '反覆執行內部的指令，直到機器人抵達綠色終點為止。',
    demo: '常搭配「如果前方有障礙物…」進行迷宮自動導航。',
  },
  if: {
    label: '❓ 如果 (if)',
    category: '條件類',
    color: '#059669',
    desc: '當條件成立時，才執行內部的動作。',
    demo: '例如：如果 (腳下有能源) 執行 { 撿取能源 }。',
  },
  if_else: {
    label: '⚖️ 如果…否則 (if/else)',
    category: '條件類',
    color: '#059669',
    desc: '條件成立時執行第一段動作，否則執行第二段動作。',
    demo: '例如：如果 (前方有障礙物) { 向右轉 } 否則 { 前進一步 }。',
  },
  var_compare: {
    label: '🔢 變數比較 (energy >= N)',
    category: '變數類',
    color: '#db2777',
    desc: '比較目前累積的能源數量是否達到指定門檻。',
    demo: '例如檢查 energy >= 3 是否成立。',
  },
  logic_and: {
    label: '🔗 且 (AND) / 或 (OR)',
    category: '邏輯類',
    color: '#4f46e5',
    desc: '組合兩個條件：AND 需兩者皆成立；OR 只需任一成立。',
    demo: '用於雙重安全鎖等多重條件判斷。',
  },
  func_def: {
    label: '📦 建立自訂函式',
    category: '函式類',
    color: '#e11d48',
    desc: '將一組常用動作命名打包成一個新技能（例如 collect_step）。',
    demo: '建立後記得使用「呼叫函式」積木來執行它！',
  },
  func_call: {
    label: '▶️ 呼叫自訂函式',
    category: '函式類',
    color: '#e11d48',
    desc: '執行先前建立好的自訂函式內容。',
    demo: '可重複呼叫多次，讓主程式簡潔好讀！',
  },
};

export const QUICK_MESSAGES_LIST = [
  { key: 'idea', label: '💡 我有一個想法！' },
  { key: 'try_again', label: '🔄 再試一次！' },
  { key: 'check_here', label: '🔍 這裡順序可能有問題' },
  { key: 'use_loop', label: '🔁 試試看用迴圈？' },
  { key: 'watch_obstacle', label: '⚠️ 注意前方障礙物！' },
  { key: 'check_energy', label: '⚡ 記得撿取能源！' },
  { key: 'good_job', label: '🎉 太棒了！' },
  { key: 'pass_turn', label: '🤝 交給下一位隊友操作' },
];

export const EMOJI_REACTIONS = ['👍', '💡', '⚡', '🤖', '🎉', '🔍', '❤️'];

