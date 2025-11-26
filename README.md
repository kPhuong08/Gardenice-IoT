# Gardenice-IoT 🌿

**Hệ thống Internet of Things (IoT) quản lý vườn thông minh**

## 📘 Giới thiệu / Overview

**Gardenice-IoT** là dự án giải pháp công nghệ nhằm tự động hóa, giám sát và điều khiển mô hình "vườn thông minh" (smart garden). Hệ thống kết hợp các thiết bị IoT, bộ điều khiển và máy chủ để theo dõi môi trường, tưới cây tự động, thu thập dữ liệu và hỗ trợ điều khiển từ xa.

**Mục tiêu của dự án:**

* Giám sát các thông số môi trường: độ ẩm đất, ánh sáng, nhiệt độ...
* Điều khiển tưới nước và các chế độ chăm sóc cây tự động.
* Xây dựng kiến trúc Client-Server linh hoạt, dễ dàng mở rộng số lượng thiết bị và quy mô vườn.

---

## 🎯 Tính năng chính / Key Features

* **Giám sát môi trường thời gian thực:** Thu thập dữ liệu từ cảm biến (độ ẩm, nhiệt độ, ánh sáng).
* **Kết nối Client-Server:** Gửi dữ liệu từ thiết bị IoT (Client) về Server (Local hoặc Cloud) để lưu trữ và phân tích.
* **Điều khiển từ xa:** Cơ chế gửi lệnh từ Server xuống thiết bị (ví dụ: kích hoạt máy bơm, bật đèn, bật quạt...).
* **Khả năng mở rộng:** Thiết kế hỗ trợ nhiều thiết bị (nodes) và nhiều khu vực vườn khác nhau.
* **Linh hoạt trong triển khai:** Hỗ trợ chạy trên server cá nhân (Local) hoặc triển khai lên đám mây (AWS, Cloud VPS).

---

## 🛠️ Cấu trúc dự án / Project Structure

Dự án được chia thành các module chính như sau:

```text
Gardenice-IoT/
├── aws/                # (Optional) Infrastructure as Code, cấu hình deploy AWS
├── cloud_server/       # Backend Server: API, xử lý logic, lưu trữ dữ liệu
├── device_server/      # Code chạy trên thiết bị IoT (ESP32, Arduino, Raspberry Pi...)
├── .gitignore
└── README.md
