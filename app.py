import streamlit as st
import io, os, json
from datetime import datetime
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

# -------------------- CONFIG --------------------
st.set_page_config(page_title="FrenchClass File Hub", layout="wide")

USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "teacher": {"password": "12345", "role": "teacher"},
    "a": {"password": "a123", "role": "student"},
    "b": {"password": "b123", "role": "student"},
    "c": {"password": "c123", "role": "student"},
}

METADATA_FILE = "metadata.json"   # local mapping: list of {name,id,uploaded_at,uploader}
LOG_FILE = "activity_log.txt"
CLIENT_SECRET_FILE = "client_secret.json"  # put your downloaded OAuth JSON here
DRIVE_FOLDER_NAME = "FrenchClass_Files"
SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive.metadata']

# -------------------- HELPERS: Logging & Metadata --------------------
def log_event(user, action, filename=""):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"{ts} | {user} | {action} | {filename}\n")

def load_metadata():
    if not os.path.exists(METADATA_FILE):
        return []
    with open(METADATA_FILE, "r") as f:
        return json.load(f)

def save_metadata(data):
    with open(METADATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def add_metadata(entry):
    data = load_metadata()
    data.append(entry)
    save_metadata(data)

def remove_metadata_by_id(file_id):
    data = load_metadata()
    data = [d for d in data if d["id"] != file_id]
    save_metadata(data)

# -------------------- GOOGLE DRIVE AUTH --------------------
@st.cache_resource(show_spinner=False)
def get_drive_service():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
    service = build('drive', 'v3', credentials=creds)
    return service

service = None
try:
    service = get_drive_service()
except Exception as e:
    st.error("Google Drive authentication is required. Make sure client_secret.json is present.")
    st.stop()

# -------------------- DRIVE: ensure folder exists --------------------
def get_or_create_folder(folder_name):
    # search for folder
    q = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
    resp = service.files().list(q=q, spaces='drive', fields='files(id, name)').execute()
    files = resp.get('files', [])
    if files:
        return files[0]['id']
    # create folder
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = service.files().create(body=file_metadata, fields='id').execute()
    return folder.get('id')

FOLDER_ID = get_or_create_folder(DRIVE_FOLDER_NAME)

# -------------------- DRIVE: upload / delete / download --------------------
def upload_to_drive(file_obj, filename, mimetype, parent_folder_id, uploader):
    # file_obj is a BytesIO or similar (pointer at start)
    file_obj.seek(0)
    media = MediaIoBaseUpload(file_obj, mimetype=mimetype, resumable=False)
    file_metadata = {'name': filename, 'parents': [parent_folder_id]}
    created = service.files().create(body=file_metadata, media_body=media, fields='id, name').execute()
    file_id = created.get('id')
    add_metadata({
        "name": filename,
        "id": file_id,
        "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "uploader": uploader
    })
    log_event(uploader, "UPLOAD", filename)
    return file_id

def delete_from_drive(file_id, filename, user):
    try:
        service.files().delete(fileId=file_id).execute()
    except Exception as e:
        # maybe already deleted — still remove metadata
        pass
    remove_metadata_by_id(file_id)
    log_event(user, "DELETE", filename)

def download_from_drive(file_id):
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.seek(0)
    return fh.read()  # bytes

# -------------------- UI: Login --------------------
def login():
    st.title("🔐 FrenchClass File Hub Login")
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

# -------------------- ADMIN --------------------
def admin_dashboard():
    st.title("👑 Admin Dashboard")
    st.info("Activity log and metadata")
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            st.text(f.read())
    else:
        st.info("No logs yet.")
    st.markdown("---")
    st.subheader("Metadata (local)")
    st.write(load_metadata())
    if st.button("🗑 Clear Logs"):
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
        with open(LOG_FILE, "w") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | admin | LOGS CLEARED |\n")
        st.success("Logs cleared.")
        st.experimental_rerun()
    if st.button("Logout"):
        st.session_state.clear()
        st.experimental_rerun()

# -------------------- TEACHER --------------------
def teacher_dashboard():
    st.title("👨‍🏫 Teacher Dashboard")
    st.info(f"Files saved to Google Drive folder: {DRIVE_FOLDER_NAME}")
    uploaded = st.file_uploader("Upload file (teacher)", type=None)
    if uploaded:
        # read bytes and upload
        data = uploaded.read()
        bio = io.BytesIO(data)
        file_id = upload_to_drive(bio, uploaded.name, uploaded.type or 'application/octet-stream', FOLDER_ID, st.session_state["user"])
        st.success(f"Uploaded {uploaded.name} (Drive ID: {file_id})")
        st.experimental_rerun()

    st.subheader("Uploaded Files (Newest First)")
    meta = load_metadata()
    # show newest first
    for entry in sorted(meta, key=lambda x: x["uploaded_at"], reverse=True):
        name = entry["name"]
        fid = entry["id"]
        uploaded_at = entry["uploaded_at"]
        st.write(f"📄 {name} — uploaded at {uploaded_at} by {entry.get('uploader','')}")
        col1, col2 = st.columns([1,1])
        with col1:
            # provide a download link (download via server)
            if st.button(f"⬇️ Download {name}", key=f"dl-{fid}"):
                try:
                    file_bytes = download_from_drive(fid)
                    st.download_button(label=f"Download {name}", data=file_bytes, file_name=name)
                except Exception as e:
                    st.error("Failed to download: perhaps file was deleted from Drive.")
        with col2:
            if st.button(f"🗑 Delete {name}", key=f"del-{fid}"):
                delete_from_drive(fid, name, st.session_state["user"])
                st.warning(f"Deleted {name}")
                st.experimental_rerun()

    if st.button("Logout"):
        st.session_state.clear()
        st.experimental_rerun()

# -------------------- STUDENT --------------------
def student_dashboard():
    st.title("🎓 Study Materials")
    meta = load_metadata()
    if not meta:
        st.info("No files uploaded yet.")
        return

    st.subheader("Available Files (Newest First)")
    for entry in sorted(meta, key=lambda x: x["uploaded_at"], reverse=True):
        name = entry["name"]
        fid = entry["id"]
        uploaded_at = entry["uploaded_at"]
        uploader = entry.get("uploader", "")
        with st.expander(f"{name} — Uploaded on {uploaded_at} by {uploader}"):
            # Show a download button that fetches bytes from Drive when clicked
            if st.button(f"📥 Download {name}", key=f"stu-dl-{fid}"):
                try:
                    file_bytes = download_from_drive(fid)
                    st.download_button(label=f"Download {name}", data=file_bytes, file_name=name)
                    log_event(st.session_state["user"], "DOWNLOAD", name)
                except Exception as e:
                    st.error("Download failed: maybe file was deleted or you lack permission.")
    if st.button("Logout"):
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
