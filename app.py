import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import streamlit as st
import streamlit.components.v1 as components


# ============================
# Local component
# ============================
_DRONE_CANVAS = components.declare_component(
    "drone_canvas",
    path=str(Path(__file__).parent / "drone_canvas"),
)

# ============================
# Tactical HUD CSS
# ============================
components.html(
    """
<style>
:root{
  --bg:#070b08; --panel:#0c1310; --border:#1a2a22;
  --green:#00ff88; --green-dim:#1f3b2c; --green-glow:rgba(0,255,136,.55);
  --text:#e8fff3; --text-muted:#9fdcc0;
  --mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}
html, body, [data-testid="stApp"] { background: var(--bg); color: var(--text); font-family: var(--mono); }
h1,h2,h3,h4 { color: var(--green); letter-spacing:.04em; font-family: var(--mono); }
small,.stCaption { color: var(--text-muted); font-family: var(--mono); }
section[data-testid="stSidebar"]{
  background: var(--panel) !important;
  border-right: 1px solid var(--border);
}
div[data-testid="stContainer"], div[data-testid="stExpander"]{
  background: var(--panel) !important;
  border: 1px solid var(--border);
  border-radius: 12px;
}
.hud { color: var(--text-muted); letter-spacing: .08em; text-transform: uppercase; font-size: 12px; }
</style>
""",
    height=0,
)

# ============================
# Models
# ============================
@dataclass(frozen=True)
class Zone:
    key: str
    display_name: str
    xy: Tuple[float, float]  # normalized 0..1


@dataclass
class Part:
    id: str
    label: str
    kind: str
    x: float
    y: float
    locked: bool = False
    locked_zone: Optional[str] = None


