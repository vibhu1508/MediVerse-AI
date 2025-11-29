import torch
import torch.nn as nn
import torch.nn.functional as F
from unet_utils import DoubleConv ,EncoderBlock, DecoderBlock


class UNet(nn.Module):
    def __init__(self, n_classes=1):
        super().__init__()
        self.enc1 = EncoderBlock(3, 64)
        self.enc2 = EncoderBlock(64, 128)
        self.enc3 = EncoderBlock(128, 256)
        self.enc4 = EncoderBlock(256, 512)


        self.bottleneck = DoubleConv(512, 1024)

        self.dec1 = DecoderBlock(1024, 512)
        self.dec2 = DecoderBlock(512, 256)
        self.dec3 = DecoderBlock(256, 128)
        self.dec4 = DecoderBlock(128, 64)
        self.final = nn.Conv2d(64, n_classes, kernel_size=1)

    def forward(self, x):
        s1, x1 = self.enc1(x)
        s2, x2 = self.enc2(x1)
        s3, x3 = self.enc3(x2)
        s4, x4 = self.enc4(x3)

        x = self.bottleneck(x4)

        d1 = self.dec1(x, s4)
        d2 = self.dec2(d1, s3)
        d3 = self.dec3(d2, s2)
        d4 = self.dec4(d3, s1)

        return self.final(d4)


def dice_coeff(pred, target, smooth=1e-6):
    pred = (torch.sigmoid(pred) > 0.5).float()
    intersection = (pred * target).sum(dim=(1, 2, 3))
    return ((2. * intersection + smooth) /
            (pred.sum(dim=(1, 2, 3)) + target.sum(dim=(1, 2, 3)) + smooth)).mean()


def iou_score(pred, target, smooth=1e-6):
    pred = (torch.sigmoid(pred) > 0.5).float()
    intersection = (pred * target).sum(dim=(1, 2, 3))
    union = (pred + target - pred * target).sum(dim=(1, 2, 3))
    return ((intersection + smooth) / (union + smooth)).mean()


if __name__ == "__main__":
    model = UNet()
    total_params = sum(p.numel() for p in model.parameters())
    print(f"Total parameters: {total_params:,}")

    input_tensor = torch.randn(1, 3, 224, 224)
    output = model(input_tensor)
    print(f"Input shape: {input_tensor.shape}")
    print(f"Output shape: {output.shape}") 
