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
model.load_state_dict(torch.load("resnet18 (6).pth", map_location=device))

model.to(device)
model.eval()

for image, filename in zip(images, filenames):
        # 2. Transform → Tensor
        tensor_img = transform(image)
        tensor_img = tensor_img.unsqueeze(0).to(device)

        # 3. Inference
        output = model(tensor_img)

        # Vì model output 3 class → dùng softmax
        probs = torch.softmax(output, dim=1)
        print("Probabilities:", probs)

        # 4. Lấy class dự đoán
        pred_class = torch.argmax(probs, dim=1).item()

        # 5. Ánh xạ class → label
        id2label = {0: "bacterial", 1: "fungal", 2: "healthy"}
        result = id2label[pred_class]

        confidence = probs[0][pred_class].item()
        print(f"Image: {filename}")
        print(f"Result: {result}, Confidence: {confidence:.4f}")