# ============================
# Technical icon SVG sprites (embedded, consistent style)
# ============================
def svg_icon(kind: str) -> str:
    stroke = "#00ff88"
    muted = "#9fdcc0"
    fill = "rgba(0,0,0,0)"

    if kind == "prop":
        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80">
          <g stroke="{stroke}" stroke-width="3" fill="{fill}">
            <circle cx="40" cy="40" r="6"/>
            <path d="M40 40 C20 25, 16 18, 18 14 C22 10, 30 16, 40 28 Z"/>
            <path d="M40 40 C60 25, 64 18, 62 14 C58 10, 50 16, 40 28 Z"/>
            <path d="M40 40 C25 60, 18 64, 14 62 C10 58, 16 50, 28 40 Z"/>
            <path d="M40 40 C55 60, 62 64, 66 62 C70 58, 64 50, 52 40 Z"/>
          </g>
        </svg>"""
    if kind == "motor":
        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80">
          <g stroke="{stroke}" stroke-width="3" fill="{fill}">
            <rect x="18" y="18" width="44" height="44" rx="10"/>
            <circle cx="40" cy="40" r="12"/>
            <path d="M40 28 L40 52"/>
            <path d="M28 40 L52 40"/>
            <circle cx="40" cy="40" r="3" fill="{stroke}"/>
          </g>
        </svg>"""
    if kind == "esc":
        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80">
          <g stroke="{stroke}" stroke-width="3" fill="{fill}">
            <rect x="16" y="22" width="48" height="36" rx="6"/>
            <path d="M22 30 H58"/><path d="M22 38 H58"/><path d="M22 46 H58"/>
            <path d="M24 58 C24 66, 18 66, 18 70" />
            <path d="M40 58 C40 66, 34 66, 34 70" />
            <path d="M56 58 C56 66, 62 66, 62 70" />
          </g>
        </svg>"""
    if kind == "fc":
        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80">
          <g stroke="{stroke}" stroke-width="3" fill="{fill}">
            <rect x="18" y="18" width="44" height="44" rx="8"/>
            <circle cx="40" cy="40" r="10"/>
            <path d="M10 28 H18"/><path d="M10 40 H18"/><path d="M10 52 H18"/>
            <path d="M62 28 H70"/><path d="M62 40 H70"/><path d="M62 52 H70"/>
          </g>
        </svg>"""
    if kind == "pdb":
        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80">
          <g stroke="{stroke}" stroke-width="3" fill="{fill}">
            <rect x="14" y="20" width="52" height="40" rx="10"/>
            <circle cx="26" cy="40" r="4" fill="{stroke}"/>
            <circle cx="40" cy="40" r="4" fill="{stroke}"/>
            <circle cx="54" cy="40" r="4" fill="{stroke}"/>
            <path d="M40 20 V12" /><path d="M36 12 H44" />
          </g>
        </svg>"""
    if kind == "rx":
        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80">
          <g stroke="{stroke}" stroke-width="3" fill="{fill}">
            <rect x="18" y="26" width="44" height="28" rx="6"/>
            <path d="M26 54 V70"/><path d="M54 54 V70"/>
            <path d="M40 26 V18"/><circle cx="40" cy="18" r="4" fill="{stroke}"/>
          </g>
        </svg>"""
    if kind == "vtx":
        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80">
          <g stroke="{stroke}" stroke-width="3" fill="{fill}">
            <rect x="18" y="24" width="44" height="32" rx="7"/>
            <path d="M26 56 V68"/><path d="M54 56 V68"/>
            <path d="M62 30 C70 34, 70 46, 62 50" />
            <path d="M58 33 C64 36, 64 44, 58 47" />
          </g>
        </svg>"""
    if kind == "antenna":
        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80">
          <g stroke="{stroke}" stroke-width="3" fill="{fill}">
            <path d="M40 64 V24" /><circle cx="40" cy="20" r="5" fill="{stroke}"/>
            <path d="M26 28 C18 36, 18 48, 26 56" />
            <path d="M54 28 C62 36, 62 48, 54 56" />
            <path d="M32 34 C28 38, 28 46, 32 50" />
            <path d="M48 34 C52 38, 52 46, 48 50" />
          </g>
        </svg>"""
    if kind == "camera":
        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80">
          <g stroke="{stroke}" stroke-width="3" fill="{fill}">
            <rect x="16" y="26" width="48" height="30" rx="8"/>
            <circle cx="40" cy="41" r="10"/><circle cx="40" cy="41" r="3" fill="{stroke}"/>
            <path d="M24 26 L30 18 H50 L56 26" />
          </g>
        </svg>"""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80">
      <g stroke="{muted}" stroke-width="3" fill="{fill}">
        <rect x="16" y="16" width="48" height="48" rx="10"/>
        <text x="40" y="46" text-anchor="middle" fill="{muted}" font-family="monospace" font-size="14">{kind}</text>
      </g>
    </svg>"""


# ============================
# Zones (normalized layout)
# ============================
ZONES: List[Zone] = [
    Zone("z_prop_tl", "Prop (TL)", (0.18, 0.22)),
    Zone("z_prop_tr", "Prop (TR)", (0.82, 0.22)),
    Zone("z_prop_bl", "Prop (BL)", (0.18, 0.78)),
    Zone("z_prop_br", "Prop (BR)", (0.82, 0.78)),

    Zone("z_motor_tl", "Motor (TL)", (0.26, 0.30)),
    Zone("z_motor_tr", "Motor (TR)", (0.74, 0.30)),
    Zone("z_motor_bl", "Motor (BL)", (0.26, 0.70)),
    Zone("z_motor_br", "Motor (BR)", (0.74, 0.70)),

    Zone("z_esc_tl", "ESC (TL arm)", (0.35, 0.36)),
    Zone("z_esc_tr", "ESC (TR arm)", (0.65, 0.36)),
    Zone("z_esc_bl", "ESC (BL arm)", (0.35, 0.64)),
    Zone("z_esc_br", "ESC (BR arm)", (0.65, 0.64)),

    Zone("z_rx", "Receiver", (0.42, 0.34)),
    Zone("z_vtx", "VTX", (0.58, 0.34)),
    Zone("z_ant", "Antenna", (0.50, 0.16)),
    Zone("z_pdb", "PDB", (0.50, 0.50)),
    Zone("z_fc", "Flight Ctrl", (0.50, 0.62)),
    Zone("z_cam", "Camera", (0.50, 0.86)),
]
ZMAP = {z.key: z for z in ZONES}

