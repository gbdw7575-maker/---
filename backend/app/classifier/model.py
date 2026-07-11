"""
皮肤病变分类模型 — EfficientNet-B0

基于 HAM10000 数据集训练的 7 类皮肤病变分类器。
支持懒加载模型（首次调用时自动下载预训练权重）。
"""

import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from PIL import Image

logger = logging.getLogger(__name__)

# 懒加载 torch（可能未安装）
TORCH_AVAILABLE = False
try:
    import torch
    import torch.nn as nn
    from torchvision import transforms
    TORCH_AVAILABLE = True
except ImportError:
    torch = None
    nn = None
    transforms = None

logger = logging.getLogger(__name__)

# HAM10000 数据集 7 类病变
CLASS_NAMES = [
    "良性角化病 (BKL)",         # Benign keratosis
    "基底细胞癌 (BCC)",         # Basal cell carcinoma
    "光化性角化病 (AKIEC)",     # Actinic keratosis
    "黑色素瘤 (MEL)",           # Melanoma
    "痣 (NV)",                  # Melanocytic nevus
    "血管病变 (VASC)",          # Vascular lesion
    "皮肤纤维瘤 (DF)",          # Dermatofibroma
]

CLASS_SHORT = ["BKL", "BCC", "AKIEC", "MEL", "NV", "VASC", "DF"]

CLASS_DESCRIPTIONS = {
    "BKL": "良性角化病，一种常见的良性皮肤增生，通常无需治疗",
    "BCC": "基底细胞癌，最常见的皮肤癌类型，早期治疗预后良好",
    "AKIEC": "光化性角化病，癌前病变，部分可能发展为鳞状细胞癌",
    "MEL": "黑色素瘤，最危险的皮肤癌，需立即就医",
    "NV": "良性痣，通常 harmless，但需定期观察变化",
    "VASC": "血管病变，多为良性，如血管瘤",
    "DF": "皮肤纤维瘤，良性纤维组织增生",
}

# 模型保存路径
MODEL_DIR = Path(__file__).resolve().parent / "weights"
MODEL_PATH = MODEL_DIR / "efficientnet_b0_ham10000.pth"

# 下载 URL（如果使用在线权重）
MODEL_URL = "https://github.com/your-org/health-models/releases/download/v1.0/efficientnet_b0_ham10000.pth"


class SkinClassifier:
    """皮肤病变分类器"""

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or str(MODEL_PATH)
        self.device = "cpu"
        self.model = None
        self.transform = None

        if TORCH_AVAILABLE:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ])

    def load_model(self) -> bool:
        """加载模型权重。返回 True 表示加载成功。"""
        if self.model is not None:
            return True

        if not TORCH_AVAILABLE:
            logger.warning("PyTorch 未安装，无法加载模型")
            logger.info("请安装 PyTorch: pip install torch torchvision")
            return False

        if not os.path.exists(self.model_path):
            logger.warning(f"模型文件不存在: {self.model_path}")
            logger.info("请先运行 python -m app.classifier.download_model --real")
            return False

        try:
            from torchvision.models import efficientnet_b0

            # 创建模型结构
            self.model = efficientnet_b0(weights=None)
            num_features = self.model.classifier[1].in_features
            self.model.classifier[1] = nn.Linear(num_features, 7)

            # 加载权重
            state_dict = torch.load(self.model_path, map_location=self.device)
            self.model.load_state_dict(state_dict)
            self.model.to(self.device)
            self.model.eval()

            logger.info(f"模型加载成功 (设备: {self.device})")
            return True

        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            return False

    def predict(self, image: Image.Image, topk: int = 3) -> Dict[str, Any]:
        """
        对单张图片进行分类预测。

        Args:
            image: PIL Image 对象
            topk: 返回前 k 个预测结果

        Returns:
            {
                "success": bool,
                "predictions": [
                    {"class_name": str, "class_short": str, "probability": float, "description": str},
                    ...
                ],
                "error": str | None
            }
        """
        if self.model is None:
            loaded = self.load_model()
            if not loaded:
                return {
                    "success": False,
                    "predictions": [],
                    "error": "模型未加载，请先下载预训练权重",
                }

        try:
            # 预处理
            img_tensor = self.transform(image).unsqueeze(0).to(self.device)

            # 推理
            outputs = self.model(img_tensor)
            probabilities = torch.softmax(outputs, dim=1)[0]

            # 取 top-k
            top_probs, top_indices = torch.topk(probabilities, min(topk, len(CLASS_NAMES)))

            predictions = []
            for prob, idx in zip(top_probs.tolist(), top_indices.tolist()):
                short = CLASS_SHORT[idx]
                predictions.append({
                    "class_name": CLASS_NAMES[idx],
                    "class_short": short,
                    "probability": round(prob, 4),
                    "description": CLASS_DESCRIPTIONS.get(short, ""),
                })

            return {
                "success": True,
                "predictions": predictions,
                "error": None,
            }

        except Exception as e:
            logger.error(f"预测失败: {e}")
            return {
                "success": False,
                "predictions": [],
                "error": str(e),
            }


# 全局单例
_classifier: Optional[SkinClassifier] = None


def get_classifier() -> SkinClassifier:
    """获取全局分类器实例"""
    global _classifier
    if _classifier is None:
        _classifier = SkinClassifier()
    return _classifier
