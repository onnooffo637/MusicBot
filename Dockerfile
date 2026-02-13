FROM python:3.10-slim-bookworm

# تحديث النظام وتنزيل FFmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg git build-essential && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# تحديث pip
RUN pip install --upgrade pip

# تنزيل المكتبات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نقل الملفات
COPY . .

# أمر التشغيل
CMD ["python", "main.py"]
