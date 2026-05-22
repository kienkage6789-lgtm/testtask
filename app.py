import streamlit as st
from modules import db_engine, manager, staff, dashboard, account_ui

st.set_page_config(page_title="Hệ Thống Quản Lý R&D Cao Cấp", page_icon="📋", layout="wide")
db_engine.init_db()

# --- KHỞI TẠO CÁC BIẾN SESSION ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "role" not in st.session_state: st.session_state.role = ""
if "username" not in st.session_state: st.session_state.username = ""
if "current_user" not in st.session_state: st.session_state.current_user = ""
if "need_rerun" not in st.session_state: st.session_state.need_rerun = False

def login():
    st.title("🔐 Đăng Nhập Hệ Thống")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    # Lấy danh sách user từ Database thay vì code cứng
    user_list = db_engine.load_users()
    
    with col2:
        with st.form("login_form"):
            user_type = st.selectbox("Chọn Tài Khoản", user_list)
            submit = st.form_submit_button("Đăng Nhập System", type="primary", use_container_width=True)
            if submit:
                st.session_state.logged_in = True
                st.session_state.username = user_type
                st.session_state.current_user = user_type # Đồng bộ cho các file module
                st.session_state.role = "Manager" if user_type == "Manager" else "Staff"
                st.session_state.need_rerun = True

# Không dùng on_click callback nữa để tránh lỗi rerun
def render_sidebar():
    with st.sidebar:
        st.write(f"💼 Tài khoản: **{st.session_state.username}**")
        
        # Đăng xuất an toàn bằng cờ
        if st.button("Đăng Xuất", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.role = ""
            st.session_state.username = ""
            st.session_state.current_user = ""
            st.session_state.need_rerun = True
            
        st.divider()
        
        # Menu điều hướng
        if st.session_state.role == "Manager":
            menu_selection = st.radio("Chức năng quản trị", ["💻 Quản Lý & Duyệt Việc", "📈 Báo Cáo Nhân Viên"])
            # Hiển thị UI quản lý tài khoản ở thanh bên
            account_ui.render_account_management()
        else:
            menu_selection = st.radio("Chức năng", ["📝 Việc Trong Ngày"])
            
        return menu_selection

# --- LUỒNG CHÍNH ---
if not st.session_state.logged_in:
    login()
else:
    menu = render_sidebar()
    
    if st.session_state.role == "Manager":
        if menu == "💻 Quản Lý & Duyệt Việc": 
            manager.render()
        elif menu == "📈 Báo Cáo Nhân Viên": 
            dashboard.render()
    else:
        staff.render()

# --- TRẠM XỬ LÝ RERUN AN TOÀN ---
# Nằm ở dưới cùng để đảm bảo không bị xung đột với các callback hoặc form
if st.session_state.get('need_rerun'):
    st.session_state['need_rerun'] = False
    st.rerun()
