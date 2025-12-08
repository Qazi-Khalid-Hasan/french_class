import streamlit as st
import os
from datetime import datetime

# -------------------- CONFIG --------------------
st.set_page_config(page_title="FrenchClass Hub", layout="wide")

USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "teacher": {"password": "12345", "role": "teacher"},
    "a": {"password": "a123", "role": "student"},
    "b": {"password": "b123", "role": "student"},
    "c": {"password": "c123", "role": "student"},
}

DATA_FOLDER = "uploaded_files"
LOG_FILE = "activity_log.txt"

os.makedirs(DATA_FOLDER, exist_ok=True)

# -------------------- LOGGING --------------------
def log_event(user, action, filename=""):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} | {user} | {action} | {filename}\n")

# -------------------- LOGIN SYSTEM --------------------
def login():
    st.title("📘 FrenchClass Hub")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    login_button = st.button("Login")

    if login_button:
        if username in USERS and USERS[username]["password"] == password:
            st.session_state["user"] = username
            st.session_state["role"] = USERS[username]["role"]
            log_event(username, "LOGIN")
        else:
            st.error("Wrong username or password.")

# -------------------- ADMIN PAGE --------------------
def admin_dashboard():
    st.title("👑 Admin Panel")
    st.info("Admin can only view activity logs.")

    st.subheader("Activity Logs")
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            st.text(f.read())
    else:
        st.warning("No logs available.")

    if st.button("Logout"):
        log_event(st.session_state["user"], "LOGOUT")
        st.session_state.clear()

# -------------------- TEACHER PAGE --------------------
def teacher_dashboard():
    st.title("👨‍🏫 Teacher Dashboard")
    st.success("Upload and delete files.")

    upload = st.file_uploader("Upload file", type=["pdf", "docx", "txt", "jpg", "png", "mp4"])

    if upload:
        path = os.path.join(DATA_FOLDER, upload.name)
        with open(path, "wb") as f:
            f.write(upload.read())
        log_event(st.session_state["user"], "UPLOAD", upload.name)
        st.success(f"Uploaded: {upload.name}")

    st.subheader("Files")

    files = os.listdir(DATA_FOLDER)

    for f_name in files:
        file_path = os.path.join(DATA_FOLDER, f_name)

        st.write(f"📄 **{f_name}**")

        col1, col2 = st.columns(2)

        with col1:
            with open(file_path, "rb") as f:
                st.download_button("⬇️ Download", f, file_name=f_name)

        with col2:
            if st.button(f"🗑 Delete {f_name}"):
                os.remove(file_path)
                log_event(st.session_state["user"], "DELETE", f_name)
                st.warning(f"Deleted {f_name}")
                st.session_state["refresh"] = True

    if st.button("Logout"):
        log_event(st.session_state["user"], "LOGOUT")
        st.session_state.clear()

# -------------------- STUDENT PAGE --------------------
def student_dashboard():
    st.title("📚 Study Materials")

    files = load_files()

    if not files:
        st.info("No files uploaded yet.")
        return

    st.subheader("Available Files (Newest First)")

    # Sort files by uploaded date (DESC)
    files_sorted = sorted(files.items(), key=lambda x: x[1]["uploaded_at"], reverse=True)

    for file_name, info in files_sorted:
        file_path = os.path.join(DATA_FOLDER, file_name)

        with st.expander(f"{file_name} — Uploaded on {info['uploaded_at']}"):
            with open(file_path, "rb") as f:
                st.download_button(
                    label="📥 Download",
                    data=f,
                    file_name=file_name,
                    use_container_width=True
                )

           

# -------------------- ROUTER --------------------
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

