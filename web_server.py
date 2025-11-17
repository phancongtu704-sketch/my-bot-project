import json
import os
import time
import random 
from flask import Flask, request, jsonify, redirect, url_for
import disnake
from disnake.ext import commands
import threading

# -------------------------------------------------------------------
# 0. CẤU HÌNH DỮ LIỆU VÀ BIẾN TOÀN CỤC
# -------------------------------------------------------------------
USERS_FILE = 'users.json'
temp_message = None 

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

    users_data[user_id]['candies'] -= candy_cost 
    save_data(users_data) 
    
    await inter.response.send_message(
        f"🎉 {inter.author.mention} đã đổi thành công **{candy_cost} Kẹo Halloween** lấy **2500 Hcoin** (Giả lập). Số kẹo còn lại: {users_data[user_id]['candies']}",
    )

# -------------------------------------------------------------------
# 3. LOGIC FLASK WEB SERVER (XỬ LÝ API VÀ TRANG CHỦ)
# -------------------------------------------------------------------

@app.route('/web_claim', methods=['POST'])
def web_claim_candy():
    global temp_message
    
    user_id = request.form.get('discord_id')
    candy_to_add = 50
    cooldown = 24 * 60 * 60

    if not user_id or not user_id.isdigit():
        temp_message = "🚨 Lỗi: Vui lòng nhập **ID Discord** hợp lệ (chỉ là số)."
        return redirect(url_for('home'))

    users_data = load_data()
    current_time = int(time.time())
    
    if user_id not in users_data:
        users_data[user_id] = {'candies': 0, 'last_claim': 0}

    last_claim = users_data[user_id].get('last_claim', 0)
    
    if current_time - last_claim < cooldown:
        remaining = cooldown - (current_time - last_claim)
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        
        temp_message = f"🛑 Đã nhận rồi! Vui lòng chờ {hours} giờ {minutes} phút nữa."
        return redirect(url_for('home'))
    
    users_data[user_id]['candies'] += candy_to_add
    users_data[user_id]['last_claim'] = current_time
    
    save_data(users_data) 
    
    temp_message = f"🎉 CHÚC MỪNG! ID {user_id} đã nhận thành công {candy_to_add} Kẹo Halloween!"
    return redirect(url_for('home'))


