#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <WiFiClient.h>
// #include <DHT.h> // Tạm thời comment thư viện này lại vì không dùng đến

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
const unsigned long IMAGE_SEND_INTERVAL = 30000; 

#define MAX_IMAGE_SIZE 10000
uint8_t imageBuffer[MAX_IMAGE_SIZE];
size_t imageSize = 0;
bool isForwarding = false; 

// =======================
// 3. CẤU HÌNH CẢM BIẾN & RELAY (MÁY BƠM)
// =======================
unsigned long lastSensorUpdate = 0;
const unsigned long SENSOR_INTERVAL = 1000; 

// --- Relay Máy Bơm ---
#define RELAY_PIN 14          // Chân nối Relay
#define RELAY_ON HIGH         // Mức kích hoạt 
#define RELAY_OFF LOW         // Mức tắt
bool isPumpRunning = false;   // Trạng thái bơm
unsigned long pumpStartTime = 0; // Thời điểm bắt đầu bơm
const unsigned long PUMP_DURATION = 5000; // Thời gian bơm: 5000ms = 5 giây

// --- Cảm biến Mưa ---
#define RAIN_AO_PIN 2       
int RAIN_THRESHOLD = 2500;  

// --- Cảm biến Độ ẩm đất ---
#define SOIL_PIN 1          
#define SOIL_MAX 4095
#define SOIL_MIN 0

// (Đã bỏ khai báo DHT vì đang bị hư)

// =======================
// HÀM ĐỌC CẢM BIẾN
// =======================
float readSoilMoisture() {
  int raw = analogRead(SOIL_PIN);
  float moisture = map(raw, SOIL_MIN, SOIL_MAX, 100, 0); 
  if (moisture < 0) moisture = 0;
  if (moisture > 100) moisture = 100;
  return moisture;
}

String readRainStatus() {
  int aoValue = analogRead(RAIN_AO_PIN);
  return (aoValue < RAIN_THRESHOLD) ? "1" : "0";
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
      Serial.print(mqttClient.state());
      Serial.println(" try again in 5s");
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
// XỬ LÝ KẾT QUẢ AI
// =======================
void processAIResponse(String responseBody) {
  DynamicJsonDocument doc(1024);
  DeserializationError error = deserializeJson(doc, responseBody);

  if (error) {
    Serial.print(F("❌ deserializeJson() failed: "));
    Serial.println(error.f_str());
    return;
  }

  const char* result = doc["result"];
  float confidence = doc["confidence"]; 

  Serial.printf("🔍 AI Analysis -> Result: %s | Conf: %.2f\n", result, confidence);

  // LOGIC KÍCH HOẠT MÁY BƠM
  if (String(result) != "healthy") {
    if (!isPumpRunning) {
      Serial.println("⚠️ Cây bị bệnh! -> 💦 BẬT MÁY BƠM THUỐC (5s)");
      digitalWrite(RELAY_PIN, RELAY_ON);
      isPumpRunning = true;
      pumpStartTime = millis(); 
    } else {
      Serial.println("⚠️ Bơm đang chạy, bỏ qua lệnh kích hoạt lại.");
    }
  } else {
    Serial.println("✅ Cây khỏe mạnh. Không cần bơm.");
  }
}

// =======================
// GATEWAY LOGIC
// =======================
int readHeaders(WiFiClient &client, String &request) {
    request = "";
    int contentLength = 0;
    unsigned long timeout = millis();
    while (client.connected() && client.available() && millis() - timeout < 3000) {
        String line = client.readStringUntil('\n');
        line.trim();
        if (line.length() == 0) break;
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
  http.setTimeout(15000); 
  
  int code = http.POST(imageBuffer, imageSize);

  if (code > 0) {
    String responseBody = http.getString();
    Serial.printf("✅ [FWD] HTTP %d | Resp: %s\n", code, responseBody.c_str());
    
    processAIResponse(responseBody); 
    
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
  while (client.available() && imageSize < contentLength) {
    imageBuffer[imageSize++] = client.read();
  }
  size_t bytesToRead = contentLength - imageSize;
  if (bytesToRead > 0) {
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
  if (isForwarding) { delay(10); return; }
  WiFiClient client = tcpServer.available();
  if (client) {
    client.setTimeout(3000);
    Serial.println("\n📡 Client connected");
    String firstLine = client.readStringUntil('\n');
    firstLine.trim();
    if (firstLine.indexOf("POST /upload") >= 0) {
      String headers;
      int contentLength = readHeaders(client, headers);
      handleImageUpload(client, contentLength);
    } else {
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
  
  // 1. Setup Relay
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, RELAY_OFF); 

  // 2. Khởi tạo Cảm biến (Bỏ DHT)
  pinMode(SOIL_PIN, INPUT);

  // 3. Setup WiFi & MQTT
  WiFi.mode(WIFI_STA);
  setup_wifi();
  espClient.setInsecure();
  mqttClient.setServer(mqtt_server, mqtt_port);

  // 4. Setup Server
  tcpServer.begin();
  tcpServer.setNoDelay(true); 
  Serial.println("✅ System Ready (Fake Sensor Mode)");
}

// =======================
// LOOP
// =======================
void loop() {
  // Task 1: MQTT
  if (!mqttClient.connected()) reconnectMQTT();
  mqttClient.loop();

  // Task 2: Quản lý tắt bơm (Non-blocking)
  if (isPumpRunning) {
    if (millis() - pumpStartTime >= PUMP_DURATION) {
      digitalWrite(RELAY_PIN, RELAY_OFF); // Tắt bơm
      isPumpRunning = false;
      Serial.println("🛑 Đã bơm xong 5s -> TẮT BƠM");
    }
  }

  // Task 3: Đọc Cảm biến & FAKE Dữ Liệu (5 giây/lần)
  if (millis() - lastSensorUpdate > SENSOR_INTERVAL) {
    float soil = readSoilMoisture();
    String rain = readRainStatus(); 

    Serial.printf("Sensors -> Soil: %.1f%% | Rain: %s | Temp: %.1f | Hum: %.1f\n", soil, rain.c_str(), temp, humi);

    DynamicJsonDocument doc(256);
    doc["soil_moisture"] = soil;
    doc["rain"] = rain;
    doc["temperature"] = temp;
    doc["humidity"] = humi;

    char mqtt_msg[256];
    serializeJson(doc, mqtt_msg);
    publishMessage(mqtt_topic_sensor, mqtt_msg, true);

    lastSensorUpdate = millis();
  }

  // Task 4: Gateway (Camera)
  handleTCPClient();
  
  delay(10);
}