# app.py
import streamlit as st
import os
from datetime import datetime
import pandas as pd

# -------------------- CONFIG --------------------
st.set_page_config(layout="wide")
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

# -------------------- HELPERS --------------------
def log_event(user, action, filename=""):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{ts} | {user} | {action} | {filename}\n")

def read_logs():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return [l.strip() for l in f.readlines()]

def logs_to_df(lines):
    rows = []
    for L in lines:
        parts = [p.strip() for p in L.split("|")]
        if len(parts) == 4:
            rows.append({
                "timestamp": parts[0],
                "user": parts[1],
                "action": parts[2],
                "filename": parts[3]
            })
    if rows:
        return pd.DataFrame(rows)
    return pd.DataFrame(columns=["timestamp","user","action","filename"])

def safe_logout():
    user = st.session_state.get("user")
    if user:
        log_event(user, "LOGOUT")
    # remove only our keys
    for k in ("user","role","page"):
        if k in st.session_state:
            del st.session_state[k]

# -------------------- DEFAULT PROFESSIONAL LOGO (SVG) --------------------
# Small square "FC" logo encoded as an inline SVG. Rendered in the sidebar.
LOGO_SVG = """
<svg xmlns='http://www.w3.org/2000/svg' width='64' height='64' viewBox='0 0 64 64'>
  <rect rx='10' ry='10' width='64' height='64' fill='#0b5ed7'/>
  <text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' font-family='Arial' font-size='26' fill='white'>FC</text>
</svg>
"""
SVG_DATA_URI = "data:image/svg+xml;utf8," + LOGO_SVG

# -------------------- UI: SIDEBAR --------------------
def sidebar_ui():
    # Brand & nav
    st.sidebar.markdown(f"<div style='display:flex;align-items:center;gap:12px'>"
                        f"<img src=\"{SVG_DATA_URI}\" width='48'/>"
                        f"<div style='font-weight:600'>French Class Portal</div></div>",
                        unsafe_allow_html=True)
    st.sidebar.markdown("---")
    # Show login or user info
    if "user" not in st.session_state:
        st.sidebar.subheader("Sign in")
        username = st.sidebar.text_input("Username", key="login_user")
        password = st.sidebar.text_input("Password", type="password", key="login_pw")
        if st.sidebar.button("Login", key="login_btn"):
            u = username.strip()
            p = password
            if u and u in USERS and USERS[u]["password"] == p:
                st.session_state["user"] = u
                st.session_state["role"] = USERS[u]["role"]
                st.session_state["page"] = "home"
                log_event(u, "LOGIN")
            else:
                st.sidebar.error("Invalid username or password")
        st.sidebar.markdown("Default accounts: admin/teacher/a/b/c")
    else:
        st.sidebar.write(f"**{st.session_state['user']}**")
        st.sidebar.write(f"*{st.session_state['role']}*")
        st.sidebar.markdown("---")
        # navigation depending on role
        role = st.session_state["role"]
        if role == "admin":
            page = st.sidebar.radio("Admin menu", ["Activity Dashboard", "Export Logs"], index=0)
            st.session_state["page"] = "admin_" + page.lower().replace(" ", "_")
        elif role == "teacher":
            page = st.sidebar.radio("Teacher menu", ["Files", "Uploads History"], index=0)
            st.session_state["page"] = "teacher_" + page.lower().replace(" ", "_")
        else:
            page = st.sidebar.radio("Student menu", ["Files"], index=0)
            st.session_state["page"] = "student_files"
        st.sidebar.markdown("---")
        if st.sidebar.button("Logout"):
            safe_logout()
            st.rerun()

# -------------------- PAGES --------------------
def page_teacher_files():
    st.header("Teacher — Manage Files")
    st.write("Upload files for students. Deleting files is permanent and logged.")
    # upload
    uploaded = st.file_uploader("Upload a file", type=None, key="teacher_uploader")
    if uploaded is not None:
        # safe overwrite handling
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
        st.success(f"Saved {save_name}")

    st.markdown("### Files available to students")
    files = sorted(os.listdir(DATA_FOLDER))
    if not files:
        st.info("No files uploaded yet.")
        return
    for fn in files:
        col1, col2, col3 = st.columns([6,1,1])
        col1.write(fn)
        # download
        path = os.path.join(DATA_FOLDER, fn)
        with open(path, "rb") as f:
            data = f.read()
        if col2.download_button("Download", data, file_name=fn, key=f"t_dl_{fn}"):
            log_event(st.session_state["user"], "DOWNLOAD", fn)
        # delete (teacher only)
        if col3.button("Delete", key=f"del_{fn}"):
            try:
                os.remove(path)
                log_event(st.session_state["user"], "DELETE", fn)
                st.warning(f"Deleted {fn}")
                # after delete, refresh the app (safe place to rerun)
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Could not delete {fn}: {e}")

