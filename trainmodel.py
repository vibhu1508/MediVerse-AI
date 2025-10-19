import torch
from torch import optim, nn
from torch.utils.data import DataLoader, random_split
from tqdm import tqdm
from tumordata import TumorDataset
from model import UNet

LEARNING_RATE = 3e-4
BATCH_SIZE = 4  
EPOCHS = 10
TRAIN_DATA_PATH = "/content/Unet/Tumor_dataset/train"
VAL_DATA_PATH = "/content/Unet/Tumor_dataset/val"  
MODEL_SAVE_PATH = "/content/Unet/unet2.pth"

device = "cuda" if torch.cuda.is_available() else "cpu"

# Create datasets
train_dataset = TumorDataset(TRAIN_DATA_PATH, is_train=True)
val_dataset = TumorDataset(VAL_DATA_PATH, is_train=False)

print(f"Training samples: {len(train_dataset)}")
print(f"Validation samples: {len(val_dataset)}")

# Create data loaders
train_dataloader = DataLoader(
    dataset=train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True
)

val_dataloader = DataLoader(
    dataset=val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False
)


model = UNet(n_classes=1).to(device)
optimizer = optim.AdamW(model.parameters(), lr=LEARNING_RATE)
criterion = nn.BCEWithLogitsLoss()


for epoch in range(EPOCHS):
    model.train()
    train_running_loss = 0
    
    # Training phase
    for idx, (img, mask) in enumerate(tqdm(train_dataloader, desc=f"Epoch {epoch+1}/{EPOCHS}")):
        img = img.float().to(device)
        mask = mask.float().to(device)
        
        y_pred = model(img)
        loss = criterion(y_pred, mask)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        train_running_loss += loss.item()
    
    train_loss = train_running_loss / len(train_dataloader)
    

    model.eval()
    val_running_loss = 0
    with torch.no_grad():
        for idx, (img, mask) in enumerate(val_dataloader):
            img = img.float().to(device)
            mask = mask.float().to(device)
            
            y_pred = model(img)
            loss = criterion(y_pred, mask)
            val_running_loss += loss.item()
    
    val_loss = val_running_loss / len(val_dataloader)
    
    print("-" * 50)
    print(f"Epoch {epoch+1}/{EPOCHS}")
    print(f"Train Loss: {train_loss:.4f}")
    print(f"Valid Loss: {val_loss:.4f}")
    print("-" * 50)


torch.save(model.state_dict(), MODEL_SAVE_PATH)
print(f"Model saved to {MODEL_SAVE_PATH}")