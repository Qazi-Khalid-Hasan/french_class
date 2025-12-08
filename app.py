import streamlit as st
import os
import json
from datetime import datetime

# -------------------------
# USERS
# -------------------------
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin133"

TEACHER_USERNAME = "teacher"
TEACHER_PASSWORD = "12345"

STUDENTS = {
    "a": "a123",
    "b": "b123",
    "c": "c123",
    "d": "d123",
    "e": "e123",
    "f": "f123"
}

# -------------------------
# FOLDERS
# -------------------------
DATA_FOLDER = "data"
FILES_FOLDER = "uploaded_files"
LOG_FILE = "activity_log.json"

os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(FILES_FOLDER, exist_ok=True)

# -------------------------
# ACTIVITY LOGGING
# -------------------------
def log_activity(user, action, details=""):
    log_path = os.path.join(DATA_FOLDER, LOG_FILE)
    logs = []

    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            try:
                logs = json.load(f)
            except:
                logs = []

    logs.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": user,
        "action": action,
        "details": details
    })

    with open(log_path, "w") as f:
        json.dump(logs, f, indent=4)

# -------------------------
# LOGIN PAGE
# -------------------------
def login():
    st.title("📘 Smart Study App")

    st.write("Login to continue")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        # Admin Login
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            st.session_state["role"] = "admin"
            st.session_state["username"] = username
            log_activity(username, "login")
            st.experimental_rerun()

        # Teacher Login
        elif username == TEACHER_USERNAME and password == TEACHER_PASSWORD:
            st.session_state["role"] = "teacher"
            st.session_state["username"] = username
            log_activity(username, "login")
            st.experimental_rerun()

        # Student Login
        elif username in STUDENTS and password == STUDENTS[username]:
            st.session_state["role"] = "student"
            st.session_state["username"] = username
            log_activity(username, "login")
            st.experimental_rerun()
        else:
            st.error("Incorrect username or password.")

# -------------------------
# ADMIN DASHBOARD
# -------------------------
def admin_dashboard():
    st.title("👨‍💼 Admin Dashboard")
    st.subheader("Activity Logs")

    log_path = os.path.join(DATA_FOLDER, LOG_FILE)

    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            logs = json.load(f)

        for entry in logs:
            st.write(
                f"**{entry['timestamp']}** | **{entry['user']}** → {entry['action']} ({entry['details']})"
            )
    else:
        st.info("No logs yet.")

    if st.button("Logout"):
        st.session_state.clear()
        st.experimental_rerun()

# -------------------------
# TEACHER DASHBOARD
# -------------------------
def teacher_dashboard():
    st.title("👩‍🏫 Teacher Dashboard")

    st.subheader("Upload Study Materials")
    uploaded = st.file_uploader("Upload file", type=["pdf", "docx", "png", "jpg", "jpeg"])

    if uploaded:
        save_path = os.path.join(FILES_FOLDER, uploaded.name)
        with open(save_path, "wb") as f:
            f.write(uploaded.read())

        st.success(f"{uploaded.name} uploaded successfully.")
        log_activity("teacher", "uploaded file", uploaded.name)

    st.subheader("Manage Uploaded Files")
    files = sorted(
        os.listdir(FILES_FOLDER),
        key=lambda x: os.path.getmtime(os.path.join(FILES_FOLDER, x)),
        reverse=True
    )

    for f_name in files:
        col1, col2, col3 = st.columns([3, 1, 1])

        file_path = os.path.join(FILES_FOLDER, f_name)
        mtime = datetime.fromtimestamp(os.path.getmtime(file_path))

        col1.write(f"📄 **{f_name}**")
        col1.caption(f"Uploaded on {mtime}")

        with open(file_path, "rb") as f:
            col2.download_button("Download", f, file_name=f_name)

        if col3.button("❌ Delete", key=f_name):
            os.remove(file_path)
            log_activity("teacher", "deleted file", f_name)
            st.warning(f"{f_name} deleted.")
            st.experimental_rerun()

    if st.button("Logout"):
        st.session_state.clear()
        st.experimental_rerun()

# -------------------------
# STUDENT DASHBOARD
# -------------------------
def student_dashboard():
    st.title("🎓 Student Dashboard")

    st.subheader("Study Materials (Sorted by Date)")

    files = sorted(
        os.listdir(FILES_FOLDER),
        key=lambda x: os.path.getmtime(os.path.join(FILES_FOLDER, x)),
        reverse=True
    )

    for f_name in files:
        file_path = os.path.join(FILES_FOLDER, f_name)
        file_type = f_name.split(".")[-1].lower()
        mtime = datetime.fromtimestamp(os.path.getmtime(file_path))

        st.write(f"### 📄 {f_name}")
        st.caption(f"Uploaded on: {mtime}")

        # ---------- File Preview ----------
        if file_type in ["png", "jpg", "jpeg"]:
            st.image(file_path)
        elif file_type == "pdf":
            st.write(f"Preview not supported here, download instead.")
        elif file_type == "docx":
            st.write("DOCX preview not supported, download to view.")

        # ---------- Download ----------
        with open(file_path, "rb") as f:
            st.download_button("Download File", f, file_name=f_name)

        st.divider()

    if st.button("Logout"):
        st.session_state.clear()
        st.experimental_rerun()

# -------------------------
# MAIN APP CONTROLLER
# -------------------------
if "role" not in st.session_state:
    login()
else:
    role = st.session_state["role"]

    if role == "admin":
        admin_dashboard()
    elif role == "teacher":
        teacher_dashboard()
    else:
        student_dashboard()
