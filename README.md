# Gardenice-IoT 🌿

**Hệ thống Internet of Things (IoT) quản lý vườn thông minh (Smart Garden)**

## 📘 Giới thiệu / Overview

**Gardenice-IoT** là một dự án giải pháp công nghệ nhằm tự động hóa, giám sát và điều khiển mô hình "vườn thông minh". Hệ thống kết hợp các thiết bị IoT, bộ điều khiển và máy chủ để theo dõi môi trường, tưới cây tự động, thu thập dữ liệu và hỗ trợ điều khiển từ xa.

**Mục tiêu của dự án:**

* Giám sát các thông số môi trường: độ ẩm đất, ánh sáng, nhiệt độ...
* Điều khiển tưới nước và các chế độ chăm sóc cây tự động.
* Xây dựng kiến trúc Client-Server linh hoạt, dễ dàng mở rộng số lượng thiết bị và quy mô vườn.
* (Tương lai) Tích hợp giao diện Web/Mobile App và phân tích dữ liệu.


## 🎯 Tính năng chính / Key Features

* **Giám sát môi trường thời gian thực:** Thu thập dữ liệu từ cảm biến (độ ẩm, nhiệt độ, ánh sáng).
* **Kết nối Client-Server:** Gửi dữ liệu từ thiết bị IoT (Client) về Server (Local hoặc Cloud) để lưu trữ và phân tích.
* **Điều khiển từ xa:** Cơ chế gửi lệnh từ Server xuống thiết bị (ví dụ: kích hoạt máy bơm, bật đèn, bật quạt...).
* **Khả năng mở rộng:** Thiết kế hỗ trợ nhiều thiết bị (nodes) và nhiều khu vực vườn khác nhau.
* **Linh hoạt trong triển khai:** Hỗ trợ chạy trên server cá nhân (Local), Docker hoặc triển khai lên đám mây (AWS, Cloud VPS).


## 🛠️ Cấu trúc dự án / Project Structure

Dự án được chia thành các module chính như sau:

```text
Gardenice-IoT/
├── aws/                # (Optional) Infrastructure as Code, cấu hình deploy AWS
├── cloud_server/       # Backend Server: API, xử lý logic, lưu trữ dữ liệu
├── device_server/      # Code chạy trên thiết bị IoT (ESP32, Arduino, Raspberry Pi...)
├── .gitignore
└── README.md

```

### Chi tiết chức năng (Module Details)

* **`device_server/`**: Chứa mã nguồn cho các thiết bị nhúng/vi điều khiển.
    * *Nhiệm vụ:* Đọc cảm biến, gửi dữ liệu, nhận lệnh điều khiển.
* **`cloud_server/`**: Chứa mã nguồn Backend.
    * *Nhiệm vụ:* Cung cấp API, lưu trữ database, điều phối lệnh cho thiết bị.
* **`aws/`** *(Tùy chọn)*: Chứa các script hoặc file cấu hình (Terraform/CloudFormation).
    * *Nhiệm vụ:* Hỗ trợ deploy server/database lên Amazon Web Services.

---

### 📦 Yêu cầu hệ thống / Prerequisites

Trước khi bắt đầu, hãy đảm bảo bạn đã chuẩn bị đầy đủ các thành phần sau:

**Phần cứng:**
* **Board mạch:** Thiết bị hỗ trợ IoT (ESP32, ESP8266, Raspberry Pi...).
* **Module:** Các cảm biến (nhiệt độ, độ ẩm đất, ánh sáng...) và cơ cấu chấp hành (relay, máy bơm...).

**Phần mềm & Môi trường:**
* **Device:** Python (MicroPython) hoặc C/C++ (Arduino IDE/PlatformIO) tùy thuộc vào mã nguồn trong `device_server`.
* **Server:** Môi trường chạy backend (Python, Node.js, hoặc Docker).
* **Kiến thức nền:** Hiểu biết cơ bản về giao thức mạng (HTTP/MQTT/WebSocket).
* **(Optional):** Tài khoản AWS và cấu hình IAM nếu sử dụng thư mục `aws/`.

---

## 🚀 Cài đặt & Chạy thử / Getting Started

### 1. Clone Repository
Tải mã nguồn về máy tính của bạn:
```bash
git clone [https://github.com/kPhuong08/Gardenice-IoT.git](https://github.com/kPhuong08/Gardenice-IoT.git)
cd Gardenice-IoT
```

### 2. Cài đặt Server Backend
Truy cập thư mục server và cài đặt các thư viện cần thiết:
```bash
cd cloud_server
```
#### Ví dụ nếu dùng Python/Pip
```bash
pip install -r requirements.txt
```
#### Hoặc nếu dùng Node.js
```bash
npm install
```

Cấu hình các biến môi trường (Database URL, Port, API Keys...) trong file .env hoặc file config tương ứng.

#### Khởi động server:
```bash
python server.py
```

### 3. Cài đặt thiết bị IoT (Device)
* Truy cập thư mục device_server.

* Mở code bằng IDE phù hợp (Arduino IDE, VS Code + PlatformIO, Thonny...).

* Cài đặt các thư viện driver cho cảm biến.

* Quan trọng: Cấu hình thông tin kết nối trong code (Wifi SSID/Pass, Server Endpoint/IP, API Token).

* Nạp code (Upload) vào thiết bị.

### 4. Kiểm thử kết nối
* Bật thiết bị IoT và quan sát Serial Monitor.

* Kiểm tra log tại cloud_server xem dữ liệu đã được nhận hay chưa.

* Thử gửi lệnh từ server xuống thiết bị để kiểm tra phản hồi.

## 💡 Cách sử dụng / Usage

1.  **Thu thập dữ liệu:** Khi khởi động, thiết bị sẽ định kỳ đọc cảm biến và gửi gói tin về Server.
2.  **Quản lý:** Dữ liệu được lưu tại Database của Server.
3.  **Mở rộng:**
    * Bạn có thể xây dựng thêm **Frontend (Web/Mobile App)** gọi vào API của `cloud_server` để hiển thị Dashboard.
    * Thiết lập các rule tự động: *Nếu độ ẩm < 30% thì Server gửi lệnh Bật Bơm*.
