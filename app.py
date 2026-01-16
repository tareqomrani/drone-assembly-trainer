import base64
import io
import math
import struct
import time
import wave
from dataclasses import dataclass
from typing import Dict, Tuple, List, Set, Optional

import numpy as np
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from streamlit_sortables import sort_items
import streamlit.components.v1 as components


# ----------------------------
# Data model
# ----------------------------
@dataclass(frozen=True)
class Zone:
    key: str
    display_name: str
    xy: Tuple[float, float]   # normalized (0..1)


ASSET_PATH = "assets/parts_of_drone.jpg"


# ----------------------------
# Digital-Green Tactical HUD Theme (CSS)
# ----------------------------
components.html("""
<style>
:root{
  --bg:#070b08; --panel:#0c1310; --border:#1a2a22;
  --green:#00ff88; --green-dim:#1f3b2c; --green-glow:rgba(0,255,136,.55);
  --blue:#44aaff; --amber:#ffaa44; --red:#ff4466;
  --text:#e8fff3; --text-muted:#9fdcc0;
  --mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

/* Global */
html, body, [data-testid="stApp"] { background: var(--bg); color: var(--text); font-family: var(--mono); }
h1,h2,h3,h4 { color: var(--green); letter-spacing:.04em; font-family: var(--mono); }
p,span,li,label { color: var(--text); font-family: var(--mono); }
small,.stCaption { color: var(--text-muted); font-family: var(--mono); }

/* Panels */
section[data-testid="stSidebar"],
div[data-testid="stContainer"],
div[data-testid="stExpander"]{
  background: var(--panel) !important;
  border: 1px solid var(--border);
  border-radius: 12px;
}

/* Buttons */
button[kind="primary"]{
  background: linear-gradient(180deg,#00ff88,#00cc6a);
  color:#002b18; border:none;
  box-shadow: 0 0 16px var(--green-glow);
  font-family: var(--mono);
}
button{
  background: var(--panel);
  color: var(--green);
  border: 1px solid var(--green-dim);
  font-family: var(--mono);
}

/* Progress bars */
div[role="progressbar"] > div{
  background: linear-gradient(90deg,#00ff88,#44ffbb);
  box-shadow: 0 0 10px var(--green-glow);
}

/* Metrics */
[data-testid="stMetricValue"]{ color: var(--green); font-weight: 800; font-family: var(--mono); }
[data-testid="stMetricLabel"]{ color: var(--text-muted); font-family: var(--mono); }

/* Toasts + alerts */
div[data-testid="stToast"]{
  background:#0f2018 !important;
  border-left:4px solid var(--green);
  color: var(--text);
  font-family: var(--mono);
}
div.stAlert-error{ background: rgba(255,68,102,.12); border-left:4px solid var(--red); }
div.stAlert-warning{ background: rgba(255,170,68,.15); border-left:4px solid var(--amber); }

/* LOCKED badge */
.locked-badge{
  display:inline-block; padding:2px 10px; border-radius:999px;
  background: var(--green-dim);
  color: var(--green);
  border:1px solid var(--green);
  box-shadow: 0 0 10px var(--green-glow);
  font-size: 12px;
  margin-left: 6px;
}

/* Shake (wrong placement) */
@keyframes shake {
  0% { transform: translateX(0); }
  25% { transform: translateX(-6px); }
  50% { transform: translateX(6px); }
  75% { transform: translateX(-6px); }
  100% { transform: translateX(0); }
}
.shake { animation: shake 0.22s ease-in-out 0s 2; }

/* Pulse animation (newly locked) */
@keyframes greenPulse{
  0%{ box-shadow:0 0 0 rgba(0,255,136,0); transform: scale(1.0); }
  35%{ box-shadow:0 0 18px var(--green-glow); transform: scale(1.03); }
  100%{ box-shadow:0 0 0 rgba(0,255,136,0); transform: scale(1.0); }
}
.pulse { animation: greenPulse .55s ease-out 1; }

/* HUD label */
.hud { color: var(--text-muted); letter-spacing: .08em; text-transform: uppercase; font-size: 12px; }
</style>
""", height=0)


