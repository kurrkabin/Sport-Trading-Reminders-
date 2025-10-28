import json
import uuid
from datetime import datetime, date, time, timedelta, timezone
from pathlib import Path
import base64
import streamlit as st
from streamlit import runtime

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

# Short beep (44.1kHz mono PCM WAV) ~100ms, inlined as base64 to avoid extra files
BEEP_WAV_BASE64 = (
    "UklGRsQAAABXQVZFZm10IBAAAAABAAEAESsAACJWAAACABAAZGF0YcAAAAAAAP8AAP8AAP8AAP8A"
    "AP8AAP8AAP8AAP8AAP4AAP8AAP4AAP8AAP4AAP8AAP8AAP8AAP8AAP4AAP8AAP8AAP4AAP8AAP8A"
    "AP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8A"  # (trimmed-ish simple tone)
)

# --------------------------- Helpers ---------------------------
def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()

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
    if "played_this_cycle" not in st.session_state:
        st.session_state.played_this_cycle = False

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

def snooze_task(task_id: str, minutes: int = 2):
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

def play_beep():
    # Use HTML audio tag with autoplay to guarantee playback when tab is focused
    audio_bytes = base64.b64decode(BEEP_WAV_BASE64)
    b64 = base64.b64encode(audio_bytes).decode("ascii")
    beep_html = f"""
        <audio autoplay>
            <source src="data:audio/wav;base64,{b64}" type="audio/wav">
        </audio>
    """
    st.components.v1.html(beep_html, height=0)

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

# --------------------------- App ---------------------------
ensure_state()

st.title("⏰ Sport Trading Reminders (UTC)")
st.caption("Everything here runs in **UTC**. Keep this tab open; it will auto-refresh and beep on due items.")

# Auto-refresh every 10 seconds so due items trigger without clicks
if hasattr(st, "autorefresh"):
    st.autorefresh(interval=10_000, key="auto_ref")
else:
    try:
        from streamlit_autorefresh import st_autorefresh  # fallback if older Streamlit
        st_autorefresh(interval=10_000, key="auto_ref_fallback")
    except Exception:
        pass  # worst case: manual refresh button below

# Header info
col_a, col_b, col_c = st.columns([1, 1, 2])
with col_a:
    st.metric("Current UTC time", now_utc().strftime("%H:%M:%S"))
with col_b:
    st.write("")
    st.button("Manual refresh", on_click=lambda: None, help="If auto-refresh is unavailable, use this.")
with col_c:
    pending_count = sum(1 for t in st.session_state.tasks if not t["done"])
    due_count = sum(1 for t in st.session_state.tasks if (not t["done"]) and (now_utc() >= parse_iso(t["when_utc"])))
    st.write(f"**Pending:** {pending_count} • **Due:** {due_count}")

st.markdown("---")

# Adders per sport
st.subheader("Add reminders (UTC)")
today_utc = now_utc().date()
for sport in SPORTS:
    with st.expander(f"➕ {sport}", expanded=False):
        c1, c2, c3, c4 = st.columns([1.0, 1.0, 3.0, 1.0])
        with c1:
            d = st.date_input(f"Date (UTC) – {sport}", value=today_utc, key=f"{sport}_date")
        with c2:
            tm = st.time_input(f"Time (UTC) – {sport}", value=time(0, 0), key=f"{sport}_time")
        with c3:
            txt = st.text_input(f"Free text – {sport}", placeholder="e.g., Freeze BBL MKT 10m pre, Heat vs Sixers", key=f"{sport}_text")
        with c4:
            if st.button("Add", key=f"{sport}_add"):
                if txt.strip():
                    # Combine date & time as UTC-aware datetime
                    dt_utc = datetime.combine(d, tm).replace(tzinfo=timezone.utc)
                    add_task(sport, txt, dt_utc)
                    st.success(f"Added for {sport} at {format_dt(dt_utc)}")
                else:
                    st.warning("Please enter some text.")

st.markdown("---")

# Live boards
nowt = now_utc()
tasks_sorted = sorted(st.session_state.tasks, key=lambda t: (parse_iso(t["when_utc"]), t["sport"]))

due_tasks = [t for t in tasks_sorted if (not t["done"]) and nowt >= parse_iso(t["when_utc"])]
upcoming_tasks = [t for t in tasks_sorted if (not t["done"]) and nowt < parse_iso(t["when_utc"])]
done_tasks = [t for t in tasks_sorted if t["done"]]

# Trigger beep exactly once per refresh cycle if there are newly-due tasks that haven't been alerted
newly_due = [t for t in due_tasks if not t.get("alerted", False)]
if newly_due:
    # Mark them alerted and save, then play beep
    for t in newly_due:
        t["alerted"] = True
    save_tasks(st.session_state.tasks)
    play_beep()
    st.toast("🔔 Reminder due now!", icon="🔔")

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
                st.button("⏱️ Snooze +2m", key=f"snooze_{t['id']}", on_click=snooze_task, args=(t["id"], 2))
            with c3:
                st.button("🗑️ Delete", key=f"del_{t['id']}", on_click=delete_task, args=(t["id"],))

st.subheader("⏳ Upcoming (today & future, UTC)")
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
                st.button("⏱️ Snooze +2m", key=f"usnooze_{t['id']}", on_click=snooze_task, args=(t["id"], 2))
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
st.caption("Tip: keep this tab visible. If auto-refresh is disabled on your Streamlit version, click **Manual refresh** occasionally.")
