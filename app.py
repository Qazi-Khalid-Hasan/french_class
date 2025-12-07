import streamlit as st

# ---------------------------------------------
# CONFIG: Teacher + 5 Students (A to F)
# ---------------------------------------------
USERS = {
    "teacher": {"username": "teacher", "password": "teacher123", "role": "teacher"},
    "student_a": {"username": "a", "password": "a123", "role": "student"},
    "student_b": {"username": "b", "password": "b123", "role": "student"},
    "student_c": {"username": "c", "password": "c123", "role": "student"},
    "student_d": {"username": "d", "password": "d123", "role": "student"},
    "student_e": {"username": "e", "password": "e123", "role": "student"},
    "student_f": {"username": "f", "password": "f123", "role": "student"},
}

# Storage for resources & vocabulary
if "resources" not in st.session_state:
    st.session_state.resources = []
if "vocab" not in st.session_state:
    st.session_state.vocab = []
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None

# ---------------------------------------------
# LOGIN PAGE
# ---------------------------------------------
def login_page():
    st.title("French Learning Portal 🇫🇷")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        for user in USERS.values():
            if username == user["username"] and password == user["password"]:
                st.session_state.logged_in = True
                st.session_state.role = user["role"]
                st.success(f"Welcome, {username}!")
                return
        st.error("Invalid username or password.")

# ---------------------------------------------
# TEACHER DASHBOARD
# ---------------------------------------------
def teacher_dashboard():
    st.title("Teacher Dashboard 👩‍🏫")

    st.subheader("Upload Resources")
    res = st.text_area("Add resource text (lesson, notes, PDF link, etc.)")
    if st.button("Add Resource"):
        if res:
            st.session_state.resources.append(res)
            st.success("Resource added.")

    st.subheader("Add Vocabulary Words")
    word = st.text_input("Vocabulary Word")
    meaning = st.text_input("Meaning")
    if st.button("Add Vocab"):
        if word and meaning:
            st.session_state.vocab.append({"word": word, "meaning": meaning})
            st.success("Vocabulary added.")

    st.subheader("Current Resources")
    for r in st.session_state.resources:
        st.markdown(f"- {r}")

    st.subheader("Vocabulary List")
    for v in st.session_state.vocab:
        st.markdown(f"**{v['word']}** → {v['meaning']}")

# ---------------------------------------------
# STUDENT DASHBOARD
# ---------------------------------------------
def student_dashboard():
    st.title("Student Dashboard 🎓")

    st.sidebar.markdown(f"**Resources:** {len(st.session_state.resources)}  **Vocab:** {len(st.session_state.vocab)}")

    st.header("Study Materials")
    for r in st.session_state.resources:
        st.markdown(f"- {r}")

    st.header("Vocabulary List")
    for v in st.session_state.vocab:
        st.markdown(f"**{v['word']}** → {v['meaning']}")

# ---------------------------------------------
# MAIN APP LOGIC
# ---------------------------------------------
if not st.session_state.logged_in:
    login_page()
else:
    if st.session_state.role == "teacher":
        teacher_dashboard()
    else:
        student_dashboard()
