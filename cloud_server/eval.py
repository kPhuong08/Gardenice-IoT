import torch
from utils import set_seed
from sklearn.metrics import f1_score

set_seed(22520465)

def evaluate(model, val_loader, criterion, device):
    model.eval()
    val_loss = 0.0
    val_correct = 0
    val_total = 0
    val_labels_list = []
    val_preds_list = []

    with torch.no_grad():
        for images, labels in val_loader:
            images = images.to(device)
            
            labels = labels.to(device).float().unsqueeze(1)  
            outputs = model(images)

            loss = criterion(outputs, labels)

            val_loss += loss.item() * images.size(0)

            # Predict
            probs = torch.sigmoid(outputs)
            predicted = (probs > 0.5).int()

            val_total += labels.size(0)
            val_correct += (predicted == labels.int()).sum().item()

            val_labels_list.extend(labels.cpu().numpy())
            val_preds_list.extend(predicted.cpu().numpy())

    val_loss = val_loss / val_total
    val_acc = val_correct / val_total
    val_f1 = f1_score(val_labels_list, val_preds_list, average='weighted')

    return val_loss, val_acc, val_f1, val_labels_list, val_preds_list