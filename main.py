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

# --- FLASK KEEP-ALIVE CHO RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "Bot Discord Gemini đang chạy!"

def run_flask():
    # Sử dụng cổng Render cung cấp (hoặc mặc định là 8080)
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 8080)) 

def keep_alive():
    t = Thread(target=run_flask)
    t.start()
# -----------------------------------

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not DISCORD_TOKEN or not GEMINI_API_KEY:
    print("Lỗi: Thiếu DISCORD_TOKEN hoặc GEMINI_API_KEY trong Environment Variables.")
    exit()

try:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    MODEL_NAME = "gemini-2.5-flash" 
    print(f'Đã khởi tạo Gemini Client với model: {MODEL_NAME}')
except Exception as e:
    print(f"Lỗi khởi tạo Gemini Client: {e}")
    exit()

intents = discord.Intents.default()
intents.message_content = True 

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot đã đăng nhập với tên: {bot.user}')
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
    
    async with message.channel.typing():
        try:
            contents = []
            
            # Cấu hình System Instruction để trả lời toàn diện
            system_instruction = "Bạn là một Bot Discord thân thiện, chuyên nghiệp, và là chuyên gia về công nghệ, lập trình. Luôn trả lời bằng TIẾNG VIỆT, sử dụng Markdown và chia đoạn rõ ràng. Hãy cung cấp câu trả lời đầy đủ và chi tiết nhất có thể cho mọi câu hỏi."
            config = types.GenerateContentConfig(system_instruction=system_instruction)

            image_parts = []
            
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
                response = gemini_client.models.generate_content(
                    model=MODEL_NAME,
                    contents=contents,
                    config=config
                )
                
                # Logic phản hồi nhanh 1 giây
                elapsed_time = time.time() - start_time
                MIN_RESPONSE_TIME = 1.0 
                if elapsed_time < MIN_RESPONSE_TIME:
                    sleep_time = MIN_RESPONSE_TIME - elapsed_time
                    await asyncio.sleep(sleep_time)
                    
                await message.channel.send(response.text)
                
        except APIError as e:
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
