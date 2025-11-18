import os
from flask import Flask
import discord
from threading import Thread
from discord.ext import commands # Dùng commands.Bot

# === KHAI BÁO THÔNG SỐ ===
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN") 
PORT = os.environ.get("PORT", 5000)

app = Flask(__name__)
intents = discord.Intents.default()
intents.message_content = True 
intents.presences = True # Bật tất cả Intents

# SỬ DỤNG COMMANDS.BOT
bot = commands.Bot(command_prefix='!', intents=intents) 

def run_bot():
    if DISCORD_BOT_TOKEN:
        bot.run(DISCORD_BOT_TOKEN)
    else:
        print("LỖI: Thiếu Token bot! Vui lòng kiểm tra biến môi trường DISCORD_BOT_TOKEN.")

# === LOGIC BOT DISCORD ===

@bot.event
async def on_ready():
    print(f"Bot đã sẵn sàng: {bot.user}")

# SỬ DỤNG @BOT.COMMAND()
@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

# === LOGIC WEB SERVER (FLASK) ===
@app.route('/')
def home():
    return "<h1>Dashboard Bot HANAMI đang hoạt động! (Deployed)</h1>"

# === CHẠY ĐỒNG THỜI BOT VÀ WEB SERVER ===
if __name__ == '__main__':
    print("Khởi động Bot và Web Server...")
    
    Thread(target=run_bot).start()
    
    print(f"Web Server đang chờ lệnh chạy từ Procfile...")
