import random
import time
import os
import json
from flask import Flask, request, jsonify, redirect, url_for
from disnake.ext import commands
import disnake
import threading

# 0. CẤU HÌNH DỮ LIỆU VÀ BIẾN TOÀN CỤC
USERS_FILE = 'users.json'
temp_message = None

# Thiết lập tốc độ đào
Hcoin_PER_SECOND = 100

def load_data():
    """Tải dữ liệu người dùng từ tệp JSON và đảm bảo các trường cần thiết."""
    users_data = {}
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                users_data = json.load(f)
        except json.JSONDecodeError:
            print(f"LỖI: Không thể giải mã JSON từ {USERS_FILE}. Khởi tạo lại dữ liệu.")
            users_data = {}

    # Đảm bảo mỗi user có trường hcoin, candies và last_claim
    for user_id, data in users_data.items():
        if 'hcoin' not in data:
            data['hcoin'] = 10000 # Gán Hcoin mặc định
        if 'candies' not in data:
            data['candies'] = 0
        if 'last_collect' not in data:
            data['last_collect'] = 0
        if 'last_claim' not in data:
            data['last_claim'] = 0
            
    return users_data

def save_data(data):
    """Lưu dữ liệu người dùng vào tệp JSON."""
    with open(USERS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# 1. CẤU HÌNH DISCORD & FLASK
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
intents = disnake.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)
app = Flask(__name__)

# 2. LOGIC DISCORD BOT (LỆNH XÉT /)
@bot.event
async def on_ready():
    print(f"✅ Discord Bot ĐÃ ĐĂNG NHẬP: {bot.user.name} (ID: {bot.user.id})")

@bot.slash_command(name="hello", description="Kiểm tra trạng thái bot và đăng ký ID")
async def hello_command(inter: disnake.ApplicationCommandInteraction):
    await inter.response.send_message(f"👋 Chào bạn, tôi là {bot.user.name}. Bot Discord đang chạy 24/7. ID của bạn đã được đăng ký.")
    # Logic đăng ký user (Duy trì code cũ)
    users_data = load_data()
    user_id_str = str(inter.author.id)
    if user_id_str not in users_data:
        users_data[user_id_str] = {
            'hcoin': 10000,
            'candies': 0,
            'last_claim': 0,
            'last_collect': 0
        }
        save_data(users_data)
        await inter.followup.send("✅ ID Discord của bạn đã được đăng ký vào hệ thống.")

@bot.slash_command(name="coin", description="Kiểm tra Hcoin và Kẹo")
async def coin_command(inter: disnake.ApplicationCommandInteraction):
    users_data = load_data()
    user_id_str = str(inter.author.id)
    
    if user_id_str not in users_data:
        await inter.response.send_message("❌ Vui lòng sử dụng lệnh /hello để đăng ký ID trước.")
        return

    hcoin = users_data[user_id_str].get('hcoin', 0)
    candies = users_data[user_id_str].get('candies', 0)
    
    await inter.response.send_message(f"💰 Bạn có **{hcoin:,} Hcoin** và **{candies} Kẹo**.")

@bot.slash_command(name="doikẹo", description="Đổi 50 Kẹo lấy 100 Hcoin")
async def trade_command(inter: disnake.ApplicationCommandInteraction):
    users_data = load_data()
    user_id_str = str(inter.author.id)
    
    if user_id_str not in users_data or users_data[user_id_str].get('candies', 0) < 50:
        await inter.response.send_message("❌ Bạn cần ít nhất 50 Kẹo để đổi lấy Hcoin.")
        return

    users_data[user_id_str]['candies'] -= 50
    users_data[user_id_str]['hcoin'] += 100
    save_data(users_data)
    
    await inter.response.send_message("🎉 Đổi Kẹo thành công! Bạn mất 50 Kẹo và nhận được 100 Hcoin.")

