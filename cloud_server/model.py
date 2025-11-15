import torch
import torch.nn as nn
from torchvision import models

device = "cuda" if torch.cuda.is_available() else "cpu"

model_dict = {
    # ResNet
    "resnet18": models.resnet18,
    "resnet34": models.resnet34,

    # MobileNet
    "mobilenet_v2": models.mobilenet_v2,
    "mobilenet_v3_large": models.mobilenet_v3_large,
    "mobilenet_v3_small": models.mobilenet_v3_small,

    # ShuffleNet
    "shufflenet_v2_x0_5": models.shufflenet_v2_x0_5,
    "shufflenet_v2_x1_0": models.shufflenet_v2_x1_0,
    "shufflenet_v2_x1_5": models.shufflenet_v2_x1_5,
    "shufflenet_v2_x2_0": models.shufflenet_v2_x2_0,

    # EfficientNet
    "efficientnet_b0": models.efficientnet_b0,
}

class Model2Class(nn.Module): 
    def __init__(self, model_name="resnet18", model_dict=model_dict): 
        super(Model2Class, self).__init__()
        self.model = model_dict[model_name](pretrained=True)
        
        # Update the final layer depending on the model type
        if model_name.startswith("mobilenet") or model_name.startswith("efficientnet"):
            # For MobileNet and EfficientNet
            self.model.classifier[-1] = nn.Linear(
                self.model.classifier[-1].in_features, 1, bias=True
            )
        elif model_name.startswith("shufflenet") or model_name.startswith("resnet"):
            # For ShuffleNet and ResNet
            self.model.fc = nn.Linear(
                self.model.fc.in_features, 1, bias=True
            )
        else:
            raise ValueError(f"Model {model_name} not supported!")
        
        self.model = self.model.to(device)
        self.num_params = sum(p.numel() for p in self.model.parameters())

    def forward(self, x): 
        return self.model(x)