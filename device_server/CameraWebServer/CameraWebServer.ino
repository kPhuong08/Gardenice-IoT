#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <WiFiClient.h>

// =======================
// Cấu hình WiFi
// =======================
const char* ssid = "HT";
const char* password = "Thien@123";

unsigned long lastImageSend = 0;
const unsigned long IMAGE_SEND_INTERVAL = 30000; // 30 giây

// =======================
// Cấu hình MQTT
// =======================
const char* mqtt_server = "3a28ae8aa3b449dba0a906bd966f1576.s1.eu.hivemq.cloud";
const int mqtt_port = 8883;
const char* mqtt_username = "lethien";
const char* mqtt_password = "Thien@123";

// =======================
// Cấu hình AI Server
// =======================
const char* aiServerUrl = "http://server-alb-645944439.us-east-1.elb.amazonaws.com/inference";

// =======================
// Biến toàn cục
// =======================
WiFiClientSecure espClient;
PubSubClient mqttClient(espClient);
WiFiServer tcpServer(80);

unsigned long lastSoilUpdate = 0;

// Cấu hình cảm biến độ ẩm đất
#define SOIL_PIN 1
#define SOIL_MAX 4095
#define SOIL_MIN 0

// Buffer cho ảnh
#define MAX_IMAGE_SIZE 10000
uint8_t imageBuffer[MAX_IMAGE_SIZE];
size_t imageSize = 0;
bool isForwarding = false;
unsigned long lastForwardTime = 0;

// =======================
// Hàm đọc độ ẩm đất
// =======================
float readSoilMoisture() {
  int raw = analogRead(SOIL_PIN);
  Serial.print("Raw ADC: ");
  Serial.println(raw);

  float moisture = map(raw, SOIL_MIN, SOIL_MAX, 0, 100);
  if (moisture < 0) moisture = 0;
  if (moisture > 100) moisture = 100;
  return moisture;
}

// =======================
// WiFi Setup
// =======================
void setup_wifi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
  Serial.println("IP Address: " + WiFi.localIP().toString());
}

// =======================
// MQTT Functions
// =======================
void reconnectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Connecting to MQTT...");
    String clientID = "ESP32S3-" + String(random(0xffff), HEX);
    if (mqttClient.connect(clientID.c_str(), mqtt_username, mqtt_password)) {
      Serial.println("connected!");
    } else {
      Serial.print("Failed, rc=");
      Serial.println(mqttClient.state());
      delay(5000);
    }
  }
}

void publishMessage(const char* topic, String payload, bool retained) {
  if (mqttClient.publish(topic, payload.c_str(), retained)) {
    Serial.println("Published: " + payload);
  }
}

// =======================
// AI Gateway Functions
// =======================
void sendResponse(WiFiClient &client, String status, String contentType, String body) {
  client.println(status);
  client.println("Content-Type: " + contentType);
  client.println("Connection: close");
  client.println();
  client.println(body);
}

void handleImageUpload(WiFiClient &client, String &request) {
  int lengthIndex = request.indexOf("Content-Length: ");
  if (lengthIndex >= 0) {
    int lengthStart = lengthIndex + 16;
    int lengthEnd = request.indexOf("\r", lengthStart);
    String lengthStr = request.substring(lengthStart, lengthEnd);
    int contentLength = lengthStr.toInt();
    
    Serial.printf("Content-Length: %d\n", contentLength);
    
    if (contentLength > 0 && contentLength <= MAX_IMAGE_SIZE) {
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
      
      sendResponse(client, "HTTP/1.1 200 OK", "application/json", "{\"status\":\"received\"}");
      client.stop();
      
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

void forwardToAI() {
  if (imageSize == 0) return;

  if (isForwarding) {
    Serial.println("⚠️  Already forwarding, skipping...");
    return;
  }

  // --- Giới hạn 30 giây gửi 1 lần ---
  if (millis() - lastImageSend < IMAGE_SEND_INTERVAL) {
    Serial.println("⏳ Chưa đủ 30 giây => Không gửi ảnh");
    isForwarding = false;
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

  size_t currentImageSize = imageSize;
  uint8_t* currentImageBuffer = imageBuffer;

  HTTPClient http;
  http.begin(String(aiServerUrl));
  http.addHeader("Content-Type", "image/jpeg");
  http.setTimeout(15000);
  http.setReuse(false);

  Serial.println("[FWD] Sending to AI server...");

  int code = http.POST(currentImageBuffer, currentImageSize);

  if (code > 0) {
    Serial.printf("✅ [FWD] HTTP %d\n", code);
    String response = http.getString();
    Serial.println("🤖 AI Response: " + response);

    // Cập nhật lần gửi cuối
    lastImageSend = millis();

  } else {
    Serial.printf("❌ [FWD] Error %d: %s\n", code, http.errorToString(code).c_str());
  }

  http.end();
  delay(100);

  imageSize = 0;
  isForwarding = false;

  Serial.printf("[FWD] Complete. Free RAM: %d bytes\n\n", ESP.getFreeHeap());
}

void handleTCPClient() {
  if (isForwarding && millis() - lastForwardTime < 2000) {
    delay(100);
    return;
  }
  
  WiFiClient client = tcpServer.available();
  
  if (client) {
    client.setTimeout(1000);
    Serial.println("\n📡 Client connected");
    
    String request = "";
    unsigned long timeout = millis();
    
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
    
    if (request.indexOf("GET /test") >= 0) {
      Serial.println("-> GET /test");
      sendResponse(client, "HTTP/1.1 200 OK", "text/plain", "ESP32 OK!");
    }
    else if (request.indexOf("GET /info") >= 0) {
      Serial.println("-> GET /info");
      String json = "{\"status\":\"ok\",\"ram\":" + String(ESP.getFreeHeap()) + "}";
      sendResponse(client, "HTTP/1.1 200 OK", "application/json", json);
    }
    else if (request.indexOf("POST /upload") >= 0) {
      Serial.println("-> POST /upload");
      handleImageUpload(client, request);
    }
    else {
      sendResponse(client, "HTTP/1.1 404 Not Found", "text/plain", "Not Found");
    }
    
    delay(50);
    client.stop();
    Serial.println("Client closed");
  }
}

// =======================
// Setup + Loop
// =======================
void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n=== ESP32-S3 COMBINED GATEWAY ===");
  Serial.printf("Free RAM: %d bytes\n", ESP.getFreeHeap());

  pinMode(SOIL_PIN, INPUT);

  // Setup WiFi
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  setup_wifi();

  // Setup MQTT
  espClient.setInsecure();
  mqttClient.setServer(mqtt_server, mqtt_port);

  // Setup TCP Server
  tcpServer.begin();
  tcpServer.setNoDelay(true);
  Serial.println("✅ TCP Server started on port 80");
  Serial.println("✅ MQTT Client initialized");
  Serial.println("================================\n");
}

void loop() {
  // Xử lý MQTT
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  mqttClient.loop();

  // Gửi dữ liệu độ ẩm đất mỗi 5 giây
  if (millis() - lastSoilUpdate > 10000) {
    float soil = readSoilMoisture();
    Serial.printf("Soil Moisture: %.2f %%\n", soil);

    DynamicJsonDocument doc(256);
    doc["soil_moisture"] = soil;

    char mqtt_msg[128];
    serializeJson(doc, mqtt_msg);

    publishMessage("esp32s3/soil", mqtt_msg, true);

    lastSoilUpdate = millis();
  }

  // Xử lý TCP client (AI Gateway)
  handleTCPClient();

  delay(10);
}