# *** LỖI BẢO MẬT ĐÃ VÁ: COOLDOWN 24 GIỜ ***
@app.route('/web_claim_candies', methods=['POST'])
def web_claim_candies():
    global temp_message
    
    user_id = request.form.get('discord_id')
    users_data = load_data()

    if not user_id:
        temp_message = "LỖI: Vui lòng nhập ID Discord của bạn."
        return redirect(url_for('home'))

    if user_id not in users_data:
        temp_message = f"LỖI: Không tìm thấy ID Discord {user_id}. Vui lòng đăng ký bằng lệnh /hello trên Discord."
        return redirect(url_for('home'))

    # Thiết lập trị cố định và Cooldown 24h (86400 giây)
    CANDY_TO_ADD = 50
    COOLDOWN_SECONDS = 86400
    current_time = int(time.time())

    last_claim = users_data[user_id].get('last_claim', 0)
    
    # 1. Kiểm tra Cooldown
    remaining = last_claim + COOLDOWN_SECONDS - current_time
    
    if remaining > 0:
        minutes = int((remaining % 3600) / 60)
        hours = int(remaining // 3600)
        temp_message = f"Đã nhận rồi! Vui lòng chờ {hours} giờ {minutes} phút nữa."
        return redirect(url_for('home'))

    # 2. CỘNG KẸO
    users_data[user_id]['candies'] += CANDY_TO_ADD
    users_data[user_id]['last_claim'] = current_time # Cập nhật thời gian claim
    save_data(users_data)
    
    temp_message = f"CHÚC MỪNG! ID {user_id} đã nhận thành công {CANDY_TO_ADD} Kẹo."
    return redirect(url_for('home'))


@app.route('/web_collect_mined_hcoin', methods=['POST'])
def web_collect_mined_hcoin():
    global temp_message
    
    # Xử lý yêu cầu thu thập Hcoin đã đào từ form trên web (CỘNG Hcoin và áp dụng Cooldown)
    user_id = request.form.get('discord_id_collect')
    amount_str = request.form.get('mined_amount')

    # 1. Kiểm tra dữ liệu đầu vào
    if not user_id or not amount_str:
        temp_message = "LỖI: Vui lòng nhập ID Discord và số lượng Hcoin đã đào."
        return redirect(url_for('home'))

    try:
        amount = int(amount_str)
    except ValueError:
        temp_message = "LỖI: Số lượng Hcoin phải là số nguyên."
        return redirect(url_for('home'))

    if amount <= 0:
        temp_message = "LỖI: Số lượng thu thập phải lớn hơn 0."
        return redirect(url_for('home'))
        
    users_data = load_data()

    if user_id not in users_data:
        temp_message = f"LỖI: Không tìm thấy ID Discord {user_id}."
        return redirect(url_for('home'))

    # Thiết lập trị cố định và Cooldown 24h (86400 giây)
    FIXED_COLLECT_AMOUNT = 1000 # Bot luôn cộng 1000 Hcoin
    COOLDOWN_SECONDS = 86400 # 24 giờ
    current_time = int(time.time())

    # 2. Kiểm tra Cooldown
    last_collect = users_data[user_id].get('last_collect', 0)
    remaining = last_collect + COOLDOWN_SECONDS - current_time
    
    if remaining > 0:
        minutes = int((remaining % 3600) / 60)
        hours = int(remaining // 3600)
        temp_message = f"Đã thu thập rồi! Vui lòng chờ {hours} giờ {minutes} phút nữa."
        return redirect(url_for('home'))

    # 3. Thực hiện cộng Hcoin
    users_data[user_id]['hcoin'] += FIXED_COLLECT_AMOUNT
    users_data[user_id]['last_collect'] = current_time # Cập nhật thời gian thu thập
    save_data(users_data)

    temp_message = f"🎉 THU THẬP THÀNH CÔNG! ID {user_id} đã cộng {FIXED_COLLECT_AMOUNT} Hcoin vào tài khoản."
    return redirect(url_for('home'))


# 3. LOGIC FLASK (WEB DASHBOARD)
@app.route('/', methods=['GET'])
def home():
    global temp_message
    global bot
    
    # ########################################################
    # LOGIC PYTHON TRÊN WEB
    # ########################################################
    
    # Xử lý thông báo
    alert_html = ""
    if temp_message:
        alert_html = f"""
        <div class="alert-message">{temp_message}</div>
        """
        temp_message = None # Đảm bảo tin nhắn chỉ hiển thị một lần
        
    # LẤY DỮ LIỆU BẢNG XẾP HẠNG (THẬT) TỪ FILE USERS.JSON
    users_data = load_data()
    
    # Lọc ra những người chơi có Hcoin và sắp xếp
    sorted_users = sorted(
        [(user_id, data['hcoin']) for user_id, data in users_data.items() if data.get('hcoin', 0) > 0],
        key=lambda x: x[1],
        reverse=True
    )
    
    leaderboard_data = []
    rank = 1
    
    # Lặp qua dữ liệu đã sắp xếp, giới hạn TOP 10
    for user_id, hcoin in sorted_users[:10]:
        user_name = "..." # Mặc định là dấu ba chấm
        
        # *** LOGIC QUAN TRỌNG: Lấy Tên Người Dùng từ Discord ***
        try:
            # Chúng ta dùng ID để tìm kiếm User Object qua bot
            user = bot.get_user(int(user_id)) 
            if user:
                user_name = user.name # Lấy username Discord thật
            else:
                user_name = f"ID: {user_id}" # Nếu không tìm thấy, hiển thị ID
        except ValueError:
            user_name = f"ID: {user_id}"
        
        leaderboard_data.append({
            'rank': rank,
            'name': user_name,
            'hcoin': hcoin
        })
        rank += 1
    # KẾT THÚC LOGIC BẢNG XẾP HẠNG THẬT
    
    
    # DỮ LIỆU SỰ KIỆN (Không đổi)
    event_data = [
        {"icon": "🎉", "title": "Chào mừng Tháng 11!", "detail": "Tham gia máy chủ Discord để nhận gói quà tân thủ trị giá 100 Hcoin."},
        {"icon": "🎃", "title": "Sự Kiện Lễ Tạ Ơn", "detail": "Thời gian giao dịch Kẹo diễn ra mỗi cuối tuần."},
        {"icon": "🍬", "title": "Khuyến mãi Đổi Kẹo", "detail": "Nhận 200 Hcoin miễn phí khi đổi 50 Kẹo lần đầu."},
        {"icon": "🏆", "title": "Giải Đấu Coin Hàng Tuần", "detail": "Tỉ lệ đột kích Boss Dungeon tăng 50%."},
        {"icon": "🛠️", "title": "Cập nhật Anti-Cheat", "detail": "Hệ thống chống gian lận mới được triển khai để bảo vệ công bằng."},
        {"icon": "⚒️", "title": "Bảo Trì Hệ Thống", "detail": "Hệ thống sẽ bảo trì hàng tuần vào 2 giờ sáng ngày thứ Hai."},
    ]
    
    # Kiểm tra an toàn trước khi truy cập bot.user
if bot.is_ready() and bot.user:
    bot_status_name = bot.user.name
else:
    bot_status_name = "Discord Bot 704" 

status_text = "ONLINE"
status_color = "#00FF00" 

if not bot.is_ready():
    status_text = "KHỞI ĐỘNG..." 
    status_color = "#FFA500"
    bot_status_name = "..."
    
 
    
    # Lấy dữ liệu bảng xếp hạng HTML
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

    # ########################################################
    # PHẦN HTML
    # ########################################################
    
    html_start = f"""
    
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <title>🤖 {bot_status_name} - Dashboard Hiện Đại</title>
        <link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@700&display=swap" rel="stylesheet">
        <style>
            :root {{
                --main-color: #00FFEE; /* Cyan Neon */
                --accent-color: #FF00FF; /* Magenta Neon */
                --dark-bg: #111111;
                --card-bg: #222222;
                --border-color: #333333;
                --mine-color: #FFFF00; /* Vàng Neon */
            }}
            body {{
                background-color: var(--dark-bg);
                color: var(--main-color);
                font-family: 'Space Mono', monospace;
                padding-top: 50px;
                margin: 0;
            }}
            .container {{
                width: 90%;
                max-width: 800px;
                margin: 0 auto;
            }}
            h1 {{
                color: var(--accent-color);
                border-bottom: 2px solid var(--border-color);
                padding-bottom: 10px;
            }}
            .dashboard-card {{
                background-color: var(--card-bg);
                border: 1px solid var(--border-color);
                padding: 20px;
                margin-bottom: 20px;
                border-radius: 8px;
            }}
            .status-card {{
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .status-text {{
                font-size: 1.2em;
                font-weight: bold;
                padding: 5px 10px;
                border-radius: 4px;
            }}
            /* CẢNH BÁO */
            .alert-message {{
                background-color: #FF0000;
                color: white;
                padding: 15px;
                margin-bottom: 20px;
                border-radius: 4px;
                font-weight: bold;
                text-align: center;
                animation: fadeinout 5s linear forwards;
            }}
            @keyframes fadeinout {{
                0%, 100% {{ opacity: 0; }}
                10% {{ opacity: 1; }}
                90% {{ opacity: 1; }}
            }}

            /* FORM & BUTTON */
            form {{
                margin-top: 15px;
                padding: 15px;
                border: 1px dashed var(--border-color);
                border-radius: 4px;
            }}
            input[type="text"], input[type="number"] {{
                width: calc(100% - 20px);
                padding: 10px;
                margin-bottom: 10px;
                background-color: var(--dark-bg);
                border: 1px solid var(--border-color);
                color: var(--main-color);
                border-radius: 4px;
            }}
            button {{
                background-color: var(--accent-color);
                color: var(--dark-bg);
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-family: 'Space Mono', monospace;
                font-weight: bold;
                width: 100%;
                transition: opacity 0.3s;
            }}
            button:hover {{
                opacity: 0.8;
            }}
            .mine-btn {{
                background-color: var(--mine-color);
            }}
            .hidden {{
                display: none;
            }}

            /* BẢNG XẾP HẠNG */
            .leaderboard-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
            }}
            .leaderboard-table th, .leaderboard-table td {{
                padding: 10px;
                text-align: left;
                border-bottom: 1px solid var(--border-color);
            }}
            .leaderboard-table th {{
                background-color: var(--card-bg);
                color: var(--accent-color);
            }}
            .leaderboard-table tr:hover {{
                background-color: #2a2a2a;
            }}
            .leaderboard-table tr:nth-child(odd) {{
                background-color: #1a1a1a;
            }}

            /* SỰ KIỆN */
            .event-item {{
                display: flex;
                margin-bottom: 15px;
                padding: 10px;
                background-color: #2a2a2a;
                border-radius: 4px;
            }}
            .event-icon {{
                font-size: 1.5em;
                margin-right: 15px;
            }}
            .event-content strong {{
                color: var(--mine-color);
                display: block;
            }}
            .event-content p {{
                margin: 0;
                font-size: 0.9em;
                color: #bbb;
            }}
        </style>
        <script>
            let mining_interval = null;
            let hcoin_balance = 0;
            const Hcoin_PER_SECOND = {Hcoin_PER_SECOND};

            function update_display() {{
                document.getElementById('hcoin-count').innerText = hcoin_balance.toLocaleString('en-US');
            }}

            function start_mining() {{
                if (mining_interval) return;

                document.getElementById('start-btn').classList.add('hidden');
                document.getElementById('stop-btn').classList.remove('hidden');
                
                document.getElementById('mining-status').innerText = "Đang đào... ⛏️";

                // Thay cập nhật 1000ms (1 giây)
                mining_interval = setInterval(() => {{
                    hcoin_balance += Hcoin_PER_SECOND;
                    update_display();
                }}, 1000);
            }}

            function stop_mining() {{
                if (mining_interval === null) return;

                clearInterval(mining_interval);
                mining_interval = null;

                document.getElementById('start-btn').classList.remove('hidden');
                document.getElementById('stop-btn').classList.add('hidden');
                
                document.getElementById('mining-status').innerText = "Đã dừng. Đã đào được " + hcoin_balance.toLocaleString('en-US') + " Hcoin.";
            }}
            
            window.onload = function() {{
                update_display();
                document.getElementById('mining-status').innerText = "Sẵn sàng Đào Hcoin! (Tốc độ: {Hcoin_PER_SECOND} Hcoin/s)";
                
                // Gán giá trị Hcoin đã đào vào form
                document.getElementById('web_collect_mined_hcoin').onsubmit = function() {{
                    document.getElementById('mined_amount').value = hcoin_balance;
                    hcoin_balance = 0; // Reset số dư sau khi thu thập
                    stop_mining();
                }};
            }};
        </script>
    </head>
    <body>
        <div class="container">
            
            {alert_html}
            
            <h1>{bot_status_name} DASHBOARD :: Hcoin Mining</h1>

            <div class="dashboard-card status-card">
                <h2>TRẠNG THÁI BOT</h2>
                <div class="status-text" style="background-color: {status_color}; color: var(--dark-bg);">
                    {status_text}
                </div>
            </div>

            <div class="dashboard-card mining-card">
                <h2>⫸ MÁY ĐÀO Hcoin TỐC ĐỘ CAO</h2>
                <p style="color: var(--mine-color); font-weight: bold;">Hcoin Đã Đào: <span id="hcoin-count">0</span> Hcoin</p>
                <p id="mining-status" style="font-style: italic;"></p>
                
                <button class="mine-btn" id="start-btn" onclick="start_mining()">🔥 BẮT ĐẦU ĐÀO</button>
                <button class="mine-btn hidden" id="stop-btn" onclick="stop_mining()">🛑 DỪNG ĐÀO</button>
                <p style="color: #999; font-size: 0.8em; margin-top: 15px;">* LƯU Ý: Số Hcoin này chưa được cộng vào tài khoản.</p>
            </div>
            
            <div class="dashboard-card event-list">
                <h2>SỰ KIỆN & CẬP NHẬT MỚI</h2>
                {html_event_list}
            </div>
            
            <div class="dashboard-card claim-card">
                <h2>⫸ NHẬN KẸO MIỄN PHÍ | CLAIM REWARD</h2>
                <p style="color: #bbb;">**Nhập **ID Discord** để nhận **50 Kẹo** mỗi 24 giờ.**</p>
                
                <form method="POST" action="{url_for('web_claim_candies')}">
                    <input type="text" id="discord_id" name="discord_id" placeholder="ID Discord (Ví dụ: 704123456789...)" required>
                    <button type="submit" style="border-color: var(--border-color); margin: 25px 0;">CLAIM KẸO NGAY</button>
                </form>

                <hr style="border-color: var(--border-color); margin: 25px 0;">
                
                <h2>⫸ VÍ (WALLET)</h2>
                <p style="color: var(--mine-color); font-weight: bold;">Chức năng này cần được sử dụng qua Bot Discord.</p>
                
                <a href="https://discord.com/channels/@me" target="_blank" style="text-decoration: none;">
                    <button style="background-color: var(--mine-color); color: var(--dark-bg); border: none;">
                        💸 ĐI ĐẾN DISCORD ĐỂ RÚT/KIỂM TRA VÍ
                    </button>
                </a>


                <hr style="border-color: var(--border-color); margin: 25px 0;">
                
                <h2>⫸ THU THẬP HCOIN ĐÃ ĐÀO (Cố định: 1000 Hcoin)</h2>
                <p style="color: var(--mine-color); font-weight: bold;">*Nhập ID và số lượng Hcoin đã đào để cộng vào tài khoản (Cooldown 24h).</p>
                
                <form method="POST" action="{url_for('web_collect_mined_hcoin')}" id="web_collect_mined_hcoin">
                    <input type="text" name="discord_id_collect" placeholder="ID Discord (Ví dụ: 704123456789...)" required>
                    <input type="number" name="mined_amount" id="mined_amount" value="0" hidden>
                    <button type="submit" style="background-color: var(--mine-color); color: var(--dark-bg);">
                        💰 THU THẬP HCOIN NGAY
                    </button>
                </form>
            </div>
            
            <div class="dashboard-card leaderboard-card">
                <h2>⫸ BẢNG XẾP HẠNG HCOIN | TOP USERS</h2>
                {html_table}
                <p style="margin-top: 50px; color: #888;">Sử dụng lệnh **/hello**, **/coin**, **/doikẹo** trong Discord và chọn **{bot.user.name}**.</p>
            </div>

        </div>
    </body>
    </html>
    """
    
    return html_start
