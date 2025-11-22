import os
from flask import Flask, request, jsonify
from google import genai
from google.genai.errors import APIError

# --- KHỞI TẠO FLASK VÀ GEMINI ---
app = Flask(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash" 

if not GEMINI_API_KEY:
    print("Lỗi: Thiếu GEMINI_API_KEY trong Environment Variables.")
    gemini_client = None
else:
    try:
        # Client được khởi tạo ngay khi ứng dụng bắt đầu
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        print(f'Đã khởi tạo Gemini Client với model: {MODEL_NAME}')
    except Exception as e:
        print(f"Lỗi khởi tạo Gemini Client: {e}")
        gemini_client = None

# --- API ENDPOINT DÙNG ĐỂ KIỂM TRA TÌNH TRẠNG DỊCH VỤ ---
@app.route('/', methods=['GET'])
def home():
    # Trang chủ xác nhận dịch vụ đang chạy
    return "Dịch vụ Web AI Gemini đang hoạt động. Sử dụng /api/gemini để gọi API.", 200

# --- API CHÍNH XỬ LÝ YÊU CẦU AI ---
@app.route('/api/gemini', methods=['POST'])
def gemini_api():
    if not gemini_client:
        return jsonify({"error": "Lỗi: Dịch vụ Gemini không được cấu hình do thiếu Key API."}), 500
    
    # Lấy dữ liệu từ yêu cầu POST
    try:
        data = request.get_json()
        prompt = data.get('prompt')
    except Exception:
        return jsonify({"error": "Lỗi: Yêu cầu phải là JSON hợp lệ."}), 400

    if not prompt:
        return jsonify({"error": "Thiếu trường 'prompt' trong yêu cầu."}), 400

    try:
        # Gọi API Gemini (đã tối ưu hóa để tránh lỗi 400)
        response = gemini_client.models.generate_content(
            model=MODEL_NAME,
            contents=[prompt]
        )
        
        return jsonify({
            "status": "success",
            "model": MODEL_NAME,
            "prompt_received": prompt,
            "response": response.text
        }), 200

    except APIError as e:
        # Lỗi 400 Bad Request (API bị giới hạn Quota)
        error_message = "Lỗi Gemini API: Yêu cầu bị từ chối. Vui lòng kiểm tra Key API và Quota."
        return jsonify({"error": "Lỗi Gemini API", "details": str(e), "message": error_message}), 400
        
    except Exception as e:
        return jsonify({"error": "Lỗi máy chủ không xác định", "details": str(e)}), 500

if __name__ == '__main__':
    # Render sẽ sử dụng gunicorn, nhưng lệnh này dùng để kiểm tra cục bộ
    # app.run(host='0.0.0.0', port=os.environ.get('PORT', 8080))
    print("Sử dụng Gunicorn để chạy ứng dụng trong môi trường Render.")
    
