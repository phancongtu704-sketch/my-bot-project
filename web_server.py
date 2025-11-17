# File: web_server.py (Code Web Server + Discord Bot - Dùng Lệnh Xẹt /)

from flask import Flask, jsonify
import disnake
from disnake.ext import commands
import threading
import os 

# -------------------------------------------------------------------
# 1. CẤU HÌNH
# -------------------------------------------------------------------
# LẤY TOKEN TỪ BIẾN MÔI TRƯỜNG (Tuyệt đối KHÔNG dán Token ở đây!)
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN") 

# Cấu hình Intents
# Lệnh Xẹt KHÔNG cần Intents MESSAGE_CONTENT, nên ta dùng Intents.default() cho bảo mật
intents = disnake.Intents.default()
# intents.messages = True 
# intents.message_content = True 

# Khởi tạo Bot và Flask
# LƯU Ý: Lệnh Xẹt KHÔNG cần command_prefix
bot = commands.Bot(intents=intents)
app = Flask(__name__)

# -------------------------------------------------------------------
# 2. LOGIC DISCORD BOT (DÙNG LỆNH XẸT /)
# -------------------------------------------------------------------

@bot.event
async def on_ready():
    # In ra log để xác nhận bot online trên Render
    print(f"🎉 Discord Bot Đã Đăng Nhập: {bot.user}")

# Lệnh Xẹt MỚI: /hello
@bot.slash_command(name="hello", description="Kiểm tra trạng thái bot và chào mừng.")
async def hello_command(inter: disnake.ApplicationCommandInteraction):
    await inter.response.send_message(
        f"Chào {inter.author.mention}! Bot Discord đã nâng cấp sang lệnh xẹt (Slash Command) và đang chạy 24/7."
    )

# Lệnh Xẹt MỚI: /coin (Ví dụ về lệnh mới)
@bot.slash_command(name="coin", description="Xem số Hcoin hiện tại của bạn.")
async def coin_command(inter: disnake.ApplicationCommandInteraction):
    # Đây là dữ liệu cố định, sau này có thể kết nối database
    await inter.response.send_message(f"Bạn đang có 10,000 Hcoin.", ephemeral=True)


# -------------------------------------------------------------------
# 3. LOGIC FLASK WEB SERVER (THÊM BẢNG XẾP HẠNG HCOIN)
# -------------------------------------------------------------------

@app.route('/', methods=['GET'])
def home():
    # Dữ liệu Bảng Xếp Hạng Hcoin (Bạn có thể thay đổi tùy thích)
    leaderboard_data = [
        {"rank": 1, "name": "Người Tạo Bot (Bạn)", "hcoin": 50000},
        {"rank": 2, "name": "Thành viên A", "hcoin": 35000},
        {"rank": 3, "name": "Thành viên B", "hcoin": 15000},
        {"rank": 4, "name": "Thành viên C", "hcoin": 8000},
        {"rank": 5, "name": "Thành viên D", "hcoin": 2500},
    ]

    # Bắt đầu tạo nội dung HTML
    html_table = ""
    for item in leaderboard_data:
        # Tạo hàng cho mỗi người chơi
        html_table += f"""
        <tr>
            <td>{item['rank']}</td>
            <td>{item['name']}</td>
            <td>{item['hcoin']:,} Hcoin</td>
        </tr>
        """
    
    # Kiểm tra trạng thái bot
    bot_status = f"{bot.user} (Online)" if bot.is_ready() else "Bot đang khởi động..."

    # Trả về toàn bộ nội dung HTML
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hcoin Leaderboard Của Discord Bot</title>
        <style>
            body {{ background-color: #2c2f33; color: #dcddde; font-family: sans-serif; text-align: center; }}
            .container {{ width: 80%; margin: 50px auto; }}
            h1 {{ color: #7289da; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #4f545c; padding: 12px; text-align: left; }}
            th {{ background-color: #4f545c; color: white; }}
            .status-box {{ padding: 10px; background-color: #43b581; color: white; border-radius: 5px; margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Bảng Xếp Hạng Hcoin</h1>
            <div class="status-box">Bot Status: {bot_status}</div>
            
            <table>
                <thead>
                    <tr>
                        <th>Hạng</th>
                        <th>Tên Thành Viên</th>
                        <th>Số Hcoin</th>
                    </tr>
                </thead>
                <tbody>
                    {html_table}
                </tbody>
            </table>

            <p style="margin-top: 30px;">Để thử bot: Gõ lệnh **/** trong Discord và chọn lệnh **hello**.</p>
        </div>
    </body>
    </html>
    """

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
