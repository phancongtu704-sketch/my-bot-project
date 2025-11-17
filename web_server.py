# File: web_server.py (Code Web Server + Discord Bot - Sửa logic Nhận Kẹo)

from flask import Flask, jsonify
import disnake
from disnake.ext import commands
import threading
import os 

# -------------------------------------------------------------------
# 1. CẤU HÌNH
# -------------------------------------------------------------------
# LẤY TOKEN TỪ BIẾN MÔI TRƯỜNG
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN") 

# Cấu hình Intents
intents = disnake.Intents.default()

# Khởi tạo Bot và Flask
bot = commands.Bot(intents=intents)
app = Flask(__name__)

# -------------------------------------------------------------------
# 2. LOGIC DISCORD BOT (LỆNH XẸT /)
# -------------------------------------------------------------------

@bot.event
async def on_ready():
    print(f"🎉 Discord Bot Đã Đăng Nhập: {bot.user}")

# Lệnh Xẹt: /hello
@bot.slash_command(name="hello", description="Kiểm tra trạng thái bot và chào mừng.")
async def hello_command(inter: disnake.ApplicationCommandInteraction):
    await inter.response.send_message(
        f"Chào {inter.author.mention}! Bot Discord đã nâng cấp sang lệnh xẹt (Slash Command) và đang chạy 24/7."
    )

# Lệnh Xẹt: /coin 
@bot.slash_command(name="coin", description="Xem số Hcoin hiện tại của bạn.")
async def coin_command(inter: disnake.ApplicationCommandInteraction):
    await inter.response.send_message(f"Bạn đang có 10,000 Hcoin.", ephemeral=True)

# Lệnh Xẹt: /doikeo
@bot.slash_command(name="doikeo", description="Đổi Kẹo Halloween thành Hcoin (Chức năng mới).")
async def doikeo_command(inter: disnake.ApplicationCommandInteraction, soluong: int = 10):
    if soluong > 0:
        await inter.response.send_message(
            f"🎉 {inter.author.mention} đã đổi thành công **{soluong} Kẹo Halloween** thành **{soluong * 50} Hcoin**!"
        )
    else:
        await inter.response.send_message("Số lượng kẹo đổi phải lớn hơn 0.", ephemeral=True)

# Lệnh Xẹt MỚI: /xemkeo
@bot.slash_command(name="xemkeo", description="Xem số dư Kẹo Halloween hiện tại.")
async def xemkeo_command(inter: disnake.ApplicationCommandInteraction):
    # Giả lập số kẹo
    await inter.response.send_message(
        f"🎃 {inter.author.mention}, bạn hiện đang có **50 Kẹo Halloween**.", 
        ephemeral=True
    )

# -------------------------------------------------------------------
# 3. LOGIC FLASK WEB SERVER (Giao diện Halloween)
# -------------------------------------------------------------------

