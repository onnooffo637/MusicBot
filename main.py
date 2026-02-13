import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
import yt_dlp
from aiohttp import web

# --- 1. إعدادات المتغيرات (من السيرفر) ---
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# --- 2. إعداد البوت والاتصال ---
app = Client("music_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
call_py = PyTgCalls(app)

# --- 3. السيرفر الوهمي (Keep-Alive) ---
async def web_handler(request):
    return web.Response(text="Bot is Running High Quality! 🎵")

async def start_web_server():
    # إنشاء سيرفر ويب بسيط
    server = web.Application()
    server.add_routes([web.get('/', web_handler)])
    runner = web.AppRunner(server)
    await runner.setup()
    # السيرفر لازم يسمع على 0.0.0.0 والبورت اللي ريندر بيديهولنا
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌍 Web Server started on port {port}")

# --- 4. دالة التحميل والتشغيل ---
async def download_and_play(query, chat_id):
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'outtmpl': '%(id)s.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192',}],
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
            file_path = f"{info['id']}.mp3"
            
            if not os.path.exists(file_path):
                ydl.download([info['webpage_url']])
            
            return file_path, info['title'], info['thumbnail'], info['duration']
        except Exception as e:
            print(f"Error: {e}")
            return None, None, None, None

# --- 5. أوامر البوت ---

@app.on_message(filters.command("play") & filters.group)
async def play_music(client, message: Message):
    if not message.reply_to_message and len(message.command) < 2:
        await message.reply_text("❗ **عشان تشغل حاجة اكتب:**\n`/play اسم الاغنية`")
        return

    query = message.text.split(None, 1)[1]
    m = await message.reply_text("🔎 **جاري البحث...**")

    try:
        file_path, title, thumbnail, duration = await download_and_play(query, message.chat.id)
        
        if not file_path:
            await m.edit("❌ لم يتم العثور على نتائج.")
            return

        # الدخول للكول والتشغيل
        await call_py.play(
            message.chat.id,
            MediaStream(file_path)
        )

        # تصميم الرسالة الاحترافي
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text="⏸ إيقاف مؤقت", callback_data="pause"),
                    InlineKeyboardButton(text="▶️ استئناف", callback_data="resume"),
                ],
                [
                    InlineKeyboardButton(text="⏹ إيقاف وإنهاء", callback_data="stop"),
                ]
            ]
        )

        await message.reply_photo(
            photo=thumbnail,
            caption=f"💿 **تم التشغيل بنجاح!**\n\n🎵 **الاسم:** `{title}`\n⏱ **المدة:** {duration} ثانية\n👤 **بواسطة:** {message.from_user.mention}",
            reply_markup=buttons
        )
        await m.delete()

    except Exception as e:
        await m.edit(f"حدث خطأ أثناء التشغيل: {e}")

@app.on_callback_query()
async def callbacks(client, callback_query):
    data = callback_query.data
    chat_id = callback_query.message.chat.id
    
    try:
        if data == "pause":
            await call_py.pause_stream(chat_id)
            await callback_query.answer("تم الإيقاف المؤقت ⏸")
        elif data == "resume":
            await call_py.resume_stream(chat_id)
            await callback_query.answer("تم الاستئناف ▶️")
        elif data == "stop":
            await call_py.leave_group_call(chat_id)
            await callback_query.message.delete()
    except Exception as e:
        await callback_query.answer("أمر غير متاح حالياً", show_alert=True)

# --- 6. التشغيل النهائي ---
async def main():
    # تشغيل السيرفر الوهمي أولاً
    await start_web_server()
    # تشغيل البوت
    await app.start()
    await call_py.start()
    print("🤖 Bot & Server Started Successfully!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())