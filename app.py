import streamlit as st
import os
import json
from datetime import datetime

# -------------------------
# CONFIG
# -------------------------
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

DATA_FOLDER = "uploaded_files"
META_FILE = "file_metadata.json"

# Ensure folders exist
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

if not os.path.exists(META_FILE):
    with open(META_FILE, "w") as f:
        json.dump([], f, indent=4)


# -------------------------
# LOAD / SAVE METADATA
# -------------------------
def load_metadata():
    with open(META_FILE, "r") as f:
        return json.load(f)


def save_metadata(data):
    with open(META_FILE, "w") as f:
        json.dump(data, f, indent=4)


# -------------------------
# LOGIN PAGE
# -------------------------
def login():
    st.title("📚 French Classroom Portal")

    role = st.selectbox("I am a", ["Teacher", "Student"])

    username = st.text_input("Username")
    pw = st.text_input("Password", type="password")

    if st.button("Login"):
        if role == "Teacher":
            if username == TEACHER_USERNAME and pw == TEACHER_PASSWORD:
                st.session_state.role = "teacher"
                st.session_state.logged_in = True
            else:
                st.error("❌ Invalid teacher credentials.")

        else:  # Student
            if username in STUDENTS and pw == STUDENTS[username]:
                st.session_state.role = "student"
                st.session_state.username = username
                st.session_state.logged_in = True
            else:
                st.error("❌ Invalid student credentials.")


# -------------------------
# TEACHER DASHBOARD
def teacher_dashboard():
    st.title("👩‍🏫 Teacher Dashboard")
        # LOGOUT BUTTON
    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.experimental_rerun()

    
    st.subheader("Upload New Study Material")

    uploaded_file = st.file_uploader(
        "Choose file to upload",
        type=["pdf", "png", "jpg", "jpeg", "mp4", "mp3", "txt", "docx"]
    )
    description = st.text_input("Description (optional)")

    if st.button("Upload"):
        if uploaded_file:
            file_path = os.path.join(DATA_FOLDER, uploaded_file.name)

            # Save file
            with open(file_path, "wb") as f:
                f.write(uploaded_file.read())

            # Save metadata
            metadata = load_metadata()
            metadata.append({
                "filename": uploaded_file.name,
                "description": description,
                "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            })
            save_metadata(metadata)

            st.success("✅ File uploaded successfully!")
        else:
            st.error("Please select a file before uploading.")

    st.divider()
    st.subheader("📁 All Uploaded Materials")

    metadata = load_metadata()
    new_metadata = []

    for item in metadata:
        st.write(f"**📄 {item['filename']}**")
        st.write(f"📝 {item['description']}")
        st.write(f"📅 Uploaded at: {item['uploaded_at']}")

        file_path = os.path.join(DATA_FOLDER, item["filename"])

        col1, col2 = st.columns(2)

        with col1:
            # Download
            st.download_button(
                "Download",
                data=open(file_path, "rb").read(),
                file_name=item["filename"]
            )

        with col2:
            # Delete Button
            if st.button(f"❌ Delete {item['filename']}"):
                # Remove physical file
                if os.path.exists(file_path):
                    os.remove(file_path)
                st.warning(f"Deleted: {item['filename']}")
            else:
                # Keep if not deleted
                new_metadata.append(item)

        st.markdown("---")

    # Save updated list excluding deleted ones
    save_metadata(new_metadata)



# -------------------------
# STUDENT DASHBOARD
# -------------------------
def student_dashboard():
    st.title("👨‍🎓 Student Resources")
        # LOGOUT BUTTON
    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.experimental_rerun()


    metadata = load_metadata()

    if len(metadata) == 0:
        st.info("No files uploaded yet.")
        return

    for item in metadata:
        st.write(f"### 📄 {item['filename']}")
        st.write(f"📝 {item['description']}")
        st.write(f"📅 Uploaded at: {item['uploaded_at']}")

        st.download_button(
            "Download",
            data=open(os.path.join(DATA_FOLDER, item["filename"]), "rb").read(),
            file_name=item["filename"]
        )
        st.markdown("---")


# -------------------------
# APP LOGIC
# -------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login()
else:
    if st.session_state.role == "teacher":
        teacher_dashboard()
    else:
        student_dashboard()


