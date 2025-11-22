#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h> // <-- 1. THÊM THƯ VIỆN

// ===================
// Select camera model
// ===================
#define CAMERA_MODEL_ESP32S3_EYE 


#include "camera_pins.h"

// ===========================
// === 3. CẬP NHẬT THÔNG TIN WIFI VÀ SERVER ===
// ===========================
// const char* ssid = "B5-901";         
// const char* password = "123456Aa@"; 

const char* ssid = "Redmi Note 13 Pro";        
const char* password = "12341234";

// Địa chỉ server AI của bạn
const char* serverUrl = "http://3.91.53.20:5000/inference";

// Biến để theo dõi thời gian upload
unsigned long lastUploadTime = 0;
const long uploadInterval = 30000; // Gửi ảnh mỗi 3 giây

void startCameraServer();

// ===================================
// === 4. THÊM HÀM MỚI ĐỂ GỬI ẢNH ===
// ===================================
void uploadImage() {
  Serial.println("\nTaking picture...");
  
  // 1. Chụp ảnh
  camera_fb_t * fb = NULL;
  fb = esp_camera_fb_get(); 
  if(!fb) {
    Serial.println("✗ Camera capture FAILED");
    return;
  }
  
  Serial.printf("✓ Picture taken! Size: %zu bytes\n", fb->len);

  // 2. Chuẩn bị gửi HTTP POST
  HTTPClient http;
  http.begin(serverUrl);
  
  // 3. Đặt header
  http.addHeader("Content-Type", "image/jpeg");
  
  // 4. Gửi request
  Serial.println("Uploading image via HTTP POST...");
  int httpResponseCode = http.POST(fb->buf, fb->len);

  // 5. Kiểm tra kết quả
  if(httpResponseCode > 0) {
    Serial.printf("✓ HTTP Response: %d\n", httpResponseCode);
    String responseBody = http.getString();
    Serial.println("Server response:");
    Serial.println(responseBody);
  } else {
    Serial.printf("✗ HTTP POST FAILED! Error: %s\n", http.errorToString(httpResponseCode).c_str());
  }

  // 6. Dọn dẹp
  http.end();
  esp_camera_fb_return(fb); // Quan trọng: Trả lại buffer
}


void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  delay(2000); 
  
  Serial.println("\n\n");
  Serial.println("================================");
  Serial.println("   ESP32-S3 CAM Starting...     ");
  Serial.println("================================");
  
  // Kiểm tra PSRAM
  if(psramFound()){
    Serial.println("✓ PSRAM found!");
    Serial.printf("  PSRAM size: %d bytes\n", ESP.getPsramSize());
  } else {
    Serial.println("✗ PSRAM not found!");
  }
  
  Serial.println("\nInitializing camera...");
  
  // (Phần cấu hình camera giữ nguyên... không thay đổi)
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.frame_size = FRAMESIZE_UXGA;
  config.pixel_format = PIXFORMAT_JPEG;
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = 12;
  config.fb_count = 1;

  if(psramFound()){
    config.jpeg_quality = 10;
    config.fb_count = 2;
    config.grab_mode = CAMERA_GRAB_LATEST;
    Serial.println("Camera config: UXGA + PSRAM");
  } else {
    config.frame_size = FRAMESIZE_SVGA;
    config.fb_location = CAMERA_FB_IN_DRAM;
    Serial.println("Camera config: SVGA (no PSRAM)");
  }

  // Camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("✗ Camera init FAILED! Error: 0x%x\n", err);
    Serial.println("Please check camera connection and restart!");
    while(1) {
      delay(1000);
      Serial.println("Camera init failed...");
    }
  }
  Serial.println("✓ Camera initialized successfully!");

  // Get camera sensor and adjust settings
  sensor_t * s = esp_camera_sensor_get();
  if(s != NULL) {
    s->set_vflip(s, 0);
    s->set_brightness(s, 1);
    s->set_saturation(s, 0);
    Serial.println("✓ Camera sensor settings applied");
  } else {
    Serial.println("✗ Failed to get camera sensor");
  }

  // === 5. THAY ĐỔI: KẾT NỐI WIFI (STA MODE) ===
  Serial.println("\n--- Connecting to WiFi (STA Mode) ---");
  Serial.printf("SSID: %s\n", ssid);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  Serial.print("Connecting");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✓ WiFi connected!");
  
  IPAddress IP = WiFi.localIP(); // Lấy IP từ router
  Serial.println("\n================================");
  Serial.println("  WiFi STA Information");
  Serial.println("================================");
  Serial.print("IP address: ");
  Serial.println(IP);
  Serial.println("================================");

  // Start camera web server (vẫn giữ để bạn xem stream nếu muốn)
  Serial.println("\nStarting camera web server...");
  startCameraServer();
  Serial.println("✓ Camera web server started!");

  Serial.println("\n================================");
  Serial.println("      SETUP COMPLETE!");
  Serial.println("================================");
  Serial.print("Web Stream open at: http://");
  Serial.println(IP);
  Serial.println("Auto-upload to server is RUNNING!");
  Serial.println("================================\n");
}

// ===================================
// === 6. THAY ĐỔI: SỬA HÀM LOOP() ===
// ===================================
void loop() {
  unsigned long now = millis();
  
  // Kiểm tra xem đã đến lúc gửi ảnh
  if (now - lastUploadTime >= uploadInterval) {
    lastUploadTime = now;
    
    // Đảm bảo đã kết nối WiFi trước khi gửi
    if(WiFi.status() == WL_CONNECTED) {
      uploadImage();
    } else {
      Serial.println("✗ WiFi disconnected. Skipping upload.");
    }
  }
  
  delay(100);
}