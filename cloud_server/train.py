from PIL.Image import os
from torch.utils.data import DataLoader
from model import Model2Class
from utils import load_dataset
from custom_dataset import CustomDataset
from utils import transform
from utils import set_seed
from eval import evaluate
from sklearn.metrics import f1_score
import torch
import torch.nn as nn
import argparse
import pandas as pd

set_seed(22520465)

if __name__ == "__main__": 
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str, default="resnet18")
    parser.add_argument("--num_epochs", type=int, default=2)
    parser.add_argument("--lr", type=float, default=0.0001)
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--root_dir", type=str, default="dataset")
    args = parser.parse_args()
    model_name = args.model_name
    num_epochs = args.num_epochs
    lr = args.lr
    device = args.device
    root_dir = args.root_dir

    # Load dataset
    train_paths, train_labels, val_paths, val_labels = load_dataset(root_dir=root_dir, train_ratio=0.8) 
    train_dataset = CustomDataset(train_paths, train_labels, transform=transform)
    val_dataset = CustomDataset(val_paths, val_labels, transform=transform)
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)

    # Load model
    model = Model2Class(model_name=model_name)
    print(model.num_params) 

    # define criterion and optimizer
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)

    # Evaluate model
    before_train_val_loss, before_train_val_acc, before_train_val_f1, before_train_val_labels_list, before_train_val_preds_list = evaluate(model, val_loader, criterion, device)
    print(f"Before Train - Val Loss: {before_train_val_loss:.4f}, Val Acc: {before_train_val_acc:.4f}, Val F1: {before_train_val_f1:.4f}")

    # Train model
    train_losses = []
    train_accs = []
    train_f1s = []
    val_losses = []
    val_accs = []
    val_f1s = []
    model.train()
    for epoch in range(num_epochs):
        running_loss = 0.0
        correct = 0
        total = 0
        all_labels = []
        all_preds = []
        for images, labels in train_loader:
            images = images.to(device)
            labels = labels.to(device).float().unsqueeze(1)   # <── CHỈNH
            
            optimizer.zero_grad()

            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item() * images.size(0)

            # Predict
            probs = torch.sigmoid(outputs)
            predicted = (probs > 0.5).int()                   # <── CHỈNH
            
            total += labels.size(0)
            correct += (predicted == labels.int()).sum().item()

            all_labels.extend(labels.cpu().numpy())
            all_preds.extend(predicted.cpu().numpy())
        
        train_loss = running_loss / total
        train_acc = correct / total
        train_f1 = f1_score(all_labels, all_preds, average='weighted')
        train_losses.append(train_loss)
        train_accs.append(train_acc)
        train_f1s.append(train_f1)
        print(f"Epoch {epoch+1}, Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f}, Train F1: {train_f1:.4f}")
        
        # Evaluate model
        val_loss, val_acc, val_f1, val_labels_list, val_preds_list = evaluate(model, val_loader, criterion, device)
        val_losses.append(val_loss)
        val_accs.append(val_acc)
        val_f1s.append(val_f1)
        print(f"Epoch {epoch+1}, Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}, Val F1: {val_f1:.4f}")
    
    # Save log 
    log_df = pd.DataFrame({
        "before_train_val_loss": before_train_val_loss,
        "before_train_val_acc": before_train_val_acc,
        "before_train_val_f1": before_train_val_f1,
        "train_losses": train_losses,
        "train_accs": train_accs,
        "train_f1s": train_f1s,
        "val_losses": val_losses,
        "val_accs": val_accs,
        "val_f1s": val_f1s,
    })
    os.makedirs("logs", exist_ok=True)
    log_df.to_csv(f"logs/{model_name}.csv", index=False)
    print(f"Log saved to logs/{model_name}.csv")
    # Save model
    os.makedirs("models", exist_ok=True)
    torch.save(model.state_dict(), f"models/{model_name}.pth")
    print(f"Model saved to models/{model_name}.pth")
    print("Training completed!")



