# File: web_server.py (Code Web Server + Discord Bot)

from flask import Flask, jsonify
import disnake
from disnake.ext import commands
import threading
import asyncio

# -------------------------------------------------------------------
# 1. CẤU HÌNH
# -------------------------------------------------------------------
# TOKEN DISCORD CỦA BẠN
DISCORD_BOT_TOKEN = "MTQzODAxNTgyMzk2Mzc1MDQ1Mg.GvH-IY.r8KAh03fm1N80fmu826ZfW27DABtEp--FlWoJo" 

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
    
    if user_text == '!hello':
        await message.channel.send(f"Chào {message.author.mention}! Bot Discord đang chạy trên Web Server.")
    
    await bot.process_commands(message)

# -------------------------------------------------------------------
# 3. LOGIC FLASK WEB SERVER
# -------------------------------------------------------------------

@app.route('/', methods=['GET'])
def home():
    return f"<h1>Discord Bot Web Server is Running!</h1><p>Bot Status: {bot.user} (Online)</p>"

@app.route('/api/status', methods=['GET'])
def api_status():
    return jsonify({"status": "live", "bot_user": str(bot.user), "bot_id": bot.user.id})

# -------------------------------------------------------------------
# 4. CHẠY CẢ HAI CÙNG LÚC
# -------------------------------------------------------------------

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False)

def run_discord_bot():
    bot.loop.create_task(bot.start(DISCORD_BOT_TOKEN))

if __name__ == '__main__':
    discord_thread = threading.Thread(target=run_discord_bot)
    discord_thread.start()
    run_flask()
