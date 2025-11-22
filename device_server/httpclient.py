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
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        
        print("\n" + "=" * 50)
        print("✅ Camera laptop đã sẵn sàng!")
        print(f"🎯 Target ESP32: {self.esp32_url}")
        print(f"⏰ Send interval: {interval}s")
        print("📷 Nhấn 'q' để thoát")
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
                    print(f"\n📸 [CAPTURE #{self.send_count}] Taking snapshot...")
                    
                    thread = threading.Thread(
                        target=self.send_image_to_esp32, 
                        args=(frame, self.send_count)
                    )
                    thread.daemon = True
                    thread.start()
                    
                    last_send_time = current_time
                
                # Hiển thị stats
                cv2.putText(frame, f"Sent: {self.send_count} | Success: {self.success_count}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                cv2.imshow('Laptop Camera - Press Q to quit', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        except KeyboardInterrupt:
            print("\n⏹️  Dừng chương trình...")
        finally:
            self.cleanup()
    
    def send_image_to_esp32(self, frame, count):
        """Gửi ảnh đến ESP32"""
        try:
            print(f"🔄 [SEND #{count}] Processing image...")
            
            # Encode ảnh
            small_frame = cv2.resize(frame, (320, 240))
            encode_param = [cv2.IMWRITE_JPEG_QUALITY, 50]
            _, img_encoded = cv2.imencode('.jpg', small_frame, encode_param)
            image_data = img_encoded.tobytes()
            
            print(f"📦 [SEND #{count}] Image size: {len(image_data)} bytes")
            print(f"📤 [SEND #{count}] POSTing to {self.esp32_url}/upload...")
            
            start_time = time.time()
            
            response = requests.post(
                f"{self.esp32_url}/upload",
                data=image_data,
                headers={'Content-Type': 'image/jpeg'},
                timeout=10
            )
            
            elapsed = time.time() - start_time
            
            print(f"📥 [SEND #{count}] Response received in {elapsed:.2f}s")
            print(f"📥 [SEND #{count}] Status: {response.status_code}")
            print(f"📥 [SEND #{count}] Response: {response.text}")
            
            if response.status_code == 200:
                self.success_count += 1
                print(f"✅ [SEND #{count}] SUCCESS! (Total success: {self.success_count}/{self.send_count})")
                return True
            else:
                print(f"❌ [SEND #{count}] FAILED with status {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"⏱️  [SEND #{count}] TIMEOUT - ESP32 not responding")
            return False
        except requests.exceptions.ConnectionError as e:
            print(f"🔌 [SEND #{count}] CONNECTION ERROR: {e}")
            return False
        except Exception as e:
            print(f"❌ [SEND #{count}] ERROR: {type(e).__name__}: {e}")
            return False
    
    def test_connection(self):
        """Test kết nối với ESP32"""
        print("\n" + "=" * 50)
        print("🔍 TESTING CONNECTION TO ESP32")
        print("=" * 50)
        
        tests = [
            ("/test", "Simple test"),
            ("/info", "System info"),
            ("/status", "Detailed status")
        ]
        
        for endpoint, description in tests:
            print(f"\n🧪 Testing {endpoint} - {description}")
            try:
                url = f"{self.esp32_url}{endpoint}"
                print(f"   URL: {url}")
                
                response = requests.get(url, timeout=5)
                print(f"   ✅ Status: {response.status_code}")
                print(f"   📄 Response: {response.text[:200]}")
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
        
        print("\n" + "=" * 50)
        return True
    
    def cleanup(self):
        """Dọn dẹp"""
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print(f"\n📊 Statistics:")
        print(f"   Total sent: {self.send_count}")
        print(f"   Successful: {self.success_count}")
        print(f"   Failed: {self.send_count - self.success_count}")
        print("✅ Camera closed")

if __name__ == "__main__":
    ESP32_IP = "http://192.168.60.225"
    
    client = LaptopCameraClient(esp32_url=ESP32_IP, camera_index=0)
    
    # Test connection first
    if client.test_connection():
        print("\n🚀 Starting camera stream in 3 seconds...")
        time.sleep(3)
        client.start_streaming(interval=5)
    else:
        print("\n❌ Connection test failed!")