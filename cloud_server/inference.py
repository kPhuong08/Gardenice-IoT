import os
import time
import boto3
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from PIL import Image
import io
from utils import transform
from model import Model2Class
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# load model
model = Model2Class()
model.load_state_dict(torch.load("resnet18.pth", map_location=device))
model.to(device)
model.eval()

app = FastAPI()

# init S3 client
s3 = boto3.client("s3")
BUCKET = "lettuce-bucket"

print("Server AI đang khởi động...")

@app.post("/inference")
async def upload_image(request: Request):
    try:
        # 1. Nhận raw bytes từ ESP32
        image_data = await request.body()
        if not image_data:
            raise HTTPException(status_code=400, detail="Không có dữ liệu ảnh")

        # 2. Convert raw bytes to PIL (để upload)
        pil_image = Image.open(io.BytesIO(image_data))

        # 3. Transform + inference
        tensor_img = transform(pil_image)
        tensor_img = tensor_img.unsqueeze(0).to(device)

        output = model(tensor_img)
        probs = torch.sigmoid(output)

        result = "Healthy" if probs.item() > 0.5 else "Unhealthy"

        print(f"Result: {result}, Confidence: {probs.item()}")

        # 4. SAVE TO S3
        timestamp = int(time.time())
        image_key = f"images/{timestamp}.jpg"
        result_key = f"results/{timestamp}.txt"

        # Upload image
        buffer = io.BytesIO()
        pil_image.save(buffer, format="JPEG")
        buffer.seek(0)

        s3.upload_fileobj(
            buffer,
            BUCKET,
            image_key,
            ExtraArgs={"ContentType": "image/jpeg"}
        )

        # Upload result text
        s3.put_object(
            Bucket=BUCKET,
            Key=result_key,
            Body=f"{result}\n{probs.item()}".encode("utf-8"),
            ContentType="text/plain"
        )

        # 5. Trả response
        return JSONResponse(content={
            "result": result,
            "confidence": probs.item(),
            "saved_image": image_key,
            "saved_text": result_key
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
