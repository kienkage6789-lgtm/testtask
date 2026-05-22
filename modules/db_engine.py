import os
import pandas as pd
import json
from datetime import datetime

DB_DIR = "database"
JOBS_DB = f"{DB_DIR}/jobs_db.csv"
HISTORY_DB = f"{DB_DIR}/history_db.csv"
TEMPLATES_DB = f"{DB_DIR}/templates.json"

def init_db():
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
        
    if not os.path.exists(JOBS_DB):
        df_jobs = pd.DataFrame(columns=[
            "job_id", "customer", "description", "assignee", 
            "deadline", "sub_tasks", "progress", "status", "created_at"
        ])
        df_jobs.to_csv(JOBS_DB, index=False)
        
    if not os.path.exists(HISTORY_DB):
        df_history = pd.DataFrame(columns=[
            "job_id", "customer", "description", "assignee", 
            "deadline", "sub_tasks", "progress", "status", "created_at",
            "completed_at", "rating"
        ])
        df_history.to_csv(HISTORY_DB, index=False)

    if not os.path.exists(TEMPLATES_DB):
        default_templates = {
            "Trống (Tự nhập)": [],
            "Quy trình R&D Tiêu chuẩn": [
                {"id": 1, "task_name": "Nghiên cứu yêu cầu khách hàng", "done": False},
                {"id": 2, "task_name": "Thiết kế bản vẽ sơ bộ", "done": False},
                {"id": 3, "task_name": "Thử nghiệm mẫu & Đánh giá", "done": False}
            ]
        }
        with open(TEMPLATES_DB, 'w', encoding='utf-8') as f:
            json.dump(default_templates, f, ensure_ascii=False, indent=4)

def load_jobs(): 
    df = pd.read_csv(JOBS_DB)
    if not df.empty:
        df = df.sort_values(by="deadline", ascending=True)
    return df

def save_jobs(df): df.to_csv(JOBS_DB, index=False)
def load_history(): return pd.read_csv(HISTORY_DB)
def save_history(df): df.to_csv(HISTORY_DB, index=False)

def load_templates():
    with open(TEMPLATES_DB, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_templates(templates_dict):
    with open(TEMPLATES_DB, 'w', encoding='utf-8') as f:
        json.dump(templates_dict, f, ensure_ascii=False, indent=4)

def update_job_progress(job_id, new_sub_tasks, new_progress, new_status):
    df = load_jobs()
    idx = df.index[df['job_id'] == job_id].tolist()[0]
    df.at[idx, 'sub_tasks'] = json.dumps(new_sub_tasks)
    df.at[idx, 'progress'] = new_progress
    df.at[idx, 'status'] = new_status
    save_jobs(df)

def move_to_history(job_id, rating):
    df_jobs = load_jobs()
    df_history = load_history()
    
    job_row = df_jobs[df_jobs['job_id'] == job_id].copy()
    if job_row.empty: return False
        
    job_row['completed_at'] = datetime.now().strftime("%Y-%m-%d %H:%M")
    job_row['rating'] = rating
    job_row['status'] = "Đã duyệt"
    
    df_history = pd.concat([df_history, job_row], ignore_index=True)
    save_history(df_history)
    
    df_jobs = df_jobs[df_jobs['job_id'] != job_id]
    save_jobs(df_jobs)
    return True

# ==========================================
# QUẢN LÝ TÀI KHOẢN NHÂN VIÊN
# ==========================================
import json

USER_FILE = "data/users.json"

def init_users():
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(USER_FILE):
        with open(USER_FILE, "w", encoding="utf-8") as f:
            json.dump(["Manager", "Staff 1", "Staff 2"], f, ensure_ascii=False, indent=4)

def load_users():
    init_users()
    try:
        with open(USER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return ["Manager", "Staff 1", "Staff 2"]

def add_user(name):
    users = load_users()
    if name not in users:
        users.append(name)
        with open(USER_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=4)
        return True
    return False

def delete_user(name):
    users = load_users()
    if name in users:
        users.remove(name)
        with open(USER_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=4)
        return True
    return False
