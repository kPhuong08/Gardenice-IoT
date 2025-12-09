import cv2
import requests
import time
import threading
import json

class LaptopCameraClient:
    def __init__(self, esp32_url, camera_index=0):
        self.esp32_url = esp32_url
        self.camera_index = camera_index
        self.cap = None
        self.send_count = 0
        self.success_count = 0
        
    def start_streaming(self, interval=5):
        """Bắt đầu stream ảnh đến ESP32"""
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            print("❌ Không thể mở camera laptop!")
            return False
        
        # Đặt độ phân giải nhỏ để tối ưu cho ESP32
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        
        print("\n" + "=" * 50)
        print("✅ Camera laptop đã sẵn sàng!")
        print(f"🎯 Target ESP32: {self.esp32_url}")
        print("📷 Cửa sổ Camera đang mở (Không có chữ). Nhấn 'q' để thoát.")
        print("=" * 50 + "\n")
        
        last_send_time = 0
        
        try:
            while True:
                current_time = time.time()
                
                ret, frame = self.cap.read()
                if not ret:
                    print("❌ Không thể chụp ảnh!")
                    continue
                
                # Gửi ảnh định kỳ
                if current_time - last_send_time >= interval:
                    self.send_count += 1
                    
                    # Dùng threading để gửi không làm chậm luồng hiển thị camera
                    # Copy frame để đảm bảo luồng gửi ảnh không bị ảnh hưởng bởi luồng hiển thị
                    frame_to_send = frame.copy()
                    
                    thread = threading.Thread(
                        target=self.send_image_to_esp32, 
                        args=(frame_to_send, self.send_count)
                    )
                    thread.daemon = True
                    thread.start()
                    
                    last_send_time = current_time
                
                # --- PHẦN ĐÃ CHỈNH SỬA: XÓA BỎ cv2.putText ---
                # Chỉ hiển thị khung hình sạch
                cv2.imshow('Camera Feed (Clean)', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        except KeyboardInterrupt:
            print("\n⏹️  Dừng chương trình...")
        finally:
            self.cleanup()
    
    def send_image_to_esp32(self, frame, count):
        """Gửi ảnh đến ESP32"""
        try:
            print(f"🔄 [SEND #{count}] Đang gửi ảnh...")
            
            # Encode ảnh
            small_frame = cv2.resize(frame, (320, 240))
            encode_param = [cv2.IMWRITE_JPEG_QUALITY, 30] 
            _, img_encoded = cv2.imencode('.jpg', small_frame, encode_param)
            image_data = img_encoded.tobytes()
            
            response = requests.post(
                f"{self.esp32_url}/upload",
                data=image_data,
                headers={'Content-Type': 'image/jpeg'},
                timeout=15 
            )
            
            if response.status_code == 200:
                self.success_count += 1
                print(f"✅ [SEND #{count}] Gửi thành công!")
            else:
                print(f"❌ [SEND #{count}] Thất bại: {response.status_code}")
                
        except Exception as e:
            print(f"❌ [SEND #{count}] Lỗi: {e}")
    
    def test_connection(self):
        """Test kết nối với ESP32"""
        print(f"Testing connection to {self.esp32_url}...")
        try:
            requests.get(f"{self.esp32_url}/test", timeout=3)
            print("✅ Kết nối OK")
            return True
        except:
            print("❌ Không thể kết nối tới ESP32")
            return False
    
    def cleanup(self):
        """Dọn dẹp"""
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("✅ Camera closed")

if __name__ == "__main__":
    # Đảm bảo IP này chính xác
    ESP32_IP = "http://192.168.67.225" 
    
    client = LaptopCameraClient(esp32_url=ESP32_IP, camera_index=0)
    
    if client.test_connection():
        print("\n🚀 Bắt đầu sau 3 giây...")
        time.sleep(3)
        client.start_streaming(interval=15) 
    else:
        print("\n❌ Lỗi kết nối! Kiểm tra IP.")