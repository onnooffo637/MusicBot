import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
import yt_dlp
from aiohttp import web

# --- 1. التأكد من المتغيرات ---
# هنا بنطبع رسالة في اللوج عشان نتأكد إن البيانات مقروءة صح
api_id_env = os.environ.get("API_ID", "0")
print(f"DEBUG: API_ID is set to: {api_id_env}") 

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")


# --- 2. إعداد البوت (التعديل: التشغيل في الذاكرة) ---
app = Client(
    "music_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True # <--- ده بيحل مشاكل كتير في سيرفرات دوكر
)
call_py = PyTgCalls(app)

# --- 3. السيرفر الوهمي ---
async def web_handler(request):
    return web.Response(text="Bot is Running High Quality! 🎵")

async def start_web_server():
    server = web.Application()
    server.add_routes([web.get('/', web_handler)])
    runner = web.AppRunner(server)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌍 Web Server started on port {port}")

# --- 4. دالة التحميل ---
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
            return None, None, None, None

# --- 5. الأوامر ---
@app.on_message(filters.command("play") & filters.group)
async def play_music(client, message):
    if not message.reply_to_message and len(message.command) < 2:
        await message.reply_text("❗ **/play اسم الاغنية**")
        return

    query = message.text.split(None, 1)[1]
    m = await message.reply_text("🔎 **جاري البحث...**")

    try:
        file_path, title, thumbnail, duration = await download_and_play(query, message.chat.id)
        
        if not file_path:
            await m.edit("❌ لم يتم العثور على نتائج.")
            return

        await call_py.play(message.chat.id, MediaStream(file_path))

        buttons = InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="⏹ إنهاء", callback_data="stop")]]
        )

        await message.reply_photo(
            photo=thumbnail,
            caption=f"💿 **تم التشغيل!**\n🎵 `{title}`",
            reply_markup=buttons
        )
        await m.delete()

    except Exception as e:
        await m.edit(f"خطأ: {e}")

@app.on_callback_query()
async def callbacks(client, callback_query):
    if callback_query.data == "stop":
        try:
            await call_py.leave_group_call(callback_query.message.chat.id)
            await callback_query.message.delete()
        except:
            pass

# --- 6. التشغيل ---
async def main():
    await start_web_server()
    print("🚀 Starting Pyrogram Client...")
    await app.start()
    print("🚀 Starting PyTgCalls...")
    await call_py.start()
    print("✅ Bot Started Successfully!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