# ----------------------------
# Threat-style SFX pack (replaces beep/buzz)
# ----------------------------
def wav_from_samples(x: np.ndarray, sr: int = 22050) -> bytes:
    x = np.clip(x, -1, 1)
    pcm = (x * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    return buf.getvalue()

def env(n, sr, attack=0.003, decay=0.08):
    t = np.arange(n) / sr
    a = np.clip(t / max(attack, 1e-6), 0, 1)
    d = np.exp(-t / max(decay, 1e-6))
    return a * d

def soft_click(sr=22050, dur=0.045):
    n = int(sr * dur)
    noise = (np.random.randn(n) * 0.25).astype(np.float32)
    e = env(n, sr, attack=0.001, decay=0.03)
    smooth = np.convolve(noise, np.ones(12)/12, mode="same")
    x = (noise - smooth) * e
    return wav_from_samples(x, sr)

def confirm_chime(sr=22050, dur=0.18):
    n = int(sr * dur)
    t = np.arange(n) / sr
    e = env(n, sr, attack=0.004, decay=0.12)
    x = 0.18*np.sin(2*np.pi*740*t) + 0.12*np.sin(2*np.pi*980*t)
    return wav_from_samples((x * e).astype(np.float32), sr)

def error_thud(sr=22050, dur=0.16):
    n = int(sr * dur)
    t = np.arange(n) / sr
    e = env(n, sr, attack=0.002, decay=0.08)
    x = 0.30*np.sin(2*np.pi*90*t) + 0.08*np.sin(2*np.pi*60*t)
    return wav_from_samples((x * e).astype(np.float32), sr)

def win_sweep(sr=22050, dur=0.55):
    n = int(sr * dur)
    t = np.arange(n) / sr
    e = env(n, sr, attack=0.01, decay=0.35)
    f0, f1 = 320, 1100
    freq = f0 + (f1 - f0) * (t / t.max())
    phase = 2*np.pi*np.cumsum(freq)/sr
    x = 0.22*np.sin(phase) + 0.10*np.sin(2*phase)
    return wav_from_samples((x * e).astype(np.float32), sr)

SFX = {
    "drag": soft_click(),
    "correct": confirm_chime(),
    "wrong": error_thud(),
    "win": win_sweep(),
}

def play_sound(wav_bytes: bytes):
    b64 = base64.b64encode(wav_bytes).decode("utf-8")
    components.html(
        f"""
        <audio autoplay>
          <source src="data:audio/wav;base64,{b64}" type="audio/wav">
        </audio>
        """,
        height=0
    )


def confetti_burst():
    components.html(
        """
        <style>
        .confetti {
          position: fixed; top: -10px; left: 50%;
          width: 10px; height: 10px; opacity: 0.9;
          animation: fall 1.1s linear forwards;
        }
        @keyframes fall {
          0% { transform: translateX(0px) translateY(0px) rotate(0deg); }
          100% { transform: translateX(var(--dx)) translateY(85vh) rotate(720deg); opacity: 0.0; }
        }
        </style>
        <div class="confetti" style="background:#00ff88; --dx:-140px;"></div>
        <div class="confetti" style="background:#44aaff; --dx:-70px;"></div>
        <div class="confetti" style="background:#ffaa44; --dx:45px;"></div>
        <div class="confetti" style="background:#ff4466; --dx:120px;"></div>
        """,
        height=0
    )


# ----------------------------
# Parts (x4 props/motors/ESCs)
# ----------------------------
PART_CARDS: List[str] = (
    [f"Propeller {i}" for i in range(1, 5)]
    + [f"Motor {i}" for i in range(1, 5)]
    + [f"ESC {i}" for i in range(1, 5)]
    + [
        "Power Distribution Panel",
        "Flight Controller",
        "Control Receiver",
        "FPV Transmitter",
        "Antenna",
        "FPV Camera",
    ]
)


# ----------------------------
# Zones (tweak xy to match your image)
# ----------------------------
ZONES: List[Zone] = [
    # Props (4)
    Zone("z_prop_tl", "Propeller (Top-Left)", (0.16, 0.27)),
    Zone("z_prop_tr", "Propeller (Top-Right)", (0.86, 0.27)),
    Zone("z_prop_bl", "Propeller (Bottom-Left)", (0.19, 0.64)),
    Zone("z_prop_br", "Propeller (Bottom-Right)", (0.83, 0.64)),

    # Motors (4)
    Zone("z_motor_tl", "Motor (Top-Left)", (0.19, 0.36)),
    Zone("z_motor_tr", "Motor (Top-Right)", (0.86, 0.36)),
    Zone("z_motor_bl", "Motor (Bottom-Left)", (0.22, 0.73)),
    Zone("z_motor_br", "Motor (Bottom-Right)", (0.81, 0.73)),

    # ESCs (4)
    Zone("z_esc_tl", "ESC (Top-Left Arm)", (0.31, 0.42)),
    Zone("z_esc_tr", "ESC (Top-Right Arm)", (0.70, 0.42)),
    Zone("z_esc_bl", "ESC (Bottom-Left Arm)", (0.33, 0.69)),
    Zone("z_esc_br", "ESC (Bottom-Right Arm)", (0.69, 0.69)),

    # Core electronics
    Zone("z_receiver", "Control Receiver", (0.43, 0.33)),
    Zone("z_tx", "FPV Transmitter", (0.60, 0.34)),
    Zone("z_antenna", "Antenna", (0.52, 0.16)),
    Zone("z_pdb", "Power Distribution Panel", (0.53, 0.49)),
    Zone("z_fc", "Flight Controller", (0.50, 0.60)),
    Zone("z_camera", "FPV Camera", (0.50, 0.82)),
]
ZONES_MAP: Dict[str, Zone] = {z.key: z for z in ZONES}


# ----------------------------
# Correctness rules
# ----------------------------
def is_prop(part: str) -> bool: return part.startswith("Propeller ")
def is_motor(part: str) -> bool: return part.startswith("Motor ")
def is_esc(part: str) -> bool: return part.startswith("ESC ")

PROP_ZONES = ("z_prop_tl", "z_prop_tr", "z_prop_bl", "z_prop_br")
MOTOR_ZONES = ("z_motor_tl", "z_motor_tr", "z_motor_bl", "z_motor_br")
ESC_ZONES = ("z_esc_tl", "z_esc_tr", "z_esc_bl", "z_esc_br")

CORRECT_ZONE_FOR: Dict[str, Tuple[str, ...]] = {}
for p in PART_CARDS:
    if is_prop(p):
        CORRECT_ZONE_FOR[p] = PROP_ZONES
    elif is_motor(p):
        CORRECT_ZONE_FOR[p] = MOTOR_ZONES
    elif is_esc(p):
        CORRECT_ZONE_FOR[p] = ESC_ZONES
    elif p == "Power Distribution Panel":
        CORRECT_ZONE_FOR[p] = ("z_pdb",)
    elif p == "Flight Controller":
        CORRECT_ZONE_FOR[p] = ("z_fc",)
    elif p == "Control Receiver":
        CORRECT_ZONE_FOR[p] = ("z_receiver",)
    elif p == "FPV Transmitter":
        CORRECT_ZONE_FOR[p] = ("z_tx",)
    elif p == "Antenna":
        CORRECT_ZONE_FOR[p] = ("z_antenna",)
    elif p == "FPV Camera":
        CORRECT_ZONE_FOR[p] = ("z_camera",)
    else:
        CORRECT_ZONE_FOR[p] = tuple()


# ----------------------------
# Mini lessons + quiz scoring
# ----------------------------
PART_LESSONS = {
    "Propeller": {
        "title": "Propeller",
        "what": "Generates thrust by accelerating air. Size/pitch affects efficiency, speed, and current draw.",
        "gotchas": [
            "CW vs CCW orientation must match motor direction.",
            "Too much pitch/diameter can overdraw current and overheat motor/ESC."
        ],
        "check": ("If prop pitch increases (all else equal), motor load generally…",
                  ["Increases", "Decreases", "Stays identical"], 0)
    },
    "Motor": {
        "title": "Brushless Motor",
        "what": "Spins the prop. Kv (~RPM per volt) influences speed vs torque behavior.",
        "gotchas": [
            "High Kv often suits smaller props (higher RPM, lower torque).",
            "Overheating usually means too much load or poor cooling."
        ],
        "check": ("Higher Kv generally means…",
                  ["More RPM per volt", "More torque per amp", "Lower RPM per volt"], 0)
    },
    "ESC": {
        "title": "ESC (Electronic Speed Controller)",
        "what": "Turns battery DC into timed 3-phase power for the motor; controls speed via PWM/commutation.",
        "gotchas": [
            "ESC rating must exceed peak current draw (with margin).",
            "Signal protocol (PWM/DShot) must match the flight controller."
        ],
        "check": ("An undersized ESC most commonly fails due to…",
                  ["Overcurrent/overheating", "Too much thrust", "Low battery voltage"], 0)
    },
    "Power Distribution Panel": {
        "title": "Power Distribution Panel (PDB)",
        "what": "Splits battery power to ESCs and accessories; often includes filtering or a BEC.",
        "gotchas": [
            "Bad solder joints create voltage drop + heat.",
            "Filtering reduces video noise and FC interference."
        ],
        "check": ("A PDB is mainly used to…",
                  ["Distribute battery power", "Control yaw", "Transmit FPV video"], 0)
    },
    "Flight Controller": {
        "title": "Flight Controller",
        "what": "The drone’s brain—reads sensors, runs stabilization loops, and commands the ESCs.",
        "gotchas": [
            "Wrong orientation/calibration can cause instant flip on arm.",
            "Vibration isolation improves gyro signal quality."
        ],
        "check": ("The FC outputs commands primarily to…",
                  ["ESCs", "Props directly", "Battery cells"], 0)
    },
    "Control Receiver": {
        "title": "Control Receiver",
        "what": "Receives pilot/control-link commands and feeds them to the flight controller.",
        "gotchas": [
            "Antenna placement matters—avoid carbon shadowing and noisy wires.",
            "Configure failsafe behavior to prevent flyaways."
        ],
        "check": ("Failsafe defines behavior when…",
                  ["Signal is lost", "Battery is full", "Props are removed"], 0)
    },
    "FPV Transmitter": {
        "title": "FPV Video Transmitter (VTX)",
        "what": "Sends the FPV camera feed to goggles/ground receiver. Higher power can mean more heat.",
        "gotchas": [
            "Never power a VTX without an antenna attached.",
            "Higher power can cause overheating and RF interference."
        ],
        "check": ("A VTX should not be powered without…",
                  ["An antenna", "A flight controller", "A motor"], 0)
    },
    "Antenna": {
        "title": "Antenna",
        "what": "Radiates/receives RF for video or control. Polarization and placement strongly affect range.",
        "gotchas": [
            "Match polarization (RHCP with RHCP) for best performance.",
            "Avoid shielding by battery/carbon frame."
        ],
        "check": ("Mismatched polarization typically…",
                  ["Reduces signal", "Increases thrust", "Improves range"], 0)
    },
    "FPV Camera": {
        "title": "FPV Camera",
        "what": "Captures the live video feed. Latency + dynamic range matter a lot for flying.",
        "gotchas": [
            "Camera tilt affects perceived speed and handling.",
            "Power noise can cause rolling lines—use filtering if needed."
        ],
        "check": ("A higher camera tilt is generally used for…",
                  ["Faster forward flight", "Hover-only flight", "Lower RPM motors"], 0)
    },
}

# Bonus rules
QUIZ_POINTS_CORRECT = 15
QUIZ_POINTS_WRONG = -5
STREAK_BONUS_EVERY = 3
STREAK_BONUS_POINTS = 10


def lesson_key_for_part(part_name: str) -> str:
    if part_name.startswith("Propeller"):
        return "Propeller"
    if part_name.startswith("Motor"):
        return "Motor"
    if part_name.startswith("ESC"):
        return "ESC"
    return part_name


def ensure_build_log():
    if "build_log" not in st.session_state:
        st.session_state.build_log = []


def ensure_quiz_state():
    if "quiz_scored" not in st.session_state:
        st.session_state.quiz_scored = {}
    if "quiz_streak" not in st.session_state:
        st.session_state.quiz_streak = 0
    if "quiz_best_streak" not in st.session_state:
        st.session_state.quiz_best_streak = 0
    if "quiz_points_total" not in st.session_state:
        st.session_state.quiz_points_total = 0


def lesson_id(entry: dict) -> str:
    return entry.get("id", f"{entry.get('ts','')}_{entry.get('part','')}_{entry.get('zone','')}")


def add_build_log(entry: dict):
    ensure_build_log()
    st.session_state.build_log.append(entry)


def apply_quiz_result(entry: dict, is_correct: bool):
    ensure_quiz_state()
    lid = lesson_id(entry)
    if st.session_state.quiz_scored.get(lid):
        return

    st.session_state.quiz_scored[lid] = True

    if is_correct:
        st.session_state.score += QUIZ_POINTS_CORRECT
        st.session_state.quiz_points_total += QUIZ_POINTS_CORRECT
        st.session_state.quiz_streak += 1
        st.session_state.quiz_best_streak = max(st.session_state.quiz_best_streak, st.session_state.quiz_streak)

        if st.session_state.quiz_streak % STREAK_BONUS_EVERY == 0:
            st.session_state.score += STREAK_BONUS_POINTS
            st.session_state.quiz_points_total += STREAK_BONUS_POINTS
            st.toast(f"🔥 Streak bonus! +{STREAK_BONUS_POINTS}", icon="🔥")
    else:
        st.session_state.score += QUIZ_POINTS_WRONG
        st.session_state.quiz_points_total += QUIZ_POINTS_WRONG
        st.session_state.quiz_streak = 0


def render_lesson(entry: dict, key_prefix: str):
    ensure_quiz_state()
    lid = lesson_id(entry)
    scored = bool(st.session_state.quiz_scored.get(lid, False))

    st.markdown(f"### {entry['title']}")
    st.caption(f"Locked: **{entry['part']}** → **{entry['zone']}**")
    st.write(entry["what"])
    st.write("**Gotchas:**")
    for g in entry["gotchas"]:
        st.write(f"• {g}")

    q, opts, correct_i = entry["check"]
    choice = st.radio(q, opts, key=f"{key_prefix}_radio", horizontal=False)

    cols = st.columns([0.45, 0.55])
    with cols[0]:
        if st.button("Check answer", key=f"{key_prefix}_check", disabled=scored):
            is_correct = (opts.index(choice) == correct_i)
            apply_quiz_result(entry, is_correct)
            if is_correct:
                st.success(f"✅ Correct! +{QUIZ_POINTS_CORRECT}")
            else:
                st.error(f"❌ Not quite. Correct: **{opts[correct_i]}** ({QUIZ_POINTS_WRONG})")
            st.rerun()

    with cols[1]:
        if scored:
            st.info("Quiz already scored for this lesson ✅ (no farming).")
        else:
            st.caption(f"Rewards: +{QUIZ_POINTS_CORRECT} correct / {QUIZ_POINTS_WRONG} wrong")


# ----------------------------
# Board drawing + ISR scanlines
# ----------------------------
def load_board(path: str) -> Image.Image:
    return Image.open(path).convert("RGB")

def get_font():
    return ImageFont.load_default()

def apply_scanlines(img: Image.Image, spacing: int = 3, alpha: int = 24) -> Image.Image:
    img = img.convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    W, H = img.size
    for y in range(0, H, spacing):
        d.line((0, y, W, y), fill=(0, 0, 0, alpha), width=1)
    return Image.alpha_composite(img, overlay).convert("RGB")

def apply_vignette(img: Image.Image, strength: float = 0.28) -> Image.Image:
    img = img.convert("RGBA")
    W, H = img.size
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    steps = 18
    for i in range(steps):
        a = int(255 * strength * (i / steps) ** 2)
        d.rectangle((i, i, W - i, H - i), outline=(0, 0, 0, a), width=2)
    return Image.alpha_composite(img, overlay).convert("RGB")

def draw_board(board: Image.Image, placements: Dict[str, str], show_hints: bool, pulse_zone: Optional[str] = None) -> Image.Image:
    img = board.copy()
    W, H = img.size
    d = ImageDraw.Draw(img)
    font = get_font()

    # Hint rings (tactical green instead of bright blue)
    if show_hints:
        for z in ZONES:
            x, y = int(z.xy[0] * W), int(z.xy[1] * H)
            r = max(10, int(min(W, H) * 0.016))
            d.ellipse((x - r, y - r, x + r, y + r), outline=(0, 255, 136), width=3)

    for zone_key, part in placements.items():
        z = ZONES_MAP[zone_key]
        x, y = int(z.xy[0] * W), int(z.xy[1] * H)
        r = max(12, int(min(W, H) * 0.018))

        ok = zone_key in CORRECT_ZONE_FOR.get(part, tuple())
        fill = (40, 180, 90) if ok else (220, 70, 70)
        outline = (10, 80, 40) if ok else (120, 20, 20)
        d.ellipse((x - r, y - r, x + r, y + r), fill=fill, outline=outline, width=3)

        # Pulse ring (newly locked zone)
        if pulse_zone and zone_key == pulse_zone and ok:
            pr = r + 10
            d.ellipse((x - pr, y - pr, x + pr, y + pr), outline=(0, 255, 136), width=4)

        pad = 4
        tw, th = d.textbbox((0, 0), part, font=font)[2:]
        bx0, by0 = x + r + 6, y - th // 2 - pad
        bx1, by1 = bx0 + tw + 2 * pad, by0 + th + 2 * pad
        d.rounded_rectangle((bx0, by0, bx1, by1), radius=8, fill=(0, 0, 0))
        d.text((bx0 + pad, by0 + pad), part, fill=(255, 255, 255), font=font)

    return img


# ----------------------------
# Game logic helpers
# ----------------------------
def compute_placements(containers: Dict[str, list]) -> Dict[str, str]:
    placements = {}
    for z in ZONES:
        items = containers.get(z.key, [])
        if items:
            placements[z.key] = items[0]
    return placements

def evaluate(containers: Dict[str, list]) -> Tuple[Set[str], Set[str]]:
    placements = compute_placements(containers)
    correct_z, wrong_z = set(), set()
    for zone_key, part in placements.items():
        allowed = CORRECT_ZONE_FOR.get(part, tuple())
        if zone_key in allowed:
            correct_z.add(zone_key)
        else:
            wrong_z.add(zone_key)
    return correct_z, wrong_z

def enforce_one_card_per_zone(containers: Dict[str, list]):
    for z in ZONES:
        items = containers.get(z.key, [])
        if len(items) > 1:
            keep = [items[-1]]
            push_back = items[:-1]
            containers["parts_bin"].extend(push_back)
            containers[z.key] = keep

def snapback_wrong(containers: Dict[str, list]) -> bool:
    placements = compute_placements(containers)
    changed = False
    for zone_key, part in list(placements.items()):
        if zone_key not in CORRECT_ZONE_FOR.get(part, tuple()):
            containers[zone_key] = []
            containers["parts_bin"].append(part)
            changed = True
    return changed


# ----------------------------
# State
# ----------------------------
def reset_game():
    st.session_state.start_time = time.time()
    st.session_state.score = 0
    st.session_state.last_eval = {"correct": set(), "wrong": set()}
    st.session_state.locked_zones = set()
    st.session_state.did_win = False
    st.session_state.pending_lesson = None
    st.session_state.build_log = []
    st.session_state.quiz_scored = {}
    st.session_state.quiz_streak = 0
    st.session_state.quiz_best_streak = 0
    st.session_state.quiz_points_total = 0
    st.session_state.pulse_zone = None
    st.session_state.pulse_until = 0.0

    st.session_state.containers = {"parts_bin": PART_CARDS.copy()}
    for z in ZONES:
        st.session_state.containers[z.key] = []

def init_state():
    if "start_time" not in st.session_state:
        st.session_state.start_time = time.time()
    if "score" not in st.session_state:
        st.session_state.score = 0
    if "last_eval" not in st.session_state:
        st.session_state.last_eval = {"correct": set(), "wrong": set()}
    if "locked_zones" not in st.session_state:
        st.session_state.locked_zones = set()
    if "did_win" not in st.session_state:
        st.session_state.did_win = False
    if "pending_lesson" not in st.session_state:
        st.session_state.pending_lesson = None
    if "pulse_zone" not in st.session_state:
        st.session_state.pulse_zone = None
    if "pulse_until" not in st.session_state:
        st.session_state.pulse_until = 0.0
    ensure_build_log()
    ensure_quiz_state()
    if "containers" not in st.session_state:
        reset_game()

def elapsed_s() -> int:
    return int(time.time() - st.session_state.start_time)


# ----------------------------
# UI
# ----------------------------
st.set_page_config(page_title="Drone Assembly (Game)", layout="wide")
init_state()

st.title("🧩 Drone Assembly — Tactical HUD (Quiz Points + Streak)")
st.markdown('<div class="hud">SYSTEM: DRONE-ASSEMBLY // MODE: TRAINING // THEME: DIGITAL-GREEN</div>', unsafe_allow_html=True)

try:
    board = load_board(ASSET_PATH)
except Exception as e:
    st.error("Save your image as `assets/parts_of_drone.jpg`.\n\n" + f"Error: {e}")
    st.stop()

# Top stats
top_l, top_r = st.columns([0.62, 0.38], gap="large")

with top_r:
    st.metric("Score", st.session_state.score)
    st.metric("Time (s)", elapsed_s())
    st.metric("Quiz Streak", st.session_state.quiz_streak)
    st.metric("Best Streak", st.session_state.quiz_best_streak)
    st.metric("Quiz Points", st.session_state.quiz_points_total)

    show_hints = st.toggle("Show hint rings", value=True)
    sound_on = st.toggle("Sound effects", value=True)
    snapback_on = st.toggle("Auto snap-back wrong drops", value=True)
    lock_on = st.toggle("Lock correct placements", value=True)
    if st.button("🔄 Reset"):
        reset_game()
        st.rerun()

containers = st.session_state.containers
locked_zones = set(st.session_state.locked_zones)

st.caption("Drag cards from **Parts Bin** into **Drop Zones**. Correct locks unlock a mini-lesson quiz (with points).")

left, right = st.columns([0.33, 0.67], gap="large")

with left:
    st.subheader("Parts Bin")
    containers["parts_bin"] = sort_items(
        containers["parts_bin"],
        direction="vertical",
        key="parts_bin_sort_final2",
    )

with right:
    st.subheader("Drop Zones")
    zone_cols = st.columns(3, gap="medium")

    # clear pulse after short duration
    if st.session_state.pulse_until < time.time():
        st.session_state.pulse_zone = None

    for i, z in enumerate(ZONES):
        with zone_cols[i % 3]:
            locked = (z.key in locked_zones) and lock_on
            is_pulse = (st.session_state.get("pulse_zone") == z.key)
            badge = f'<span class="locked-badge {"pulse" if is_pulse else ""}">LOCKED</span>' if locked else ""
            st.markdown(f"**{z.display_name}** {badge}", unsafe_allow_html=True)

            if locked:
                items = containers.get(z.key, [])
                if items:
                    st.info(items[0])
                else:
                    st.warning("(locked but empty)")
            else:
                containers[z.key] = sort_items(
                    containers[z.key],
                    direction="vertical",
                    key=f"{z.key}_sort_final2",
                )

# Enforce one per zone
enforce_one_card_per_zone(containers)

# Snapback wrong drops
snapped = False
if snapback_on:
    snapped = snapback_wrong(containers)

# Evaluate
correct_zones, wrong_zones = evaluate(containers)

# Locking + detect NEW locks
new_locks: List[str] = []
if lock_on:
    for zkey in correct_zones:
        if containers.get(zkey):
            if zkey not in locked_zones:
                new_locks.append(zkey)
            locked_zones.add(zkey)
else:
    locked_zones = set()

# Score + SFX based on placement deltas
prev_correct = st.session_state.last_eval["correct"]
prev_wrong = st.session_state.last_eval["wrong"]

newly_correct = correct_zones - prev_correct
newly_wrong = wrong_zones - prev_wrong

st.session_state.score += 10 * len(newly_correct)
st.session_state.score -= 3 * len(newly_wrong)

if sound_on:
    if snapped or newly_wrong:
        play_sound(SFX["wrong"])
    elif newly_correct:
        play_sound(SFX["correct"])

st.session_state.last_eval = {"correct": set(correct_zones), "wrong": set(wrong_zones)}
st.session_state.locked_zones = set(locked_zones)
st.session_state.containers = containers

placements = compute_placements(containers)

# Pulse effects when a lock happens
if new_locks:
    st.session_state.pulse_zone = new_locks[-1]
    st.session_state.pulse_until = time.time() + 0.8

# Create pending lesson for the newest lock (one per run)
if new_locks:
    zkey = new_locks[-1]
    part = containers[zkey][0]
    lk = lesson_key_for_part(part)
    lesson = PART_LESSONS.get(lk)
    if lesson:
        entry = {
            "id": f"{int(time.time()*1000)}_{zkey}_{part}",
            "ts": time.time(),
            "part": part,
            "zone": ZONES_MAP[zkey].display_name,
            "lesson_key": lk,
            "title": lesson["title"],
            "what": lesson["what"],
            "gotchas": lesson["gotchas"],
            "check": lesson["check"],
        }
        add_build_log(entry)
        st.session_state.pending_lesson = entry
        st.toast(f"🔒 Locked: {lesson['title']} — quiz unlocked (+points)", icon="🔒")

# Board
with top_l:
    st.subheader("Build Board")
    overlay = draw_board(board, placements, show_hints=show_hints, pulse_zone=st.session_state.get("pulse_zone"))
    overlay = apply_scanlines(overlay, spacing=3, alpha=24)
    overlay = apply_vignette(overlay, strength=0.28)
    st.image(overlay, use_container_width=True)

# Progress + status
total_zones = len(ZONES)
placed_count = len(placements)
st.progress(placed_count / total_zones)
st.caption(f"Filled zones: {placed_count} / {total_zones}")

# Streak meter
st.write("**Knowledge streak meter**")
st.progress(min(1.0, st.session_state.quiz_streak / 10.0))
st.caption(f"Every {STREAK_BONUS_EVERY} correct answers in a row: **+{STREAK_BONUS_POINTS} streak bonus**")

if snapped:
    st.toast("↩️ Wrong drop snapped back to Parts Bin.", icon="↩️")

if wrong_zones:
    st.markdown('<div class="shake">', unsafe_allow_html=True)
    st.error(
        "Wrong placements detected in:\n\n"
        + "\n".join([f"- {ZONES_MAP[z].display_name}" for z in sorted(wrong_zones)])
    )
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.success("No incorrect placements right now.")

# Win
win = (placed_count == total_zones) and (not wrong_zones)
if win:
    if not st.session_state.did_win:
        st.session_state.did_win = True
        if sound_on:
            play_sound(SFX["win"])
        confetti_burst()
        st.balloons()
    st.success("✅ Perfect build! Drone assembled correctly.")
else:
    st.session_state.did_win = False


# ----------------------------
# Auto-opening lesson dialog
# ----------------------------
pending = st.session_state.pending_lesson
if pending:
    with st.dialog(f"📘 Mini Lesson Quiz: {pending['title']}"):
        render_lesson(pending, key_prefix=f"dlg_{pending['id']}")
        st.divider()
        if st.button("Close lesson"):
            st.session_state.pending_lesson = None
            st.rerun()


# ----------------------------
# Mini Lessons Library (revisit anytime)
# ----------------------------
st.divider()
st.subheader("📚 Mini Lessons Library (locked parts)")

if not st.session_state.build_log:
    st.info("Lock a part in correctly to unlock mini lessons.")
else:
    for idx, entry in enumerate(reversed(st.session_state.build_log)):
        with st.expander(f"{entry['title']} — {entry['part']}"):
            render_lesson(entry, key_prefix=f"lib_{entry['id']}_{idx}")
