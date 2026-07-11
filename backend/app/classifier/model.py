"""Lightweight ONNX classifier for common visible skin conditions.

This module provides educational screening hints only. It must not be used as
a medical diagnosis or as a reason to delay professional care.
"""

import logging
from pathlib import Path
from typing import Any, Optional

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

try:
    import onnxruntime as ort

    ONNX_AVAILABLE = True
except ImportError:
    ort = None
    ONNX_AVAILABLE = False


MODEL_NAME = "MobileNetV2 Common Skin Conditions"
MODEL_VERSION = "1.0"
MODEL_SOURCE = "Zeynepcklc/skin-mobilenetv2"
MODEL_LICENSE = "MIT"
MODEL_SHA256 = "f68630720ea3afb2aff40557b091887006ad40c53b6f906674fd56bb30014374"
MODEL_DIR = Path(__file__).resolve().parent / "weights"
MODEL_PATH = MODEL_DIR / "skin_disease_mobilenetv2.onnx"

CLASS_SHORT = ["AD", "BCC", "ECZEMA", "MEL", "WARTS"]
CLASS_NAMES = [
    "特应性皮炎",
    "基底细胞癌",
    "湿疹",
    "黑色素瘤",
    "疣或传染性软疣",
]
CLASS_DESCRIPTIONS = {
    "AD": "常见慢性炎症性皮肤问题，可表现为干燥、发红和瘙痒，需要结合病史判断。",
    "BCC": "模型发现与基底细胞癌训练样本相似的特征，建议尽快由皮肤科医生面诊确认。",
    "ECZEMA": "常见炎症性皮肤表现，可能与刺激、过敏或皮肤屏障受损有关。",
    "MEL": "模型发现与黑色素瘤训练样本相似的特征，请尽快到皮肤科进行专业评估。",
    "WARTS": "可能与疣或传染性软疣的外观相似，部分具有传染性，应避免抓挠和共用毛巾。",
}
CLASS_RISK = {
    "AD": "routine",
    "BCC": "urgent",
    "ECZEMA": "routine",
    "MEL": "urgent",
    "WARTS": "routine",
}


class SkinClassifier:
    """Run the five-class MobileNetV2 model with ONNX Runtime on CPU."""

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = str(model_path or MODEL_PATH)
        self.device = "cpu"
        self.model = None
        self.input_name: Optional[str] = None
        self.output_name: Optional[str] = None

    def load_model(self) -> bool:
        if self.model is not None:
            return True
        if not ONNX_AVAILABLE:
            logger.warning("onnxruntime is not installed")
            return False
        if not Path(self.model_path).is_file():
            logger.warning("Model file does not exist: %s", self.model_path)
            return False

        try:
            options = ort.SessionOptions()
            options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            self.model = ort.InferenceSession(
                self.model_path,
                sess_options=options,
                providers=["CPUExecutionProvider"],
            )
            self.input_name = self.model.get_inputs()[0].name
            self.output_name = self.model.get_outputs()[0].name
            return True
        except Exception as exc:
            logger.exception("Failed to load skin classifier: %s", exc)
            self.model = None
            return False

    @staticmethod
    def _preprocess(image: Image.Image) -> np.ndarray:
        resized = image.convert("RGB").resize((224, 224), Image.Resampling.BILINEAR)
        array = np.asarray(resized, dtype=np.float32)
        array = array / 127.5 - 1.0
        return np.expand_dims(array, axis=0)

    @staticmethod
    def _normalize_output(values: np.ndarray) -> np.ndarray:
        probabilities = np.asarray(values, dtype=np.float32).reshape(-1)
        if len(probabilities) != len(CLASS_NAMES):
            raise ValueError("模型输出类别数量不正确")
        if np.any(probabilities < 0) or not np.isclose(probabilities.sum(), 1.0, atol=0.01):
            shifted = probabilities - probabilities.max()
            probabilities = np.exp(shifted) / np.exp(shifted).sum()
        return probabilities

    def predict(self, image: Image.Image, topk: int = 3) -> dict[str, Any]:
        if not self.load_model():
            return {
                "success": False,
                "predictions": [],
                "uncertain": True,
                "notice": "分类模型尚未安装，请运行模型下载脚本并安装 onnxruntime。",
                "error": "模型不可用",
            }

        try:
            tensor = self._preprocess(image)
            raw = self.model.run([self.output_name], {self.input_name: tensor})[0]
            probabilities = self._normalize_output(raw[0])
            indices = np.argsort(probabilities)[::-1][: min(topk, len(CLASS_NAMES))]
            predictions = []
            for index in indices:
                short = CLASS_SHORT[int(index)]
                predictions.append(
                    {
                        "class_name": CLASS_NAMES[int(index)],
                        "class_short": short,
                        "probability": round(float(probabilities[index]), 4),
                        "description": CLASS_DESCRIPTIONS[short],
                        "risk_level": CLASS_RISK[short],
                    }
                )

            top_probability = predictions[0]["probability"]
            uncertain = top_probability < 0.60
            notice = (
                "图片与模型已知类别的匹配度较低，请勿依据本结果自行用药。"
                if uncertain
                else "结果仅表示图像相似度，不构成医疗诊断。"
            )
            return {
                "success": True,
                "predictions": predictions,
                "uncertain": uncertain,
                "notice": notice,
                "error": None,
            }
        except Exception as exc:
            logger.exception("Skin classification failed: %s", exc)
            return {
                "success": False,
                "predictions": [],
                "uncertain": True,
                "notice": "无法完成图片初筛，请稍后重试或咨询医生。",
                "error": str(exc),
            }


_classifier: Optional[SkinClassifier] = None


def get_classifier() -> SkinClassifier:
    global _classifier
    if _classifier is None:
        _classifier = SkinClassifier()
    return _classifier
