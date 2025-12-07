import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime
import json
import base64
import os

# -----------------------
# Simple Streamlit app for a French class
# Features:
# - Teacher (simple auth) can upload files (pdf, docx, images, audio), add words, notes, and tags
# - Student can browse, preview (images/audio), download files, and 'mark practiced'
# - Metadata stored in local SQLite DB (or a lightweight JSON fallback)
# - Designed as a single-file app ready to push to GitHub and deploy on Streamlit Cloud
# -----------------------

# ---------- Configuration (change before deploy) ----------
CONFIG = {
    "teacher_username": "teacher",
    "teacher_password": "changeme",  # change this before deploying
    "db_path": "data/french_class.db",
    "uploads_dir": "data/uploads"
}

# ---------- Ensure folders exist ----------
Path("data").mkdir(exist_ok=True)
Path(CONFIG["uploads_dir"]).mkdir(parents=True, exist_ok=True)

# ---------- Database helpers ----------

def get_conn():
    conn = sqlite3.connect(CONFIG["db_path"], check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY,
            title TEXT,
            description TEXT,
            filename TEXT,
            uploaded_by TEXT,
            role TEXT,
            tags TEXT,
            level TEXT,
            added_at TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY,
            word TEXT,
            meaning TEXT,
            sentence TEXT,
            added_by TEXT,
            added_at TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS activity (
            id INTEGER PRIMARY KEY,
            resource_id INTEGER,
            username TEXT,
            action TEXT,
            action_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()


init_db()

# ---------- Utility functions ----------

def save_file(uploaded_file):
    # Save file to uploads dir and return filename
    filename = uploaded_file.name
    safe_name = f"{int(datetime.utcnow().timestamp())}_{filename}"
    out_path = Path(CONFIG["uploads_dir"]) / safe_name
    with open(out_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return safe_name


def insert_resource(title, description, filename, uploaded_by, role, tags, level):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO resources (title, description, filename, uploaded_by, role, tags, level, added_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (title, description, filename, uploaded_by, role, tags, level, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def insert_word(word, meaning, sentence, added_by):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO words (word, meaning, sentence, added_by, added_at) VALUES (?, ?, ?, ?, ?)",
        (word, meaning, sentence, added_by, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def record_activity(resource_id, username, action):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO activity (resource_id, username, action, action_at) VALUES (?, ?, ?, ?)",
        (resource_id, username, action, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def load_resources(filters=None):
    conn = get_conn()
    cur = conn.cursor()
    query = "SELECT * FROM resources"
    params = []
    if filters:
        where = []
        if filters.get("tag"):
            where.append("tags LIKE ?")
            params.append(f"%{filters['tag']}%")
        if filters.get("level"):
            where.append("level = ?")
            params.append(filters["level"])
        if where:
            query += " WHERE " + " AND ".join(where)
    query += " ORDER BY added_at DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def load_words():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM words ORDER BY added_at DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

# ---------- UI helpers ----------

def sidebar_login():
    st.sidebar.title("Login / Role")
    role = st.sidebar.selectbox("I am a", ["Student", "Teacher"])
    username = st.sidebar.text_input("Username", value="")
    password = st.sidebar.text_input("Password", type="password")
    login = st.sidebar.button("Login")
    if login:
        if role == "Teacher":
            if username == CONFIG["teacher_username"] and password == CONFIG["teacher_password"]:
                st.session_state["auth"] = True
                st.session_state["role"] = "Teacher"
                st.session_state["username"] = username
                st.experimental_rerun()
            else:
                st.sidebar.error("Invalid teacher credentials. Change password in app config before deploy.")
        else:
            # Students can login with any username (for simplicity)
            if username.strip() == "":
                st.sidebar.error("Enter a username to continue as a student.")
            else:
                st.session_state["auth"] = True
                st.session_state["role"] = "Student"
                st.session_state["username"] = username
                st.experimental_rerun()


if "auth" not in st.session_state:
    st.session_state["auth"] = False
    st.session_state["role"] = None
    st.session_state["username"] = None

# draw sidebar login
sidebar_login()

# ---------- Main App ----------

st.set_page_config(page_title="French Class Hub", layout="wide")
st.title("French Class — Teacher ⇄ Students Hub")

if not st.session_state["auth"]:
    st.info("Please login from the left panel to continue. Use role=Teacher and the configured password to upload content.")
    st.stop()

role = st.session_state["role"]
username = st.session_state["username"]

st.markdown(f"**Signed in as**: {username} — **Role**: {role}")

col1, col2 = st.columns([2, 3])

with col1:
    st.header("Browse resources")
    tag_filter = st.text_input("Filter by tag (e.g., 'vocab', 'pdf', 'dance')")
    level_filter = st.selectbox("Level", ["", "A1", "A2", "B1", "B2", "C1", "C2"]) 
    res = load_resources(filters={"tag": tag_filter} if tag_filter or level_filter else None)

    if res:
        for r in res:
            st.subheader(r["title"]) 
            st.caption(f"by {r['uploaded_by']} — {r['added_at'][:19]}")
            st.write(r["description"])
            filename = r["filename"]
            file_path = Path(CONFIG["uploads_dir"]) / filename
            if file_path.exists():
                suffix = file_path.suffix.lower()
                if suffix in [".png", ".jpg", ".jpeg", ".gif"]:
                    st.image(str(file_path))
                    st.download_button("Download image", data=open(file_path, "rb"), file_name=file_path.name)
                elif suffix in [".mp3", ".wav", ".m4a"]:
                    st.audio(open(file_path, "rb"))
                    st.download_button("Download audio", data=open(file_path, "rb"), file_name=file_path.name)
                else:
                    st.download_button("Download file", data=open(file_path, "rb"), file_name=file_path.name)
            else:
                st.warning("File missing on server — teacher may need to re-upload.")

            # Mark practiced
            if role == "Student":
                if st.button(f"Mark practiced: {r['title']}", key=f"pr_{r['id']}"):
                    record_activity(r["id"], username, "practiced")
                    st.success("Marked as practiced — activity recorded.")

            st.markdown("---")
    else:
        st.write("No resources yet. Teachers: please upload materials from the right panel.")

with col2:
    if role == "Teacher":
        st.header("Teacher — Upload content")
        with st.form("upload_form"):
            title = st.text_input("Title")
            description = st.text_area("Short description / instructions")
            uploaded_file = st.file_uploader("Choose a file to upload (pdf/docx/images/audio)")
            tags = st.text_input("Tags (comma separated)")
            level = st.selectbox("Difficulty level", ["", "A1", "A2", "B1", "B2", "C1", "C2"]) 
            submit = st.form_submit_button("Upload")
            if submit:
                if not title or not uploaded_file:
                    st.error("Please add a title and select a file to upload.")
                else:
                    saved = save_file(uploaded_file)
                    insert_resource(title, description, saved, username, "teacher", tags, level)
                    st.success("Uploaded and saved.")
                    st.experimental_rerun()

        st.markdown("---")
        st.header("Teacher — Add vocab / words")
        with st.form("word_form"):
            word = st.text_input("French word")
            meaning = st.text_input("Meaning / translation")
            sentence = st.text_input("Sample sentence (optional)")
            add_word = st.form_submit_button("Add word")
            if add_word:
                if not word or not meaning:
                    st.error("Please provide both the word and its meaning.")
                else:
                    insert_word(word, meaning, sentence, username)
                    st.success("Word added to vocabulary list.")
                    st.experimental_rerun()

        st.markdown("---")
        st.header("Teacher tools")
        if st.button("Export resources metadata as CSV"):
            rows = load_resources()
            df = pd.DataFrame(rows)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", data=csv, file_name="resources.csv")

        if st.button("Export vocab as CSV"):
            rows = load_words()
            df = pd.DataFrame(rows)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download vocab CSV", data=csv, file_name="vocab.csv")

    else:
        st.header("Student — Vocabulary practice")
        words = load_words()
        if words:
            for w in words:
                with st.expander(w["word"] + (f" — {w['meaning']}" if w['meaning'] else "")):
                    if w['sentence']:
                        st.write(f"Example: {w['sentence']}")
                    if st.button(f"I practiced this: {w['word']}", key=f"w_{w['id']}"):
                        record_activity(None, username, f"practiced_word:{w['word']}")
                        st.success("Recorded practice for this word.")
        else:
            st.write("No vocabulary yet — ask your teacher to add words.")

# ---------- Activity feed ----------

st.sidebar.markdown("---")
st.sidebar.header("Recent activity")
conn = get_conn()
cur = conn.cursor()
cur.execute("SELECT * FROM activity ORDER BY action_at DESC LIMIT 10")
acts = cur.fetchall()
conn.close()
if acts:
    for a in acts:
        ts = a["action_at"][:19]
        st.sidebar.write(f"{a['username']}: {a['action']} — {ts}")
else:
    st.sidebar.write("No activity yet.")

# ---------- Footer / Help ----------
st.sidebar.markdown("---")
if st.sidebar.button("Help / How to use"):
    st.sidebar.info(
        "Teachers: login with role=Teacher and the configured password; upload files from right panel.\n\n"
        "Students: login with role=Student and any username; browse and mark items as practiced.\n\n"
        "Deployment: commit this file and the `data/` folder (or create an empty DB on deploy), then connect the repo to Streamlit Cloud and set the app command `streamlit run streamlit_french_class_app.py`."
    )

# small neatness: show counts
conn = get_conn()
cur = conn.cursor()
cur.execute("SELECT COUNT(*) as c FROM resources")
num_res = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) as c FROM words")
num_words = cur.fetchone()[0]
conn.close()

st.sidebar.markdown(f"**Resources:** {num_res} **Vocab:** {num_words}")

# End of file

