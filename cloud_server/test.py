from PIL import Image
import os

folder_path = "image"   
images = []            # list chứa ảnh
filenames = []         # list chứa tên file

for filename in os.listdir(folder_path):
    if filename.lower().endswith(".jpg"):
        img_path = os.path.join(folder_path, filename)
        img = Image.open(img_path)
        images.append(img)
        filenames.append(filename)   # lưu tên file
        

# load model 
from model import Model2Class
import torch
from utils import transform

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = Model2Class()
model.load_state_dict(torch.load("resnet18 (2).pth", map_location=device))

model.to(device)
model.eval()

for image, filename in zip(images, filenames):
    tensor_img = transform(image)
    tensor_img = tensor_img.unsqueeze(0).to(device)

    output = model(tensor_img)
    probs = torch.sigmoid(output)

    result = "Unhealthy" if probs.item() > 0.5 else "Healthy"
    print(f"File: {filename}, Result: {result}, Confidence: {probs.item():.4f}")
