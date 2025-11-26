#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <WiFiClient.h>
#include <Wire.h>
#include <BH1750.h>

// =======================
// 1. CẤU HÌNH WIFI & MQTT
// =======================
const char* ssid = "HT";
const char* password = "Thien@123";

const char* mqtt_server = "3a28ae8aa3b449dba0a906bd966f1576.s1.eu.hivemq.cloud";
const int mqtt_port = 8883;
const char* mqtt_username = "lethien";
const char* mqtt_password = "Thien@123";
const char* mqtt_topic_sensor = "esp32s3/sensors"; 

// =======================
// 2. CẤU HÌNH AI SERVER & GATEWAY
// =======================
const char* aiServerUrl = "http://54.87.95.47:5000/inference";

WiFiClientSecure espClient;
PubSubClient mqttClient(espClient);
WiFiServer tcpServer(80);

unsigned long lastImageSend = 0;
// Giới hạn gửi ảnh 30s/lần để tránh spam server
const unsigned long IMAGE_SEND_INTERVAL = 30000; 

#define MAX_IMAGE_SIZE 10000
uint8_t imageBuffer[MAX_IMAGE_SIZE];
size_t imageSize = 0;
bool isForwarding = false; 

// =======================
// 3. CẤU HÌNH CẢM BIẾN
// =======================
unsigned long lastSensorUpdate = 0;
const unsigned long SENSOR_INTERVAL = 5000; // 5 giây cập nhật 1 lần

// --- Cảm biến Mưa ---
#define RAIN_AO_PIN 2       
int RAIN_THRESHOLD = 2500;  

// --- Cảm biến Độ ẩm đất ---
#define SOIL_PIN 1          
#define SOIL_MAX 4095
#define SOIL_MIN 0

// --- Cảm biến Ánh sáng (BH1750) ---
// SDA = 7, SCL = 8 (Cấu hình trong setup)
BH1750 lightMeter;

// =======================
// HÀM ĐỌC CẢM BIẾN
// =======================

// 1. Đọc độ ẩm đất (Logic: Giá trị thấp = Ẩm ướt)
float readSoilMoisture() {
  int raw = analogRead(SOIL_PIN);
  // Map: raw=0 -> 100%, raw=4095 -> 0%
  float moisture = map(raw, SOIL_MIN, SOIL_MAX, 100, 0); 
  
  if (moisture < 0) moisture = 0;
  if (moisture > 100) moisture = 100;
  return moisture;
}

// 2. Đọc trạng thái mưa
String readRainStatus() {
  int aoValue = analogRead(RAIN_AO_PIN);
  if (aoValue < RAIN_THRESHOLD) {
    return "rain"; 
  } else {
    return "dry"; 
  }
}

// 3. Đọc ánh sáng BH1750
float readLightLevel() {
  if (lightMeter.measurementReady()) {
    return lightMeter.readLightLevel();
  }
  return 0.0;
}

// =======================
// KẾT NỐI WIFI & MQTT
// =======================
void setup_wifi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected: " + WiFi.localIP().toString());
}

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
    Serial.println("MQTT Sent: " + payload);
  }
}

// =======================
// GATEWAY LOGIC (TỐI ƯU HÓA)
// =======================

// Hàm đọc Header để tách lấy Content-Length
int readHeaders(WiFiClient &client, String &request) {
    request = "";
    int contentLength = 0;
    unsigned long timeout = millis();
    
    while (client.connected() && client.available() && millis() - timeout < 3000) {
        String line = client.readStringUntil('\n');
        line.trim();

        if (line.length() == 0) {
            break; // Kết thúc header
        }

        if (line.startsWith("Content-Length: ")) {
            contentLength = line.substring(16).toInt();
        }
        
        request += line + "\n";
    }
    return contentLength;
}

void sendResponse(WiFiClient &client, String status, String contentType, String body) {
  client.println(status);
  client.println("Content-Type: " + contentType);
  client.println("Connection: close");
  client.println();
  client.println(body);
}

void forwardToAI() {
  if (imageSize == 0) return;

  // Giới hạn 30 giây gửi 1 lần
  if (millis() - lastImageSend < IMAGE_SEND_INTERVAL) {
    Serial.println("⏳ [FWD] Chưa đủ 30 giây => Bỏ qua");
    return;
  }
  
  if (isForwarding) return;

  isForwarding = true;
  Serial.println("\n[FWD] Forwarding to AI server...");

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("❌ [FWD] WiFi disconnected");
    isForwarding = false;
    return;
  }

  HTTPClient http;
  http.begin(String(aiServerUrl));
  http.addHeader("Content-Type", "image/jpeg");
  http.setTimeout(15000); // 15 giây timeout
  
  size_t currentImageSize = imageSize;
  int code = http.POST(imageBuffer, currentImageSize);

  if (code > 0) {
    Serial.printf("✅ [FWD] HTTP %d | Resp: %s\n", code, http.getString().c_str());
    lastImageSend = millis();
  } else {
    Serial.printf("❌ [FWD] Error %d: %s\n", code, http.errorToString(code).c_str());
  }

  http.end();
  imageSize = 0;
  isForwarding = false;
  Serial.printf("[FWD] Done. Free Heap: %d\n", ESP.getFreeHeap());
}

