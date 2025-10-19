import torch
import torch.nn as nn
import torch.nn.functional as F
from unet_utils import DoubleConv ,EncoderBlock, DecoderBlock


class UNet(nn.Module):
    def __init__(self, n_classes=1):
        super().__init__()
        
        # Encoder
        self.enc1 = EncoderBlock(3, 64)
        self.enc2 = EncoderBlock(64, 128)
        self.enc3 = EncoderBlock(128, 256)
        self.enc4 = EncoderBlock(256, 512)
        
        # Bottleneck
        self.bottleneck = DoubleConv(512, 1024)
        
        # Decoder
        self.dec1 = DecoderBlock(1024, 512)
        self.dec2 = DecoderBlock(512, 256)
        self.dec3 = DecoderBlock(256, 128)
        self.dec4 = DecoderBlock(128, 64)
        
        # Final layer
        self.final = nn.Conv2d(64, n_classes, 1)
    
    def forward(self, x):
        # Encoder
        x1, skip1 = self.enc1(x)
        x2, skip2 = self.enc2(x1)
        x3, skip3 = self.enc3(x2)
        x4, skip4 = self.enc4(x3)
        
        # Bottleneck
        x = self.bottleneck(x4)
        
        # Decoder with skip connections
        x = self.dec1(x, skip4)
        x = self.dec2(x, skip3)
        x = self.dec3(x, skip2)
        x = self.dec4(x, skip1)
        
        return self.final(x)
    


model = UNet()
input_tensor = torch.randn(1, 3, 572, 572)
output = model(input_tensor)
print(f"Input shape: {input_tensor.shape}")
print(f"Output shape: {output.shape}") 