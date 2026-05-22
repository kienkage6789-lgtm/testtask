import streamlit as st
import pandas as pd
from datetime import datetime, time
import json
import uuid
from modules import db_engine, tasks

def render():
    st.header("👑 Bảng Điều Khiển Quản Lý (Manager)")
    
    # 1. Đưa Báo cáo lên làm Tab đầu tiên
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Báo Cáo & Thống Kê", 
        "📝 Giao Việc Mới", 
        "🏃 Giám Sát Tiến Độ", 
        "🔍 Phê Duyệt", 
        "📂 Quản Lý Mẫu Việc", 
        "🗓️ Lịch Sử Hệ Thống"
    ])
    
    # === TAB 1: BÁO CÁO & THỐNG KÊ (MỚI ĐƯA LÊN ĐẦU) ===
    with tab1:
        st.subheader("📊 Thống kê hiệu suất & Tiến độ công việc")
        
        df_jobs = db_engine.load_jobs()
        df_hist = db_engine.load_history()
        
        # Xử lý an toàn các cột thời gian
        now = pd.Timestamp.now()
        if not df_jobs.empty:
            df_jobs['deadline_dt'] = pd.to_datetime(df_jobs['deadline'], format='mixed', errors='coerce')
        if not df_hist.empty:
            df_hist['completed_dt'] = pd.to_datetime(df_hist['completed_at'], format='mixed', errors='coerce')
            df_hist['deadline_dt'] = pd.to_datetime(df_hist['deadline'], format='mixed', errors='coerce')
        
        # Bộ lọc thời gian
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            start_date = st.date_input("Từ ngày (Bộ lọc)", pd.Timestamp.today().date().replace(day=1))
        with col_f2:
            end_date = st.date_input("Đến ngày (Bộ lọc)", pd.Timestamp.today().date())
            
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        
        # Lọc dữ liệu theo ngày
        # Công việc hoàn thành
        filtered_hist = pd.DataFrame()
        if not df_hist.empty:
            mask_hist = (df_hist['completed_dt'] >= start_dt) & (df_hist['completed_dt'] <= end_dt)
            filtered_hist = df_hist.loc[mask_hist]
            
        # Công việc chưa hoàn thành (đang chạy)
        filtered_jobs = pd.DataFrame()
        if not df_jobs.empty:
            # Lấy công việc có hạn chót nằm trong khoảng lọc
            mask_jobs = (df_jobs['deadline_dt'] >= start_dt) & (df_jobs['deadline_dt'] <= end_dt)
            filtered_jobs = df_jobs.loc[mask_jobs]
            
        # Tính toán chỉ số
        count_done = len(filtered_hist)
        count_in_prog = len(filtered_jobs[filtered_jobs['status'] == "Đang tiến hành"]) if not filtered_jobs.empty else 0
        count_review = len(filtered_jobs[filtered_jobs['status'] == "Chờ phê duyệt"]) if not filtered_jobs.empty else 0
        
        # Phân tích việc TRỄ HẠN
        count_late_running = len(filtered_jobs[(filtered_jobs['status'] == "Đang tiến hành") & (filtered_jobs['deadline_dt'] < now)]) if not filtered_jobs.empty else 0
        count_late_done = len(filtered_hist[filtered_hist['completed_dt'] > filtered_hist['deadline_dt']]) if not filtered_hist.empty else 0

        # Hiển thị số liệu tổng quan
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("✅ Đã hoàn thành", count_done)
        c2.metric("🏃 Đang tiến hành", count_in_prog)
        c3.metric("🔍 Chờ phê duyệt", count_review)
        c4.metric("🚨 Vi phạm tiến độ (Trễ)", count_late_running + count_late_done)
        
        st.markdown("---")
        
        # Biểu đồ trạng thái công việc
        st.write("**Biểu đồ phân bổ trạng thái công việc trong kỳ**")
        chart_data = pd.DataFrame({
            "Trạng thái": ["Hoàn thành (Đúng hạn)", "Hoàn thành (Trễ hạn)", "Đang chạy (Đúng hạn)", "Đang chạy (Trễ hạn)", "Chờ phê duyệt"],
            "Số lượng": [
                count_done - count_late_done, 
                count_late_done, 
                count_in_prog - count_late_running, 
                count_late_running, 
                count_review
            ]
        }).set_index("Trạng thái")
        
        st.bar_chart(chart_data)
        
        # Bảng Đánh giá nhân viên (Tính số việc trễ)
        st.markdown("### 👤 Đánh Giá Nhân Viên (Dựa trên lịch sử)")
        if not filtered_hist.empty:
            filtered_hist['is_late'] = filtered_hist['completed_dt'] > filtered_hist['deadline_dt']
            staff_stats = filtered_hist.groupby('assignee').agg(
                Tổng_việc=('job_id', 'count'),
                Hoàn_thành_trễ=('is_late', 'sum')
            ).reset_index()
            staff_stats['Tỉ lệ trễ (%)'] = round((staff_stats['Hoàn_thành_trễ'] / staff_stats['Tổng_việc']) * 100, 2)
            st.dataframe(staff_stats, use_container_width=True, hide_index=True)
        else:
            st.info("Chưa có dữ liệu hoàn thành trong khoảng thời gian này.")
    
    # === TAB 2: GIAO VIỆC ===
    with tab2:
        st.subheader("📝 Tạo Đầu Việc Mới")
        
        template_choice = st.selectbox("Tải nhanh mẫu công việc có sẵn", tasks.get_template_names(), key="job_template")
        template_data = tasks.get_tasks_from_template(template_choice)
        
        with st.form("new_job_form", clear_on_submit=True):
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                customer = st.text_input("Tên Khách Hàng / Dự Án")
                assignee = st.selectbox("Người Phụ Trách", ["Staff 1", "Staff 2", "Staff 3"])
            with col2:
                deadline_date = st.date_input("Hạn Chót (Ngày)")
            with col3:
                deadline_time = st.time_input("Hạn Chót (Giờ)", value=time(17, 30))
                
            description = st.text_area("Mô tả nội dung chính cần thực hiện")
            
            st.write("**Danh sách các việc con:**")
            df_tasks = pd.DataFrame([{"Nhiệm vụ": t["task_name"]} for t in template_data]) if template_data else pd.DataFrame(columns=["Nhiệm vụ"])
            edited_tasks = st.data_editor(df_tasks, num_rows="dynamic", use_container_width=True, key=f"editor_{template_choice}")
            
            if st.form_submit_button("Giao Việc", type="primary"):
                if customer == "" or description == "":
                    st.error("Vui lòng điền đủ tên khách hàng và mô tả!")
                else:
                    final_tasks = []
                    if "Nhiệm vụ" in edited_tasks.columns:
                        for i, row in edited_tasks.iterrows():
                            if pd.notna(row["Nhiệm vụ"]) and str(row["Nhiệm vụ"]).strip() != "":
                                final_tasks.append({"id": i+1, "task_name": str(row["Nhiệm vụ"]), "done": False})
                    
                    full_deadline_str = f"{deadline_date.strftime('%Y-%m-%d')} {deadline_time.strftime('%H:%M')}"
                    df = db_engine.load_jobs()
                    new_job = {
                        "job_id": str(uuid.uuid4())[:8],
                        "customer": customer,
                        "description": description,
                        "assignee": assignee,
                        "deadline": full_deadline_str,
                        "sub_tasks": json.dumps(final_tasks),
                        "progress": 0.0,
                        "status": "Đang tiến hành",
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    df = pd.concat([df, pd.DataFrame([new_job])], ignore_index=True)
                    db_engine.save_jobs(df)
                    st.success(f"🎉 Đã giao việc thành công cho {assignee}!")

    # === TAB 3: GIÁM SÁT TIẾN ĐỘ (CÓ CẢNH BÁO CHẬM) ===
    with tab3:
        st.subheader("🏃 Các công việc đang tiến hành")
        df = db_engine.load_jobs()
        jobs_in_progress = df[df['status'] == "Đang tiến hành"]
        
        if jobs_in_progress.empty:
            st.info("Hiện không có công việc nào đang chạy.")
        else:
            now = pd.Timestamp.now()
            cols = st.columns(2)
            for i, (_, row) in enumerate(jobs_in_progress.iterrows()):
                deadline_dt = pd.to_datetime(row['deadline'], format='mixed', errors='coerce')
                is_late = pd.notna(deadline_dt) and deadline_dt < now
                
                with cols[i % 2]:
                    # Nếu trễ hạn, hiển thị khung cảnh báo nổi bật
                    if is_late:
                        container = st.container(border=True)
                        container.error(f"🔴 **CHẬM TIẾN ĐỘ** | 👤 {row['assignee']}")
                    else:
                        container = st.container(border=True)
                        container.info(f"🟢 **Trong hạn** | 👤 {row['assignee']}")
                        
                    with container:
                        st.markdown(f"### 📌 {row['customer']}")
                        st.caption(f"⏳ **Hạn chót:** {row['deadline']}")
                        st.write(f"**Nội dung:** {row['description']}")
                        st.progress(row['progress'] / 100, text=f"Tiến độ: {row['progress']}%")
                        
                        with st.expander("✏️ Cập nhật / Xóa việc này"):
                            edit_customer = st.text_input("Dự Án", value=row['customer'], key=f"edit_cust_{row['job_id']}")
                            edit_desc = st.text_area("Mô tả", value=row['description'], key=f"edit_desc_{row['job_id']}")
                            
                            sub_tasks = tasks.parse_sub_tasks(row['sub_tasks'])
                            df_sub_edit = pd.DataFrame([{"Nhiệm vụ": t["task_name"], "Đã xong": t["done"]} for t in sub_tasks])
                            edited_sub_df = st.data_editor(df_sub_edit, num_rows="dynamic", use_container_width=True, key=f"edit_sub_{row['job_id']}")
                            
                            c_update, c_del = st.columns(2)
                            with c_update:
                                if st.button("Lưu", key=f"btn_update_{row['job_id']}", type="secondary", use_container_width=True):
                                    updated_tasks = []
                                    done_count = 0
                                    if "Nhiệm vụ" in edited_sub_df.columns:
                                        for idx_row, r in edited_sub_df.iterrows():
                                            if pd.notna(r["Nhiệm vụ"]) and str(r["Nhiệm vụ"]).strip() != "":
                                                is_done = bool(r["Đã xong"]) if "Đã xong" in edited_sub_df.columns else False
                                                if is_done: done_count += 1
                                                updated_tasks.append({"id": idx_row+1, "task_name": str(r["Nhiệm vụ"]), "done": is_done})
                                    
                                    new_prog = int((done_count / len(updated_tasks) * 100)) if len(updated_tasks) > 0 else 100
                                    df_all = db_engine.load_jobs()
                                    idx = df_all.index[df_all['job_id'] == row['job_id']].tolist()[0]
                                    df_all.at[idx, 'customer'] = edit_customer
                                    df_all.at[idx, 'description'] = edit_desc
                                    df_all.at[idx, 'sub_tasks'] = json.dumps(updated_tasks)
                                    df_all.at[idx, 'progress'] = new_prog
                                    db_engine.save_jobs(df_all)
                                    st.rerun()
                                    
                            with c_del:
                                if st.button("Xóa", key=f"btn_del_{row['job_id']}", type="primary", use_container_width=True):
                                    df_all = db_engine.load_jobs()
                                    df_all = df_all[df_all['job_id'] != row['job_id']]
                                    db_engine.save_jobs(df_all)
                                    st.rerun()

    # === TAB 4: CHỜ PHÊ DUYỆT ===
    with tab4:
        st.subheader("🔍 Yêu cầu nghiệm thu từ nhân viên")
        df = db_engine.load_jobs()
        jobs_in_review = df[df['status'] == "Chờ phê duyệt"]
        
        if jobs_in_review.empty:
            st.info("Tuyệt vời! Không có công việc nào đang chờ duyệt.")
        else:
            now = pd.Timestamp.now()
            cols = st.columns(2)
            for i, (_, row) in enumerate(jobs_in_review.iterrows()):
                deadline_dt = pd.to_datetime(row['deadline'], format='mixed', errors='coerce')
                is_late = pd.notna(deadline_dt) and deadline_dt < now
                
                with cols[i % 2]:
                    container = st.container(border=True)
                    if is_late:
                        container.warning(f"⚠️ **NỘP TRỄ HẠN** | 👤 {row['assignee']}")
                    else:
                        container.success(f"✅ **Nộp đúng hạn** | 👤 {row['assignee']}")
                        
                    with container:
                        st.markdown(f"### 📌 {row['customer']}")
                        st.caption(f"⏳ **Hạn chót:** {row['deadline']}")
                        st.write(f"**Nội dung:** {row['description']}")
                        
                        st.markdown("**Đánh giá & Nghiệm thu:**")
                        c_ok, c_ex = st.columns(2)
                        with c_ok:
                            if st.button("✅ Duyệt (Đạt)", key=f"btn_ok_{row['job_id']}", use_container_width=True):
                                db_engine.move_to_history(row['job_id'], "Hoàn thành")
                                st.rerun()
                        with c_ex:
                            if st.button("🌟 Xuất Sắc", key=f"btn_ex_{row['job_id']}", type="primary", use_container_width=True):
                                db_engine.move_to_history(row['job_id'], "Xuất sắc")
                                st.rerun()
                        
                        if st.button("🔙 Từ chối (Yêu cầu làm lại)", key=f"btn_rej_{row['job_id']}", use_container_width=True):
                            sub_tasks = tasks.parse_sub_tasks(row['sub_tasks'])
                            db_engine.update_job_progress(row['job_id'], sub_tasks, 90, "Đang tiến hành")
                            st.rerun()

    # === TAB 5: QUẢN LÝ MẪU VIỆC ===
    with tab5:
        st.subheader("📂 Thiết Kế Mẫu Công Việc")
        current_templates = db_engine.load_templates()
        options = ["➕ Tạo mẫu hoàn toàn mới"] + list(current_templates.keys())
        edit_target = st.selectbox("Chọn mẫu để thao tác", options)
        
        if edit_target == "➕ Tạo mẫu hoàn toàn mới":
            template_name_input = st.text_input("Nhập tên cho mẫu công việc mới của bạn:")
            df_edit = pd.DataFrame(columns=["Nhiệm vụ"])
        else:
            template_name_input = edit_target
            df_edit = pd.DataFrame([{"Nhiệm vụ": t["task_name"]} for t in current_templates[edit_target]]) if current_templates[edit_target] else pd.DataFrame(columns=["Nhiệm vụ"])
            
        edited_template_df = st.data_editor(df_edit, num_rows="dynamic", use_container_width=True, key=f"edit_mode_{edit_target}")
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            if st.button("💾 Lưu Cấu Hình Mẫu Việc", type="primary"):
                if template_name_input.strip() == "":
                    st.error("Tên mẫu không được để trống!")
                else:
                    final_tasks = []
                    if "Nhiệm vụ" in edited_template_df.columns:
                        for i, r in edited_template_df.iterrows():
                            if pd.notna(r["Nhiệm vụ"]) and str(r["Nhiệm vụ"]).strip() != "":
                                final_tasks.append({"id": i+1, "task_name": str(r["Nhiệm vụ"]), "done": False})
                    db_engine.save_template(template_name_input, final_tasks)
                    st.success("Đã lưu mẫu thành công!")
                    
        with col_t2:
            if edit_target != "➕ Tạo mẫu hoàn toàn mới":
                if st.button("🗑️ Xóa Mẫu Này", type="secondary"):
                    db_engine.delete_template(edit_target)
                    st.rerun()

    # === TAB 6: LỊCH SỬ HỆ THỐNG ===
    with tab6:
        st.subheader("🗓️ Nhật ký công việc đã xử lý")
        df_hist = db_engine.load_history()
        
        if df_hist.empty:
            st.info("Chưa có lịch sử công việc nào.")
        else:
            # Gắn nhãn trễ hạn
            df_hist['completed_dt'] = pd.to_datetime(df_hist['completed_at'], format='mixed', errors='coerce')
            df_hist['deadline_dt'] = pd.to_datetime(df_hist['deadline'], format='mixed', errors='coerce')
            df_hist['Tình trạng'] = df_hist.apply(lambda r: "🔴 Trễ hạn" if r['completed_dt'] > r['deadline_dt'] else "🟢 Đúng hạn", axis=1)
            
            # Format bảng hiển thị
            display_df = df_hist[['job_id', 'customer', 'assignee', 'Tình trạng', 'rating', 'completed_at', 'deadline']].copy()
            display_df = display_df.rename(columns={
                "job_id": "Mã Việc", "customer": "Dự án/Khách", "assignee": "Nhân viên",
                "rating": "Đánh giá", "completed_at": "Ngày xong", "deadline": "Hạn chót"
            })
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
