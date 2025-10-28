import json
import uuid
from datetime import datetime, date, time, timedelta, timezone
from pathlib import Path
import streamlit as st

# --------------------------- Config ---------------------------
st.set_page_config(page_title="Sport Trading Reminders (UTC)", page_icon="⏰", layout="wide")

SPORTS = [
    "Cricket",
    "Darts",
    "Rugby Union",
    "Rugby League",
    "MotorSports",
    "Aussie Rules",
    "Boxing",
    "Snooker",
]

DATA_PATH = Path("tasks.json")

# Server-side background check cadence (ms). Keep at 5 minutes as requested.
AUTO_REFRESH_MS = 300_000

# --------------------------- Helpers ---------------------------
def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")

def parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s)

def load_tasks() -> list[dict]:
    if DATA_PATH.exists():
        try:
            return json.loads(DATA_PATH.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def save_tasks(tasks: list[dict]) -> None:
    DATA_PATH.write_text(json.dumps(tasks, indent=2), encoding="utf-8")

def ensure_state():
    if "tasks" not in st.session_state:
        st.session_state.tasks = load_tasks()
    if "sound_enabled" not in st.session_state:
        st.session_state.sound_enabled = False

def add_task(sport: str, txt: str, dt_utc: datetime):
    t = {
        "id": str(uuid.uuid4()),
        "sport": sport,
        "text": txt.strip(),
        "when_utc": iso(dt_utc),
        "created_utc": iso(now_utc()),
        "done": False,
        "alerted": False,
        "snoozed_minutes": 0,
    }
    st.session_state.tasks.append(t)
    save_tasks(st.session_state.tasks)

def snooze_task(task_id: str, minutes: int = 5):
    for t in st.session_state.tasks:
        if t["id"] == task_id:
            when = parse_iso(t["when_utc"])
            t["when_utc"] = iso(when + timedelta(minutes=minutes))
            t["alerted"] = False
            t["snoozed_minutes"] = t.get("snoozed_minutes", 0) + minutes
            break
    save_tasks(st.session_state.tasks)

def mark_done(task_id: str):
    for t in st.session_state.tasks:
        if t["id"] == task_id:
            t["done"] = True
            break
    save_tasks(st.session_state.tasks)

def delete_task(task_id: str):
    st.session_state.tasks = [t for t in st.session_state.tasks if t["id"] != task_id]
    save_tasks(st.session_state.tasks)

def format_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")

def due_status(t: dict, nowt: datetime) -> str:
    if t["done"]:
        return "✅ Done"
    when = parse_iso(t["when_utc"])
    if nowt >= when:
        return "🔔 Due"
    else:
        mins = int((when - nowt).total_seconds() // 60)
        return f"⏳ In {mins} min"

# --------------------------- UI: UTC live clock ---------------------------
def live_utc_clock():
    # Proper component so scripts always run
    st.components.v1.html(
        """
        <div style="display:flex;justify-content:flex-end;margin-bottom:.25rem">
          <div style="font:600 16px/1.2 system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
                      font-variant-numeric:tabular-nums;letter-spacing:.5px">
            <span style="opacity:.7;margin-right:.4rem;">UTC</span>
            <strong id="utc-time">--:--:--</strong>
          </div>
        </div>
        <script>
          function pad(n){return n.toString().padStart(2,'0');}
          function tick(){
            const d=new Date();
            const s=`${d.getUTCFullYear()}-${pad(d.getUTCMonth()+1)}-${pad(d.getUTCDate())} `+
                    `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}:${pad(d.getUTCSeconds())}`;
            const el=document.getElementById("utc-time");
            if(el) el.textContent=s;
          }
          tick(); setInterval(tick,1000);
        </script>
        """,
        height=28,
    )

# --------------------------- UI: Sound priming & alarm ---------------------------
def sound_enable_banner():
    """
    One-time button to grant audio permission and keep the audio context alive
    (auto-resume on visibility changes so background alarms work).
    """
    clicked = st.button("🔊 Enable sound (one-time)", help="Click once at the start of your shift.")
    if clicked:
        st.session_state.sound_enabled = True

    if st.session_state.sound_enabled:
        st.success("Sound enabled for background alarms.")
        st.components.v1.html(
            """
            <script>
              (function(){
                try {
                  const Ctor = window.AudioContext || window.webkitAudioContext;
                  const ctx = new Ctor();
                  // Keep-alive: resume periodically & on visibility change
                  function ensureResume(){
                    if (ctx.state === 'suspended') { ctx.resume(); }
                  }
                  ensureResume();
                  setInterval(ensureResume, 15000);
                  document.addEventListener('visibilitychange', ensureResume);
                  window._alarmCtx = ctx;
                } catch(e) { console.log('Audio init error', e); }
              })();
            </script>
            """,
            height=0,
        )

def play_long_alarm():
    """
    6-second pulsing dual-tone (880Hz + 660Hz) with tremolo—noticeable, even in background.
    Requires sound to be enabled earlier.
    """
    if not st.session_state.get("sound_enabled"):
        return
    st.components.v1.html(
        """
        <script>
          (function(){
            try {
              const Ctor = window.AudioContext || window.webkitAudioContext;
              const ctx = window._alarmCtx || new Ctor();
              if (ctx.state === 'suspended') { ctx.resume(); }

              const osc1 = ctx.createOscillator(); // 880 Hz
              const osc2 = ctx.createOscillator(); // 660 Hz
              const gain = ctx.createGain();       // master
              const trem = ctx.createOscillator(); // amplitude modulation
              const tremGain = ctx.createGain();

              osc1.type = 'square';
              osc2.type = 'square';
              osc1.frequency.value = 880;
              osc2.frequency.value = 660;

              gain.gain.setValueAtTime(0.0001, ctx.currentTime);

              // Tremolo ~6 Hz for "urgent" feel
              trem.frequency.value = 6;
              tremGain.gain.value = 0.5;
              trem.connect(tremGain);
              tremGain.connect(gain.gain);

              osc1.connect(gain);
              osc2.connect(gain);
              gain.connect(ctx.destination);

              // Fade in quickly, play 6 seconds, fade out
              const t0 = ctx.currentTime + 0.01;
              gain.gain.exponentialRampToValueAtTime(0.6, t0 + 0.05);

              osc1.start(t0);
              osc2.start(t0 + 0.02);
              trem.start(t0);

              const tEnd = t0 + 6.0;
              gain.gain.exponentialRampToValueAtTime(0.0001, tEnd - 0.1);
              osc1.stop(tEnd);
              osc2.stop(tEnd);
              trem.stop(tEnd);
            } catch(e) { console.log('Alarm error', e); }
          })();
        </script>
        """,
        height=0,
    )

# --------------------------- App ---------------------------
ensure_state()

st.title("⏰ Sport Trading Reminders (UTC)")

# Live UTC clock (always visible, 1s updates)
live_utc_clock()

# One-time sound enable (do this once at the start of your shift)
sound_enable_banner()

# Silent server-side auto-check every 5 minutes
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=AUTO_REFRESH_MS, key="auto_check_5m")
except Exception:
    pass

st.markdown("---")

# Add reminders
st.subheader("Add reminders (UTC)")
today_utc = now_utc().date()
for sport in SPORTS:
    with st.expander(f"➕ {sport}", expanded=False):
        c1, c2, c3, c4 = st.columns([1.0, 1.0, 2.2, 1.2])

        with c1:
            d = st.date_input(f"Date (UTC) – {sport}", value=today_utc, key=f"{sport}_date")
        with c2:
            tm = st.time_input(
                f"Time (UTC) – {sport}",
                value=time(0, 0),
                key=f"{sport}_time",
                step=timedelta(minutes=5),
            )
        with c3:
            txt = st.text_input(
                f"Action / note – {sport}",
                placeholder="e.g., goes live; freeze groups; freeze main market; settle score; trade live…",
                key=f"{sport}_text",
            )
        with c4:
            if st.button("Add", key=f"{sport}_add"):
                if txt.strip():
                    dt_utc = datetime.combine(d, tm).replace(tzinfo=timezone.utc)
                    add_task(sport, txt, dt_utc)
                    st.success(f"Added for {sport} at {format_dt(dt_utc)}")
                else:
                    st.warning("Please enter an action/note.")

st.markdown("---")

# Boards
nowt = now_utc()
tasks_sorted = sorted(st.session_state.tasks, key=lambda t: (parse_iso(t["when_utc"]), t["sport"]))
due_tasks = [t for t in tasks_sorted if (not t["done"]) and nowt >= parse_iso(t["when_utc"])]
upcoming_tasks = [t for t in tasks_sorted if (not t["done"]) and nowt < parse_iso(t["when_utc"])]
done_tasks = [t for t in tasks_sorted if t["done"]]

# Play long alarm for newly-due items (only once per item)
newly_due = [t for t in due_tasks if not t.get("alerted", False)]
if newly_due:
    for t in newly_due:
        t["alerted"] = True
    save_tasks(st.session_state.tasks)
    play_long_alarm()
    st.toast(f"🔔 {len(newly_due)} reminder(s) due now", icon="🔔")

st.subheader("🔔 Due now")
if not due_tasks:
    st.info("No due reminders at the moment.")
else:
    for t in due_tasks:
        with st.container(border=True):
            when = parse_iso(t["when_utc"])
            st.markdown(f"**{t['sport']}** — {t['text']}")
            st.caption(f"Scheduled: {format_dt(when)}")
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                st.button("✅ Mark done", key=f"done_{t['id']}", on_click=mark_done, args=(t["id"],))
            with c2:
                st.button("⏱️ Snooze +5m", key=f"snooze_{t['id']}", on_click=snooze_task, args=(t["id"], 5))
            with c3:
                st.button("🗑️ Delete", key=f"del_{t['id']}", on_click=delete_task, args=(t["id"],))

st.subheader("⏳ Upcoming (UTC)")
if not upcoming_tasks:
    st.info("Nothing upcoming.")
else:
    for t in upcoming_tasks:
        with st.container(border=True):
            when = parse_iso(t["when_utc"])
            st.markdown(f"**{t['sport']}** — {t['text']}")
            st.caption(f"Scheduled: {format_dt(when)} • {due_status(t, nowt)} • Snoozed: {t.get('snoozed_minutes',0)} min")
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                st.button("✅ Mark done", key=f"udone_{t['id']}", on_click=mark_done, args=(t["id"],))
            with c2:
                st.button("⏱️ Snooze +5m", key=f"usnooze_{t['id']}", on_click=snooze_task, args=(t["id"], 5))
            with c3:
                st.button("🗑️ Delete", key=f"udel_{t['id']}", on_click=delete_task, args=(t["id"],))

with st.expander("✔️ Completed"):
    if not done_tasks:
        st.caption("No completed items yet.")
    else:
        for t in done_tasks:
            when = parse_iso(t["when_utc"])
            st.write(f"• **{t['sport']}** — {t['text']}  _(scheduled {format_dt(when)})_")

st.markdown("---")
st.caption(
    "For background alarms: click “Enable sound” once, keep this tab unmuted, and exclude it from any tab-sleep features."
)