@app.route('/', methods=['GET'])
def home():
    # Dữ liệu Bảng Xếp Hạng Hcoin (Chủ đề Halloween)
    leaderboard_data = [
        {"rank": 1, "name": "Bóng Ma", "hcoin": 66666},
        {"rank": 2, "name": "Phù Thủy", "hcoin": 31100},
        {"rank": 3, "name": "Ma Cà Rồng", "hcoin": 13000},
        {"rank": 4, "name": "Người Sói", "hcoin": 9000},
        {"rank": 5, "name": "Bí Ngô", "hcoin": 4000},
    ]

    html_table = ""
    for item in leaderboard_data:
        html_table += f"""
        <tr>
            <td>{item['rank']}</td>
            <td>{item['name']}</td>
            <td>{item['hcoin']:,} Hcoin</td>
        </tr>
        """
    
    bot_status = f"{bot.user} (Online)" if bot.is_ready() else "Bot đang khởi động..."

    # Trả về toàn bộ nội dung HTML với CSS chủ đề Halloween và thêm form nhận kẹo
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>🎃 Sự kiện Halloween - {bot.user.name}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Creepster&family=Roboto&display=swap');
            body {{ 
                background-color: #0d0d0d; 
                background-image: url('https://www.transparenttextures.com/patterns/dark-mosaic.png');
                color: #f7f3e8; 
                font-family: 'Roboto', sans-serif; 
                text-align: center; 
                padding-bottom: 50px;
            }}
            .container {{ 
                width: 90%; 
                max-width: 800px; 
                margin: 50px auto; 
                background: rgba(0, 0, 0, 0.7); 
                border-radius: 15px; 
                padding: 30px; 
                box-shadow: 0 0 20px #ff6600;
            }}
            h1 {{ 
                color: #ff6600; 
                font-family: 'Creepster', cursive; 
                font-size: 3.5em; 
                text-shadow: 2px 2px 5px #8b0000; 
                margin-bottom: 20px;
            }}
            h2 {{ color: #7289da; margin-top: 5px; }}
            table {{ 
                width: 100%; 
                border-collapse: collapse; 
                margin-top: 30px; 
                background: #1a1a1a; 
                border-radius: 10px;
            }}
            th, td {{ 
                border: none; 
                padding: 15px; 
                text-align: center; 
                border-bottom: 1px solid #333;
            }}
            th {{ 
                background-color: #8b0000; 
                color: white; 
                font-size: 1.1em;
            }}
            tr:nth-child(even) {{ background-color: #121212; }}
            tr:hover {{ background-color: #2a0000; }}
            .status-box {{ 
                padding: 15px; 
                background-color: #43b581; 
                color: white; 
                border-radius: 8px; 
                margin-bottom: 30px; 
                font-size: 1.1em;
            }}
            .command-info {{ 
                margin-top: 40px; 
                font-size: 1.2em; 
                padding: 15px; 
                border-top: 2px dashed #ff6600;
            }}
            .candy-box {{
                background: #333;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 30px;
                border: 2px solid #ff6600;
            }}
            .candy-box input[type=text], .candy-box button {{
                padding: 10px;
                margin: 5px;
                border-radius: 5px;
                border: 1px solid #555;
                font-size: 1em;
            }}
            .candy-box input[type=text] {{
                background: #222;
                color: white;
                width: 60%;
            }}
            .candy-box button {{
                background-color: #ff6600;
                color: white;
                cursor: pointer;
                transition: background-color 0.3s;
            }}
            .candy-box button:hover {{
                background-color: #e05c00;
            }}
        </style>
        <script>
            // Sửa logic: Chỉ hiển thị thông báo và khuyến khích dùng lệnh Discord
            function receiveCandy() {{
                const username = document.getElementById('username').value;
                if (username) {{
                    alert('🎃 Cảm ơn ' + username + '! Vui lòng dùng lệnh /doikeo trong Discord để thực sự nhận Kẹo!');
                }} else {{
                    alert('Vui lòng nhập tên người chơi Discord của bạn!');
                }}
            }}
        </script>
    </head>
    <body>
        <div class="container">
            <h1>🎃 Lễ Hội Ma Quái Halloween!</h1>
            <div class="status-box">👻 Trạng thái Bot: {bot_status}</div>
            
            <div class="candy-box">
                <h2>🎁 Nhận Kẹo Halloween! (Dùng Lệnh Discord)</h2>
                <p>Nhập tên Discord của bạn và nhấn nút. Sau đó, **dùng lệnh /doikeo trong Discord** để nhận kẹo thực sự!</p>
                
                <input type="text" id="username" placeholder="Nhập Tên Discord của bạn">
                <button onclick="receiveCandy()">Nhận Kẹo Halloween</button>
            </div>

            <h2>📊 Bảng Xếp Hạng Hcoin (Ma Quái)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Hạng</th>
                        <th>Tên Quái Vật</th>
                        <th>Số Kẹo Hcoin</th>
                    </tr>
                </thead>
                <tbody>
                    {html_table}
                </tbody>
            </table>

            <div class="command-info">
                Các lệnh Bot: Gõ **/** trong Discord và chọn **hello**, **coin**, **xemkeo** hoặc **doikeo**!
            </div>
        </div>
    </body>
    </html>
    """

# -------------------------------------------------------------------
# 4. CHẠY CẢ HAI CÙNG LÚC
# -------------------------------------------------------------------

def run_flask():
    """Chạy Flask Web Server."""
    if not DISCORD_BOT_TOKEN:
        print("🚨 Lỗi: KHÔNG tìm thấy DISCORD_BOT_TOKEN.")
        return

    # Khởi tạo và chạy Bot Discord trong một luồng (thread) riêng
    discord_thread = threading.Thread(target=lambda: bot.loop.run_until_complete(bot.start(DISCORD_BOT_TOKEN)))
    discord_thread.start()
    
    # Bật Flask Web Server trong luồng chính
    print("Web Server đã khởi động trên 0.0.0.0:5000")
    app.run(host='0.0.0.0', port=os.environ.get("PORT", 5000), debug=False)


if __name__ == '__main__':
    run_flask()
