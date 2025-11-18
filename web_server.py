import random
import time
import os
import json
from flask import Flask, request, jsonify, redirect, url_for
from disnake.ext import commands
import disnake
from gevent.pywsgi import WSGIServer  # FIX: Thay thế threading
from gevent import spawn            # FIX: Thay thế threading

# Tên file lưu dữ liệu người dùng
USERS_FILE = 'users.json'
# Biến tạm để lưu thông báo (sẽ hiển thị trên web)
temp_message = None

# Tốc độ đào Hcoin (100 Hcoin/giây)
HCOIN_PER_SECOND = 100

def load_data():
    users_data = {}
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                users_data = json.load(f)
        except json.JSONDecodeError:
            print(f"LỖI: Không thể giải mã JSON từ {USERS_FILE}. Khởi tạo dữ liệu trống.")
            users_data = {}

    # Đảm bảo tất cả người dùng đều có các trường dữ liệu cần thiết
    for user_id, data in users_data.items():
        if 'hcoin' not in data:
            data['hcoin'] = 10000
        if 'candies' not in data:
            data['candies'] = 0
        if 'last_collect' not in data:
            data['last_collect'] = 0
        if 'last_claim' not in data:
            data['last_claim'] = 0
    return users_data

def save_data(data):
    with open(USERS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Load dữ liệu người dùng khi khởi động
users_data = load_data()

# Cấu hình Bot Disnake
DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
bot = commands.Bot(command_prefix='!', intents=disnake.Intents.all())

# Cấu hình Flask Web Server
app = Flask(__name__)
# Đảm bảo ứng dụng Flask luôn sẵn sàng
app.config['ENV'] = 'production'


# === LOGIC BOT DISCORD (NẰM TRONG BOT) ===

@bot.event
async def on_ready():
    print(f"Bot đã sẵn sàng: {bot.user}")

@bot.slash_command(description="Hiển thị số Hcoin và Kẹo của bạn.")
async def wallet(inter):
    user_id = str(inter.author.id)
    if user_id not in users_data:
        users_data[user_id] = {'hcoin': 10000, 'candies': 0, 'last_collect': 0, 'last_claim': 0}
        save_data(users_data)
    
    hcoin_balance = users_data[user_id]['hcoin']
    candies_balance = users_data[user_id]['candies']
    
    embed = disnake.Embed(
        title=f"Ví Của {inter.author.display_name}",
        description=f"💰 Hcoin: {hcoin_balance:,}\n🍬 Kẹo: {candies_balance:,}",
        color=0x00ff00
    )
    await inter.response.send_message(embed=embed, ephemeral=True)


@bot.slash_command(description="Đào Hcoin (Mỗi 24 giờ).")
async def collect(inter):
    global users_data, temp_message
    user_id = str(inter.author.id)
    current_time = int(time.time())
    
    if user_id not in users_data:
        users_data[user_id] = {'hcoin': 10000, 'candies': 0, 'last_collect': 0, 'last_claim': 0}
        save_data(users_data)

    last_collect = users_data[user_id].get('last_collect', 0)
    cooldown = 24 * 3600 # 24 giờ

    if current_time - last_collect >= cooldown:
        collected_amount = 1000 # Số Hcoin cố định nhận được

        users_data[user_id]['hcoin'] += collected_amount
        users_data[user_id]['last_collect'] = current_time
        save_data(users_data)
        
        embed = disnake.Embed(
            title="Đào Hcoin Thành Công! ⛏️",
            description=f"Bạn đã nhận được **{collected_amount:,} Hcoin**.\nTổng số Hcoin hiện tại: **{users_data[user_id]['hcoin']:,}**",
            color=0x00ff00
        )
        temp_message = f"✅ Đào thành công! Bạn nhận được {collected_amount:,} Hcoin."
        await inter.response.send_message(embed=embed, ephemeral=True)
    else:
        time_left = cooldown - (current_time - last_collect)
        hours = int(time_left // 3600)
        minutes = int((time_left % 3600) // 60)
        seconds = int(time_left % 60)
        
        embed = disnake.Embed(
            title="⏳ Đang trong thời gian chờ",
            description=f"Bạn có thể đào lại sau **{hours} giờ, {minutes} phút, và {seconds} giây**.",
            color=0xffa500
        )
        temp_message = f"⚠️ Bạn cần chờ thêm {hours}h {minutes}m."
        await inter.response.send_message(embed=embed, ephemeral=True)


@bot.slash_command(description="Đổi Hcoin lấy Kẹo (1000 Hcoin = 1 Kẹo).")
async def claim(inter, amount: int):
    global users_data
    user_id = str(inter.author.id)

    if amount <= 0:
        await inter.response.send_message("Số lượng phải lớn hơn 0.", ephemeral=True)
        return

    hcoin_needed = amount * 1000
    
    if user_id not in users_data or users_data[user_id]['hcoin'] < hcoin_needed:
        await inter.response.send_message(f"Bạn không có đủ {hcoin_needed:,} Hcoin để đổi {amount:,} Kẹo.", ephemeral=True)
        return

    users_data[user_id]['hcoin'] -= hcoin_needed
    users_data[user_id]['candies'] += amount
    save_data(users_data)

    embed = disnake.Embed(
        title="Đổi Kẹo Thành Công! 🍬",
        description=f"Bạn đã đổi **{hcoin_needed:,} Hcoin** lấy **{amount:,} Kẹo**.\nTổng số Kẹo hiện tại: **{users_data[user_id]['candies']:,}**",
        color=0x00ff00
    )
    await inter.response.send_message(embed=embed, ephemeral=True)


@bot.slash_command(description="Hiển thị bảng xếp hạng Hcoin.")
async def leaderboard(inter):
    sorted_users = sorted(users_data.items(), key=lambda item: item[1]['hcoin'], reverse=True)
    
    description = "**TOP 10 NGƯỜI DÙNG**\n\n"
    for i, (user_id, data) in enumerate(sorted_users[:10]):
        user = bot.get_user(int(user_id))
        username = user.display_name if user else f"Người dùng ID: {user_id}"
        description += f"**#{i+1}** - {username}: **{data['hcoin']:,} Hcoin**\n"
        
    embed = disnake.Embed(
        title="🏆 Bảng Xếp Hạng Hcoin 🏆",
        description=description,
        color=0xffd700
    )
    await inter.response.send_message(embed=embed)


# === LOGIC WEB SERVER (NẰM TRONG FLASK) ===

@app.route('/', methods=['GET', 'POST'])
def home():
    global temp_message
    
    # LẤY DỮ LIỆU CHUẨN HÓA VÀ XẾP HẠNG
    leaderboard_data = []
    sorted_users = sorted(users_data.items(), key=lambda item: item[1]['hcoin'], reverse=True)
    for i, (user_id, data) in enumerate(sorted_users):
        user = bot.get_user(int(user_id))
        username = user.display_name if user else f"ID: {user_id[:5]}..."
        leaderboard_data.append({'rank': i+1, 'name': username, 'hcoin': data['hcoin']})


# LOGIC TRẠNG THÁI BOT ĐÃ SỬA LỖI ATTRIBUTE ERROR (DÁN ĐÈ KHỐI CŨ)
if bot.is_ready() and bot.user:
    bot_status_name = bot.user.name
    status_text = "ONLINE"
    status_color = "#00FF00"
else:
    # Đảm bảo tên bot mặc định là "..." khi chưa đăng nhập
    bot_status_name = "..."
    status_text = "KHỞI ĐỘNG..."
    status_color = "#FFA500"

# LẤY DỮ LIỆU BẢNG XẾP HẠNG HTML
html_table = f"""
<table class="leaderboard-table">
    <tr>
        <th>Hạng</th>
        <th>Tên Người Chơi</th>
        <th>Hcoin (Coin)</th>
    </tr>
"""

for item in leaderboard_data:
    html_table += f"""
    <tr>
        <td>{item['rank']}</td>
        <td>{item['name']}</td>
        <td>{item['hcoin']:,}</td>
    </tr>
"""
html_table += "</table>"

# LẤY DỮ LIỆU BẢNG SỰ KIỆN HTML (ví dụ)
html_event_list = ""
event_data = [
    {"icon": "🏆", "title": "Giải Đấu Coin Hàng Tuần", "detail": "Top 10 Hcoin nhận thêm 100 Kẹo."},
    {"icon": "🛠️", "title": "Cập nhật Anti-Cheat", "detail": "Bot sẽ tự động kiểm tra gian lận."},
    {"icon": "🛡️", "title": "Bảo Trì Hệ Thống", "detail": "Hệ thống sẽ bảo trì định kỳ vào 2 giờ sáng."},
]

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

# PHẦN 1: HTML MỞ ĐẦU, CSS, VÀ JAVASCRIPT
html_start = f"""
<!DOCTYPE html>
<html lang="vi">
<head>
    <title>{bot_status_name} - Dashboard Hiện Đại</title>
    <link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --main-color: #00FF00;
            --mine-color: #EE44EE;
            --dark-bg: #1e1e1e;
            --card-bg: #2d2d2d;
            --text-color: #ffffff;
            --border-color: #3f3f3f;
        }}
        body {{
            font-family: 'Space Mono', monospace;
            background-color: var(--dark-bg);
            color: var(--text-color);
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
        }}
        .container {{
            width: 100%;
            max-width: 1200px;
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
        }}
        .dashboard-main {{
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}
        .dashboard-card {{
            background-color: var(--card-bg);
            padding: 25px;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }}
        .dashboard-card h2 {{
            color: var(--main-color);
            margin-top: 0;
            margin-bottom: 20px;
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 10px;
            font-size: 1.5em;
        }}
        .status-badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            text-transform: uppercase;
            font-size: 0.9em;
        }}
        /* Màu trạng thái Bot */
        .status-online {{
            background-color: var(--main-color);
            color: var(--dark-bg);
        }}
        .status-loading {{
            background-color: var(--status-color);
            color: var(--dark-bg);
        }}
        /* Bảng xếp hạng */
        .leaderboard-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        .leaderboard-table th, .leaderboard-table td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}
        .leaderboard-table th {{
            color: var(--mine-color);
            text-transform: uppercase;
            font-size: 0.8em;
        }}
        .leaderboard-table tr:nth-child(even) {{
            background-color: rgba(0, 0, 0, 0.1);
        }}
        /* Form và Input */
        form {{
            display: flex;
            flex-direction: column;
            gap: 15px;
            margin-top: 15px;
        }}
        input[type="text"], input[type="number"] {{
            padding: 12px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            background-color: var(--dark-bg);
            color: var(--text-color);
            font-size: 1em;
            font-family: 'Space Mono', monospace;
        }}
        button[type="submit"] {{
            padding: 12px 20px;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            font-size: 1em;
            font-weight: bold;
            transition: background-color 0.3s;
            font-family: 'Space Mono', monospace;
        }}
        button[type="submit"]:hover {{
            opacity: 0.9;
        }}
        /* Events Sidebar */
        .events-sidebar {{
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}
        .event-item {{
            display: flex;
            gap: 15px;
            padding: 15px;
            border-radius: 8px;
            background-color: #3a3a3a;
            border-left: 5px solid var(--mine-color);
        }}
        .event-icon {{
            font-size: 1.5em;
        }}
        .event-content strong {{
            color: var(--main-color);
        }}
        .event-content p {{
            margin: 5px 0 0;
            font-size: 0.9em;
            color: #ccc;
        }}
        /* Thông báo */
        #notification-box {{
            position: fixed;
            top: 20px;
            right: 20px;
            background-color: #333;
            color: white;
            padding: 15px 25px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
            z-index: 1000;
            display: none;
            font-size: 1em;
        }}
    </style>
</head>
<body>
    <div id="notification-box"></div>
    <div class="container">
        <div class="dashboard-main">
            <div class="dashboard-card">
                <h2 style="border-color: var(--main-color);">👾 TRẠNG THÁI BOT</h2>
                <span class="status-badge" id="bot-status-display" style="background-color: {status_color}; color: var(--dark-bg);">
                    {status_text}
                </span>
                <p style="margin-top: 15px; color: #aaa;">Bot Discord đang chạy và phục vụ bạn! Tên bot: <strong>{bot_status_name}</strong></p>
                <hr style="border-color: var(--border-color); margin: 25px 0;"/>
                
                <h2>💵 VÍ (WALLET)</h2>
                <p style="color: var(--mine-color); font-weight: bold;">Chức năng này cần dùng lệnh /wallet trong Discord để kiểm tra ví!</p>
                <a href="https://discord.com/channels/@me" target="_blank" style="text-decoration: none;">
                    <button style="background-color: var(--mine-color); color: var(--dark-bg); border: none;">
                        <span style="font-size: 1.2em;">➡️</span> ĐI ĐẾN DISCORD ĐỂ RÚT/KIỂM TRA VÍ
                    </button>
                </a>
                
                <hr style="border-color: var(--border-color); margin: 25px 0;"/>
                
                <h2>⛏️ THU THẬP HCOIN ĐÃ ĐÀO (Cố định: 1000 Hcoin)</h2>
                <p style="color: var(--mine-color); font-weight: bold;">Nhập ID và số lượng Hcoin muốn đào (Dùng lệnh /collect trong Discord để thu thập)</p>
                
                <form method="POST" action="{url_for('web_collect_mined_hcoin')}">
                    <input type="text" name="discord_id_collect" placeholder="ID Discord (Tùy chọn)" required>
                    <input type="number" name="mined_amount" id="mined_amount" value="1000" placeholder="Số lượng Hcoin muốn đào (1000)" required min="1000">
                    <button type="submit" style="background-color: var(--mine-color); color: var(--dark-bg);">
                        ⛏️ THU THẬP HCOIN NGAY
                    </button>
                </form>
            </div>
            
            <div class="dashboard-card leaderboard-card">
                <h2>🏆 BẢNG XẾP HẠNG HCOIN | TOP USERS</h2>
                {html_table}
                <p style="margin-top: 50px; color: #888;">Sử dụng lệnh /leaderboard trong Discord để xem chi tiết.</p>
            </div>
        </div>
        
        <div class="events-sidebar dashboard-card">
            <h2>📢 THÔNG BÁO VÀ SỰ KIỆN</h2>
            {html_event_list}
        </div>
    </div>
    <script>
        const notificationBox = document.getElementById('notification-box');
        const tempMessage = "{temp_message}";

        if (tempMessage && tempMessage !== "None") {{
            notificationBox.textContent = tempMessage;
            notificationBox.style.display = 'block';
            setTimeout(() => {{
                notificationBox.style.display = 'none';
            }}, 5000);
            
            // Xóa thông báo khỏi Python sau khi hiển thị
            fetch('{url_for("clear_message")}', {{ method: 'POST' }});
        }}

        // Cập nhật trạng thái Bot (Nếu cần)
        // Đây chỉ là giao diện tĩnh, trạng thái thực được lấy từ Python khi tải trang
    </script>
</body>
</html>
"""
    temp_message = None # Reset thông báo sau khi render
    return html_start

@app.route('/collect-hcoin', methods=['POST'])
def web_collect_mined_hcoin():
    # Chức năng này chỉ gọi /collect của bot. Chỉ có thể dùng lệnh /collect
    # trong Discord để thu thập Hcoin, không thể thu thập qua Web để tránh gian lận.
    global temp_message
    temp_message = "⚠️ Chức năng Thu thập Hcoin chỉ có thể được thực hiện bằng lệnh /collect trực tiếp trong Discord để đảm bảo an toàn."
    return redirect(url_for('home'))

@app.route('/clear-message', methods=['POST'])
def clear_message():
    global temp_message
    temp_message = None
    return jsonify({'status': 'ok'})

# KHỐI CODE CUỐI CÙNG ĐÃ CHUẨN HÓA VÀ FIX LỖI CÚ PHÁP
def run_bot():
    bot.run(DISCORD_BOT_TOKEN)

def run_web():
    # Sử dụng gevent để chạy Flask web server trên luồng phụ
    http_server = WSGIServer(('', 5000), app)
    http_server.serve_forever()

if __name__ == '__main__':
    # Chạy Web Server trên luồng phụ
    spawn(run_web)
    
    # Chạy Bot trên luồng chính
    run_bot()
