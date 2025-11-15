import os
from flask import Flask, request, jsonify
from datetime import datetime

# Tạo thư mục 'uploads' nếu nó chưa tồn tại
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

print("Server AI đang khởi động...")

# Đây là "endpoint" mà ESP32 sẽ gọi đến
@app.route('/api/upload', methods=['POST'])
def upload_image():
    try:
        # 1. Nhận dữ liệu ảnh thô (raw data) từ ESP32
        image_data = request.data
        
        if not image_data:
            return jsonify({"error": "Không có dữ liệu ảnh"}), 400

        # 2. Tạo một tên file duy nhất dựa trên thời gian
        now = datetime.now()
        filename = now.strftime("%Y-%m-%d_%H-%M-%S") + ".jpg"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # 3. Lưu dữ liệu ảnh vào file
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        print(f"✓ Đã nhận và lưu ảnh: {filename} ({len(image_data)} bytes)")

        # 4. Phản hồi lại cho ESP32 (báo là đã thành công)
        # (Mô hình AI của bạn có thể xử lý ảnh ở đây và trả về kết quả)
        return jsonify({
            "message": "Upload thành công!",
            "filename": filename,
            "result": "Processing_AI..." # Đây là ví dụ
        }), 200

    except Exception as e:
        print(f"✗ Lỗi: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Chạy server trên tất cả các IP của máy tính (0.0.0.0)
    # và ở cổng (port) 5000
    app.run(debug=True, host='0.0.0.0', port=5000)