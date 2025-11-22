import os
import discord
from discord.ext import commands
from google import genai
from google.genai.errors import APIError
from flask import Flask
from threading import Thread
import time 
import asyncio 

# --- FLASK KEEP-ALIVE CHO RENDER ---
app = Flask('')

@app.route('/')
def home():
    # Trang chủ xác nhận dịch vụ đang chạy
    return "Bot Discord Gemini đang chạy và được giữ Online!"

def run_flask():
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 8080)) 

def keep_alive():
    t = Thread(target=run_flask)
    t.start()
# ------------------------------------

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not DISCORD_TOKEN or not GEMINI_API_KEY:
    print("Lỗi: Thiếu DISCORD_TOKEN hoặc GEMINI_API_KEY trong Environment Variables.")
    exit()

try:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    
    # CHỈ SỬ DỤNG FLASH để tránh lỗi Quota từ model PRO
    MODEL_NAME = "gemini-2.5-flash" 
    print(f'Đã khởi tạo Gemini Client với model: {MODEL_NAME}')
except Exception as e:
    print(f"Lỗi khởi tạo Gemini Client: {e}")
    exit()

intents = discord.Intents.default()
# BẮT BUỘC phải bật Message Content Intent trên Discord Dev Portal
intents.message_content = True 

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot đã đăng nhập với tên: {bot.user}')
    keep_alive() # Khởi động Flask Keep-Alive

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    text_prompt = message.content.strip()
    
    # Hiển thị trạng thái đang gõ (Typing)
    async with message.channel.typing():
        try:
            # Gửi yêu cầu tới Gemini (KHÔNG LỊCH SỬ CHAT, KHÔNG SYSTEM INSTRUCTION)
            response = gemini_client.models.generate_content(
                model=MODEL_NAME,
                contents=[text_prompt]
            )
            
            await message.channel.send(response.text)
                
        except APIError as e:
            # Lỗi 400 Bad Request dai dẳng chỉ ra Key API bị lỗi Quota
            error_message = f"❌ LỖI API 400: Yêu cầu bị từ chối do Hết Quota/Rate Limit. Vui lòng kiểm tra cài đặt tài khoản Google của bạn. Chi tiết lỗi: {e}"
            await message.channel.send(error_message)
        except Exception as e:
            error_message = f"❌ LỖI HỆ THỐNG: {type(e).__name__}: {e}. Vui lòng kiểm tra Intent Discord."
            await message.channel.send(error_message)

if __name__ == "__main__":
    try:
        bot.run(DISCORD_TOKEN)
    except discord.errors.LoginFailure:
        print("Lỗi: Token Discord không hợp lệ.")
    except Exception as e:
        print(f"Lỗi không xác định khi chạy bot: {e}")
    