@app.route('/', methods=['GET'])
def home():
    """TRANG CHỦ - Giao diện SIÊU HIỆN ĐẠI."""
    global temp_message
    global bot 

    # Dữ liệu Bảng Xếp Hạng Hcoin (Giả lập)
    leaderboard_data = [
        {"rank": 1, "name": "Bóng Ma", "hcoin": 66666},
        {"rank": 2, "name": "Phù Thủy", "hcoin": 31100},
        {"rank": 3, "name": "Ma Cà Rồng", "hcoin": 13000},
        {"rank": 4, "name": "Người Sói", "hcoin": 9000},
        {"rank": 5, "name": "Bí Ngô", "hcoin": 4000},
    ]

    # --- DỮ LIỆU SỰ KIỆN MỚI (Đã tăng số lượng) ---
    event_data = [
        {"icon": "🎉", "title": "Chào mừng Tháng 11!", "detail": "Tham gia máy chủ Discord để nhận gói quà tân thủ trị giá 5,000 Hcoin."},
        {"icon": "🎁", "title": "Sự Kiện Lễ Tạ Ơn", "detail": "Nhận 200 Hcoin miễn phí mỗi ngày từ 24/11 đến 30/11."},
        {"icon": "💰", "title": "Khuyến mãi Đổi Kẹo", "detail": "Tỉ lệ đổi Kẹo Halloween lấy Hcoin tăng 10% trong vòng 48 giờ tới."},
        {"icon": "🏆", "title": "Giải Đấu Coin Hàng Tuần", "detail": "Top 10 Bảng xếp hạng sẽ nhận thưởng Hcoin gấp đôi vào Chủ Nhật."},
        {"icon": "🛡️", "title": "Cập nhật Anti-Cheat", "detail": "Hệ thống chống gian lận mới đã được triển khai để bảo vệ sự công bằng."},
        {"icon": "🛠️", "title": "Bảo Trì Hệ Thống", "detail": "Hệ thống sẽ bảo trì nâng cấp vào 2h sáng ngày 20/11 (30 phút)."},
    ]
    
    # Kiểm tra an toàn trước khi truy cập bot.user
    if bot.is_ready() and bot.user:
        bot_status_name = bot.user.name
    else:
        bot_status_name = "Discord Bot"

    # Trạng thái Bot
    status_text = "ONLINE" if bot.is_ready() else "KHỞI ĐỘNG"
    status_color = "#00FF00" if bot.is_ready() else "#FFA500"
    
    # Lấy dữ liệu bảng xếp hạng HTML
    html_table = ""
    for item in leaderboard_data:
        html_table += f"""
        <tr>
            <td data-label="Hạng">{item['rank']}</td>
            <td data-label="Tên">{item['name']}</td>
            <td data-label="Hcoin">{item['hcoin']:,}</td>
        </tr>
        """
        
    # Lấy dữ liệu Bảng Sự Kiện HTML
    html_event_list = ""
    for event in event_data:
        html_event_list += f"""
        <div class="event-item">
            <div class="event-icon">{event['icon']}</div>
            <div class="event-content">
                <strong>{event['title']}</strong>
                <p>{event['detail']}</p>
            </div>
        </div>
        """
        
    # HIỂN THỊ THÔNG BÁO TỪ REDIRECT
    alert_html = ""
    if temp_message:
        alert_html = f'<div class="alert-message">{temp_message}</div>'
        temp_message = None 

    # Trả về toàn bộ nội dung HTML với CSS, FORM
    return f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <title>🤖 {bot_status_name} - Dashboard Hiện Đại</title>
        <link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
        <style>
            :root {{
                --main-color: #00FFFF; /* Cyan Neon */
                --accent-color: #FF00FF; /* Magenta Neon */
                --dark-bg: #111111;
                --card-bg: #1e1e1e;
                --border-color: #333333;
            }}
            body {{ 
                background-color: var(--dark-bg); 
                color: var(--main-color); 
                font-family: 'Space Mono', monospace; 
                text-align: center; 
                margin: 0;
                padding: 40px 0;
            }}
            .container {{ 
                width: 95%; 
                max-width: 800px; 
                margin: 0 auto; 
            }}
            h1 {{ 
                color: var(--accent-color); 
                font-size: 2.5em; 
                text-transform: uppercase;
                text-shadow: 0 0 10px var(--accent-color);
                margin-bottom: 30px;
            }}
            h2 {{ 
                color: var(--main-color); 
                font-size: 1.5em; 
                border-bottom: 2px solid var(--border-color);
                padding-bottom: 10px;
                margin-top: 40px;
            }}

            /* === STATUS CARD === */
            .status-card {{ 
                padding: 15px; 
                background-color: var(--card-bg); 
                border: 2px solid var(--main-color);
                box-shadow: 0 0 15px var(--main-color);
                border-radius: 5px; 
                margin-bottom: 40px; 
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 20px;
            }}
            .status-indicator {{
                width: 15px;
                height: 15px;
                border-radius: 50%;
                background-color: {status_color};
                box-shadow: 0 0 10px {status_color};
                animation: pulse 1.5s infinite;
            }}
            .status-text {{
                font-size: 1.2em;
                font-weight: bold;
                color: white;
            }}
            @keyframes pulse {{
                0% {{ box-shadow: 0 0 10px {status_color}; }}
                50% {{ box-shadow: 0 0 20px {status_color}; }}
                100% {{ box-shadow: 0 0 10px {status_color}; }}
            }}

            /* === EVENT LIST CARD === */
            .event-list {{
                background: var(--card-bg);
                padding: 20px;
                border-radius: 8px;
                border: 2px solid #FFA500; /* Màu cam nổi bật */
                box-shadow: 0 0 10px #FFA500;
                margin-bottom: 40px;
                text-align: left;
            }}
            .event-item {{
                display: flex;
                gap: 15px;
                padding: 15px 0;
                border-bottom: 1px dashed var(--border-color);
                align-items: center;
            }}
            .event-item:last-child {{
                border-bottom: none;
            }}
            .event-icon {{
                font-size: 1.8em;
            }}
            .event-content p {{
                margin: 5px 0 0 0;
                color: #aaa;
                font-size: 0.9em;
            }}


            /* === CLAIM CARD === */
            .claim-card {{
                background: var(--card-bg);
                padding: 30px;
                border-radius: 8px;
                border: 2px solid var(--accent-color);
                box-shadow: 0 0 10px var(--accent-color);
                margin-bottom: 40px;
            }}
            .claim-card input[type=text], .claim-card button {{
                padding: 12px;
                margin: 10px;
                border-radius: 5px;
                border: 1px solid var(--border-color);
                font-size: 1em;
                font-family: 'Space Mono', monospace;
            }}
            .claim-card input[type=text] {{
                background: #2a2a2a;
                color: var(--main-color);
                width: 70%;
                max-width: 300px;
            }}
            .claim-card button {{
                background-color: var(--accent-color);
                color: var(--dark-bg);
                cursor: pointer;
                font-weight: bold;
                transition: background-color 0.3s, box-shadow 0.3s;
                border: none;
            }}
            .claim-card button:hover {{
                background-color: #FF69B4;
                box-shadow: 0 0 15px var(--accent-color);
            }}

            /* === ALERT MESSAGE === */
            .alert-message {{
                padding: 15px;
                background-color: #FFA500;
                color: #111;
                border-radius: 5px;
                margin-bottom: 20px;
                font-weight: bold;
                border: 2px dashed #000;
            }}

            /* === LEADERBOARD TABLE (RESPONSIVE) === */
            table {{ 
                width: 100%; 
                border-collapse: collapse; 
                margin-top: 20px; 
                background: #222; 
                border: 1px solid var(--main-color);
                box-shadow: 0 0 8px var(--main-color);
                border-radius: 5px;
            }}
            th, td {{ 
                padding: 15px 10px; 
                text-align: left; 
                border-bottom: 1px dashed var(--border-color);
            }}
            th {{ 
                background-color: #000; 
                color: var(--accent-color); 
                font-weight: 700;
                text-transform: uppercase;
            }}
            tr:nth-child(even) {{ background-color: #1a1a1a; }}
            tr:hover {{ background-color: #2a2a2a; }}

            /* Mobile optimization */
            @media (max-width: 600px) {{
                table, thead, tbody, th, td, tr {{ 
                    display: block; 
                }}
                thead tr {{ 
                    position: absolute;
                    top: -9999px;
                    left: -9999px;
                }}
                tr {{ border: 1px solid var(--border-color); margin-bottom: 15px; }}
                td {{ 
                    border: none;
                    border-bottom: 1px solid #333;
                    position: relative;
                    padding-left: 50%;
                    text-align: right;
                }}
                td:before {{ 
                    content: attr(data-label);
                    position: absolute;
                    left: 10px;
                    width: 45%;
                    padding-right: 10px;
                    white-space: nowrap;
                    text-align: left;
                    font-weight: bold;
                    color: var(--accent-color);
                }}
            }}
        </style>
        <script>
        </script>
    </head>
    <body>
        <div class="container">
            <h1>:: {bot_status_name} DASHBOARD ::</h1>

            <div class="status-card">
                <div class="status-indicator"></div>
                <div class="status-text">
                    [ TRẠNG THÁI BOT: {status_text} ]
                </div>
            </div>
            
            {alert_html}

            <div class="event-list">
                <h2>⫸ SỰ KIỆN & CẬP NHẬT MỚI</h2>
                {html_event_list}
            </div>
            
            <div class="claim-card">
                <h2>⫸ NHẬN KẸO MIỄN PHÍ | CLAIM REWARD</h2>
                <p style="color: #bbb;">Nhập **ID Discord** để nhận **50 Kẹo** mỗi 24 giờ. Đừng quên /doikeo trong Discord!</p>
                
                <form method="POST" action="/web_claim">
                    <input type="text" id="discord_id" name="discord_id" placeholder="Nhập ID Discord (chỉ là số)">
                    <button type="submit">CLAIM KẸO NGAY</button>
                </form>
            </div>
            
            <h2>⫸ BẢNG XẾP HẠNG HCOIN | TOP USERS</h2>
            <table>
                <thead>
                    <tr>
                        <th>Hạng</th>
                        <th>Tên Người Chơi</th>
                        <th>Hcoin (Coin)</th>
                    </tr>
                </thead>
                <tbody>
                    {html_table}
                </tbody>
            </table>

            <p style="margin-top: 50px; color: #888;">
                Sử dụng lệnh **/** trong Discord và chọn **hello**, **coin**, **xemkeo** hoặc **doikeo**.
            </p>
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
        
