#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClient.h>

// ===================
// Cấu hình
// ===================
const char* ssid = "HT";        
const char* password = "Thien@123";
const char* aiServerUrl = "http://192.168.60.253:5000/api/upload";

WiFiServer server(80);

// Buffer 5KB
#define MAX_IMAGE_SIZE 50000
uint8_t imageBuffer[MAX_IMAGE_SIZE];
size_t imageSize = 0;

void setup() {
  Serial.begin(115200);
  delay(2000);
  
  Serial.println("\n=== ESP32 ULTRA MINIMAL ===");
  Serial.printf("Free RAM: %d bytes\n", ESP.getFreeHeap());
  
  // WiFi
  WiFi.mode(WIFI_STA);
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
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n❌ WiFi FAIL");
    ESP.restart();
  }
  
  // Start TCP server
  server.begin();
  Serial.println("✅ TCP Server started on port 80");
  Serial.println("================================\n");
}

void loop() {
  WiFiClient client = server.available();
  
  if (client) {
    Serial.println("\n📡 Client connected");
    
    String request = "";
    unsigned long timeout = millis();
    
    // Đọc request header
    while (client.connected() && millis() - timeout < 5000) {
      if (client.available()) {
        char c = client.read();
        request += c;
        
        if (request.endsWith("\r\n\r\n")) {
          break;
        }
      }
    }
    
    Serial.println("Request:");
    Serial.println(request.substring(0, 100));
    
    // Handle GET /test
    if (request.indexOf("GET /test") >= 0) {
      Serial.println("-> GET /test");
      client.println("HTTP/1.1 200 OK");
      client.println("Content-Type: text/plain");
      client.println("Connection: close");
      client.println();
      client.println("ESP32 OK!");
    }
    // Handle GET /info
    else if (request.indexOf("GET /info") >= 0) {
      Serial.println("-> GET /info");
      client.println("HTTP/1.1 200 OK");
      client.println("Content-Type: application/json");
      client.println("Connection: close");
      client.println();
      client.print("{\"status\":\"ok\",\"ram\":");
      client.print(ESP.getFreeHeap());
      client.println("}");
    }
    // Handle POST /upload
    else if (request.indexOf("POST /upload") >= 0) {
      Serial.println("-> POST /upload");
      
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
          timeout = millis();
          
          while (imageSize < contentLength && millis() - timeout < 10000) {
            if (client.available()) {
              imageBuffer[imageSize++] = client.read();
              timeout = millis();
            }
          }
          
          Serial.printf("Received: %d bytes\n", imageSize);
          
          // Response
          client.println("HTTP/1.1 200 OK");
          client.println("Content-Type: application/json");
          client.println("Connection: close");
          client.println();
          client.println("{\"status\":\"ok\"}");
          
          client.stop();
          
          // Forward
          delay(100);
          forwardToAI();
        } else {
          client.println("HTTP/1.1 400 Bad Request");
          client.println("Connection: close");
          client.println();
        }
      }
    }
    else {
      // 404
      client.println("HTTP/1.1 404 Not Found");
      client.println("Connection: close");
      client.println();
    }
    
    delay(10);
    client.stop();
    Serial.println("Client closed");
  }
  
  delay(1);
}

// ===================
// Forward
// ===================
void forwardToAI() {
  if(imageSize == 0) return;
  
  Serial.println("\n[FWD] Start");
  Serial.printf("[FWD] Size: %d\n", imageSize);
  
  if(WiFi.status() != WL_CONNECTED) {
    Serial.println("[FWD] No WiFi");
    return;
  }
  
  HTTPClient http;
  WiFiClient client;
  
  if(!http.begin(client, aiServerUrl)) {
    Serial.println("[FWD] Begin failed");
    return;
  }
  
  http.addHeader("Content-Type", "image/jpeg");
  http.setTimeout(10000);
  
  Serial.println("[FWD] Sending...");
  int code = http.POST(imageBuffer, imageSize);
  
  if (code > 0) {
    Serial.printf("[FWD] HTTP %d\n", code);
    String resp = http.getString();
    Serial.println(resp);
  } else {
    Serial.printf("[FWD] Error %d\n", code);
  }
  
  http.end();
  imageSize = 0;
  Serial.printf("[FWD] RAM: %d\n", ESP.getFreeHeap());
}