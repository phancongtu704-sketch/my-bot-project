import os
import io
import requests
import discord
from discord.ext import commands
from google import genai
from google.genai import types
from PIL import Image
from flask import Flask
from threading import Thread
from google.genai.errors import APIError
import time 
import asyncio 

# --- FLASK KEEP-ALIVE CHO RENDER (Cấu trúc web hiện đại) ---
app = Flask('')

@app.route('/')
def home():
    # Trang chủ Render sẽ luôn trả về thông báo này để xác nhận dịch vụ đang chạy
    return "Bot Discord Gemini đang chạy và được giữ Online!"

def run_flask():
    # Sử dụng cổng Render cung cấp (hoặc mặc định là 8080)
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 8080)) 

def keep_alive():
    # Chạy Flask server trên một luồng riêng biệt (thread)
    t = Thread(target=run_flask)
    t.start()
# -----------------------------------------------------------

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not DISCORD_TOKEN or not GEMINI_API_KEY:
    print("Lỗi: Thiếu DISCORD_TOKEN hoặc GEMINI_API_KEY trong Environment Variables.")
    exit()

try:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Model ổn định và dễ truy cập nhất
    MODEL_NAME = "gemini-2.5-flash" 
    print(f'Đã khởi tạo Gemini Client với model: {MODEL_NAME}')
except Exception as e:
    print(f"Lỗi khởi tạo Gemini Client: {e}")
    exit()

intents = discord.Intents.default()
# MESSAGE CONTENT INTENT BẮT BUỘC PHẢI BẬT TRÊN DISCORD DEV PORTAL
intents.message_content = True 

# Khởi tạo Bot
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot đã đăng nhập với tên: {bot.user}')
    # Khởi động Flask Keep-Alive để giữ bot Online trên Render
    keep_alive()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    text_prompt = message.content.strip()
    has_text = bool(text_prompt)
    has_attachments = bool(message.attachments)
    
    if not has_text and not has_attachments:
        return
        
    start_time = time.time()
    
    # Hiển thị trạng thái đang gõ (Typing)
    async with message.channel.typing():
        try:
            contents = []
            
            image_parts = []
            
            # Xử lý ảnh đính kèm
            if has_attachments:
                for attachment in message.attachments:
                    if 'image' in attachment.content_type:
                        response = requests.get(attachment.url)
                        
                        if response.status_code == 200:
                            image = Image.open(io.BytesIO(response.content))
                            image_parts.append(image)
                        else:
                            await message.channel.send("Lỗi: Không thể tải ảnh từ Discord.")
                            return

            if text_prompt:
                contents.append(text_prompt)

            for image in image_parts:
                contents.append(image)

            if not has_text and has_attachments:
                 contents.insert(0, "Mô tả và phân tích hình ảnh này cho tôi.")
            
            if contents:
                # Gửi yêu cầu tới Gemini (Đã loại bỏ CONFIG/SYSTEM INSTRUCTION để tránh lỗi 400)
                response = gemini_client.models.generate_content(
                    model=MODEL_NAME,
                    contents=contents
                )
                
                # Logic phản hồi nhanh 1 giây
                elapsed_time = time.time() - start_time
                MIN_RESPONSE_TIME = 1.0 
                if elapsed_time < MIN_RESPONSE_TIME:
                    sleep_time = MIN_RESPONSE_TIME - elapsed_time
                    await asyncio.sleep(sleep_time)
                    
                await message.channel.send(response.text)
                
        except APIError as e:
            # Lỗi 400 Bad Request dai dẳng chỉ ra Key API bị lỗi
            error_message = f"❌ LỖI API: Yêu cầu bị từ chối. Vui lòng kiểm tra lại Key API **MỚI NHẤT** và Quota. Chi tiết lỗi: {e}"
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
    
