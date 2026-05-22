import streamlit as st
import pandas as pd
import plotly.express as px
from modules import db_engine

def render():
    st.header("📊 Báo Cáo Hiệu Suất & Đánh Giá Nhân Viên")
    
    df_jobs = db_engine.load_jobs()
    df_history = db_engine.load_history()
    
    # === THIẾT LẬP BỘ LỌC CẤP CAO ===
    st.markdown("### 🔍 Bộ Lọc Đánh Giá")
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        staff_filter = st.selectbox("Chọn Nhân Viên", ["Tất cả nhân viên", "Staff 1", "Staff 2", "Staff 3"])
    
    # Xác định mốc thời gian lọc
    all_dates = []
    if not df_jobs.empty:
        all_dates += pd.to_datetime(df_jobs['created_at'], format='mixed', errors='coerce').dt.date.tolist()
    if not df_history.empty:
        all_dates += pd.to_datetime(df_history['completed_at'], format='mixed', errors='coerce').dt.date.tolist()
        
    min_date = min(all_dates) if all_dates else pd.datetime.today().date()
    max_date = max(all_dates) if all_dates else pd.datetime.today().date()
    
    with col_f2:
        filter_start = st.date_input("Lọc từ ngày", min_date)
    with col_f3:
        filter_end = st.date_input("Đến ngày", max_date)
        
    # --- TIẾN HÀNH LỌC DỮ LIỆU ---
    if staff_filter != "Tất cả nhân viên":
        if not df_jobs.empty:
            df_jobs = df_jobs[df_jobs['assignee'] == staff_filter]
        if not df_history.empty:
            df_history = df_history[df_history['assignee'] == staff_filter]
            
    if not df_jobs.empty:
        df_jobs['date_pure'] = pd.to_datetime(df_jobs['created_at'], format='mixed', errors='coerce').dt.date
        df_jobs = df_jobs[(df_jobs['date_pure'] >= filter_start) & (df_jobs['date_pure'] <= filter_end)]
        
    if not df_history.empty:
        df_history['date_pure'] = pd.to_datetime(df_history['completed_at'], format='mixed', errors='coerce').dt.date
        df_history = df_history[(df_history['date_pure'] >= filter_start) & (df_history['date_pure'] <= filter_end)]

    # --- HIỂN THỊ SỐ LIỆU ---
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(label="Việc đang xử lý", value=len(df_jobs[df_jobs['status'] == "Đang tiến hành"]))
    with c2:
        st.metric(label="Việc chờ nghiệm thu", value=len(df_jobs[df_jobs['status'] == "Chờ phê duyệt"]))
    with c3:
        st.metric(label="Việc đã hoàn thành duyệt", value=len(df_history))
        
    # --- ĐỒ THỊ TRỰC QUAN ---
    st.markdown("---")
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("📈 Tiến độ chi tiết theo đầu việc")
        if not df_jobs.empty:
            fig = px.bar(df_jobs, x="customer", y="progress", color="assignee", text="progress",
                         title="Tiến độ % của các việc hiện tại", barmode="group")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Không có dữ liệu tiến độ trong khoảng thời gian/nhân viên đã chọn.")
            
    with col_chart2:
        st.subheader("⭐ Đánh giá xếp loại chất lượng")
        if not df_history.empty:
            fig2 = px.pie(df_history, names="rating", title="Tỷ lệ đánh giá năng lực",
                          color_discrete_map={'Hoàn thành':'#636EFA', 'Xuất sắc':'#00CC96'})
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu lịch sử hoàn thành phù hợp bộ lọc.")
