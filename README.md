# 🌱 Gardenice-IoT - Hệ thống phát hiện bệnh rau xà lách bằng IoT

Hệ thống giám sát và phát hiện bệnh cho rau xà lách sử dụng IoT, AI và cloud computing.

## 📋 Tổng quan

Dự án bao gồm 3 thành phần chính:

### 1. **Device Server** (`device_server/`)
- ESP32 camera module chụp ảnh rau xà lách
- Server Flask nhận và lưu trữ ảnh từ thiết bị
- Client camera laptop để test và phát triển

### 2. **Cloud Server** (`cloud_server/`)
- FastAPI server với mô hình PyTorch (ResNet/MobileNet)
- Phân loại bệnh: **bacterial**, **fungal**, **healthy**
- Lưu ảnh và kết quả vào AWS S3
- Endpoint `/inference` nhận ảnh và trả về kết quả phân tích

### 3. **AWS Infrastructure** (`aws/`)
- **Lambda Functions**: Xử lý dữ liệu cây trồng và MQTT
- **API Gateway**: REST API cho frontend và MQTT bridge
- **S3**: Lưu trữ ảnh và kết quả phân tích
- **CloudFront**: Hosting React frontend
- **React Frontend**: Dashboard giám sát real-time

## 🔄 Luồng hoạt động

```
ESP32 Camera → Device Server → Cloud Server (AI Inference) → AWS S3
                                                                    ↓
                                                          Lambda + API Gateway
                                                                    ↓
                                                          React Frontend
```

## 🚀 Công nghệ sử dụng

- **IoT**: ESP32, Camera Module
- **Backend**: Python, FastAPI, Flask, PyTorch
- **Cloud**: AWS (Lambda, API Gateway, S3, CloudFront)
- **Frontend**: React, Tailwind CSS
- **Infrastructure**: Terraform
- **MQTT**: HiveMQ cho sensor data

## 📁 Cấu trúc thư mục

```
Gardenice-IoT/
├── device_server/      # ESP32 code và server nhận ảnh
├── cloud_server/       # AI inference server (FastAPI)
├── aws/                # AWS infrastructure và frontend
│   ├── backend/        # Lambda functions
│   ├── frontend/       # React app
│   ├── terraform/      # Infrastructure as Code
│   └── scripts/        # Deployment scripts
└── README.md
```

## 🎯 Tính năng

- ✅ Chụp ảnh tự động từ ESP32 camera
- ✅ Phát hiện bệnh bằng AI (3 lớp: vi khuẩn, nấm, khỏe mạnh)
- ✅ Lưu trữ ảnh và kết quả trên AWS S3
- ✅ Dashboard web real-time để giám sát
- ✅ API RESTful cho tích hợp
- ✅ MQTT bridge cho sensor data

## 📝 Ghi chú

- Model AI được train với PyTorch, hỗ trợ ResNet, MobileNet, EfficientNet
- Infrastructure được quản lý bằng Terraform
- Frontend được deploy lên CloudFront qua S3
- Xem chi tiết deployment tại `aws/scripts/README.md`