# Snap radius in normalized units (board is 0..1)
ZONE_RADIUS_NORM = 0.055

# Allowed kinds per zone
ZONE_KIND_ALLOWED: Dict[str, List[str]] = {
    "z_prop_tl": ["prop"], "z_prop_tr": ["prop"], "z_prop_bl": ["prop"], "z_prop_br": ["prop"],
    "z_motor_tl": ["motor"], "z_motor_tr": ["motor"], "z_motor_bl": ["motor"], "z_motor_br": ["motor"],
    "z_esc_tl": ["esc"], "z_esc_tr": ["esc"], "z_esc_bl": ["esc"], "z_esc_br": ["esc"],
    "z_rx": ["rx"],
    "z_vtx": ["vtx"],
    "z_ant": ["antenna"],
    "z_pdb": ["pdb"],
    "z_fc": ["fc"],
    "z_cam": ["camera"],
}

# ============================
# Lessons + randomized quiz pools (stored per lock event)
# ============================
QUIZ_BANK: Dict[str, Dict] = {
    "prop": {
        "title": "Propeller",
        "what": "Generates thrust by accelerating air. Pitch/diameter strongly affect efficiency and current draw.",
        "gotchas": [
            "CW/CCW props must match motor direction.",
            "Oversized props can overcurrent motor/ESC."
        ],
        "questions": [
            ("If prop pitch increases (all else equal), motor load generally…",
             ["Increases", "Decreases", "Stays identical"], 0),
            ("A larger prop diameter usually…",
             ["Increases thrust and current draw", "Always reduces current draw", "Has no effect"], 0),
        ],
    },
    "motor": {
        "title": "Brushless Motor",
        "what": "Spins the prop. Kv (~RPM/Volt) influences speed vs torque behavior.",
        "gotchas": [
            "High Kv often suits smaller props (higher RPM, lower torque).",
            "Heat often indicates overload or poor airflow."
        ],
        "questions": [
            ("Higher Kv generally means…",
             ["More RPM per volt", "More torque per amp", "Lower RPM per volt"], 0),
            ("If motors overheat, a common cause is…",
             ["Prop load too high", "Too much altitude", "Too much GPS"], 0),
        ],
    },
    "esc": {
        "title": "ESC (Electronic Speed Controller)",
        "what": "Drives the motor using commutation. Must be rated above peak current with margin.",
        "gotchas": [
            "Underrated ESCs fail from heat/overcurrent.",
            "Protocol (PWM/DShot) must match FC."
        ],
        "questions": [
            ("An undersized ESC most commonly fails due to…",
             ["Overcurrent/overheating", "Too much thrust", "Low battery voltage"], 0),
            ("ESC current rating should be…",
             ["Above peak draw with margin", "Exactly equal to peak draw", "Below peak draw"], 0),
        ],
    },
    "pdb": {
        "title": "Power Distribution Board (PDB)",
        "what": "Distributes battery power to ESCs and accessories; sometimes adds filtering/BEC.",
        "gotchas": [
            "Bad solder joints cause voltage drop + heat.",
            "Filtering reduces FPV noise and FC interference."
        ],
        "questions": [
            ("A PDB is mainly used to…",
             ["Distribute battery power", "Control yaw", "Transmit FPV video"], 0),
            ("A bad power joint often causes…",
             ["Heat and voltage drop", "More range", "Cleaner video"], 0),
        ],
    },
    "fc": {
        "title": "Flight Controller",
        "what": "The brain: reads sensors, runs stabilization loops, commands the ESCs.",
        "gotchas": [
            "Wrong orientation/calibration can cause instant flip on arm.",
            "Vibration isolation improves gyro quality."
        ],
        "questions": [
            ("The FC outputs commands primarily to…",
             ["ESCs", "Props directly", "Battery cells"], 0),
            ("Excess vibration mainly hurts…",
             ["Gyro signal quality", "Prop color", "Receiver binding"], 0),
        ],
    },
    "rx": {
        "title": "Receiver",
        "what": "Receives the pilot/control link and feeds commands to the FC.",
        "gotchas": [
            "Antenna placement matters (carbon can shadow RF).",
            "Set failsafe to prevent flyaways."
        ],
        "questions": [
            ("Failsafe defines behavior when…",
             ["Signal is lost", "Battery is full", "Props are removed"], 0),
            ("Carbon frames can reduce range by…",
             ["Blocking/shielding RF", "Increasing thrust", "Charging the battery"], 0),
        ],
    },
    "vtx": {
        "title": "FPV Video Transmitter (VTX)",
        "what": "Transmits camera feed. Higher power increases heat and interference risk.",
        "gotchas": [
            "Never power a VTX without an antenna.",
            "High output can overheat if airflow is poor."
        ],
        "questions": [
            ("A VTX should not be powered without…",
             ["An antenna", "A flight controller", "A motor"], 0),
            ("Higher VTX power usually…",
             ["Increases heat", "Always increases battery voltage", "Improves GPS lock"], 0),
        ],
    },
    "antenna": {
        "title": "Antenna",
        "what": "Radiates/receives RF. Polarization + placement strongly affect link quality.",
        "gotchas": [
            "Match polarization (RHCP with RHCP).",
            "Avoid shielding by battery/carbon."
        ],
        "questions": [
            ("Mismatched polarization typically…",
             ["Reduces signal", "Increases thrust", "Improves range"], 0),
            ("Antenna placement should avoid…",
             ["Carbon/battery shadowing", "Wind", "Sunlight"], 0),
        ],
    },
    "camera": {
        "title": "FPV Camera",
        "what": "Captures the live feed. Low latency and good dynamic range improve control.",
        "gotchas": [
            "Tilt affects perceived speed/handling.",
            "Noise lines often come from power ripple."
        ],
        "questions": [
            ("Higher camera tilt is generally used for…",
             ["Faster forward flight", "Hover-only flight", "Lower RPM motors"], 0),
            ("Rolling lines in FPV are often caused by…",
             ["Power noise", "Too much yaw", "Too many satellites"], 0),
        ],
    },
}