void handleImageUpload(WiFiClient &client, int contentLength) {
  if (contentLength <= 0 || contentLength > MAX_IMAGE_SIZE) {
    Serial.printf("❌ Content-Length invalid: %d\n", contentLength);
    sendResponse(client, "HTTP/1.1 400 Bad Request", "text/plain", "Invalid Size");
    return;
  }
  
  Serial.printf("Content-Length: %d. Reading body...\n", contentLength);
  imageSize = 0;
  
  // 1. Đọc dữ liệu có sẵn trong buffer
  while (client.available() && imageSize < contentLength) {
    imageBuffer[imageSize++] = client.read();
  }
  
  // 2. Đọc phần còn lại (chờ mạng)
  size_t bytesToRead = contentLength - imageSize;
  if (bytesToRead > 0) {
     // Dùng readBytes có timeout tích hợp
     size_t actualRead = client.readBytes(&imageBuffer[imageSize], bytesToRead);
     imageSize += actualRead;
  }
  
  Serial.printf("✅ Received: %d bytes\n", imageSize);
  
  sendResponse(client, "HTTP/1.1 200 OK", "application/json", "{\"status\":\"received\"}");
  client.stop();
  
  if (imageSize == contentLength) {
    forwardToAI();
  } else {
    Serial.println("❌ Error: Incomplete Data");
  }
}

void handleTCPClient() {
  if (isForwarding) {
    delay(10);
    return;
  }
  
  WiFiClient client = tcpServer.available();
  if (client) {
    client.setTimeout(3000);
    Serial.println("\n📡 Client connected");
    
    // Đọc dòng đầu tiên (Request Line)
    String firstLine = client.readStringUntil('\n');
    firstLine.trim();

    if (firstLine.indexOf("POST /upload") >= 0) {
      String headers;
      // Hàm readHeaders giúp nhảy qua phần header để đến body
      int contentLength = readHeaders(client, headers);
      handleImageUpload(client, contentLength);
    }
    else {
      // Các request khác (GET /test, etc.)
      client.flush();
      sendResponse(client, "HTTP/1.1 200 OK", "text/plain", "Gateway Ready");
      client.stop();
    }
    
    Serial.println("Client closed");
  }
}

// =======================
// SETUP
// =======================
void setup() {
  Serial.begin(115200);
  
  // 1. Setup I2C cho BH1750 (SDA=7, SCL=8)
  Wire.begin(7, 8); 

  if (lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE)) {
    Serial.println(F("✅ BH1750 initialized (SDA=7, SCL=8)"));
  } else {
    Serial.println(F("❌ BH1750 Error"));
  }

  // 2. Setup GPIO
  pinMode(SOIL_PIN, INPUT);

  // 3. Setup WiFi
  WiFi.mode(WIFI_STA);
  setup_wifi();

  // 4. Setup MQTT
  espClient.setInsecure();
  mqttClient.setServer(mqtt_server, mqtt_port);

  // 5. Setup Server
  tcpServer.begin();
  tcpServer.setNoDelay(true); // Tăng tốc độ phản hồi TCP
  Serial.println("✅ System Ready");
}

// =======================
// LOOP
// =======================
void loop() {
  // Task 1: MQTT
  if (!mqttClient.connected()) reconnectMQTT();
  mqttClient.loop();

  // Task 2: Đọc Cảm biến (5 giây/lần)
  if (millis() - lastSensorUpdate > SENSOR_INTERVAL) {
    float soil = readSoilMoisture();
    String rain = readRainStatus(); 
    float lux = readLightLevel();

    Serial.printf("Sensors -> Soil: %.1f%% | Rain: %s | Light: %.1f lx\n", soil, rain.c_str(), lux);

    // JSON đầy đủ
    DynamicJsonDocument doc(256);
    doc["soil_moisture"] = soil;
    doc["rain"] = rain;
    doc["light_level"] = lux;

    char mqtt_msg[256];
    serializeJson(doc, mqtt_msg);
    publishMessage(mqtt_topic_sensor, mqtt_msg, true);

    lastSensorUpdate = millis();
  }

  // Task 3: Gateway (Camera)
  handleTCPClient();
  
  delay(10);
}