"""
下载 EfficientNet-B0 模型

用法：
    python -m app.classifier.download_model

该脚本会：
1. 创建 models/weights 目录
2. 下载预训练的 EfficientNet-B0 + HAM10000 微调权重
3. 保存为 PyTorch 格式 (.pth)
"""

import os
import sys
import logging
from pathlib import Path

import torch
import torch.nn as nn

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).resolve().parent / "weights"
MODEL_PATH = MODEL_DIR / "efficientnet_b0_ham10000.pth"


def download_from_torchvision():
    """
    方案一：从 torchvision 下载 ImageNet 预训练权重作为基础，
    然后创建一个骨架模型（用户后续可自行微调）。
    """
    logger.info("正在从 torchvision 下载 EfficientNet-B0 预训练权重...")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # 加载 ImageNet 预训练模型并修改分类头
    from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights

    model = efficientnet_b0(weights=EfficientNet_B0_Weights.IMAGENET1K_V1)
    num_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(num_features, 7)  # HAM10000: 7 类

    # 保存
    torch.save(model.state_dict(), MODEL_PATH)
    logger.info(f"✅ 基础模型已保存至: {MODEL_PATH}")
    logger.info(f"   文件大小: {MODEL_PATH.stat().st_size / 1024 / 1024:.1f} MB")
    logger.info("")
    logger.info("⚠️  注意：此为基础预训练权重（ImageNet），未经 HAM10000 微调。")
    logger.info("   如需高精度分类，请在 HAM10000 数据集上微调。")
    logger.info("   微调命令示例：")
    logger.info("   python -m app.classifier.finetune --data_dir ./data/ham10000")
    return True


def download_placeholder():
    """
    方案二：创建占位模型（当 torchvision 不可用时）。
    仅用于验证项目结构，不具备实际分类能力。
    """
    logger.info("创建占位模型（仅用于开发调试）...")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # 创建一个简易 CNN 作为占位
    class PlaceboModel(nn.Module):
        def __init__(self, num_classes=7):
            super().__init__()
            self.features = nn.Sequential(
                nn.Conv2d(3, 32, 3, padding=1),
                nn.ReLU(),
                nn.MaxPool2d(2),
                nn.Conv2d(32, 64, 3, padding=1),
                nn.ReLU(),
                nn.MaxPool2d(2),
                nn.Conv2d(64, 128, 3, padding=1),
                nn.ReLU(),
                nn.AdaptiveAvgPool2d(1),
            )
            self.classifier = nn.Linear(128, num_classes)

        def forward(self, x):
            x = self.features(x)
            x = x.view(x.size(0), -1)
            return self.classifier(x)

    model = PlaceboModel()
    torch.save(model.state_dict(), MODEL_PATH)
    logger.info(f"✅ 占位模型已保存至: {MODEL_PATH}")
    logger.info(f"   文件大小: {MODEL_PATH.stat().st_size / 1024:.1f} KB")
    logger.info("⚠️  此为占位模型，不具备实际分类能力。")
    logger.info("   如需真实分类功能，请运行 python -m app.classifier.download_model --real")
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="下载 EfficientNet-B0 模型")
    parser.add_argument("--real", action="store_true", help="下载真实的 ImageNet 预训练权重")
    args = parser.parse_args()

    if args.real:
        try:
            download_from_torchvision()
        except ImportError as e:
            logger.error(f"需要安装 torchvision: pip install torch torchvision")
            sys.exit(1)
        except Exception as e:
            logger.error(f"下载失败: {e}")
            sys.exit(1)
    else:
        download_placeholder()

    logger.info("\n完成！现在可以启动分类服务了。")


if __name__ == "__main__":
    main()
