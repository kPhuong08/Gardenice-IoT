import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
import uvicorn
from PIL import Image
import io
from utils import transform
from model import Model2Class
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# load model 
model = Model2Class()
model.load_state_dict(torch.load("resnet18.pth"))
model.eval()

# Tạo thư mục uploads nếu chưa có
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = FastAPI()

print("Server AI đang khởi động...")

@app.post("inference")
async def upload_image(request: Request):
    try:
        # 1. Nhận raw bytes từ ESP32
        image_data = await request.body()

        if not image_data:
            raise HTTPException(status_code=400, detail="Không có dữ liệu ảnh")

        # convert raw bytes to image
        image = Image.open(io.BytesIO(image_data))
        image = transform(image)
        image = image.unsqueeze(0)
        image = image.to(device)
        output = model(image)
        probs = torch.sigmoid(output)
        if probs.item() > 0.5:
            result = "Healthy"
        else:
            result = "Unhealthy"
        
        print(f"Result: {result}, Confidence: {probs.item()}")
        return JSONResponse(content={"result": result, "confidence": probs.item()})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
