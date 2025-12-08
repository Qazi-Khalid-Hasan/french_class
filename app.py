import streamlit as st
import os
from datetime import datetime

# -------------------- CONFIG --------------------
st.set_page_config(page_title="Portail de Classe (Class Portal)", layout="wide")

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

# -------------------- LOGIN --------------------
def login():
    st.title("📘 Class File System")
    st.subheader("Simple • Fast • Smart")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in USERS and USERS[username]["password"] == password:
            st.session_state["user"] = username
            st.session_state["role"] = USERS[username]["role"]
            log_event(username, "LOGIN")
            st.experimental_rerun()
        else:
            st.error("Wrong username or password.")

# -------------------- ADMIN PAGE --------------------
def admin_dashboard():
    st.title("👑 Admin Panel")
    st.info("Admin can only view activity logs.")

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            st.text(f.read())
    else:
        st.warning("No logs available yet.")

    if st.button("Logout"):
        log_event(st.session_state["user"], "LOGOUT")
        st.session_state.clear()
        st.experimental_rerun()

# -------------------- TEACHER PAGE --------------------
def teacher_dashboard():
    st.title("👨‍🏫 Teacher Dashboard")
    st.success("Upload and delete files.")

    # Upload
    file = st.file_uploader("Upload file", type=["pdf", "docx", "txt", "jpg", "png", "mp4"])
    if file:
        filepath = os.path.join(DATA_FOLDER, file.name)
        with open(filepath, "wb") as f:
            f.write(file.read())
        log_event(st.session_state["user"], "UPLOAD", file.name)
        st.success(f"Uploaded: {file.name}")
        st.experimental_rerun()

    # List files
    st.subheader("📂 Uploaded Files")
    files = os.listdir(DATA_FOLDER)

    for f_name in files:
        path = os.path.join(DATA_FOLDER, f_name)

        st.write(f"📄 **{f_name}**")
        col1, col2 = st.columns(2)

        with col1:
            with open(path, "rb") as f:
                st.download_button("⬇️ Download", data=f, file_name=f_name)

        with col2:
            if st.button(f"🗑 Delete {f_name}"):
                os.remove(path)
                log_event(st.session_state["user"], "DELETE", f_name)
                st.warning(f"Deleted {f_name}")
                st.experimental_rerun()

    if st.button("Logout"):
        log_event(st.session_state["user"], "LOGOUT")
        st.session_state.clear()
        st.experimental_rerun()

# -------------------- STUDENT PAGE --------------------
def student_dashboard():
    st.title("🎓 Student Dashboard")
    st.info("Files sorted by latest upload date.")

    files = os.listdir(DATA_FOLDER)
    files = sorted(files, key=lambda x: os.path.getmtime(os.path.join(DATA_FOLDER, x)), reverse=True)

    for f_name in files:
        path = os.path.join(DATA_FOLDER, f_name)
        date = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M")

        st.markdown(f"### 📄 {f_name}")
        st.caption(f"Uploaded on: {date}")

        # ---- TEXT PREVIEW ----
        if f_name.lower().endswith(".txt"):
            with open(path, "r") as f:
                st.text(f.read()[:400])

        # ---- IMAGE PREVIEW ----
        if f_name.lower().endswith((".jpg", ".png")):
            st.image(path, width=300)

        # ---- PDF PREVIEW ----
        if f_name.lower().endswith(".pdf"):
            st.write("📘 PDF Preview:")
            st.pdf(path)

        # Download button
        with open(path, "rb") as f:
            st.download_button("⬇️ Download", data=f, file_name=f_name)

        log_event(st.session_state["user"], "VIEW", f_name)

        st.markdown("---")

    if st.button("Logout"):
        log_event(st.session_state["user"], "LOGOUT")
        st.session_state.clear()
        st.experimental_rerun()

# -------------------- ROUTING --------------------
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
