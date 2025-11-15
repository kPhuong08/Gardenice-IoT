import torch
import numpy as np
import random
import os
from collections import Counter
from torchvision import transforms

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

def load_dataset(root_dir, train_ratio=0.8):
    all_paths = []
    all_labels = []

    class_0_dir = os.path.join(root_dir, "Healthy")
    class_1_dir = os.path.join(root_dir, "UnHealthy")

    # Lấy ảnh class 0
    for f in os.listdir(class_0_dir):
        all_paths.append(os.path.join(class_0_dir, f))
        all_labels.append(0)

    # Lấy ảnh class 1
    for f in os.listdir(class_1_dir):
        all_paths.append(os.path.join(class_1_dir, f))
        all_labels.append(1)

    # Shuffle 1 lần duy nhất
    indices = list(range(len(all_paths)))
    random.shuffle(indices)

    # Tạo train/val split
    train_size = int(len(indices) * train_ratio)
    
    train_idx = indices[:train_size]
    val_idx = indices[train_size:]

    train_paths = [all_paths[i] for i in train_idx]
    train_labels = [all_labels[i] for i in train_idx]

    val_paths = [all_paths[i] for i in val_idx]
    val_labels = [all_labels[i] for i in val_idx]

    # Thống kê số lượng mỗi class
    train_stats = Counter(train_labels)
    val_stats = Counter(val_labels)

    print("Train set stats:")
    print(f"  Healthy (0): {train_stats.get(0, 0)}")
    print(f"  UnHealthy (1): {train_stats.get(1, 0)}\n")

    print("Validation set stats:")
    print(f"  Healthy (0): {val_stats.get(0, 0)}")
    print(f"  UnHealthy (1): {val_stats.get(1, 0)}\n")

    return train_paths, train_labels, val_paths, val_labels


transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])