import os
from flask import Flask, request, jsonify
from datetime import datetime
import traceback

# Tạo thư mục uploads
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    print(f"✅ Created upload folder: {UPLOAD_FOLDER}")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max

print("=" * 50)
print("🚀 AI Server Starting...")
print("=" * 50)

@app.before_request
def log_request_info():
    """Log mọi request đến server"""
    print("\n" + "=" * 50)
    print(f"📥 NEW REQUEST: {request.method} {request.path}")
    print(f"🌐 From: {request.remote_addr}")
    print(f"📋 Headers:")
    for header, value in request.headers.items():
        print(f"   {header}: {value}")
    
    if request.data:
        print(f"📦 Content Length: {len(request.data)} bytes")
    else:
        print("📦 No data in request body")
    print("=" * 50)

@app.route('/', methods=['GET'])
def home():
    """Homepage để test server"""
    return jsonify({
        "status": "running",
        "service": "AI Image Processing Server",
        "endpoints": {
            "/api/upload": "POST - Upload image",
            "/api/status": "GET - Server status",
            "/api/test": "GET - Simple test"
        }
    })

@app.route('/api/test', methods=['GET'])
def test():
    """Simple test endpoint"""
    print("✅ Test endpoint called")
    return jsonify({"status": "ok", "message": "Server is working!"})

@app.route('/api/status', methods=['GET'])
def status():
    """Status endpoint"""
    print("✅ Status endpoint called")
    
    # Count uploaded files
    files = []
    if os.path.exists(UPLOAD_FOLDER):
        files = os.listdir(UPLOAD_FOLDER)
    
    return jsonify({
        "status": "running",
        "upload_folder": UPLOAD_FOLDER,
        "total_images": len(files),
        "recent_files": files[-5:] if files else []
    })

@app.route('/api/upload', methods=['POST'])
def upload_image():
    """Main upload endpoint"""
    try:
        print("\n🎯 [UPLOAD] Processing upload request...")
        
        # 1. Kiểm tra content type
        content_type = request.headers.get('Content-Type', '')
        print(f"📋 Content-Type: {content_type}")
        
        # 2. Lấy dữ liệu ảnh
        image_data = request.data
        
        if not image_data or len(image_data) == 0:
            print("❌ [UPLOAD] No image data received!")
            return jsonify({
                "error": "No image data",
                "received_bytes": 0
            }), 400
        
        print(f"✅ [UPLOAD] Received {len(image_data)} bytes")
        
        # 3. Tạo tên file duy nhất
        now = datetime.now()
        filename = now.strftime("%Y-%m-%d_%H-%M-%S") + ".jpg"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        print(f"💾 [UPLOAD] Saving to: {filepath}")
        
        # 4. Lưu file
        try:
            with open(filepath, 'wb') as f:
                bytes_written = f.write(image_data)
            print(f"✅ [UPLOAD] Saved successfully! ({bytes_written} bytes written)")
        except Exception as e:
            print(f"❌ [UPLOAD] Failed to save file: {e}")
            return jsonify({"error": f"Failed to save: {str(e)}"}), 500
        
        # 5. Verify file exists
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"✅ [UPLOAD] File verified on disk: {file_size} bytes")
        else:
            print(f"❌ [UPLOAD] File not found after saving!")
        
        # 6. Phản hồi thành công
        response_data = {
            "status": "success",
            "message": "Image uploaded and saved successfully",
            "filename": filename,
            "size": len(image_data),
            "saved_to": filepath,
            "timestamp": now.isoformat()
        }
        
        print(f"📤 [UPLOAD] Sending success response: {response_data}")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"❌ [UPLOAD] EXCEPTION OCCURRED!")
        print(f"❌ Error type: {type(e).__name__}")
        print(f"❌ Error message: {str(e)}")
        print(f"❌ Traceback:")
        traceback.print_exc()
        
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "type": type(e).__name__
        }), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large"""
    print(f"❌ File too large: {error}")
    return jsonify({"error": "File too large (max 10MB)"}), 413

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    print(f"❌ Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("✅ AI Server Ready!")
    print("=" * 50)
    print(f"📁 Upload folder: {os.path.abspath(UPLOAD_FOLDER)}")
    print(f"🌐 Server will run on: http://0.0.0.0:5000")
    print(f"📡 Upload endpoint: http://0.0.0.0:5000/api/upload")
    print("=" * 50)
    print("\nPress CTRL+C to stop server\n")
    
    # Chạy với debug=True và logs chi tiết
    app.run(
        debug=True, 
        host='0.0.0.0', 
        port=5000,
        threaded=True
    )