import json
import os
import time
from flask import Flask, request, jsonify
import disnake
from disnake.ext import commands
import threading

# -------------------------------------------------------------------
# 0. CẤU HÌNH DỮ LIỆU VÀ CHỨC NĂNG LƯU/TẢI FILE
# -------------------------------------------------------------------
USERS_FILE = 'users.json'

def load_data():
    """Tải dữ liệu người dùng từ tệp JSON."""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Lỗi: Không thể giải mã JSON từ {USERS_FILE}. Khởi tạo lại dữ liệu.")
            return {}
    return {}

def save_data(data):
    """Lưu dữ liệu người dùng vào tệp JSON."""
    with open(USERS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# -------------------------------------------------------------------
# 1. CẤU HÌNH DISCORD & FLASK
# -------------------------------------------------------------------
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN") 
intents = disnake.Intents.default()
bot = commands.Bot(intents=intents)
app = Flask(__name__)

# -------------------------------------------------------------------
# 2. LOGIC DISCORD BOT (LỆNH XẸT /)
# -------------------------------------------------------------------

@bot.event
async def on_ready():
    print(f"🎉 Discord Bot Đã Đăng Nhập: {bot.user}")

@bot.slash_command(name="hello", description="Kiểm tra trạng thái bot và chào mừng.")
async def hello_command(inter: disnake.ApplicationCommandInteraction):
    await inter.response.send_message(
        f"Chào {inter.author.mention}! Bot Discord đang chạy 24/7."
    )

@bot.slash_command(name="coin", description="Xem số Hcoin hiện tại của bạn.")
async def coin_command(inter: disnake.ApplicationCommandInteraction):
    await inter.response.send_message(f"Bạn đang có 10,000 Hcoin.", ephemeral=True)

@bot.slash_command(name="xemkeo", description="Xem số dư Kẹo Halloween hiện tại.")
async def xemkeo_command(inter: disnake.ApplicationCommandInteraction):
    users_data = load_data()
    user_id = str(inter.author.id)
    candies = users_data.get(user_id, {}).get('candies', 0)
    await inter.response.send_message(
        f"🎃 {inter.author.mention}, bạn hiện đang có **{candies} Kẹo Halloween**.", 
        ephemeral=True
    )

@bot.slash_command(name="doikeo", description="Đổi 50 Kẹo Halloween lấy 2500 Hcoin.")
async def doikeo_command(inter: disnake.ApplicationCommandInteraction):
    user_id = str(inter.author.id)
    candy_cost = 50 
    
    users_data = load_data()
    current_candies = users_data.get(user_id, {}).get('candies', 0)
    
    if current_candies < candy_cost:
        await inter.response.send_message(f"Không đủ kẹo! Bạn có {current_candies}, cần {candy_cost}.", ephemeral=True)
        return

    # Xử lý đổi kẹo và TRỪ KẸO
    users_data[user_id]['candies'] -= candy_cost 
    
    # LƯU DỮ LIỆU
    save_data(users_data) 
    
    await inter.response.send_message(
        f"🎉 {inter.author.mention} đã đổi thành công **{candy_cost} Kẹo Halloween** lấy **2500 Hcoin** (Giả lập). Số kẹo còn lại: {users_data[user_id]['candies']}",
    )


# -------------------------------------------------------------------
# 3. LOGIC FLASK WEB SERVER (CÁC API ROUTES VÀ TRANG CHỦ)
# -------------------------------------------------------------------

@app.route('/claim', methods=['POST'])
def claim_candy_api():
    """API cho các chức năng Web sau này, hiện tại ưu tiên dùng lệnh Discord."""
    return jsonify({'status': 'info', 'message': 'Vui lòng dùng lệnh /doikeo trong Discord.'})

@app.route('/exchange', methods=['POST'])
def exchange_candy_api():
    """API cho các chức năng Web sau này, hiện tại ưu tiên dùng lệnh Discord."""
    return jsonify({'status': 'info', 'message': 'Vui lòng dùng lệnh /doikeo trong Discord.'})


@app.route('/', methods=['GET'])
def home():
    """TRANG CHỦ - Giao diện Halloween ĐÃ KHÔI PHỤC."""
    # Dữ liệu Bảng Xếp Hạng Hcoin (Chủ đề Halloween)
    leaderboard_data = [
        {"rank": 1, "name": "Bóng Ma", "hcoin": 66666},
        {"rank": 2, "name": "Phù Thủy", "hcoin": 31100},
        {"rank": 3, "name": "Ma Cà Rồng", "hcoin": 13000},
        {"rank": 4, "name": "Người Sói", "hcoin": 9000},
        {"rank": 5, "name": "Bí Ngô", "hcoin": 4000},
    ]

    # Kiểm tra trạng thái bot
    bot_status = f"{bot.user} (Online)" if bot.is_ready() else "Bot đang khởi động..."
    
    # Lấy dữ liệu bảng xếp hạng HTML
    html_table = ""
    for item in leaderboard_data:
        html_table += f"""
        <tr>
            <td>{item['rank']}</td>
            <td>{item['name']}</td>
            <td>{item['hcoin']:,} Hcoin</td>
        </tr>
        """
        
    # Trả về toàn bộ nội dung HTML với CSS chủ đề Halloween và form nhận kẹo
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
            // Logic đã FIX: Khuyến khích dùng lệnh Discord
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
    """Chạy Flask Web Server và Discord Bot."""
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
        
