import streamlit as st
import pandas as pd
from modules import db_engine, tasks
import json

def render():
    current_user = st.session_state.get("current_user", "Staff 1")
    
    st.header(f"👋 Bảng Việc Của {current_user}")
    st.markdown("---")
    
    tab_todo, tab_review, tab_done = st.tabs([
        "🚀 Đang Xử Lý", 
        "⏳ Chờ Phê Duyệt", 
        "✅ Lịch Sử Hoàn Thành"
    ])
    
    df = db_engine.load_jobs()
    now = pd.Timestamp.now()
    
    with tab_todo:
        st.subheader("🏃 Các công việc cần hoàn thành")
        my_jobs = df[(df['assignee'] == current_user) & (df['status'] == "Đang tiến hành")]
        
        if my_jobs.empty:
            st.info("Tuyệt vời! Bạn không có công việc nào đang tồn đọng.")
        else:
            cols = st.columns(2)
            for i, (_, row) in enumerate(my_jobs.iterrows()):
                deadline_dt = pd.to_datetime(row['deadline'], format='mixed', errors='coerce')
                is_late = pd.notna(deadline_dt) and deadline_dt < now
                
                with cols[i % 2]:
                    container = st.container(border=True)
                    with container:
                        if is_late:
                            st.error(f"🔴 **CHẬM TIẾN ĐỘ** | ⏳ Hạn: {row['deadline']}")
                        else:
                            st.success(f"🟢 **Trong hạn** | ⏳ Hạn: {row['deadline']}")
                            
                        st.markdown(f"### 📌 {row['customer']}")
                        st.write(f"*{row['description']}*")
                        
                        sub_tasks = tasks.parse_sub_tasks(row['sub_tasks'])
                        df_sub = pd.DataFrame([{"Nhiệm vụ": t["task_name"], "Đã xong": t["done"]} for t in sub_tasks])
                        
                        with st.form(f"form_todo_{row['job_id']}", border=False):
                            if len(df_sub) > 0:
                                with st.expander("📝 Bấm để xem/cập nhật đầu mục nhiệm vụ"):
                                    edited_df = st.data_editor(df_sub, hide_index=True, use_container_width=True, key=f"edit_{row['job_id']}")
                            else:
                                st.write("*(Không có đầu mục con)*")
                                edited_df = pd.DataFrame()
                            
                            c_save, c_submit = st.columns(2)
                            with c_save:
                                if st.form_submit_button("💾 Lưu Tiến Độ", use_container_width=True):
                                    done_count = 0
                                    updated_tasks = []
                                    if "Nhiệm vụ" in edited_df.columns:
                                        for idx, r in edited_df.iterrows():
                                            is_done = bool(r["Đã xong"]) if "Đã xong" in edited_df.columns else False
                                            if is_done: done_count += 1
                                            updated_tasks.append({"id": idx+1, "task_name": str(r["Nhiệm vụ"]), "done": is_done})
                                    
                                    new_prog = int((done_count / len(updated_tasks) * 100)) if len(updated_tasks) > 0 else 100
                                    db_engine.update_job_progress(row['job_id'], updated_tasks, new_prog, "Đang tiến hành")
                                    # CHỈ GÁN CỜ, KHÔNG GỌI RERUN Ở ĐÂY
                                    st.session_state['need_rerun'] = True
                                    
                            with c_submit:
                                if st.form_submit_button("🚀 Gửi Duyệt", type="primary", use_container_width=True):
                                    updated_tasks = []
                                    if "Nhiệm vụ" in edited_df.columns:
                                        for idx, r in edited_df.iterrows():
                                            updated_tasks.append({"id": idx+1, "task_name": str(r["Nhiệm vụ"]), "done": True})
                                    db_engine.update_job_progress(row['job_id'], updated_tasks, 100, "Chờ phê duyệt")
                                    # CHỈ GÁN CỜ, KHÔNG GỌI RERUN Ở ĐÂY
                                    st.session_state['need_rerun'] = True

    with tab_review:
        st.subheader("🔍 Công việc đang chờ Sếp duyệt")
        my_review_jobs = df[(df['assignee'] == current_user) & (df['status'] == "Chờ phê duyệt")]
        
        if my_review_jobs.empty:
            st.info("Không có việc nào đang chờ duyệt.")
        else:
            cols_rev = st.columns(2)
            for i, (_, row) in enumerate(my_review_jobs.iterrows()):
                deadline_dt = pd.to_datetime(row['deadline'], format='mixed', errors='coerce')
                is_late = pd.notna(deadline_dt) and deadline_dt < now
                
                with cols_rev[i % 2]:
                    container = st.container(border=True)
                    with container:
                        if is_late:
                            st.warning(f"⚠️ Nộp khi đã trễ hạn | ⏳ {row['deadline']}")
                        else:
                            st.info(f"⏳ Đã nộp đúng hạn | Hạn gốc: {row['deadline']}")
                            
                        st.markdown(f"### 📌 {row['customer']}")
                        st.progress(row['progress'] / 100, text=f"Tiến độ hoàn thành: {row['progress']}%")
                        st.caption("Đang chờ quản lý kiểm tra và nghiệm thu...")

    with tab_done:
        st.subheader("📊 Lịch sử công việc (Dạng Bảng)")
        df_hist = db_engine.load_history()
        
        if df_hist.empty:
            st.info("Hệ thống chưa có lịch sử.")
        else:
            my_hist = df_hist[df_hist['assignee'] == current_user].copy()
            if my_hist.empty:
                st.info("Bạn chưa hoàn thành việc nào.")
            else:
                my_hist['completed_dt'] = pd.to_datetime(my_hist['completed_at'], format='mixed', errors='coerce')
                my_hist['deadline_dt'] = pd.to_datetime(my_hist['deadline'], format='mixed', errors='coerce')
                
                my_hist['Đánh giá Tiến độ'] = my_hist.apply(
                    lambda r: "🔴 Chậm tiến độ" if pd.notna(r['completed_dt']) and pd.notna(r['deadline_dt']) and r['completed_dt'] > r['deadline_dt'] else "🟢 Kịp tiến độ", 
                    axis=1
                )
                
                display_df = my_hist[['job_id', 'customer', 'Đánh giá Tiến độ', 'rating', 'completed_at', 'deadline']].rename(columns={
                    "job_id": "Mã Việc", "customer": "Khách hàng/Dự án", "rating": "Kết quả", 
                    "completed_at": "Thời gian Xong", "deadline": "Hạn chót"
                })
                display_df = display_df.sort_values(by="Thời gian Xong", ascending=False)
                st.dataframe(display_df, use_container_width=True, hide_index=True)

    # ==============================================================
    # NƠI XỬ LÝ RERUN AN TOÀN - THỰC HIỆN Ở DƯỚI CÙNG, NGOÀI FORM
    # ==============================================================
    if st.session_state.get('need_rerun'):
        st.session_state['need_rerun'] = False
        st.rerun()
