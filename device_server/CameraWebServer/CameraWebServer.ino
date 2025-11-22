#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClient.h>

// ===================
// Cấu hình
// ===================
const char* ssid = "HT";        
const char* password = "Thien@123";
const char* aiServerUrl = "http://server-alb-645944439.us-east-1.elb.amazonaws.com/inference";

WiFiServer server(80);

// Buffer 10KB 
#define MAX_IMAGE_SIZE 10000
uint8_t imageBuffer[MAX_IMAGE_SIZE];
size_t imageSize = 0;

// Biến để quản lý kết nối
bool isForwarding = false;
unsigned long lastForwardTime = 0;

void setup() {
  Serial.begin(115200);
  delay(3000);  // Tăng delay khởi động
  
  Serial.println("\n=== ESP32 AI GATEWAY STABLE ===");
  Serial.printf("Free RAM: %d bytes\n", ESP.getFreeHeap());
  
  // WiFi
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false); // Tắt chế độ sleep để ổn định hơn
  WiFi.begin(ssid, password);
  Serial.print("WiFi");
  
  int tries = 0;
  while (WiFi.status() != WL_CONNECTED && tries < 30) {
    delay(500);
    Serial.print(".");
    tries++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi OK");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n❌ WiFi FAIL");
    delay(2000);
    ESP.restart();
  }
  
  // Start TCP server
  server.begin();
  server.setNoDelay(true); // Tắt Nagle algorithm
  Serial.println("✅ TCP Server started on port 80");
  Serial.println("================================\n");
}

void loop() {
  // Chống quá tải - chỉ xử lý 1 request mỗi 2 giây
  if (isForwarding && millis() - lastForwardTime < 2000) {
    delay(100);
    return;
  }
  
  WiFiClient client = server.available();
  
  if (client) {
    client.setTimeout(1000); // Giảm timeout
    Serial.println("\n📡 Client connected");
    
    String request = "";
    unsigned long timeout = millis();
    
    // Đọc request header
    while (client.connected() && millis() - timeout < 3000) {
      if (client.available()) {
        char c = client.read();
        request += c;
        
        if (request.endsWith("\r\n\r\n")) {
          break;
        }
      }
    }
    
    Serial.println("Request received");
    
    // Handle GET /test
    if (request.indexOf("GET /test") >= 0) {
      Serial.println("-> GET /test");
      sendResponse(client, "HTTP/1.1 200 OK", "text/plain", "ESP32 OK!");
    }
    // Handle GET /info
    else if (request.indexOf("GET /info") >= 0) {
      Serial.println("-> GET /info");
      String json = "{\"status\":\"ok\",\"ram\":" + String(ESP.getFreeHeap()) + "}";
      sendResponse(client, "HTTP/1.1 200 OK", "application/json", json);
    }
    // Handle POST /upload
    else if (request.indexOf("POST /upload") >= 0) {
      Serial.println("-> POST /upload");
      handleImageUpload(client, request);
    }
    else {
      // 404
      sendResponse(client, "HTTP/1.1 404 Not Found", "text/plain", "Not Found");
    }
    
    delay(50);
    client.stop();
    Serial.println("Client closed");
  }
  
  delay(10);
}

void sendResponse(WiFiClient &client, String status, String contentType, String body) {
  client.println(status);
  client.println("Content-Type: " + contentType);
  client.println("Connection: close");
  client.println();
  client.println(body);
}

void handleImageUpload(WiFiClient &client, String &request) {
  // Tìm Content-Length
  int lengthIndex = request.indexOf("Content-Length: ");
  if (lengthIndex >= 0) {
    int lengthStart = lengthIndex + 16;
    int lengthEnd = request.indexOf("\r", lengthStart);
    String lengthStr = request.substring(lengthStart, lengthEnd);
    int contentLength = lengthStr.toInt();
    
    Serial.printf("Content-Length: %d\n", contentLength);
    
    if (contentLength > 0 && contentLength <= MAX_IMAGE_SIZE) {
      // Đọc body
      imageSize = 0;
      unsigned long timeout = millis();
      
      while (imageSize < contentLength && millis() - timeout < 8000) {
        if (client.available()) {
          imageBuffer[imageSize++] = client.read();
          timeout = millis();
        }
        delay(1);
      }
      
      Serial.printf("✅ Received: %d bytes\n", imageSize);
      
      // Gửi response ngay lập tức
      sendResponse(client, "HTTP/1.1 200 OK", "application/json", "{\"status\":\"received\"}");
      client.stop();
      
      // Xử lý forward sau (không block client)
      if (imageSize > 0) {
        forwardToAI();
      }
      
    } else {
      sendResponse(client, "HTTP/1.1 400 Bad Request", "text/plain", "Image too large");
    }
  } else {
    sendResponse(client, "HTTP/1.1 400 Bad Request", "text/plain", "No Content-Length");
  }
}

// ===================
// Forward với Error Handling tốt hơn
// ===================
void forwardToAI() {
  if (imageSize == 0) return;
  
  // Chống gọi đồng thời
  if (isForwarding) {
    Serial.println("⚠️  Already forwarding, skipping...");
    return;
  }
  
  isForwarding = true;
  lastForwardTime = millis();
  
  Serial.println("\n[FWD] Starting forward to AI server");
  Serial.printf("[FWD] Image size: %d bytes\n", imageSize);
  
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("❌ [FWD] WiFi disconnected");
    isForwarding = false;
    return;
  }
  
  // Sử dụng local variables để tránh conflict
  size_t currentImageSize = imageSize;
  uint8_t* currentImageBuffer = imageBuffer;
  
  HTTPClient http;
  
  // Sử dụng begin với string thay vì WiFiClient để đơn giản hóa
  http.begin(String(aiServerUrl));
  http.addHeader("Content-Type", "image/jpeg");
  http.setTimeout(15000);
  http.setReuse(false); // Quan trọng: không reuse connection
  
  Serial.println("[FWD] Sending to AI server...");
  
  int code = http.POST(currentImageBuffer, currentImageSize);
  
  if (code > 0) {
    Serial.printf("✅ [FWD] HTTP %d\n", code);
    String response = http.getString();
    Serial.println("🤖 AI Response: " + response);
  } else {
    Serial.printf("❌ [FWD] Error %d: %s\n", code, http.errorToString(code).c_str());
  }
  
  // Cleanup triệt để
  http.end();
  delay(100); // Đảm bảo cleanup hoàn tất
  
  // Reset buffer
  imageSize = 0;
  isForwarding = false;
  
  Serial.printf("[FWD] Complete. Free RAM: %d bytes\n\n", ESP.getFreeHeap());
}