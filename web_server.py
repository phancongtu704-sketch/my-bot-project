import json
import os
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

# Tên tệp dữ liệu
USERS_FILE = 'users.json'

def load_data():
    """Tải dữ liệu người dùng từ tệp JSON."""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            # Nếu tệp bị lỗi hoặc rỗng, trả về dictionary rỗng
            print(f"Lỗi: Không thể giải mã JSON từ {USERS_FILE}. Khởi tạo lại dữ liệu.")
            return {}
    return {}

def save_data(data):
    """Lưu dữ liệu người dùng vào tệp JSON."""
    with open(USERS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/')
def home():
    """Mặc định trang chủ."""
    return "Bot đang chạy! Sử dụng Discord để tương tác."

@app.route('/claim', methods=['POST'])
def claim_candy():
    """
    Logic: Người chơi nhận kẹo.
    - Đã bao gồm logic kiểm tra cooldown và thêm kẹo.
    """
    data = request.get_json()
    user_id = str(data.get('user_id'))
    
    if not user_id:
        return jsonify({'status': 'error', 'message': 'Thiếu user_id'}), 400

    users_data = load_data()
    current_time = int(time.time())
    
    # Thiết lập mặc định cho người dùng mới
    if user_id not in users_data:
        users_data[user_id] = {'candies': 0, 'last_claim': 0}

    last_claim = users_data[user_id].get('last_claim', 0)
    cooldown = 24 * 60 * 60 # 24 giờ
    
    if current_time - last_claim < cooldown:
        remaining = cooldown - (current_time - last_claim)
        return jsonify({
            'status': 'error',
            'message': 'Đã nhận rồi! Vui lòng chờ.',
            'cooldown_remaining': remaining
        }), 429
    
    # Logic NHẬN KẸO
    candy_to_add = 50 
    users_data[user_id]['candies'] += candy_to_add
    users_data[user_id]['last_claim'] = current_time
    
    save_data(users_data) # LƯU DỮ LIỆU
    
    return jsonify({
        'status': 'success',
        'message': f'Đã nhận thành công {candy_to_add} kẹo!',
        'new_balance': users_data[user_id]['candies']
    })

@app.route('/exchange', methods=['POST'])
def exchange_candy():
    """
    Logic: Người chơi đổi kẹo lấy vật phẩm.
    - FIX LỖI: Đã thêm logic TRỪ KẸO và LƯU DỮ LIỆU.
    """
    data = request.get_json()
    user_id = str(data.get('user_id'))
    candy_cost = 50 # Chi phí đổi kẹo
    
    if not user_id:
        return jsonify({'status': 'error', 'message': 'Thiếu user_id'}), 400

    users_data = load_data()
    
    if user_id not in users_data or users_data[user_id].get('candies', 0) < candy_cost:
        # Kiểm tra người dùng tồn tại và đủ kẹo
        current_candies = users_data.get(user_id, {}).get('candies', 0)
        return jsonify({
            'status': 'error', 
            'message': f'Không đủ kẹo để đổi! Bạn có {current_candies}, cần {candy_cost}.'
        }), 403

    # ===============================================
    # PHẦN FIX LỖI CHÍNH: TRỪ KẸO VÀ LƯU
    # ===============================================
    users_data[user_id]['candies'] -= candy_cost # Trừ 50 kẹo
    
    save_data(users_data) # CRITICAL: LƯU DỮ LIỆU sau khi trừ kẹo
    
    return jsonify({
        'status': 'success',
        'message': f'Đã đổi vật phẩm thành công, trừ {candy_cost} kẹo.',
        'new_balance': users_data[user_id]['candies']
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 5000))
    
