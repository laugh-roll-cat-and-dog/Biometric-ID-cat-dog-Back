import torch
import torchvision.transforms as transforms
from PIL import Image
from torch.utils.data import Dataset, DataLoader
from ..network.network import Network_ConvNext
import os

def embed_image(image):
    model = Network_ConvNext('dino', 'sb')
    model.load_state_dict(torch.load(f"./app/ai/dino_main_50_class.pt", map_location=torch.device('cpu')))
    model.eval()

    gallery_transforms = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])

    # Process single image directly
    image = Image.open(image).convert("RGB")
    image_tensor = gallery_transforms(image)
    image_batch = image_tensor.unsqueeze(0)  # Add batch dimension

    # Get embedding
    emb = None
    with torch.no_grad():
        emb = model(image_batch)
    
    return emb