import streamlit as st
from modules import db_engine

def render_account_management():
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Quản lý Nhân Viên")
    
    users = db_engine.load_users()
    
    # --- THÊM NHÂN VIÊN ---
    with st.sidebar.form("add_user_form", clear_on_submit=True):
        new_user = st.text_input("Tên nhân viên mới")
        submitted = st.form_submit_button("➕ Thêm nhân viên", use_container_width=True)
        if submitted and new_user:
            if db_engine.add_user(new_user.strip()):
                st.success(f"Đã thêm {new_user}!")
                st.session_state['need_rerun'] = True
            else:
                st.error("Tên đã tồn tại!")
                
    # --- XOÁ NHÂN VIÊN ---
    staff_only = [u for u in users if u != "Manager"]
    if staff_only:
        with st.sidebar.form("del_user_form"):
            user_to_del = st.selectbox("Chọn nhân viên để xoá", staff_only)
            del_submitted = st.form_submit_button("❌ Xoá nhân viên", use_container_width=True)
            if del_submitted and user_to_del:
                if db_engine.delete_user(user_to_del):
                    st.success(f"Đã xoá {user_to_del}!")
                    st.session_state['need_rerun'] = True
