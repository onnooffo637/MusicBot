# نستخدم نسخة بايثون خفيفة ومستقرة
FROM python:3.10-slim-buster

# تحديث النظام وتنزيل FFmpeg (مهم جداً للصوت) و Git
RUN apt-get update && apt-get install -y ffmpeg git && apt-get clean

# إعداد مجلد العمل
WORKDIR /app

# نسخ ملف المتطلبات وتنزيل المكاتب
COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات البوت
COPY . .

# فتح البورت للسيرفر الوهمي (عشان ريندر يشوفه)
EXPOSE 8080

# أمر التشغيل
CMD ["python3", "main.py"]