# ============================
# Scoring
# ============================
PLACEMENT_POINTS_CORRECT = 10
PLACEMENT_POINTS_WRONG = -3

QUIZ_POINTS_CORRECT = 15
QUIZ_POINTS_WRONG = -5

STREAK_BONUS_EVERY = 3
STREAK_BONUS_POINTS = 10


# ============================
# Utility
# ============================
def dist(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

def find_nearest_zone(x: float, y: float) -> Optional[str]:
    best = None
    best_d = 1e9
    for z in ZONES:
        d = dist((x, y), z.xy)
        if d < best_d:
            best_d = d
            best = z.key
    if best is not None and best_d <= ZONE_RADIUS_NORM:
        return best
    return None

def is_correct(kind: str, zone_key: str) -> bool:
    return kind in ZONE_KIND_ALLOWED.get(zone_key, [])

def elapsed_s() -> int:
    return int(time.time() - st.session_state.start_time)

def serialize_parts(parts: List[Part]) -> List[dict]:
    return [{
        "id": p.id,
        "label": p.label,
        "kind": p.kind,
        "x": p.x,
        "y": p.y,
        "locked": p.locked,
        "size_px": 74,
        "svg": svg_icon(p.kind),
        "disabled": False,
    } for p in parts]

def serialize_zones() -> List[dict]:
    return [{"key": z.key, "display_name": z.display_name, "x": z.xy[0], "y": z.xy[1]} for z in ZONES]

def make_event_id(part_id: str, zone_key: str) -> str:
    return f"{int(time.time()*1000)}_{part_id}_{zone_key}"

def ensure_state():
    if "parts" not in st.session_state:
        parts: List[Part] = []

        # staging layout: bottom row for props/motors/escs, upper row for core electronics
        x0, dx = 0.06, 0.082

        for i in range(4):
            parts.append(Part(id=f"prop_{i+1}", label=f"Prop {i+1}", kind="prop", x=x0 + dx*i, y=0.92))
        for i in range(4):
            parts.append(Part(id=f"motor_{i+1}", label=f"Motor {i+1}", kind="motor", x=x0 + dx*(i+4), y=0.92))
        for i in range(4):
            parts.append(Part(id=f"esc_{i+1}", label=f"ESC {i+1}", kind="esc", x=x0 + dx*(i+8), y=0.92))

        core = [
            ("pdb_1", "PDB", "pdb", 0.08, 0.80),
            ("fc_1", "FC", "fc", 0.17, 0.80),
            ("rx_1", "RX", "rx", 0.26, 0.80),
            ("vtx_1", "VTX", "vtx", 0.35, 0.80),
            ("ant_1", "ANT", "antenna", 0.44, 0.80),
            ("cam_1", "CAM", "camera", 0.53, 0.80),
        ]
        for pid, label, kind, x, y in core:
            parts.append(Part(id=pid, label=label, kind=kind, x=x, y=y))

        st.session_state.parts = parts

    st.session_state.setdefault("start_time", time.time())
    st.session_state.setdefault("score", 0)
    st.session_state.setdefault("last_msg", "Ready.")
    st.session_state.setdefault("lock_on", True)
    st.session_state.setdefault("show_hints", True)
    st.session_state.setdefault("show_zone_labels", False)
    st.session_state.setdefault("sound_on", True)

    # placement stats
    st.session_state.setdefault("wrong_drops", 0)
    st.session_state.setdefault("correct_snaps", 0)

    # quiz stats
    st.session_state.setdefault("quiz_streak", 0)
    st.session_state.setdefault("quiz_best_streak", 0)
    st.session_state.setdefault("quiz_points_total", 0)
    st.session_state.setdefault("quiz_correct", 0)
    st.session_state.setdefault("quiz_wrong", 0)
    st.session_state.setdefault("quiz_scored", {})  # event_id -> True

    # lessons
    st.session_state.setdefault("build_log", [])      # list[dict]
    st.session_state.setdefault("pending_quiz", None) # dict or None

    # for JS animations/sfx
    st.session_state.setdefault("server_event", None) # dict or None


def reset_all():
    # Reset parts to staging
    parts: List[Part] = st.session_state.parts
    x0, dx = 0.06, 0.082
    idx = 0
    core_positions = {
        "pdb": (0.08, 0.80), "fc": (0.17, 0.80), "rx": (0.26, 0.80),
        "vtx": (0.35, 0.80), "antenna": (0.44, 0.80), "camera": (0.53, 0.80),
    }

    for p in parts:
        p.locked = False
        p.locked_zone = None

        if p.kind in ("prop", "motor", "esc"):
            p.x = x0 + dx * idx
            p.y = 0.92
            idx += 1
        else:
            p.x, p.y = core_positions.get(p.kind, (0.08, 0.80))

    st.session_state.start_time = time.time()
    st.session_state.score = 0
    st.session_state.last_msg = "Reset."
    st.session_state.wrong_drops = 0
    st.session_state.correct_snaps = 0

    st.session_state.quiz_streak = 0
    st.session_state.quiz_best_streak = 0
    st.session_state.quiz_points_total = 0
    st.session_state.quiz_correct = 0
    st.session_state.quiz_wrong = 0
    st.session_state.quiz_scored = {}

    st.session_state.build_log = []
    st.session_state.pending_quiz = None
    st.session_state.server_event = None


def apply_quiz_result(entry: dict, is_correct_ans: bool):
    eid = entry["id"]
    if st.session_state.quiz_scored.get(eid):
        return
    st.session_state.quiz_scored[eid] = True

    if is_correct_ans:
        st.session_state.score += QUIZ_POINTS_CORRECT
        st.session_state.quiz_points_total += QUIZ_POINTS_CORRECT
        st.session_state.quiz_correct += 1

        st.session_state.quiz_streak += 1
        st.session_state.quiz_best_streak = max(st.session_state.quiz_best_streak, st.session_state.quiz_streak)

        if st.session_state.quiz_streak % STREAK_BONUS_EVERY == 0:
            st.session_state.score += STREAK_BONUS_POINTS
            st.session_state.quiz_points_total += STREAK_BONUS_POINTS
            st.toast(f"🔥 Streak bonus! +{STREAK_BONUS_POINTS}", icon="🔥")
    else:
        st.session_state.score += QUIZ_POINTS_WRONG
        st.session_state.quiz_points_total += QUIZ_POINTS_WRONG
        st.session_state.quiz_wrong += 1
        st.session_state.quiz_streak = 0


def render_quiz(entry: dict):
    lesson = entry["lesson"]
    q, opts, correct_i = entry["question"]

    st.markdown(f"### {lesson['title']}")
    st.caption(f"Locked: **{entry['part_label']}** → **{entry['zone_name']}**")
    st.write(lesson["what"])
    st.write("**Gotchas:**")
    for g in lesson["gotchas"]:
        st.write(f"• {g}")

    choice = st.radio(q, opts, key=f"quiz_choice_{entry['id']}")

    scored = bool(st.session_state.quiz_scored.get(entry["id"], False))
    if st.button("Check answer", key=f"quiz_check_{entry['id']}", disabled=scored):
        is_correct_ans = (opts.index(choice) == correct_i)
        apply_quiz_result(entry, is_correct_ans)
        if is_correct_ans:
            st.success(f"✅ Correct! +{QUIZ_POINTS_CORRECT}")
        else:
            st.error(f"❌ Not quite. Correct: **{opts[correct_i]}** ({QUIZ_POINTS_WRONG})")
        st.rerun()

    if scored:
        st.info("Quiz already scored for this lesson ✅ (no farming).")
    else:
        st.caption(f"Rewards: +{QUIZ_POINTS_CORRECT} correct / {QUIZ_POINTS_WRONG} wrong")


def compute_grade() -> Tuple[str, Dict[str, float]]:
    """
    Grade uses time, wrong drops, quiz accuracy, and best streak.
    Produces a 0..100 score then maps to letter.
    """
    t = max(1, elapsed_s())
    wrong = st.session_state.wrong_drops
    qc = st.session_state.quiz_correct
    qw = st.session_state.quiz_wrong
    total_q = qc + qw
    acc = (qc / total_q) if total_q else 0.0
    best_streak = st.session_state.quiz_best_streak

    # Time score: 0..35 points (fast is better)
    # ~2 minutes => near max, ~8 minutes => low
    time_score = max(0.0, 35.0 * (1.0 - min(1.0, (t - 120) / 360)))

    # Accuracy score: 0..35
    acc_score = 35.0 * acc

    # Streak score: 0..20 (cap at 10)
    streak_score = 20.0 * min(1.0, best_streak / 10.0)

    # Penalty: wrong drops 0..20
    penalty = min(20.0, wrong * 2.0)

    raw = time_score + acc_score + streak_score - penalty
    score100 = max(0.0, min(100.0, raw))

    if score100 >= 95: grade = "A+"
    elif score100 >= 90: grade = "A"
    elif score100 >= 80: grade = "B"
    elif score100 >= 70: grade = "C"
    elif score100 >= 60: grade = "D"
    else: grade = "F"

    return grade, {
        "score100": score100,
        "time_score": time_score,
        "acc_score": acc_score,
        "streak_score": streak_score,
        "penalty": penalty,
        "accuracy": acc,
    }


def apply_drag_event(ev: dict):
    """
    Process drag-end from JS:
    - update pos
    - if near zone -> snap to center (server authoritative)
    - if correct -> award points and maybe lock
    - create quiz event on lock (randomized question)
    - set server_event for JS (snap animation + pulse + sound)
    """
    st.session_state.server_event = None

    if not ev or ev.get("type") != "drag":
        return

    pid = ev["id"]
    x = float(ev["x"])
    y = float(ev["y"])

    parts: List[Part] = st.session_state.parts
    p = next((p for p in parts if p.id == pid), None)
    if p is None or p.locked:
        return

    # raw move
    p.x, p.y = x, y

    zkey = find_nearest_zone(x, y)
    if not zkey:
        st.session_state.last_msg = f"Moved: {p.label}"
        return

    # zone occupied by a locked part?
    occupied = any((q.locked and q.locked_zone == zkey) for q in parts)
    if occupied:
        st.session_state.last_msg = f"Zone occupied: {ZMAP[zkey].display_name}"
        st.session_state.server_event = {"type": "wrong"}
        st.session_state.wrong_drops += 1
        return

    # authoritative snap to center
    zx, zy = ZMAP[zkey].xy
    p.x, p.y = zx, zy
    st.session_state.server_event = {"type": "snap", "part_id": p.id, "x": zx, "y": zy}

    if is_correct(p.kind, zkey):
        st.session_state.score += PLACEMENT_POINTS_CORRECT
        st.session_state.correct_snaps += 1
        st.session_state.last_msg = f"✅ Snapped: {p.label} → {ZMAP[zkey].display_name} (+{PLACEMENT_POINTS_CORRECT})"

        # lock if enabled
        if st.session_state.lock_on:
            p.locked = True
            p.locked_zone = zkey
            st.session_state.score += 15  # lock bonus

            lesson = QUIZ_BANK.get(p.kind)
            if lesson:
                # Pick a question at lock-time and store it in the entry (prevents rerun changing question)
                q = lesson["questions"][int(time.time() * 1000) % len(lesson["questions"])]

                entry = {
                    "id": make_event_id(p.id, zkey),
                    "ts": time.time(),
                    "part_id": p.id,
                    "part_label": p.label,
                    "kind": p.kind,
                    "zone_key": zkey,
                    "zone_name": ZMAP[zkey].display_name,
                    "lesson": lesson,
                    "question": q,
                }
                st.session_state.build_log.append(entry)
                st.session_state.pending_quiz = entry

            st.session_state.server_event = {"type": "lock", "part_id": p.id, "zone_key": zkey}
            st.toast(f"🔒 Locked: {QUIZ_BANK.get(p.kind, {}).get('title', p.label)} — quiz unlocked", icon="🔒")
        else:
            st.session_state.server_event = {"type": "correct", "zone_key": zkey}
    else:
        st.session_state.score += PLACEMENT_POINTS_WRONG
        st.session_state.wrong_drops += 1
        st.session_state.last_msg = f"❌ Wrong zone: {p.label} near {ZMAP[zkey].display_name} ({PLACEMENT_POINTS_WRONG})"
        st.session_state.server_event = {"type": "wrong", "zone_key": zkey}


def is_win(parts: List[Part]) -> bool:
    return all(p.locked for p in parts)


# ============================
# App UI
# ============================
st.set_page_config(page_title="Drone Assembly Trainer", layout="wide")
ensure_state()

st.title("🧩 Drone Assembly Trainer — Drag Anywhere (All Features)")
st.markdown('<div class="hud">SYSTEM: DRONE-ASSEMBLY // MODE: TRAINING // THEME: DIGITAL-GREEN</div>', unsafe_allow_html=True)
st.caption("Drag parts anywhere. Drop near a zone to snap (animated). Correct locks unlock micro-lessons + randomized quizzes.")

with st.sidebar:
    st.subheader("Controls")
    st.session_state.show_hints = st.toggle("Show hint rings", value=st.session_state.show_hints)
    st.session_state.show_zone_labels = st.toggle("Show zone labels", value=st.session_state.show_zone_labels)
    st.session_state.lock_on = st.toggle("Lock correct snaps", value=st.session_state.lock_on)
    st.session_state.sound_on = st.toggle("Sound effects", value=st.session_state.sound_on)

    if st.button("Reset"):
        reset_all()
        st.rerun()

# HUD metrics
hudL, hudR = st.columns([0.70, 0.30], gap="large")
with hudR:
    grade, breakdown = compute_grade()

    st.metric("Score", st.session_state.score)
    st.metric("Time (s)", elapsed_s())
    st.metric("Grade", grade)
    st.metric("Wrong Drops", st.session_state.wrong_drops)
    st.metric("Quiz Streak", st.session_state.quiz_streak)
    st.metric("Best Streak", st.session_state.quiz_best_streak)
    st.metric("Quiz Points", st.session_state.quiz_points_total)

    st.info(st.session_state.last_msg)

    st.write("**Streak meter**")
    st.progress(min(1.0, st.session_state.quiz_streak / 10.0))
    st.caption(f"Every {STREAK_BONUS_EVERY} correct answers: **+{STREAK_BONUS_POINTS} bonus**")

    st.write("**Mission grade breakdown**")
    st.caption(
        f"Score100: {breakdown['score100']:.1f} | "
        f"Time: {breakdown['time_score']:.1f} | "
        f"Accuracy: {breakdown['acc_score']:.1f} | "
        f"Streak: {breakdown['streak_score']:.1f} | "
        f"Penalty: -{breakdown['penalty']:.1f}"
    )

# Canvas (responsive sizing happens inside JS via container width)
ev = _DRONE_CANVAS(
    key="drone_canvas",
    parts=serialize_parts(st.session_state.parts),
    zones=serialize_zones(),
    show_hints=st.session_state.show_hints,
    show_zone_labels=st.session_state.show_zone_labels,
    zone_radius_norm=ZONE_RADIUS_NORM,
    board_aspect=1100 / 680,
    hud_line="DRONE ASSEMBLY // DRAG ANYWHERE // DROP NEAR ZONES TO SNAP",
    sound_on=st.session_state.sound_on,
    server_event=st.session_state.server_event,
)

apply_drag_event(ev)

# Win state
parts: List[Part] = st.session_state.parts
if is_win(parts):
    st.success("✅ Perfect build! All parts locked.")
    st.balloons()
    # signal win sfx
    st.session_state.server_event = {"type": "win"}

# Auto-open quiz dialog
pending = st.session_state.pending_quiz
if pending:
    with st.dialog(f"📘 Mini Lesson Quiz: {pending['lesson']['title']}"):
        render_quiz(pending)
        st.divider()
        if st.button("Close lesson"):
            st.session_state.pending_quiz = None
            st.rerun()

# Lesson library
st.divider()
st.subheader("📚 Lesson Library (unlocked by locking parts)")

if not st.session_state.build_log:
    st.info("Lock a correct part to unlock micro-lessons.")
else:
    for i, entry in enumerate(reversed(st.session_state.build_log), start=1):
        title = entry["lesson"]["title"]
        with st.expander(f"{i}. {title} — {entry['part_label']} @ {entry['zone_name']}"):
            render_quiz(entry)
