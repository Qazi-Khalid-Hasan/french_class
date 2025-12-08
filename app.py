# Streamlit App with Admin, Teacher, Student Roles
# ADMIN → can only view activity logs
# TEACHER → can upload/delete files
# STUDENTS → can only view/download files

import streamlit as st
from streamlit_extras.app_logo import add_logo
import os
from datetime import datetime

st.set_page_config(page_title="Class App", layout="wide")

# ------------------ CONFIG ------------------
USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "teacher": {"password": "12345", "role": "teacher"},
    "a": {"password": "a123", "role": "student"},
    "b": {"password": "b123", "role": "student"},
    "c": {"password": "c123", "role": "student"}
}

DATA_FOLDER = "uploaded_files"
LOG_FILE = "audit_log.txt"

os.makedirs(DATA_FOLDER, exist_ok=True)

# -------------- LOGGING FUNCTION --------------
def log_event(user, action, filename=""):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as log:
        log.write(f"{timestamp} | {user} | {action} | {filename}")

# ---------------- LOGIN SYSTEM ----------------
def login():
    st.title("Login Page")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in USERS and USERS[username]["password"] == password:
            st.session_state["user"] = username
            st.session_state["role"] = USERS[username]["role"]
            log_event(username, "LOGIN")
            st.experimental_rerun()
        else:
            st.error("Invalid username or password")

# ---------------- ADMIN DASHBOARD ----------------
def admin_dashboard():
    st.title("Admin Dashboard — Activity Monitor")
    st.info("Admin can ONLY view logs. Cannot upload/delete files.")

    if os.path.exists(LOG_FILE):
        st.subheader("Activity Logs")
        with open(LOG_FILE, "r") as f:
            st.text(f.read())
    else:
        st.warning("No activity logs found.")

    if st.button("Logout"):
        log_event(st.session_state['user'], "LOGOUT")
        st.session_state.clear()
        st.experimental_rerun()

# ---------------- TEACHER DASHBOARD ----------------
def teacher_dashboard():
    st.title("Teacher Dashboard")
    st.success("Teacher can upload and delete files.")

    # Upload
    upload = st.file_uploader("Upload File", type=["pdf","docx","txt","png","jpg"])
    if upload:
        path = os.path.join(DATA_FOLDER, upload.name)
        with open(path, "wb") as f:
            f.write(upload.read())
        log_event(st.session_state['user'], "UPLOAD", upload.name)
        st.success("Uploaded successfully!")

    # List files
    st.subheader("Files Available")
    files = os.listdir(DATA_FOLDER)
    for file in files:
        filepath = os.path.join(DATA_FOLDER, file)
        st.write(file)
        with open(filepath, "rb") as f:
            st.download_button("Download", f, file_name=file)
        # delete button
        if st.button(f"Delete {file}"):
            os.remove(filepath)
            log_event(st.session_state['user'], "DELETE", file)
            st.warning(f"Deleted {file}")
            st.experimental_rerun()

    if st.button("Logout"):
        log_event(st.session_state['user'], "LOGOUT")
        st.session_state.clear()
        st.experimental_rerun()

# ---------------- STUDENT DASHBOARD ----------------
def student_dashboard():
    st.title("Student Dashboard")
    st.info("Students can only VIEW and DOWNLOAD files.")

    files = os.listdir(DATA_FOLDER)
    st.subheader("Available Files")
    for file in files:
        st.write(file)
        filepath = os.path.join(DATA_FOLDER, file)
        with open(filepath, "rb") as f:
            st.download_button("Download", f, file_name=file, key=file)
        log_event(st.session_state['user'], "DOWNLOAD", file)

    if st.button("Logout"):
        log_event(st.session_state['user'], "LOGOUT")
        st.session_state.clear()
        st.experimental_rerun()

# ---------------- SIDEBAR UI ----------------
def sidebar_ui():
    with st.sidebar:
        st.markdown("""
            <div style='text-align:center;'>
                <img src='https://cdn-icons-png.flaticon.com/512/3135/3135755.png' width='90'>
                <h2 style='margin-top:10px;'>📘 French Class</h2>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(f"### 👤 Logged in as: **{st.session_state['user'].upper()}**")
        st.markdown(f"**Role:** `{st.session_state['role']}`")
        st.markdown("---")

        st.markdown("#### 🌐 Navigation")
        if st.session_state['role'] == 'admin':
            st.markdown("✔️ Admin Dashboard")
        elif st.session_state['role'] == 'teacher':
            st.markdown("✔️ Teacher Dashboard")
        else:
            st.markdown("✔️ Student Dashboard")

        st.markdown("---")
        if st.button("🚪 Logout", key="logout_sidebar"):
            log_event(st.session_state['user'], "LOGOUT")
            st.session_state.clear()
            st.experimental_rerun()

# ---------------- ROUTER ----------------
if "user" not in st.session_state:
    login()
else:
    role = st.session_state["role"]
    if role == "admin":
        admin_dashboard()
    elif role == "teacher":
        teacher_dashboard()
    else:
        student_dashboard()

