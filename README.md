# Sport Trading Reminders (UTC)

A tiny Streamlit app for desk-side reminders (beep + visual) tied to **UTC** times, organized by sport.

## Features
- Per-sport quick add: **Date (UTC)** + **Time (UTC)** + **Free text**
- Auto-refresh (every 10s) and **beep** when an item becomes **Due**
- Inline controls: ✅ Mark done • ⏱️ Snooze +2m • 🗑️ Delete
- Boards: **Due now**, **Upcoming**, and **Completed**
- Data persistence to `tasks.json` in the app folder

> No Slack or external services. Keep the tab open and you’ll hear a short beep when something hits **Due**.

## Install & Run
```bash
# 1) Clone your repo, then:
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt

# 2) Launch
streamlit run app.py
