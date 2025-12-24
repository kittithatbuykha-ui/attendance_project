from fastapi import FastAPI, File, UploadFile, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from deepface import DeepFace
import os
import pandas as pd
from datetime import datetime
import shutil

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# ข้อมูลรายวิชา
COURSE_SETTINGS = {
    "subject": "วิทยาการคำนวณ",
    "room": "ห้องคอมพิวเตอร์ 1",
    "teacher": "ครูประเสริฐ",
    "start_time": "08:30",
    "late_time": "08:40"
}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "info": COURSE_SETTINGS})

@app.get("/teacher", response_class=HTMLResponse)
async def teacher_dashboard(request: Request):
    attendance_data = []
    if os.path.exists("attendance.csv"):
        df = pd.read_csv("attendance.csv")
        attendance_data = df.to_dict(orient="records")
    return templates.TemplateResponse("teacher.html", {"request": request, "data": attendance_data, "info": COURSE_SETTINGS})

# --- ระบบลงทะเบียนนักเรียนใหม่ ---
@app.post("/register")
async def register_student(
    name: str = Form(...),
    student_id: str = Form(...),
    grade: str = Form(...),
    no: str = Form(...),
    file: UploadFile = File(...)
):
    if not os.path.exists("known_faces"): os.makedirs("known_faces")
    
    # บันทึกไฟล์รูปโดยใช้ชื่อ: ชื่อ-เลขประจำตัว-ชั้น-เลขที่.jpg
    file_extension = file.filename.split(".")[-1]
    new_filename = f"{name}_{student_id}_{grade}_{no}.{file_extension}"
    file_path = os.path.join("known_faces", new_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return JSONResponse(content={"status": "success", "message": f"ลงทะเบียน {name} เรียบร้อยแล้ว"})

@app.post("/scan")
async def scan(file: UploadFile = File(...)):
    if not os.path.exists("temp"): os.makedirs("temp")
    temp_path = "temp/current.jpg"
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    name_display = "Unknown"
    now = datetime.now()
    time_str = now.strftime("%H:%M:%S")
    date_str = now.strftime("%Y-%m-%d")

    try:
        result = DeepFace.find(img_path=temp_path, db_path="known_faces", enforce_detection=False, silent=True)
        if len(result) > 0 and not result[0].empty:
            full_path = result[0]['identity'][0]
            file_name = os.path.basename(full_path).split(".")[0]
            
            # แยกข้อมูลจากชื่อไฟล์ (name_id_grade_no)
            parts = file_name.split("_")
            name_display = parts[0]
            student_id = parts[1] if len(parts) > 1 else "-"
            grade_info = f"{parts[2]}/{parts[3]}" if len(parts) > 3 else "-"

            current_time = now.time()
            late_limit = datetime.strptime(COURSE_SETTINGS["late_time"], "%H:%M").time()
            status = "มาเรียนปกติ" if current_time <= late_limit else "มาสาย"

            log_data = {
                "วันที่": [date_str],
                "เวลา": [time_str],
                "รหัส": [student_id],
                "ชื่อนักเรียน": [name_display],
                "ชั้น/เลขที่": [grade_info],
                "สถานะ": [status]
            }
            df = pd.DataFrame(log_data)
            df.to_csv("attendance.csv", mode='a', index=False, header=not os.path.exists("attendance.csv"), encoding='utf-8-sig')
            
    except Exception as e:
        print(f"Error: {e}")

    return {"name": name_display, "time": time_str}