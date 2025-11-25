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

def load_dataset(root_dir, eval_per_class=100, seed=42):
    random.seed(seed)

    all_paths = []
    all_labels = []

    class_dirs = {
        0: os.path.join(root_dir, "Bacterial"),
        1: os.path.join(root_dir, "fungal"),
        2: os.path.join(root_dir, "healthy"),
    }

    # Load toàn bộ dataset
    for label, class_dir in class_dirs.items():
        for f in os.listdir(class_dir):
            all_paths.append(os.path.join(class_dir, f))
            all_labels.append(label)

    # Gom theo class
    class_to_indices = {0: [], 1: [], 2: []}
    for idx, lbl in enumerate(all_labels):
        class_to_indices[lbl].append(idx)

    # Chọn eval set cố định
    eval_idx = []
    for cls, indices in class_to_indices.items():
        random.shuffle(indices)
        if len(indices) < eval_per_class:
            raise ValueError(f"Class {cls} không đủ {eval_per_class} ảnh!")
        eval_idx.extend(indices[:eval_per_class])

    eval_idx_set = set(eval_idx)

    # Train = những ảnh còn lại
    train_idx = [i for i in range(len(all_paths)) if i not in eval_idx_set]

    # Shuffle train và eval
    random.shuffle(train_idx)
    random.shuffle(eval_idx)

    # Lấy path/label
    train_paths = [all_paths[i] for i in train_idx]
    train_labels = [all_labels[i] for i in train_idx]

    eval_paths  = [all_paths[i] for i in eval_idx]
    eval_labels = [all_labels[i] for i in eval_idx]

    # Stats
    print("Train stats:", Counter(train_labels))
    print("Eval stats:", Counter(eval_labels))

    return train_paths, train_labels, eval_paths, eval_labels


transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])