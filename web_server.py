# File: web_server.py (Code Web Server + Discord Bot - Dùng Biến Môi Trường)

from flask import Flask, jsonify
import disnake
from disnake.ext import commands
import threading
import os # Thư viện cần thiết để đọc biến môi trường

# -------------------------------------------------------------------
# 1. CẤU HÌNH
# -------------------------------------------------------------------
# LẤY TOKEN TỪ BIẾN MÔI TRƯỜNG (Tuyệt đối KHÔNG dán Token ở đây!)
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN") 

# Cấu hình Intents
intents = disnake.Intents.default()
intents.messages = True
intents.message_content = True 

# Khởi tạo Bot và Flask
bot = commands.Bot(command_prefix="!", intents=intents)
app = Flask(__name__)

# -------------------------------------------------------------------
# 2. LOGIC DISCORD BOT
# -------------------------------------------------------------------

@bot.event
async def on_ready():
    print(f"🎉 Discord Bot Đã Đăng Nhập: {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
        
    user_text = message.content.lower()
    
    # Kiểm tra lệnh !hello
    if user_text == '!hello':
        await message.channel.send(f"Chào {message.author.mention}! Bot Discord đang chạy trên Web Server (Token bảo mật).")
    
    await bot.process_commands(message)

# -------------------------------------------------------------------
# 3. LOGIC FLASK WEB SERVER
# -------------------------------------------------------------------

@app.route('/', methods=['GET'])
def home():
    # Kiểm tra xem Bot đã đăng nhập chưa
    bot_status = f"{bot.user} (Online)" if bot.is_ready() else "Bot đang khởi động..."
    return f"<h1>Discord Bot Web Server is Running!</h1><p>Bot Status: {bot_status}</p>"

# -------------------------------------------------------------------
# 4. CHẠY CẢ HAI CÙNG LÚC
# -------------------------------------------------------------------

def run_flask():
    """Chạy Flask Web Server."""
    if not DISCORD_BOT_TOKEN:
        print("🚨 Lỗi: KHÔNG tìm thấy DISCORD_BOT_TOKEN. Vui lòng thêm vào Biến Môi trường Render.")
        return

    # Khởi tạo và chạy Bot Discord trong một luồng (thread) riêng
    discord_thread = threading.Thread(target=lambda: bot.loop.run_until_complete(bot.start(DISCORD_BOT_TOKEN)))
    discord_thread.start()
    
    # Bật Flask Web Server trong luồng chính
    print("Web Server đã khởi động trên 0.0.0.0:5000")
    app.run(host='0.0.0.0', port=os.environ.get("PORT", 5000), debug=False)


if __name__ == '__main__':
    run_flask()
        
