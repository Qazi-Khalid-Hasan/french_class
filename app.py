# app.py
# Streamlit app: Admin (view logs) / Teacher (upload/delete) / Student (view/download)
# Fixed logout behavior to avoid AttributeError on st.experimental_rerun

import streamlit as st
import os
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Class App", layout="wide")

# ---------------- CONFIG ----------------
USERS = {
    "admin":   {"password": "admin123", "role": "admin"},
    "teacher": {"password": "12345",   "role": "teacher"},
    "a":       {"password": "a123",    "role": "student"},
    "b":       {"password": "b123",    "role": "student"},
    "c":       {"password": "c123",    "role": "student"},
}

DATA_FOLDER = "uploaded_files"
LOG_FILE = "audit_log.txt"

os.makedirs(DATA_FOLDER, exist_ok=True)

# ---------------- Helpers ----------------
def log_event(user, action, filename=""):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"{timestamp} | {user} | {action} | {filename}\n")

def read_logs():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return [l.strip() for l in f.readlines()]

def logs_to_df(lines):
    rows = []
    for l in lines:
        parts = [p.strip() for p in l.split("|")]
        if len(parts) >= 4:
            rows.append({
                "timestamp": parts[0],
                "user": parts[1],
                "action": parts[2],
                "filename": parts[3]
            })
    if rows:
        return pd.DataFrame(rows)
    return pd.DataFrame(columns=["timestamp","user","action","filename"])

# Safer logout: set keys to None instead of clearing entire session_state
def logout():
    user = st.session_state.get("user")
    if user:
        log_event(user, "LOGOUT")
    # set values to None or delete only known keys
    for k in ["user","role"]:
        if k in st.session_state:
            del st.session_state[k]
    # rerun to show login screen (safe because we didn't clear internal session objects)
    st.experimental_rerun()

# ---------------- UI: Login ----------------
def login_page():
    st.title("Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            username = username.strip()
            if username in USERS and USERS[username]["password"] == password:
                st.session_state["user"] = username
                st.session_state["role"] = USERS[username]["role"]
                log_event(username, "LOGIN")
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")

# ---------------- Admin Dashboard ----------------
def admin_dashboard():
    st.title("Admin Dashboard — Activity Monitor")
    st.info("Admin can only view logs and export them. No upload/delete here.")
    lines = read_logs()
    if not lines:
        st.warning("No activity logs found.")
    else:
        df = logs_to_df(reversed(lines))  # show most recent first
        st.subheader("Recent activity (most recent first)")
        n = st.slider("How many rows to show", min_value=10, max_value=1000, value=100, step=10)
        st.dataframe(df.head(n))
        st.markdown("---")
        # summary metrics
        st.subheader("Summary statistics")
        logins = df[df["action"] == "LOGIN"].groupby("user").size().reset_index(name="login_count")
        uploads = df[df["action"] == "UPLOAD"].groupby("user").size().reset_index(name="upload_count")
        deletes = df[df["action"] == "DELETE"].groupby("user").size().reset_index(name="delete_count")
        st.write("Logins per user")
        st.table(logins)
        st.write("Uploads per user")
        st.table(uploads)
        st.write("Deletes per user")
        st.table(deletes)
        # teacher-specific deletes (teacher usernames are those in USERS with role teacher)
        teacher_usernames = [u for u,r in USERS.items() if r["role"] == "teacher"]
        teacher_deletes = deletes[deletes["user"].isin(teacher_usernames)]
        st.write("Teacher deletes")
        st.table(teacher_deletes)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download full logs (CSV)", csv, file_name="audit_log.csv", mime="text/csv")

    if st.button("Logout"):
        logout()

# ---------------- Teacher Dashboard ----------------
def teacher_dashboard():
    st.title("Teacher Dashboard — Upload & Manage Files")
    st.success("Only teacher(s) can upload and delete files. Actions are logged.")

    st.subheader("Upload file")
    uploaded = st.file_uploader("Choose file to upload", type=None)
    if uploaded is not None:
        # safe-saver: if same name exists append timestamp
        save_name = uploaded.name
        save_path = os.path.join(DATA_FOLDER, save_name)
        if os.path.exists(save_path):
            base, ext = os.path.splitext(save_name)
            ts = datetime.now().strftime("%Y%m%d%H%M%S")
            save_name = f"{base}_{ts}{ext}"
            save_path = os.path.join(DATA_FOLDER, save_name)
        with open(save_path, "wb") as f:
            f.write(uploaded.read())
        log_event(st.session_state["user"], "UPLOAD", save_name)
        st.success(f"Saved file: {save_name}")
        st.experimental_rerun()

    st.subheader("Files available to students")
    files = sorted(os.listdir(DATA_FOLDER))
    if not files:
        st.info("No files uploaded yet.")
    else:
        for fn in files:
            cols = st.columns([6,1,1])
            cols[0].write(fn)
            # download button (teacher can also download)
            path = os.path.join(DATA_FOLDER, fn)
            with open(path, "rb") as f:
                data = f.read()
            if cols[2].download_button("Download", data, file_name=fn, key=f"t_dl_{fn}"):
                log_event(st.session_state["user"], "DOWNLOAD", fn)
            if cols[1].button("Delete", key=f"del_{fn}"):
                try:
                    os.remove(path)
                    log_event(st.session_state["user"], "DELETE", fn)
                    st.warning(f"Deleted {fn}")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Failed to delete {fn}: {e}")

    if st.button("Logout"):
        logout()

# ---------------- Student Dashboard ----------------
def student_dashboard():
    st.title("Student Dashboard — View & Download")
    st.info("Students can view and download files. They cannot upload or delete.")

    files = sorted(os.listdir(DATA_FOLDER))
    if not files:
        st.info("No files available. Check back later.")
    else:
        for fn in files:
            cols = st.columns([6,1])
            cols[0].write(fn)
            path = os.path.join(DATA_FOLDER, fn)
            with open(path, "rb") as f:
                data = f.read()
            # log DOWNLOAD only if user actually clicks the button:
            if cols[1].download_button("Download", data, file_name=fn, key=f"s_dl_{fn}"):
                log_event(st.session_state["user"], "DOWNLOAD", fn)

    if st.button("Logout"):
        logout()

# ---------------- Router ----------------
if "user" not in st.session_state:
    login_page()
else:
    role = st.session_state.get("role")
    st.sidebar.write(f"Logged in as: **{st.session_state.get('user')}** ({role})")
    if role == "admin":
        admin_dashboard()
    elif role == "teacher":
        teacher_dashboard()
    else:
        student_dashboard()
