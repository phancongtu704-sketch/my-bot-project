import os
from flask import Flask
import discord
from threading import Thread

# === KHAI BÁO THÔNG SỐ ===
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN") 
PORT = os.environ.get("PORT", 5000)

app = Flask(__name__)
intents = discord.Intents.default()
# Bat Intent nay la bat buoc
intents.message_content = True 
intents.presences = True # Thu them Intent nay

bot = discord.Client(intents=intents) 

def run_bot():
    if DISCORD_BOT_TOKEN:
        bot.run(DISCORD_BOT_TOKEN)
    else:
        print("LỖI: Thiếu Token bot! Vui lòng kiểm tra biến môi trường DISCORD_BOT_TOKEN.")

# === LOGIC BOT DISCORD ===

# 1. Su kien khi bot san sang
@bot.event
async def on_ready():
    print(f"Bot đã sẵn sàng: {bot.user}")

# 2. Lệnh !ping (Su dung on_message don gian)
@bot.event
async def on_message(message):
    # Khong xu ly tin nhan cua chinh bot
    if message.author == bot.user:
        return
        
    # Lenh !ping
    if message.content.startswith('!ping'):
        await message.channel.send('Pong!')
        
    # Lenh !hello (Thu lenh phu)
    if message.content.startswith('!hello'):
        await message.channel.send(f'Xin chao, {message.author.mention}!')

# === LOGIC WEB SERVER (FLASK) ===
@app.route('/')
def home():
    return "<h1>Dashboard Bot HANAMI đang hoạt động! (Deployed)</h1>"

# === CHẠY ĐỒNG THỜI BOT VÀ WEB SERVER ===
if __name__ == '__main__':
    print("Khởi động Bot và Web Server...")
    
    Thread(target=run_bot).start()
    
    print(f"Web Server đang chờ lệnh chạy từ Procfile...")
    
