# streamlit_french_class_with_audit.py
# Streamlit app: Student view / Teacher (uploader/deleter) / Admin (activity viewer)
# NOTE: This is a demonstration template. Change usernames/passwords and paths before use.

import streamlit as st
import os
from datetime import datetime
import pandas as pd
import io

# ---------------- CONFIGURATION ----------------
DATA_FOLDER = "data_files"  # where uploaded files are saved
LOG_FILE = "audit_log.txt"

# Simple credential stores (change for production)
ADMIN = {"admin": "admin123"}
TEACHERS = {"teacher": "12345"}
STUDENTS = {
    "a": "a123",
    "b": "b123",
    "c": "c123",
}

# Create data folder if missing
os.makedirs(DATA_FOLDER, exist_ok=True)

# ----------------- Logging helpers -----------------

def log_event(user, role, action, filename=""):
    """Append a single line to the audit log."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{timestamp} | {user} | {role} | {action} | {filename}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)


def read_logs(limit=5000):
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    # return reversed (most recent first)
    return list(reversed([l.strip() for l in lines]))


def logs_to_df(lines):
    rows = []
    for l in lines:
        parts = [p.strip() for p in l.split("|")]
        if len(parts) >= 5:
            rows.append({
                "timestamp": parts[0],
                "user": parts[1],
                "role": parts[2],
                "action": parts[3],
                "filename": parts[4]
            })
    if rows:
        return pd.DataFrame(rows)
    else:
        return pd.DataFrame(columns=["timestamp", "user", "role", "action", "filename"])


# --------------- Session helpers -----------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user"] = ""
    st.session_state["role"] = ""


def do_login(username, password):
    # admin
    if username in ADMIN and ADMIN[username] == password:
        st.session_state["logged_in"] = True
        st.session_state["user"] = username
        st.session_state["role"] = "admin"
        log_event(username, "admin", "LOGIN")
        return True
    # teacher
    if username in TEACHERS and TEACHERS[username] == password:
        st.session_state["logged_in"] = True
        st.session_state["user"] = username
        st.session_state["role"] = "teacher"
        log_event(username, "teacher", "LOGIN")
        return True
    # student
    if username in STUDENTS and STUDENTS[username] == password:
        st.session_state["logged_in"] = True
        st.session_state["user"] = username
        st.session_state["role"] = "student"
        log_event(username, "student", "LOGIN")
        return True
    return False


def do_logout():
    user = st.session_state.get("user", "")
    role = st.session_state.get("role", "")
    if user:
        log_event(user, role, "LOGOUT")
    st.session_state["logged_in"] = False
    st.session_state["user"] = ""
    st.session_state["role"] = ""


# ---------------- UI -----------------
st.set_page_config(page_title="Class App with Audit", layout="wide")
st.title("Classroom File Hub — Teacher / Student / Admin")

if not st.session_state["logged_in"]:
    st.subheader("Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            ok = do_login(username.strip(), password.strip())
            if not ok:
                st.error("Invalid credentials. Change defaults in the script if needed.")
            else:
                st.experimental_rerun()
else:
    user = st.session_state["user"]
    role = st.session_state["role"]
    st.sidebar.write(f"Logged in as: **{user}** ({role})")
    if st.sidebar.button("Logout"):
        do_logout()
        st.experimental_rerun()

    # ---------------- Teacher view -----------------
    if role == "teacher":
        st.header("Teacher Dashboard — Upload & Manage Files")
        st.write("Only teachers can upload or delete files. All actions are logged.")

        # Upload area
        st.subheader("Upload new file")
        uploaded_file = st.file_uploader("Choose a file to upload", type=None)
        if uploaded_file is not None:
            save_path = os.path.join(DATA_FOLDER, uploaded_file.name)
            # avoid overwriting by default - if same name exists append timestamp
            if os.path.exists(save_path):
                base, ext = os.path.splitext(uploaded_file.name)
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                new_name = f"{base}_{timestamp}{ext}"
                save_path = os.path.join(DATA_FOLDER, new_name)
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            log_event(user, role, "UPLOAD", os.path.basename(save_path))
            st.success(f"Saved file: {os.path.basename(save_path)}")

        # List existing files
        st.subheader("Files available to students")
        files = sorted(os.listdir(DATA_FOLDER))
        if not files:
            st.info("No files uploaded yet.")
        else:
            for fn in files:
                cols = st.columns([6,1,1])
                cols[0].write(fn)
                if cols[1].button("Delete", key=f"del_{fn}"):
                    # confirm
                    confirm = st.confirm(f"Delete {fn}? This is permanent.") if hasattr(st, "confirm") else True
                    if confirm:
                        try:
                            os.remove(os.path.join(DATA_FOLDER, fn))
                            log_event(user, role, "DELETE", fn)
                            st.success(f"Deleted {fn}")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Failed to delete: {e}")
                # download for teacher too
                with open(os.path.join(DATA_FOLDER, fn), "rb") as f:
                    data = f.read()
                cols[2].download_button("Download", data, file_name=fn, key=f"dl_{fn}")

    # ---------------- Student view -----------------
    elif role == "student":
        st.header("Student Dashboard — View & Download Files")
        st.write("Students can view and download files but cannot upload or delete.")
        files = sorted(os.listdir(DATA_FOLDER))
        if not files:
            st.info("No files available. Please check back later.")
        else:
            for fn in files:
                cols = st.columns([6,1])
                cols[0].write(fn)
                with open(os.path.join(DATA_FOLDER, fn), "rb") as f:
                    data = f.read()
                if cols[1].download_button("Download", data, file_name=fn, key=f"s_dl_{fn}"):
                    log_event(user, role, "DOWNLOAD", fn)

    # ---------------- Admin view -----------------
    elif role == "admin":
        st.header("Admin Dashboard — Activity Logs")
        st.write("View all logged activities across the app. Admins cannot upload/delete here; they can only observe and export logs.")

        lines = read_logs()
        df = logs_to_df(lines)

        st.subheader("Recent activity (most recent first)")
        n = st.slider("How many recent actions to show", min_value=10, max_value=500, value=100, step=10)
        st.dataframe(df.head(n))

        st.subheader("Summary statistics")
        if not df.empty:
            # total login counts per user
            login_counts = df[df["action"] == "LOGIN"].groupby("user").size().reset_index(name="login_count")
            st.write("Logins per user")
            st.table(login_counts)

            # uploads per user
            uploads = df[df["action"] == "UPLOAD"].groupby("user").size().reset_index(name="uploads")
            st.write("Uploads per user")
            st.table(uploads)

            # deletions per user
            deletes = df[df["action"] == "DELETE"].groupby("user").size().reset_index(name="deletes")
            st.write("Deletes per user")
            st.table(deletes)

            # teacher-specific metric: how many times the teacher deleted files
            teacher_deletes = deletes[deletes["user"].isin(list(TEACHERS.keys()))]
            st.write("Teacher deletions")
            st.table(teacher_deletes)

            st.subheader("Export logs")
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download full logs (CSV)", csv, file_name="audit_log.csv")
        else:
            st.info("No activity recorded yet.")

    else:
        st.warning("Unknown role. Contact the app maintainer.")

# End of app
