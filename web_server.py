import os
from flask import Flask
import discord
from threading import Thread

# === KHAI BÁO THÔNG SỐ ===
# Lấy TOKEN bot từ biến môi trường (Render sẽ cung cấp)
# Giữ an toàn: Token sẽ được đặt trong cài đặt Render chứ không phải trong code này
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN") 
# Lấy cổng từ biến môi trường (Render sẽ cung cấp), mặc định là 5000
PORT = os.environ.get("PORT", 5000)

app = Flask(__name__)
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

def run_bot():
    # Kiểm tra Token trước khi chạy bot
    if DISCORD_BOT_TOKEN:
        bot.run(DISCORD_BOT_TOKEN)
    else:
        # Lỗi này sẽ xuất hiện trong log của Render nếu bạn quên đặt biến môi trường
        print("LỖI: Thiếu Token bot! Vui lòng kiểm tra biến môi trường DISCORD_BOT_TOKEN trên Render.")

# === LOGIC BOT DISCORD ===
@bot.event
async def on_ready():
    # Dòng này sẽ xuất hiện trong log của Render khi bot hoạt động
    print(f"Bot đã sẵn sàng: {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    # Lệnh kiểm tra bot
    if message.content.startswith('!ping'):
        await message.channel.send('Pong!')

# === LOGIC WEB SERVER (FLASK) ===
@app.route('/')
def home():
    # Nội dung Dashboard của bạn
    return "<h1>Dashboard Bot HANAMI đang hoạt động!</h1><p>Bot đang chạy trên Render Free Tier.</p>"

# === CHẠY ĐỒNG THỜI BOT VÀ WEB SERVER ===
if __name__ == '__main__':
    print("Khởi động Bot và Web Server...")
    
    # 1. Chạy Bot trong luồng riêng (Bot chạy 24/7)
    Thread(target=run_bot).start()
    
    # 2. Web Server được Gunicorn xử lý (theo Procfile)
    print(f"Web Server đang chờ lệnh chạy từ Procfile...")
    
