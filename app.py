import streamlit as st
import os
from datetime import datetime

# -------------------- CONFIG --------------------
st.set_page_config(page_title="FrenchClass File Hub", layout="wide")

USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "teacher": {"password": "12345", "role": "teacher"},
    "a": {"password": "a123", "role": "student"},
    "b": {"password": "b123", "role": "student"},
    "c": {"password": "c123", "role": "student"},
}

DATA_FOLDER = "uploaded_files"
LOG_FILE = "activity_log.txt"
META_FILE = "file_metadata.txt"

os.makedirs(DATA_FOLDER, exist_ok=True)

# -------------------- SAVE FILE METADATA --------------------
def save_file_metadata(filename):
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(META_FILE, "a") as f:
        f.write(f"{filename}|{time_now}\n")

# -------------------- LOAD FILE METADATA --------------------
def load_files():
    data = {}
    if not os.path.exists(META_FILE):
        return data

    with open(META_FILE, "r") as f:
        for line in f:
            try:
                name, dt = line.strip().split("|")
                data[name] = {"uploaded_at": dt}
            except:
                pass
    return data

# -------------------- LOGGING --------------------
def log_event(user, action, filename=""):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} | {user} | {action} | {filename}\n")

# -------------------- LOGIN --------------------
def login():
    st.title("🔐 FrenchClass File Hub Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in USERS and USERS[username]["password"] == password:
            st.session_state["user"] = username
            st.session_state["role"] = USERS[username]["role"]
            log_event(username, "LOGIN")
            st.rerun()
        else:
            st.error("Wrong username or password.")

# -------------------- ADMIN PAGE --------------------
# -------------------- ADMIN PAGE --------------------
def admin_dashboard():
    st.title("👑 Admin Dashboard")
    st.info("View activity logs below:")

    # Display logs
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            st.text(f.read())
    else:
        st.warning("No logs yet.")

    st.markdown("---")
    st.subheader("🧹 Manage Logs")

    # Clear logs button
    if st.button("🗑 Clear Full Log History"):
        # Delete the log file
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)

        # Recreate with note
        with open(LOG_FILE, "w") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | admin | LOGS CLEARED |\n")

        st.success("All previous log history has been cleared.")
        st.rerun()

    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()


# -------------------- TEACHER PAGE --------------------
def teacher_dashboard():
    st.title("👨‍🏫 Teacher Dashboard")

    file = st.file_uploader("Upload file", type=None)
    if file:
        filepath = os.path.join(DATA_FOLDER, file.name)
        with open(filepath, "wb") as f:
            f.write(file.read())
        save_file_metadata(file.name)
        log_event(st.session_state["user"], "UPLOAD", file.name)
        st.success(f"Uploaded: {file.name}")
        st.rerun()

    st.subheader("Uploaded Files")
    files = load_files()

    for file_name in sorted(files, reverse=True):
        path = os.path.join(DATA_FOLDER, file_name)

        st.write(f"📄 {file_name}")

        col1, col2 = st.columns(2)

        with col1:
            with open(path, "rb") as f:
                st.download_button("⬇️ Download", data=f, file_name=file_name)

        with col2:
            if st.button(f"🗑 Delete {file_name}"):
                os.remove(path)
                log_event(st.session_state["user"], "DELETE", file_name)
                st.warning(f"Deleted {file_name}")
                st.rerun()

    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

# -------------------- STUDENT PAGE --------------------
def student_dashboard():
    st.title("🎓 Study Materials")

    files = load_files()

    if not files:
        st.info("No files uploaded yet.")
        return

    st.subheader("Available Files (Newest First)")

    # sort by latest timestamp
    files_sorted = sorted(files.items(), key=lambda x: x[1]["uploaded_at"], reverse=True)

    for file_name, info in files_sorted:
        file_path = os.path.join(DATA_FOLDER, file_name)

        with st.expander(f"{file_name} — Uploaded on {info['uploaded_at']}"):
            with open(file_path, "rb") as f:
                st.download_button(
                    "📥 Download",
                    data=f,
                    file_name=file_name,
                    use_container_width=True
                )

            log_event(st.session_state["user"], "VIEW", file_name)

    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

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

