import os 
from PIL import Image
from torch.utils.data.dataset import Dataset
from torchvision import transforms 

class TumorDataset(Dataset):
    def __init__(self, data_path, is_train=True):
        super().__init__()
        if is_train:
            self.image_dir = os.path.join(data_path, "images")
            self.mask_dir = os.path.join(data_path, "masks")
        else:
            print("inside else")
            self.image_dir = os.path.join(data_path, "images")
            self.mask_dir = os.path.join(data_path, "masks")
        
        print(self.image_dir)
        self.image_files = sorted(os.listdir(self.image_dir))
        self.mask_files = sorted(os.listdir(self.mask_dir))
        
        assert len(self.image_files) == len(self.mask_files), "Mismatch between images and masks"
        
        self.transform_img = transforms.Compose([
            transforms.Resize((572, 572)),
            transforms.ToTensor()
        ])
        
        self.transform_mask = transforms.Compose([
            transforms.Resize((388, 388)),
            transforms.ToTensor()
        ])

    def __getitem__(self, index):
        img_path = os.path.join(self.image_dir, self.image_files[index])
        mask_path = os.path.join(self.mask_dir, self.mask_files[index])
        
        img = Image.open(img_path).convert("RGB")
        mask = Image.open(mask_path).convert("L")
        
        return self.transform_img(img), self.transform_mask(mask)

    def __len__(self):
        return len(self.image_files)
    

model_path = "unet.pth"
datapath = "dataset\\train"

dataset = TumorDataset(datapath, is_train=False)