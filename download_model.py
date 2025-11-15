"""
Download the emotion model from a reliable source.
This script fetches a pre-trained emotion recognition model.
"""
import torch
import urllib.request
import os

# Option 1: Try downloading from torch hub or a model repository
# For now, we'll create a simple placeholder that downloads a basic model

print("Downloading emotion recognition model...")

# Create a simple emotion model for testing
# This is a minimal ResNet-based model for 7-emotion classification
model_url = "https://huggingface.co/trpakov/vit-face/resolve/main/pytorch_model.bin"

try:
    # Try downloading from HuggingFace
    print("Attempting to download from HuggingFace...")
    urllib.request.urlretrieve(
        model_url,
        "/Users/avilaang/Documents/CrowdCue/affectnet_emotions.pt"
    )
    print("✓ Model downloaded successfully!")
except Exception as e:
    print(f"Could not download from HuggingFace: {e}")
    print("\nAlternative: Creating a basic emotion model for testing...")
    
    # Create a simple dummy model that returns random emotions
    # This allows the app to run while you get the real model
    import torch.nn as nn
    
    class SimpleEmotionModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.features = nn.Sequential(
                nn.Conv2d(3, 64, 3, padding=1),
                nn.ReLU(),
                nn.AdaptiveAvgPool2d((1, 1))
            )
            self.classifier = nn.Linear(64, 7)
        
        def forward(self, x):
            x = self.features(x)
            x = x.view(x.size(0), -1)
            x = self.classifier(x)
            return x
    
    model = SimpleEmotionModel()
    torch.save(model.state_dict(), "/Users/avilaang/Documents/CrowdCue/affectnet_emotions.pt")
    print("✓ Basic model created for testing!")
    print("Note: For production, download a real pre-trained model from:")
    print("  - PyTorch Hub")
    print("  - HuggingFace Model Hub")
    print("  - TensorFlow Hub")

print("Done!")
