FROM python:3.11
RUN apt-get update && apt-get install -y libgl1-mesa-glx
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
# สร้างโฟลเดอร์สำหรับ AI
RUN mkdir -p /.deepface && chmod 777 /.deepface
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]