import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Drone Assembly Trainer", layout="wide")

st.title("🧩 Drone Assembly Trainer — One-File Build (Drag Anywhere)")
st.caption("All gameplay runs client-side (canvas). No assets folders. No component folders. Works on Streamlit Cloud.")

components.html(
    r"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <script src="https://unpkg.com/konva@9/konva.min.js"></script>
  <style>
    :root{
      --bg:#070b08; --panel:#0c1310; --border:#1a2a22;
      --green:#00ff88; --muted:#9fdcc0; --text:#e8fff3;
      --mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    }
    html, body { margin:0; padding:0; background:var(--bg); color:var(--text); font-family:var(--mono); }
    .wrap{ width:100%; padding:10px 10px 14px; box-sizing:border-box; }
    .top{
      display:flex; gap:12px; flex-wrap:wrap; align-items:stretch;
    }
    .panel{
      background:var(--panel); border:1px solid var(--border); border-radius:12px;
      padding:10px 12px; box-sizing:border-box;
    }
    .hudline{
      color:var(--muted); letter-spacing:.08em; text-transform:uppercase;
      font-size:12px; margin:0 0 8px;
      user-select:none; -webkit-user-select:none;
    }
    .stats{
      min-width:260px; flex: 0 0 290px;
      display:flex; flex-direction:column; gap:8px;
    }
    .grid{
      display:grid; grid-template-columns: repeat(2, minmax(120px, 1fr));
      gap:8px;
    }
    .kpi{
      border:1px solid var(--border); border-radius:10px; padding:8px 10px;
    }
    .kpi .lab{ color:var(--muted); font-size:11px; letter-spacing:.08em; text-transform:uppercase;}
    .kpi .val{ font-size:18px; margin-top:4px; color:var(--green); }
    .controls{
      display:flex; gap:10px; flex-wrap:wrap; align-items:center;
      border-top:1px dashed var(--border); padding-top:10px; margin-top:8px;
    }
    button, label{
      font-family:var(--mono);
      font-size:12px;
    }
    button{
      background:#0a1a12; color:var(--text);
      border:1px solid var(--border); border-radius:10px;
      padding:8px 10px; cursor:pointer;
    }
    button:hover{ border-color: var(--green); }
    .toggle{ display:flex; gap:6px; align-items:center; color:var(--muted); }
    input[type="checkbox"]{ accent-color: var(--green); transform: scale(1.05); }
    .msg{
      color:var(--muted); font-size:12px; margin-top:10px;
      border-top:1px dashed var(--border); padding-top:10px;
      min-height:18px;
    }
    .boardpanel{ flex: 1 1 520px; min-width: 320px; }
    #stageWrap{ width:100%; }
    #stage{ width:100%; }
    .quizOverlay{
      position:fixed; left:0; top:0; right:0; bottom:0;
      background: rgba(0,0,0,0.62);
      display:none; align-items:center; justify-content:center;
      padding:18px; box-sizing:border-box;
      z-index:9999;
    }
    .quizCard{
      width:min(720px, 96vw);
      background:var(--panel);
      border:1px solid var(--green);
      border-radius:14px;
      padding:14px 14px 12px;
      box-shadow: 0 0 22px rgba(0,255,136,0.18);
    }
    .quizTitle{ color:var(--green); letter-spacing:.06em; text-transform:uppercase; font-size:14px; margin:0 0 6px;}
    .quizSub{ color:var(--muted); font-size:12px; margin:0 0 10px;}
    .quizWhat{ margin:0 0 10px; font-size:13px; line-height:1.35;}
    .quizGotchas{ color:var(--muted); font-size:12px; margin:0 0 10px;}
    .quizQ{ margin:10px 0 8px; font-size:13px;}
    .optRow{ display:flex; flex-direction:column; gap:6px; margin-bottom:12px;}
    .optRow label{ color:var(--text); }
    .quizBtns{ display:flex; gap:10px; flex-wrap:wrap; align-items:center; }
    .pill{
      display:inline-block; padding:2px 10px; border-radius:999px;
      border:1px solid rgba(0,255,136,0.45);
      background:#0a1a12;
      color:var(--green);
      font-size:11px;
      letter-spacing:.06em;
      text-transform:uppercase;
    }
    .result{ margin-top:10px; font-size:12px; color:var(--muted); min-height:18px; }
  </style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <div class="panel stats">
      <div class="hudline" id="hudLine">DRONE ASSEMBLY // DRAG ANYWHERE // DROP NEAR ZONES TO SNAP</div>

      <div class="grid">
        <div class="kpi"><div class="lab">Score</div><div class="val" id="kScore">0</div></div>
        <div class="kpi"><div class="lab">Time (s)</div><div class="val" id="kTime">0</div></div>
        <div class="kpi"><div class="lab">Quiz Streak</div><div class="val" id="kStreak">0</div></div>
        <div class="kpi"><div class="lab">Best Streak</div><div class="val" id="kBest">0</div></div>
        <div class="kpi"><div class="lab">Wrong Drops</div><div class="val" id="kWrong">0</div></div>
        <div class="kpi"><div class="lab">Grade</div><div class="val" id="kGrade">—</div></div>
      </div>

      <div class="controls">
        <div class="toggle"><input id="tHints" type="checkbox" checked><label for="tHints">Hint rings</label></div>
        <div class="toggle"><input id="tLabels" type="checkbox"><label for="tLabels">Zone labels</label></div>
        <div class="toggle"><input id="tLock" type="checkbox" checked><label for="tLock">Lock correct</label></div>
        <div class="toggle"><input id="tSound" type="checkbox" checked><label for="tSound">Sound</label></div>
        <button id="btnReset">Reset</button>
      </div>

      <div class="msg" id="msg">Ready.</div>
    </div>

    <div class="panel boardpanel">
      <div class="hudline" id="hoverLine">HOVER: —</div>
      <div id="stageWrap"><div id="stage"></div></div>
    </div>
  </div>
</div>

<!-- Quiz overlay -->
<div class="quizOverlay" id="quizOverlay">
  <div class="quizCard">
    <div style="display:flex; justify-content:space-between; align-items:center; gap:10px;">
      <div>
        <div class="quizTitle" id="qTitle">Mini Lesson</div>
        <div class="quizSub" id="qSub">Locked: —</div>
      </div>
      <span class="pill" id="qPill">QUIZ</span>
    </div>

    <p class="quizWhat" id="qWhat"></p>
    <div class="quizGotchas" id="qGotchas"></div>

    <div class="quizQ" id="qQuestion"></div>
    <div class="optRow" id="qOptions"></div>

    <div class="quizBtns">
      <button id="btnCheck">Check answer</button>
      <button id="btnClose">Close</button>
      <span class="pill" id="qReward">+15 / -5</span>
      <span class="pill" id="qStreak">STREAK BONUS: every 3 = +10</span>
    </div>

    <div class="result" id="qResult"></div>
  </div>
</div>

<script>
(() => {
  // --------------------- Persistence ---------------------
  const STORE_KEY = "drone_assembly_onefile_v1";
  const nowMs = () => Date.now();

  function loadState() {
    try {
      const raw = localStorage.getItem(STORE_KEY);
      if (!raw) return null;
      return JSON.parse(raw);
    } catch(e) { return null; }
  }
  function saveState() {
    try { localStorage.setItem(STORE_KEY, JSON.stringify(state)); } catch(e) {}
  }

  // --------------------- WebAudio SFX ---------------------
  let audioCtx = null;
  function ctx() {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    return audioCtx;
  }
  function playTone(freq, dur, type="sine", gain=0.06) {
    const c = ctx();
    const o = c.createOscillator();
    const g = c.createGain();
    o.type = type;
    o.frequency.value = freq;
    g.gain.value = gain;
    o.connect(g); g.connect(c.destination);
    const t0 = c.currentTime;
    g.gain.setValueAtTime(gain, t0);
    g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    o.start(t0);
    o.stop(t0 + dur);
  }
  function playNoiseThud(dur=0.14, gain=0.06) {
    const c = ctx();
    const bufferSize = Math.floor(c.sampleRate * dur);
    const buffer = c.createBuffer(1, bufferSize, c.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i=0;i<bufferSize;i++) data[i] = (Math.random()*2-1) * (1 - i/bufferSize);
    const src = c.createBufferSource();
    src.buffer = buffer;
    const g = c.createGain();
    g.gain.value = gain;
    src.connect(g); g.connect(c.destination);
    src.start();
  }
  function sfx(name) {
    if (!state.sound_on) return;
    try {
      if (name === "drag")   playTone(420, 0.03, "square", 0.03);
      if (name === "correct"){ playTone(740, 0.08, "sine", 0.06); playTone(980, 0.10, "sine", 0.035); }
      if (name === "wrong")  playNoiseThud(0.12, 0.06);
      if (name === "lock")   { playTone(600, 0.05, "triangle", 0.04); playTone(900, 0.06, "triangle", 0.03); }
      if (name === "win")    { playTone(420,0.10,"sine",0.04); playTone(640,0.12,"sine",0.04); playTone(980,0.14,"sine",0.04); }
    } catch(e) {}
  }

  // --------------------- SVG icons (technical icon style) ---------------------
  const SVG = {
    prop: (stroke="#00ff88") => `
      <svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80">
        <g stroke="${stroke}" stroke-width="3" fill="rgba(0,0,0,0)">
          <circle cx="40" cy="40" r="6"/>
          <path d="M40 40 C20 25, 16 18, 18 14 C22 10, 30 16, 40 28 Z"/>
          <path d="M40 40 C60 25, 64 18, 62 14 C58 10, 50 16, 40 28 Z"/>
          <path d="M40 40 C25 60, 18 64, 14 62 C10 58, 16 50, 28 40 Z"/>
          <path d="M40 40 C55 60, 62 64, 66 62 C70 58, 64 50, 52 40 Z"/>
        </g>
      </svg>`,
    motor: (stroke="#00ff88") => `
      <svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80">
        <g stroke="${stroke}" stroke-width="3" fill="rgba(0,0,0,0)">
          <rect x="18" y="18" width="44" height="44" rx="10"/>
          <circle cx="40" cy="40" r="12"/>
          <path d="M40 28 L40 52"/><path d="M28 40 L52 40"/>
          <circle cx="40" cy="40" r="3" fill="${stroke}"/>
        </g>
      </svg>`,
    esc: (stroke="#00ff88") => `
      <svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80">
        <g stroke="${stroke}" stroke-width="3" fill="rgba(0,0,0,0)">
          <rect x="16" y="22" width="48" height="36" rx="6"/>
          <path d="M22 30 H58"/><path d="M22 38 H58"/><path d="M22 46 H58"/>
          <path d="M24 58 C24 66, 18 66, 18 70"/>
          <path d="M40 58 C40 66, 34 66, 34 70"/>
          <path d="M56 58 C56 66, 62 66, 62 70"/>
        </g>
      </svg>`,
    fc: (stroke="#00ff88") => `
      <svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80">
        <g stroke="${stroke}" stroke-width="3" fill="rgba(0,0,0,0)">
          <rect x="18" y="18" width="44" height="44" rx="8"/>
          <circle cx="40" cy="40" r="10"/>
          <path d="M10 28 H18"/><path d="M10 40 H18"/><path d="M10 52 H18"/>
          <path d="M62 28 H70"/><path d="M62 40 H70"/><path d="M62 52 H70"/>
        </g>
      </svg>`,
    pdb: (stroke="#00ff88") => `
      <svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80">
        <g stroke="${stroke}" stroke-width="3" fill="rgba(0,0,0,0)">
          <rect x="14" y="20" width="52" height="40" rx="10"/>
          <circle cx="26" cy="40" r="4" fill="${stroke}"/>
          <circle cx="40" cy="40" r="4" fill="${stroke}"/>
          <circle cx="54" cy="40" r="4" fill="${stroke}"/>
          <path d="M40 20 V12"/><path d="M36 12 H44"/>
        </g>
      </svg>`,
    rx: (stroke="#00ff88") => `
      <svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80">
        <g stroke="${stroke}" stroke-width="3" fill="rgba(0,0,0,0)">
          <rect x="18" y="26" width="44" height="28" rx="6"/>
          <path d="M26 54 V70"/><path d="M54 54 V70"/>
          <path d="M40 26 V18"/><circle cx="40" cy="18" r="4" fill="${stroke}"/>
        </g>
      </svg>`,
    vtx: (stroke="#00ff88") => `
      <svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80">
        <g stroke="${stroke}" stroke-width="3" fill="rgba(0,0,0,0)">
          <rect x="18" y="24" width="44" height="32" rx="7"/>
          <path d="M26 56 V68"/><path d="M54 56 V68"/>
          <path d="M62 30 C70 34, 70 46, 62 50"/><path d="M58 33 C64 36, 64 44, 58 47"/>
        </g>
      </svg>`,
    antenna: (stroke="#00ff88") => `
      <svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80">
        <g stroke="${stroke}" stroke-width="3" fill="rgba(0,0,0,0)">
          <path d="M40 64 V24"/><circle cx="40" cy="20" r="5" fill="${stroke}"/>
          <path d="M26 28 C18 36, 18 48, 26 56"/>
          <path d="M54 28 C62 36, 62 48, 54 56"/>
          <path d="M32 34 C28 38, 28 46, 32 50"/>
          <path d="M48 34 C52 38, 52 46, 48 50"/>
        </g>
      </svg>`,
    camera: (stroke="#00ff88") => `
      <svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80">
        <g stroke="${stroke}" stroke-width="3" fill="rgba(0,0,0,0)">
          <rect x="16" y="26" width="48" height="30" rx="8"/>
          <circle cx="40" cy="41" r="10"/><circle cx="40" cy="41" r="3" fill="${stroke}"/>
          <path d="M24 26 L30 18 H50 L56 26"/>
        </g>
      </svg>`,
  };

  function svgToImage(svgText) {
    return new Promise((resolve) => {
      const img = new Image();
      const svg64 = btoa(unescape(encodeURIComponent(svgText)));
      img.onload = () => resolve(img);
      img.src = "data:image/svg+xml;base64," + svg64;
    });
  }

  // --------------------- Zones + rules ---------------------
  const zones = [
    { key:"z_prop_tl",   name:"Prop (TL)",   x:0.18, y:0.22, allow:["prop"] },
    { key:"z_prop_tr",   name:"Prop (TR)",   x:0.82, y:0.22, allow:["prop"] },
    { key:"z_prop_bl",   name:"Prop (BL)",   x:0.18, y:0.78, allow:["prop"] },
    { key:"z_prop_br",   name:"Prop (BR)",   x:0.82, y:0.78, allow:["prop"] },

    { key:"z_motor_tl",  name:"Motor (TL)",  x:0.26, y:0.30, allow:["motor"] },
    { key:"z_motor_tr",  name:"Motor (TR)",  x:0.74, y:0.30, allow:["motor"] },
    { key:"z_motor_bl",  name:"Motor (BL)",  x:0.26, y:0.70, allow:["motor"] },
    { key:"z_motor_br",  name:"Motor (BR)",  x:0.74, y:0.70, allow:["motor"] },

    { key:"z_esc_tl",    name:"ESC (TL arm)",x:0.35, y:0.36, allow:["esc"] },
    { key:"z_esc_tr",    name:"ESC (TR arm)",x:0.65, y:0.36, allow:["esc"] },
    { key:"z_esc_bl",    name:"ESC (BL arm)",x:0.35, y:0.64, allow:["esc"] },
    { key:"z_esc_br",    name:"ESC (BR arm)",x:0.65, y:0.64, allow:["esc"] },

    { key:"z_rx",        name:"Receiver",    x:0.42, y:0.34, allow:["rx"] },
    { key:"z_vtx",       name:"VTX",         x:0.58, y:0.34, allow:["vtx"] },
    { key:"z_ant",       name:"Antenna",     x:0.50, y:0.16, allow:["antenna"] },
    { key:"z_pdb",       name:"PDB",         x:0.50, y:0.50, allow:["pdb"] },
    { key:"z_fc",        name:"Flight Ctrl", x:0.50, y:0.62, allow:["fc"] },
    { key:"z_cam",       name:"Camera",      x:0.50, y:0.86, allow:["camera"] },
  ];

  const ZONE_RADIUS_N = 0.055;

  // --------------------- Lessons + quiz pools ---------------------
  const QUIZ = {
    prop: {
      title:"Propeller",
      what:"Generates thrust by accelerating air. Pitch/diameter strongly affect efficiency and current draw.",
      gotchas:["CW/CCW props must match motor direction.","Oversized props can overcurrent motor/ESC."],
      questions:[
        ["If prop pitch increases (all else equal), motor load generally…", ["Increases","Decreases","Stays identical"], 0],
        ["A larger prop diameter usually…", ["Increases thrust and current draw","Always reduces current draw","Has no effect"], 0]
      ]
    },
    motor: {
      title:"Brushless Motor",
      what:"Spins the prop. Kv (~RPM/Volt) influences speed vs torque behavior.",
      gotchas:["High Kv often suits smaller props.","Heat often indicates overload or poor airflow."],
      questions:[
        ["Higher Kv generally means…", ["More RPM per volt","More torque per amp","Lower RPM per volt"], 0],
        ["If motors overheat, a common cause is…", ["Prop load too high","Too much altitude","Too much GPS"], 0]
      ]
    },
    esc: {
      title:"ESC",
      what:"Drives the motor using commutation. Must be rated above peak current with margin.",
      gotchas:["Underrated ESCs fail from heat/overcurrent.","Protocol must match FC."],
      questions:[
        ["An undersized ESC most commonly fails due to…", ["Overcurrent/overheating","Too much thrust","Low battery voltage"], 0],
        ["ESC current rating should be…", ["Above peak draw with margin","Exactly equal to peak draw","Below peak draw"], 0]
      ]
    },
    pdb: {
      title:"Power Distribution Board (PDB)",
      what:"Distributes battery power to ESCs and accessories; sometimes adds filtering/BEC.",
      gotchas:["Bad solder joints cause voltage drop + heat.","Filtering reduces FPV noise."],
      questions:[
        ["A PDB is mainly used to…", ["Distribute battery power","Control yaw","Transmit FPV video"], 0],
        ["A bad power joint often causes…", ["Heat and voltage drop","More range","Cleaner video"], 0]
      ]
    },
    fc: {
      title:"Flight Controller",
      what:"The brain: reads sensors, runs stabilization loops, commands the ESCs.",
      gotchas:["Wrong orientation can flip instantly.","Vibration hurts gyro data."],
      questions:[
        ["The FC outputs commands primarily to…", ["ESCs","Props directly","Battery cells"], 0],
        ["Excess vibration mainly hurts…", ["Gyro signal quality","Prop color","Receiver binding"], 0]
      ]
    },
    rx: {
      title:"Receiver",
      what:"Receives the pilot/control link and feeds commands to the FC.",
      gotchas:["Carbon can shadow RF.","Set failsafe to prevent flyaways."],
      questions:[
        ["Failsafe defines behavior when…", ["Signal is lost","Battery is full","Props are removed"], 0],
        ["Carbon frames can reduce range by…", ["Blocking/shielding RF","Increasing thrust","Charging the battery"], 0]
      ]
    },
    vtx: {
      title:"FPV Video Transmitter (VTX)",
      what:"Transmits camera feed. Higher power increases heat and interference risk.",
      gotchas:["Never power a VTX without an antenna.","High power can overheat without airflow."],
      questions:[
        ["A VTX should not be powered without…", ["An antenna","A flight controller","A motor"], 0],
        ["Higher VTX power usually…", ["Increases heat","Always increases battery voltage","Improves GPS lock"], 0]
      ]
    },
    antenna: {
      title:"Antenna",
      what:"Radiates/receives RF. Polarization + placement strongly affect link quality.",
      gotchas:["Match polarization (RHCP with RHCP).","Avoid shielding by battery/carbon."],
      questions:[
        ["Mismatched polarization typically…", ["Reduces signal","Increases thrust","Improves range"], 0],
        ["Antenna placement should avoid…", ["Carbon/battery shadowing","Wind","Sunlight"], 0]
      ]
    },
    camera: {
      title:"FPV Camera",
      what:"Captures the live feed. Low latency and dynamic range improve control.",
      gotchas:["Tilt affects perceived speed.","Noise lines often come from power ripple."],
      questions:[
        ["Higher camera tilt is generally used for…", ["Faster forward flight","Hover-only flight","Lower RPM motors"], 0],
        ["Rolling lines in FPV are often caused by…", ["Power noise","Too much yaw","Too many satellites"], 0]
      ]
    },
  };

  // --------------------- State ---------------------
  const defaultState = () => ({
    start_ms: nowMs(),
    score: 0,
    wrong: 0,
    quiz_streak: 0,
    best_streak: 0,
    quiz_scored: {},          // lockEventId -> true
    build_log: [],            // entries for library
    pending_quiz: null,       // current quiz entry
    lock_on: true,
    show_hints: true,
    show_labels: false,
    sound_on: true,
    parts: initParts(),       // array
  });

  function initParts() {
    const parts = [];
    const x0 = 0.06, dx = 0.082;

    for (let i=0;i<4;i++) parts.push({id:`prop_${i+1}`, label:`Prop ${i+1}`, kind:"prop", x:x0+dx*i, y:0.92, locked:false, zone:null});
    for (let i=0;i<4;i++) parts.push({id:`motor_${i+1}`, label:`Motor ${i+1}`, kind:"motor", x:x0+dx*(i+4), y:0.92, locked:false, zone:null});
    for (let i=0;i<4;i++) parts.push({id:`esc_${i+1}`, label:`ESC ${i+1}`, kind:"esc", x:x0+dx*(i+8), y:0.92, locked:false, zone:null});

    parts.push({id:"pdb_1", label:"PDB", kind:"pdb", x:0.08, y:0.80, locked:false, zone:null});
    parts.push({id:"fc_1", label:"FC", kind:"fc", x:0.17, y:0.80, locked:false, zone:null});
    parts.push({id:"rx_1", label:"RX", kind:"rx", x:0.26, y:0.80, locked:false, zone:null});
    parts.push({id:"vtx_1", label:"VTX", kind:"vtx", x:0.35, y:0.80, locked:false, zone:null});
    parts.push({id:"ant_1", label:"ANT", kind:"antenna", x:0.44, y:0.80, locked:false, zone:null});
    parts.push({id:"cam_1", label:"CAM", kind:"camera", x:0.53, y:0.80, locked:false, zone:null});

    return parts;
  }

  let state = loadState() || defaultState();

  // Apply UI toggles to state (if loaded)
  function syncTogglesFromState(){
    document.getElementById("tHints").checked = !!state.show_hints;
    document.getElementById("tLabels").checked = !!state.show_labels;
    document.getElementById("tLock").checked = !!state.lock_on;
    document.getElementById("tSound").checked = !!state.sound_on;
  }

  // --------------------- UI refs ---------------------
  const kScore = document.getElementById("kScore");
  const kTime  = document.getElementById("kTime");
  const kStreak= document.getElementById("kStreak");
  const kBest  = document.getElementById("kBest");
  const kWrong = document.getElementById("kWrong");
  const kGrade = document.getElementById("kGrade");
  const msg    = document.getElementById("msg");
  const hoverLine = document.getElementById("hoverLine");

  const quizOverlay = document.getElementById("quizOverlay");
  const qTitle = document.getElementById("qTitle");
  const qSub = document.getElementById("qSub");
  const qWhat = document.getElementById("qWhat");
  const qGotchas = document.getElementById("qGotchas");
  const qQuestion = document.getElementById("qQuestion");
  const qOptions = document.getElementById("qOptions");
  const qResult = document.getElementById("qResult");
  const btnCheck = document.getElementById("btnCheck");
  const btnClose = document.getElementById("btnClose");

  // --------------------- Metrics + Grade ---------------------
  function elapsedS() { return Math.floor((nowMs() - state.start_ms) / 1000); }

  function computeGrade() {
    const t = Math.max(1, elapsedS());
    const wrong = state.wrong;
    const totalQuiz = state.build_log.length; // approximates attempts
    const correctQuiz = state.build_log.filter(e => e.quiz_correct === true).length;
    const acc = totalQuiz ? (correctQuiz / totalQuiz) : 0;
    const best = state.best_streak;

    const timeScore = Math.max(0, 35 * (1 - Math.min(1, (t - 120) / 360)));
    const accScore = 35 * acc;
    const streakScore = 20 * Math.min(1, best / 10);
    const penalty = Math.min(20, wrong * 2);

    const score100 = Math.max(0, Math.min(100, timeScore + accScore + streakScore - penalty));

    let grade = "F";
    if (score100 >= 95) grade = "A+";
    else if (score100 >= 90) grade = "A";
    else if (score100 >= 80) grade = "B";
    else if (score100 >= 70) grade = "C";
    else if (score100 >= 60) grade = "D";
    return grade;
  }

  function updateHUD(){
    kScore.textContent = String(state.score);
    kTime.textContent  = String(elapsedS());
    kStreak.textContent= String(state.quiz_streak);
    kBest.textContent  = String(state.best_streak);
    kWrong.textContent = String(state.wrong);
    kGrade.textContent = computeGrade();
  }

  // --------------------- Konva Board ---------------------
  let stage=null, bgLayer=null, zonesLayer=null, partsLayer=null;
  const zoneNodes = new Map();
  const partNodes = new Map();

  function getCanvasSize(){
    const stageDiv = document.getElementById("stage");
    const w = Math.max(420, stageDiv.clientWidth || 900);
    const aspect = 1100/680;
    const h = Math.max(320, Math.floor(w/aspect));
    return {W:w, H:h};
  }

  function normToPx(xn, yn, W, H){ return {x:xn*W, y:yn*H}; }
  function pxToNorm(x, y, W, H){
    return {x: Math.min(1, Math.max(0, x/W)), y: Math.min(1, Math.max(0, y/H))};
  }

  function drawBackground(W,H){
    bgLayer.destroyChildren();
    bgLayer.add(new Konva.Rect({x:0,y:0,width:W,height:H,fill:"#08110c"}));

    const step = Math.max(55, Math.floor(Math.min(W,H)/10));
    for (let x=0;x<=W;x+=step) bgLayer.add(new Konva.Line({points:[x,0,x,H], stroke:"#122116", strokeWidth:1, opacity:0.55}));
    for (let y=0;y<=H;y+=step) bgLayer.add(new Konva.Line({points:[0,y,W,y], stroke:"#122116", strokeWidth:1, opacity:0.55}));

    const cx=W/2, cy=H/2;
    bgLayer.add(new Konva.Line({points:[cx-55,cy,cx+55,cy], stroke:"#00ff88", strokeWidth:2, opacity:0.9}));
    bgLayer.add(new Konva.Line({points:[cx,cy-55,cx,cy+55], stroke:"#00ff88", strokeWidth:2, opacity:0.9}));
    bgLayer.add(new Konva.Circle({x:cx,y:cy,radius:10, stroke:"#00ff88", strokeWidth:2, opacity:0.9}));
  }

  function drawZones(W,H){
    zonesLayer.destroyChildren();
    zoneNodes.clear();
    const zr = Math.max(20, Math.floor(Math.min(W,H) * ZONE_RADIUS_N));

    zones.forEach(z => {
      const p = normToPx(z.x,z.y,W,H);
      const ring = new Konva.Circle({
        x:p.x, y:p.y, radius:zr,
        stroke:"#00ff88", strokeWidth:2,
        opacity: state.show_hints ? 0.9 : 0.0
      });
      zonesLayer.add(ring);
      zoneNodes.set(z.key, ring);

      if (state.show_labels) {
        zonesLayer.add(new Konva.Text({
          x: p.x + zr + 6,
          y: p.y - 7,
          text: z.name,
          fontSize: 12,
          fontFamily: "ui-monospace, Menlo, Consolas, monospace",
          fill: "#9fdcc0",
          opacity: 0.95
        }));
      }
    });
  }

  function pulseZone(zoneKey){
    const ring = zoneNodes.get(zoneKey);
    if (!ring) return;
    const base = ring.radius();
    ring.opacity(1);
    ring.strokeWidth(3);
    ring.to({
      radius: base*1.35, opacity:0.15, duration:0.35, easing: Konva.Easings.EaseOut,
      onFinish: () => {
        ring.radius(base);
        ring.opacity(state.show_hints ? 0.9 : 0.0);
        ring.strokeWidth(2);
        zonesLayer.draw();
      }
    });
  }

  function pulsePart(partId){
    const g = partNodes.get(partId);
    if (!g) return;
    g.to({
      scaleX:1.06, scaleY:1.06, duration:0.12, easing: Konva.Easings.EaseOut,
      onFinish: () => g.to({scaleX:1, scaleY:1, duration:0.16, easing: Konva.Easings.EaseOut})
    });
  }

  function tweenTo(node, x, y){
    return new Promise(res => {
      node.to({x,y,duration:0.18,easing:Konva.Easings.EaseOut,onFinish:res});
    });
  }

  async function ensurePartNode(W,H, part){
    if (partNodes.has(part.id)) return;

    const iconSize = 74;
    const svg = (SVG[part.kind] ? SVG[part.kind]() : SVG.fc());
    const img = await svgToImage(svg);

    const g = new Konva.Group({x:0,y:0,draggable:!part.locked});

    // huge hitbox for mobile
    const hit = new Konva.Rect({x:-10,y:-10,width:iconSize+20,height:iconSize+40,fill:"rgba(0,0,0,0)"});

    const glow = new Konva.Rect({
      x:-10,y:-10,width:iconSize+20,height:iconSize+20,
      stroke:"#00ff88", strokeWidth:2, cornerRadius:10,
      opacity: part.locked ? 0.95 : 0.0,
      shadowColor:"#00ff88", shadowBlur: part.locked ? 14 : 0,
      shadowOpacity: part.locked ? 0.6 : 0.0
    });

    const icon = new Konva.Image({image:img, x:0,y:0,width:iconSize,height:iconSize});

    const label = new Konva.Text({
      x:0, y: iconSize+4,
      text: part.label,
      fontSize: 12,
      fontFamily: "ui-monospace, Menlo, Consolas, monospace",
      fill: "#e8fff3"
    });

    g.add(hit); g.add(glow); g.add(icon); g.add(label);
    glow.moveToBottom();

    g.on("mouseenter", () => {
      hoverLine.textContent = `HOVER: ${part.label} // ${part.locked ? "LOCKED" : "MOVE"}`;
      document.body.style.cursor = part.locked ? "default" : "grab";
    });
    g.on("mouseleave", () => {
      hoverLine.textContent = "HOVER: —";
      document.body.style.cursor = "default";
    });

    g.on("dragstart", () => {
      sfx("drag");
      g.moveToTop();
      partsLayer.draw();
      document.body.style.cursor = "grabbing";
    });

    g.on("dragend", async () => {
      document.body.style.cursor = "grab";
      const pos = pxToNorm(g.x(), g.y(), stage.width(), stage.height());
      await handleDrop(part.id, pos.x, pos.y);
    });

    partsLayer.add(g);
    partNodes.set(part.id, g);
  }

  function updatePartStyle(g, part){
    const kids = g.getChildren();
    const glow = kids.find(k => k.className === "Rect" && k.stroke && k.stroke() === "#00ff88");
    if (glow){
      glow.opacity(part.locked ? 0.95 : 0.0);
      glow.shadowBlur(part.locked ? 14 : 0);
      glow.shadowOpacity(part.locked ? 0.6 : 0.0);
    }
    g.draggable(!part.locked);
  }

  async function drawParts(W,H){
    // remove nodes for deleted parts (not expected here)
    for (const [id,node] of partNodes.entries()){
      if (!state.parts.find(p => p.id === id)) { node.destroy(); partNodes.delete(id); }
    }

    for (const part of state.parts){
      await ensurePartNode(W,H, part);
      const g = partNodes.get(part.id);
      if (!g) continue;
      const p = normToPx(part.x, part.y, W, H);
      g.x(p.x); g.y(p.y);
      updatePartStyle(g, part);
    }
  }

  function nearestZone(xn, yn){
    let best=null, bestD=1e9;
    for (const z of zones){
      const dx = xn - z.x, dy = yn - z.y;
      const d = Math.sqrt(dx*dx+dy*dy);
      if (d < bestD){ bestD=d; best=z; }
    }
    if (best && bestD <= ZONE_RADIUS_N) return best;
    return null;
  }

  function zoneOccupied(zoneKey){
    return state.parts.some(p => p.locked && p.zone === zoneKey);
  }

  // --------------------- Quiz modal ---------------------
  function openQuiz(entry){
    state.pending_quiz = entry;
    saveState();
    qResult.textContent = "";
    const bank = QUIZ[entry.kind];

    qTitle.textContent = `Mini Lesson: ${bank.title}`;
    qSub.textContent = `Locked: ${entry.part_label} → ${entry.zone_name}`;
    qWhat.textContent = bank.what;
    qGotchas.innerHTML = `<b>Gotchas:</b><br>• ${bank.gotchas.join("<br>• ")}`;

    const [qq, opts] = entry.question;
    qQuestion.textContent = qq;

    qOptions.innerHTML = "";
    opts.forEach((o, idx) => {
      const id = `opt_${idx}`;
      const row = document.createElement("label");
      row.innerHTML = `<input type="radio" name="quizopt" value="${idx}" ${idx===0?"checked":""}/> ${o}`;
      qOptions.appendChild(row);
    });

    // disable farming
    btnCheck.disabled = !!state.quiz_scored[entry.event_id];
    quizOverlay.style.display = "flex";
  }

  function closeQuiz(){
    quizOverlay.style.display = "none";
    state.pending_quiz = null;
    saveState();
  }

  function gradeQuiz(isCorrect){
    const entry = state.pending_quiz;
    if (!entry) return;

    if (state.quiz_scored[entry.event_id]) {
      qResult.textContent = "Already scored for this lock (no farming).";
      return;
    }
    state.quiz_scored[entry.event_id] = true;

    const ptsCorrect = 15, ptsWrong = -5, bonusEvery=3, bonusPts=10;

    if (isCorrect) {
      state.score += ptsCorrect;
      state.quiz_streak += 1;
      state.best_streak = Math.max(state.best_streak, state.quiz_streak);

      // mark build_log entry as correct
      const log = state.build_log.find(e => e.event_id === entry.event_id);
      if (log) log.quiz_correct = true;

      if (state.quiz_streak % bonusEvery === 0) {
        state.score += bonusPts;
        qResult.textContent = `✅ Correct! +${ptsCorrect}. 🔥 Streak bonus +${bonusPts}!`;
      } else {
        qResult.textContent = `✅ Correct! +${ptsCorrect}.`;
      }
    } else {
      state.score += ptsWrong;
      state.quiz_streak = 0;

      const log = state.build_log.find(e => e.event_id === entry.event_id);
      if (log) log.quiz_correct = false;

      qResult.textContent = `❌ Not quite. (${ptsWrong})`;
    }

    btnCheck.disabled = true;
    msg.textContent = "Quiz scored.";
    updateHUD();
    saveState();
  }

  btnClose.onclick = closeQuiz;
  btnCheck.onclick = () => {
    const entry = state.pending_quiz;
    if (!entry) return;

    const chosen = document.querySelector('input[name="quizopt"]:checked');
    const idx = chosen ? parseInt(chosen.value, 10) : 0;
    const correctIdx = entry.question[2];
    const isCorrect = (idx === correctIdx);
    gradeQuiz(isCorrect);
  };

  // --------------------- Drop handling ---------------------
  async function handleDrop(partId, xn, yn){
    const part = state.parts.find(p => p.id === partId);
    if (!part || part.locked) return;

    // update raw pos
    part.x = xn; part.y = yn;

    const z = nearestZone(xn, yn);
    if (!z) {
      msg.textContent = `Moved: ${part.label}`;
      saveState();
      return;
    }

    if (zoneOccupied(z.key)) {
      state.score += -3;
      state.wrong += 1;
      msg.textContent = `❌ Zone occupied: ${z.name} (-3)`;
      sfx("wrong");
      updateHUD();
      saveState();
      return;
    }

    // snap
    part.x = z.x; part.y = z.y;

    // animate snap
    const g = partNodes.get(part.id);
    if (g) {
      const {W,H} = getCanvasSize();
      const p = normToPx(part.x, part.y, W, H);
      await tweenTo(g, p.x, p.y);
      partsLayer.draw();
    }

    // evaluate correctness
    const ok = z.allow.includes(part.kind);
    if (!ok) {
      state.score += -3;
      state.wrong += 1;
      msg.textContent = `❌ Wrong zone: ${part.label} near ${z.name} (-3)`;
      sfx("wrong");
      pulseZone(z.key);
      updateHUD();
      saveState();
      return;
    }

    // correct snap
    state.score += 10;
    msg.textContent = `✅ Snapped: ${part.label} → ${z.name} (+10)`;
    sfx("correct");
    pulseZone(z.key);

    // lock if enabled
    if (state.lock_on) {
      part.locked = true;
      part.zone = z.key;
      state.score += 15; // lock bonus
      sfx("lock");
      pulsePart(part.id);

      // create lock event + randomized question (stable per lock)
      const eventId = `${nowMs()}_${part.id}_${z.key}`;
      const bank = QUIZ[part.kind];
      const qIdx = nowMs() % bank.questions.length;
      const question = bank.questions[qIdx];

      const entry = {
        event_id: eventId,
        kind: part.kind,
        part_id: part.id,
        part_label: part.label,
        zone_key: z.key,
        zone_name: z.name,
        question: question,     // [q, opts, correctIdx]
        quiz_correct: null
      };

      state.build_log.push(entry);
      openQuiz(entry);
    }

    // update Konva style
    if (partNodes.get(part.id)) updatePartStyle(partNodes.get(part.id), part);

    updateHUD();
    saveState();

    // win?
    if (state.parts.every(p => p.locked)) {
      msg.textContent = "✅ Perfect build! All parts locked.";
      sfx("win");
    }
  }

  // --------------------- Render loop ---------------------
  async function render(){
    const {W,H} = getCanvasSize();

    if (!stage) {
      stage = new Konva.Stage({ container:"stage", width:W, height:H });
      bgLayer = new Konva.Layer();
      zonesLayer = new Konva.Layer();
      partsLayer = new Konva.Layer();
      stage.add(bgLayer);
      stage.add(zonesLayer);
      stage.add(partsLayer);

      window.addEventListener("resize", () => { render(); });
    } else {
      stage.width(W); stage.height(H);
    }

    drawBackground(W,H);
    drawZones(W,H);
    await drawParts(W,H);

    bgLayer.draw();
    zonesLayer.draw();
    partsLayer.draw();
  }

  // --------------------- Controls ---------------------
  document.getElementById("tHints").onchange = (e) => { state.show_hints = e.target.checked; saveState(); render(); };
  document.getElementById("tLabels").onchange = (e) => { state.show_labels = e.target.checked; saveState(); render(); };
  document.getElementById("tLock").onchange = (e) => { state.lock_on = e.target.checked; saveState(); msg.textContent = state.lock_on ? "Lock enabled." : "Lock disabled."; };
  document.getElementById("tSound").onchange = (e) => { state.sound_on = e.target.checked; saveState(); msg.textContent = state.sound_on ? "Sound enabled." : "Sound disabled."; };

  document.getElementById("btnReset").onclick = () => {
    state = defaultState();
    saveState();
    syncTogglesFromState();
    msg.textContent = "Reset.";
    updateHUD();
    render();
  };

  // --------------------- Boot ---------------------
  syncTogglesFromState();
  updateHUD();
  render();

  // Tick timer
  setInterval(() => { updateHUD(); }, 250);

  // Resume quiz if it was open (optional)
  if (state.pending_quiz) {
    // find last entry
    const last = state.build_log.find(e => e.event_id === state.pending_quiz.event_id) || state.pending_quiz;
    openQuiz(last);
  }

})();
</script>
</body>
</html>
""",
    height=820,
    scrolling=False,
)
