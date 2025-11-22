import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
from google import genai
from google.genai.errors import APIError
from flask import Flask
from threading import Thread
import httpx 

# --- CẤU HÌNH API VÀ BOT ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash"
CHECK_INTERVAL_SECONDS = 30 

# ID kênh của bạn
REPORT_CHANNEL_ID = 1438028620407771198 

# Danh sách URL để theo dõi
MONITORED_URLS = {
    "Google": {"url": "https://www.google.com", "status": "UP"},
    "Render.com": {"url": "https://render.com", "status": "UP"},
    # THÊM DỊCH VỤ CỦA BẠN VÀO ĐÂY
}

# --- KHỞI TẠO CLIENTS ---
if not DISCORD_TOKEN or not GEMINI_API_KEY:
    print("Lỗi: Thiếu DISCORD_TOKEN hoặc GEMINI_API_KEY. Bot không thể chạy.")
    exit()

try:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"Lỗi khởi tạo Gemini Client: {e}")
    exit()

# --- CẤU HÌNH DISCORD BOT VÀ SLASH COMMANDS ---
intents = discord.Intents.default()
intents.message_content = True 

bot = commands.Bot(command_prefix='!', intents=intents)
tree = app_commands.CommandTree(bot)

# --- FLASK KEEP-ALIVE CHO RENDER ---
app = Flask('')
@app.route('/')
def home():
    return "Bot Discord Gemini đang chạy và được giữ Online!"
def run_flask():
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 8080)) 
def keep_alive():
    t = Thread(target=run_flask)
    t.start()
# ------------------------------------

# --- TÍNH NĂNG BOT: KIỂM TRA UPTIME (30 GIÂY) ---
@tasks.loop(seconds=CHECK_INTERVAL_SECONDS)
async def check_uptime():
    if not bot.is_ready():
        return

    report_channel = bot.get_channel(REPORT_CHANNEL_ID)
    if not report_channel:
        print(f"Lỗi: Không tìm thấy kênh báo cáo với ID: {REPORT_CHANNEL_ID}")
        return

    # Tắt xác minh SSL (verify=False) để tránh lỗi SSL/HTTPS trên một số host
    async with httpx.AsyncClient(verify=False) as client: 
        for name, data in MONITORED_URLS.items():
            try:
                # Kiểm tra HTTP HEAD để tiết kiệm tài nguyên
                response = await client.head(data['url'], timeout=5) 
                
                new_status = "UP" if 200 <= response.status_code < 400 else "DOWN"
                
                if new_status != data['status']:
                    data['status'] = new_status
                    if new_status == "DOWN":
                        await report_channel.send(
                            f"❌ **[DOWN]** Dịch vụ **{name}** vừa bị LỖI tại {data['url']}! Code: {response.status_code}"
                        )
                    else:
                        await report_channel.send(
                            f"✅ **[UP]** Dịch vụ **{name}** đã hoạt động trở lại."
                        )

            except httpx.RequestError as e:
                if data['status'] != "DOWN":
                    data['status'] = "DOWN"
                    await report_channel.send(
                        f"❌ **[DOWN]** Dịch vụ **{name}** tại {data['url']} không thể kết nối. Chi tiết: {e}"
                    )
            except Exception as e:
                print(f"Lỗi không xác định khi kiểm tra {name}: {e}")

# --- SLASH COMMANDS ---
@tree.command(name="update", description="Sử dụng AI Gemini để tóm tắt các thông tin cập nhật.")
@app_commands.describe(url="Đường link trang cập nhật (ví dụ: https://...).")
async def update_command(interaction: discord.Interaction, url: str):
    await interaction.response.defer(thinking=True)

    prompt = f"Tóm tắt thông tin quan trọng nhất và các điểm mới từ nội dung trên đường link này: {url}. Hãy trả lời bằng tiếng Việt."

    try:
        # Gọi API Gemini (sử dụng model Flash)
        ai_response = gemini_client.models.generate_content(
            model=MODEL_NAME,
            contents=[prompt]
        )
        
        response_text = ai_response.text
        if len(response_text) > 2000:
            response_text = response_text[:1997] + "..."
            
        await interaction.followup.send(f"✅ **BẢN TÓM TẮT CẬP NHẬT (bởi Gemini):**\n\n{response_text}")
            
    except APIError as e:
        error_message = f"❌ LỖI HẠN MỨC: Yêu cầu Gemini bị từ chối do Hết Quota/Rate Limit. Chi tiết lỗi: {e}"
        await interaction.followup.send(error_message)
    except Exception as e:
        error_message = f"❌ LỖI HỆ THỐNG: Đã xảy ra lỗi không xác định. Chi tiết: {e}"
        await interaction.followup.send(error_message)

# --- KHỞI CHẠY BOT ---
@bot.event
async def on_ready():
    print(f'Bot đã đăng nhập với tên: {bot.user} - ID: {bot.user.id}')
    
    await tree.sync() 
    print("Đã đồng bộ hóa Slash Commands.")
    
    check_uptime.start() 
    print(f"Đã khởi động kiểm tra Uptime mỗi {CHECK_INTERVAL_SECONDS} giây.")
    
    keep_alive()

if __file__ == "main.py":
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"Lỗi khi chạy bot: {e}")
            
