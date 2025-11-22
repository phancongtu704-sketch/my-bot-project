import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
from google import genai
from google.genai.errors import APIError
import httpx 

# --- CẤU HÌNH API VÀ BOT ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash"
CHECK_INTERVAL_SECONDS = 30 

REPORT_CHANNEL_ID = 1438028620407771198 

MONITORED_URLS = {
    "Google": {"url": "https://www.google.com", "status": "UP"},
    "Render.com": {"url": "https://render.com", "status": "UP"},
}

# --- KHỞI TẠO CLIENTS ---
if not DISCORD_TOKEN or not GEMINI_API_KEY:
    print("Lỗi: Thiếu DISCORD_TOKEN hoặc GEMINI_API_KEY. Bot không thể chạy.")
    # Không dùng exit() để tránh lỗi crash ngay lập tức
    
try:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"Lỗi khởi tạo Gemini Client: {e}")

# --- CẤU HÌNH DISCORD BOT VÀ SLASH COMMANDS ---
intents = discord.Intents.default()
intents.message_content = True 

bot = commands.Bot(command_prefix='!', intents=intents)
tree = app_commands.CommandTree(bot)

# --- TÍNH NĂNG BOT: KIỂM TRA UPTIME (30 GIÂY) ---
@tasks.loop(seconds=CHECK_INTERVAL_SECONDS)
async def check_uptime():
    if not bot.is_ready():
        return

    report_channel = bot.get_channel(REPORT_CHANNEL_ID)
    if not report_channel:
        print(f"Lỗi: Không tìm thấy kênh báo cáo với ID: {REPORT_CHANNEL_ID}")
        return

    async with httpx.AsyncClient(verify=False) as client: 
        for name, data in MONITORED_URLS.items():
            # ... (Phần logic kiểm tra Uptime giữ nguyên) ...
            try:
                response = await client.head(data['url'], timeout=5) 
                new_status = "UP" if 200 <= response.status_code < 400 else "DOWN"
                
                if new_status != data['status']:
                    data['status'] = new_status
                    if new_status == "DOWN":
                        await report_channel.send(
                            f"❌ **[DOWN]** Dịch vụ **{name}** vừa bị LỖI! Code: {response.status_code}"
                        )
                    else:
                        await report_channel.send(
                            f"✅ **[UP]** Dịch vụ **{name}** đã hoạt động trở lại."
                        )
            except Exception:
                if data['status'] != "DOWN":
                    data['status'] = "DOWN"
                    await report_channel.send(f"❌ **[DOWN]** Dịch vụ **{name}** không thể kết nối.")

# --- SLASH COMMANDS ---
@tree.command(name="update", description="Tóm tắt thông tin cập nhật.")
@app_commands.describe(url="Đường link trang cập nhật.")
async def update_command(interaction: discord.Interaction, url: str):
    await interaction.response.defer(thinking=True)
    prompt = f"Tóm tắt thông tin quan trọng nhất từ nội dung trên đường link này: {url}. Hãy trả lời bằng tiếng Việt."

    if not gemini_client:
        await interaction.followup.send("❌ **LỖI:** Dịch vụ Gemini không sẵn sàng.")
        return
        
    try:
        # Gọi API Gemini
        ai_response = gemini_client.models.generate_content(
            model=MODEL_NAME,
            contents=[prompt]
        )
        await interaction.followup.send(f"✅ **BẢN TÓM TẮT (bởi Gemini):**\n\n{ai_response.text[:1997]}")
            
    except APIError:
        await interaction.followup.send("❌ **LỖI HẠN MỨC:** Yêu cầu Gemini bị từ chối do Hết Quota.")
    except Exception:
        await interaction.followup.send("❌ **LỖI HỆ THỐNG:** Lỗi không xác định.")


@bot.event
async def on_ready():
    print(f'Bot đã đăng nhập với tên: {bot.user}')
    await tree.sync() 
    print("Đã đồng bộ hóa Slash Commands.")
    check_uptime.start() 
    print("Đã khởi động kiểm tra Uptime.")

if __file__ == "main.py":
    try:
        # Không còn keep_alive() hoặc Flask
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"Bot CRASH: {e}")
                        
