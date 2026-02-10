import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
from transformers import  ConvNextV2ForImageClassification, AutoModel

from ..attention.BAM import BAM
from ..attention.DAM import ChannelAttentionModule, PositionAttentionModule, DualAttentionModule
from ..attention.SAM import Self_Attention
from ..attention.SEblock import FeatureFusionModule

class Network_ConvNext(nn.Module):
    def __init__(self, backbone, attention, embedding_dim=1024):
        super().__init__()
        self.attention = attention
        self.bb = backbone
        if backbone == 'dino':
            model_name = "facebook/dinov3-convnext-tiny-pretrain-lvd1689m"
            model = AutoModel.from_pretrained(
                model_name, 
                device_map="cpu", 
            )
            self.backbone = model
            num_features = model.layer_norm.normalized_shape[0]
        elif backbone == 'v2':
            model_name = "facebook/convnextv2-tiny-1k-224"
            base_model = ConvNextV2ForImageClassification.from_pretrained(model_name)
            self.backbone = base_model.convnextv2
            num_features = base_model.classifier.in_features

        self.cam = ChannelAttentionModule()
        self.pam = PositionAttentionModule(num_features)
        self.dam = DualAttentionModule(in_channels=num_features)
        self.sam = Self_Attention(num_features)
        self.bam = BAM(num_features)
        
        in_chan = 0
        if attention == 'sb':
            in_chan = num_features * 2
        else:
            in_chan = num_features

        self.orchestra = FeatureFusionModule(
            in_chan=in_chan,
            out_chan=3*num_features,
            attention=attention,
        )

        self.gap = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(3*num_features, embedding_dim, bias=False)
        #self.fc_abl = nn.Linear(num_features, embedding_dim, bias=False)
        self.ln = nn.LayerNorm(embedding_dim)

    def extract_backbone(self, x):
        out = self.backbone(x)
        if self.bb == 'dino':
            feat = out.last_hidden_state
            feat = feat[:, 1:, :]
            B, N, C = feat.shape
            
            H = W = int(N ** 0.5)

            feat = feat.transpose(1, 2).reshape(B, C, H, W)
            return feat
        return out.last_hidden_state

    def embed(self, x):
        feat = self.extract_backbone(x)

        if self.attention == 's':
            fused = self.sam(feat)
        elif self.attention == 'b':
            fused = self.bam(feat)
        elif self.attention == 'sb':
            att1 = self.sam(feat)
            att2 = self.bam(feat)
            fused = self.orchestra(fsp=att1, fcp=att2)
        else:
            fused = feat

        fused = self.gap(fused)
        fused = fused.view(fused.size(0), -1)

        if self.attention == 'sb':
            x = self.fc(fused)
        else:
            x = self.fc_abl(fused)
        x = self.ln(x)
        # x = F.normalize(x, p=2, dim=1)
        return x

    def forward(self, img):
        return self.embed(img)