def page_teacher_uploads_history():
    st.header("Upload / Delete History")
    lines = read_logs()
    if not lines:
        st.info("No activity recorded.")
        return
    df = logs_to_df(reversed(lines))
    # show only upload/delete ops
    df_ops = df[df["action"].isin(["UPLOAD","DELETE"])].copy()
    if df_ops.empty:
        st.info("No uploads or deletes yet.")
        return
    st.dataframe(df_ops)
    st.download_button("Export upload/delete (CSV)", df_ops.to_csv(index=False).encode("utf-8"), file_name="uploads_history.csv")

def page_student_files():
    st.header("Student — Available Files")
    st.write("You can download files made available by the teacher.")
    files = sorted(os.listdir(DATA_FOLDER))
    if not files:
        st.info("No files available.")
        return
    for fn in files:
        path = os.path.join(DATA_FOLDER, fn)
        with open(path, "rb") as f:
            data = f.read()
        if st.download_button(fn, data, file_name=fn, key=f"s_dl_{fn}"):
            log_event(st.session_state["user"], "DOWNLOAD", fn)

def page_admin_activity_dashboard():
    st.header("Admin — Activity Dashboard")
    st.write("Overview of app activity (LOGIN, UPLOAD, DELETE, DOWNLOAD).")
    lines = read_logs()
    if not lines:
        st.info("No activity logs found.")
        return
    df = logs_to_df(reversed(lines))
    st.subheader("Recent activity")
    st.dataframe(df.head(200))

    st.subheader("Summary Metrics")
    # compute metrics
    logins = df[df["action"] == "LOGIN"].groupby("user").size().reset_index(name="logins")
    uploads = df[df["action"] == "UPLOAD"].groupby("user").size().reset_index(name="uploads")
    deletes = df[df["action"] == "DELETE"].groupby("user").size().reset_index(name="deletes")
    downloads = df[df["action"] == "DOWNLOAD"].groupby("user").size().reset_index(name="downloads")

    col1, col2 = st.columns(2)
    col1.write("Logins per user")
    col1.table(logins)
    col2.write("Uploads per user")
    col2.table(uploads)

    col3, col4 = st.columns(2)
    col3.write("Deletes per user")
    col3.table(deletes)
    col4.write("Downloads per user")
    col4.table(downloads)

    # teacher deletes specifically
    teacher_usernames = [u for u,v in USERS.items() if v["role"] == "teacher"]
    teacher_deletes = deletes[deletes["user"].isin(teacher_usernames)]
    st.write("Teacher delete counts")
    st.table(teacher_deletes)

    # simple charts
    st.subheader("Activity chart (counts by action)")
    action_counts = df.groupby("action").size().rename("count").reset_index()
    st.bar_chart(action_counts.set_index("action"))

    # export
    st.download_button("Download full logs (CSV)", df.to_csv(index=False).encode("utf-8"), file_name="audit_log.csv")

def page_admin_export_logs():
    st.header("Admin — Export Logs")
    lines = read_logs()
    if not lines:
        st.info("No logs to export.")
        return
    df = logs_to_df(reversed(lines))
    st.download_button("Download logs (CSV)", df.to_csv(index=False).encode("utf-8"), file_name="audit_log.csv")

# -------------------- ROUTER & START --------------------
sidebar_ui()

# decide which page to show
page = st.session_state.get("page", None)
role = st.session_state.get("role", None)

if "user" not in st.session_state:
    # no user logged in; show a clean landing area (professional)
    st.title("French Class Portal")
    st.markdown("Please sign in from the left-hand panel.")
    st.write("")
    st.write("If you are an admin, teacher or student, use the credentials in the sidebar to log in.")
else:
    # role-based routing
    if role == "teacher":
        if page == "teacher_files":
            page_teacher_files()
        elif page == "teacher_uploads_history":
            page_teacher_uploads_history()
        else:
            page_teacher_files()
    elif role == "student":
        page_student_files()
    elif role == "admin":
        if page == "admin_activity_dashboard":
            page_admin_activity_dashboard()
        else:
            page_admin_export_logs()
    else:
        st.warning("Unknown role. Contact administrator.")

