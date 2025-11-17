import json
import os
import time
import random # Cần thiết cho việc giả lập giá cổ phiếu
from flask import Flask, request, jsonify, redirect, url_for
import disnake
from disnake.ext import commands
import threading

# -------------------------------------------------------------------
# 0. CẤU HÌNH DỮ LIỆU VÀ BIẾN TOÀN CỤC
# -------------------------------------------------------------------
USERS_FILE = 'users.json'
temp_message = None # Biến tạm để lưu thông báo chuyển hướng

# Dữ liệu Chứng khoán giả lập ban đầu
STOCK_PRICES = {
    "VNM": {"price": 105.00, "change": 0.00},
    "HPG": {"price": 28.50, "change": 0.00},
    "VIC": {"price": 68.20, "change": 0.00},
}

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
# ... (Giữ nguyên các lệnh Discord: on_ready, hello, coin, xemkeo, doikeo) ...

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
# 3. LOGIC FLASK WEB SERVER (XỬ LÝ API VÀ NHẬN KẸO QUA WEB)
# -------------------------------------------------------------------

def generate_stock_prices():
    """Tạo ngẫu nhiên giá cổ phiếu để mô phỏng thị trường."""
    global STOCK_PRICES
    new_data = []

    for ticker, data in STOCK_PRICES.items():
        # Mô phỏng biến động ngẫu nhiên (tăng/giảm tới 0.5)
        fluctuation = round(random.uniform(-0.5, 0.5), 2)
        
        # Tính toán giá mới và sự thay đổi
        new_price = round(data['price'] + fluctuation, 2)
        price_change = round(new_price - data['price'], 2)
        
        # Đảm bảo giá không quá thấp (chỉ là giả lập)
        if new_price < 1.0:
            new_price = 1.0 
        
        # Tính phần trăm thay đổi
        percent_change = round((price_change / data['price']) * 100, 2)
        
        # Cập nhật trạng thái toàn cục cho lần gọi tiếp theo
        STOCK_PRICES[ticker]['price'] = new_price
        STOCK_PRICES[ticker]['change'] = price_change
        
        new_data.append({
            "ticker": ticker,
            "price": f"{new_price:,.2f}đ",
            "change_abs": f"{price_change:+,.2f}",
            "change_percent": f"{percent_change:+,.2f}%"
        })
        
    return new_data


@app.route('/stock_data', methods=['GET'])
def get_stock_data():
    """API trả về dữ liệu chứng khoán trực tiếp (giả lập)."""
    return jsonify(generate_stock_prices())


@app.route('/web_claim', methods=['POST'])
def web_claim_candy():
    # ... (Giữ nguyên logic nhận kẹo qua Web bằng ID Discord) ...
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
    """TRANG CHỦ - Giao diện Halloween VỚI BẢNG CHỨNG KHOÁN."""
    global temp_message
    
    # Dữ liệu Bảng Xếp Hạng Hcoin (Chủ đề Halloween)
    leaderboard_data = [
        {"rank": 1, "name": "Bóng Ma", "hcoin": 66666},
        {"rank": 2, "name": "Phù Thủy", "hcoin": 31100},
        {"rank": 3, "name": "Ma Cà Rồng", "hcoin": 13000},
        {"rank": 4, "name": "Người Sói", "hcoin": 9000},
        {"rank": 5, "name": "Bí Ngô", "hcoin": 4000},
    ]

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
        
    # HIỂN THỊ THÔNG BÁO TỪ REDIRECT
    alert_html = ""
    if temp_message:
        alert_html = f'<div class="alert-message">{temp_message}</div>'
        temp_message = None 

    # Trả về toàn bộ nội dung HTML với CSS, FORM và Bảng Chứng khoán
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
            .candy-box, .stock-market-box {{
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
            .alert-message {{
                padding: 15px;
                background-color: #ff6600;
                color: white;
                border-radius: 8px;
                margin-bottom: 20px;
                font-weight: bold;
            }}
            
            /* CSS RIÊNG CHO CHỨNG KHOÁN */
            .stock-market-box table th {{
                background-color: #7289da; /* Màu Discord Blue */
            }}
        </style>
        <script>
            // ======================================================
            // JAVASCRIPT: CẬP NHẬT BẢNG CHỨNG KHOÁN MỖI 1 PHÚT
            // ======================================================
            function updateStockTable() {{
                fetch('/stock_data')
                    .then(response => response.json())
                    .then(data => {{
                        const tbody = document.getElementById('stock-body');
                        tbody.innerHTML = ''; // Xóa dữ liệu cũ

                        data.forEach(stock => {{
                            const is_positive = stock.change_abs.startsWith('+');
                            const color = is_positive ? '#43b581' : '#ff6600'; // Xanh lá hoặc Cam/Đỏ
                            const arrow = is_positive ? '▲' : '▼';
                            
                            const row = `
                                <tr>
                                    <td><strong>${stock.ticker}</strong></td>
                                    <td>${stock.price}</td>
                                    <td style="color: ${color}; font-weight: bold;">${arrow} ${stock.change_abs}</td>
                                    <td style="color: ${color};">${stock.change_percent}</td>
                                </tr>
                            `;
                            tbody.innerHTML += row;
                        }});
                    }})
                    .catch(error => console.error('Lỗi khi tải dữ liệu chứng khoán:', error));
            }}

            // Tải lần đầu ngay khi trang load
            window.onload = function() {{
                updateStockTable(); 
                // Thiết lập Interval để cập nhật mỗi 60 giây (1 phút)
                setInterval(updateStockTable, 60000); 
            }};
        </script>
    </head>
    <body>
        <div class="container">
            <h1>🎃 Lễ Hội Ma Quái Halloween!</h1>
            <div class="status-box">👻 Trạng thái Bot: {bot_status}</div>
            
            {alert_html}

            <div class="candy-box">
                <h2>🎁 Nhận Kẹo Halloween qua Web!</h2>
                <p>Nhập **ID Discord** của bạn (chỉ là số) để nhận **50 Kẹo** miễn phí mỗi 24 giờ!</p>
                
                <form method="POST" action="/web_claim">
                    <input type="text" id="discord_id" name="discord_id" placeholder="Nhập ID Discord của bạn (ví dụ: 1234567890)">
                    <button type="submit">Nhận Kẹo Halloween</button>
                </form>
            </div>
            
            <div class="stock-market-box">
                <h2>📈 Thị Trường Chứng Khoán Ma Quái (Giá Live)</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Mã CK</th>
                            <th>Giá</th>
                            <th>Thay đổi</th>
                            <th>% Thay đổi</th>
                        </tr>
                    </thead>
                    <tbody id="stock-body">
                        </tbody>
                </table>
                <p style="font-size: 0.8em; margin-top: 10px; color: #aaa;">Cập nhật mỗi 1 phút. Dữ liệu chỉ mang tính chất minh họa.</p>
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
