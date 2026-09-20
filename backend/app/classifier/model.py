"""Lightweight ONNX classifier for common visible skin conditions.

This module provides educational screening hints only. It must not be used as
a medical diagnosis or as a reason to delay professional care.
"""

import logging
from pathlib import Path
from typing import Any, Optional

import numpy as np
from PIL import Image

from .class_definitions import CLASS_PROFILES

logger = logging.getLogger(__name__)

try:
    import onnxruntime as ort

    ONNX_AVAILABLE = True
except ImportError:
    ort = None
    ONNX_AVAILABLE = False


MODEL_SHA256 = "f68630720ea3afb2aff40557b091887006ad40c53b6f906674fd56bb30014374"
MODEL_DIR = Path(__file__).resolve().parent / "weights"
EXPANDED_MODEL_PATH = MODEL_DIR / "skin_disease_expanded_v3.onnx"
EXPANDED_ENSEMBLE_MODEL_PATH = MODEL_DIR / "skin_disease_expanded_v3_aux.onnx"
TRAINED_MODEL_PATH = MODEL_DIR / "skin_disease_local_v2.onnx"
V2_ENSEMBLE_MODEL_PATH = MODEL_DIR / "skin_disease_mobilenet_v3_aux.onnx"
LEGACY_MODEL_PATH = MODEL_DIR / "skin_disease_mobilenetv2.onnx"
if EXPANDED_MODEL_PATH.is_file():
    MODEL_PATH = EXPANDED_MODEL_PATH
    ENSEMBLE_MODEL_PATH = EXPANDED_ENSEMBLE_MODEL_PATH
    CLASS_PROFILE = "v3"
elif TRAINED_MODEL_PATH.is_file():
    MODEL_PATH = TRAINED_MODEL_PATH
    ENSEMBLE_MODEL_PATH = V2_ENSEMBLE_MODEL_PATH
    CLASS_PROFILE = "v2"
else:
    MODEL_PATH = LEGACY_MODEL_PATH
    ENSEMBLE_MODEL_PATH = None
    CLASS_PROFILE = "v2"
ENSEMBLE_PRIMARY_WEIGHT = 0.90
LOCAL_ENSEMBLE_AVAILABLE = bool(ENSEMBLE_MODEL_PATH and ENSEMBLE_MODEL_PATH.is_file())
MODEL_NAME = "Local Expanded Skin Ensemble" if CLASS_PROFILE == "v3" and LOCAL_ENSEMBLE_AVAILABLE else "Local Expanded Skin Classifier" if CLASS_PROFILE == "v3" else "Local EfficientNet + MobileNet Ensemble" if LOCAL_ENSEMBLE_AVAILABLE else "Local Common Skin Conditions Classifier"
MODEL_VERSION = "3.0-local-ensemble" if CLASS_PROFILE == "v3" and LOCAL_ENSEMBLE_AVAILABLE else "3.0-local" if CLASS_PROFILE == "v3" else "2.1-local-ensemble" if LOCAL_ENSEMBLE_AVAILABLE else "2.0-local" if MODEL_PATH == TRAINED_MODEL_PATH else "1.0-legacy"
MODEL_SOURCE = "local-training-pipeline" if MODEL_PATH != LEGACY_MODEL_PATH else "Zeynepcklc/skin-mobilenetv2"
MODEL_LICENSE = "Source dataset terms; see docs/模型训练资源.md" if MODEL_PATH != LEGACY_MODEL_PATH else "MIT"

ACTIVE_CLASS_DEFINITIONS = CLASS_PROFILES[CLASS_PROFILE]
CLASS_SHORT = [item["short"] for item in ACTIVE_CLASS_DEFINITIONS]
CLASS_NAMES = [item["name"] for item in ACTIVE_CLASS_DEFINITIONS]
CLASS_DESCRIPTIONS = {item["short"]: item["description"] for item in ACTIVE_CLASS_DEFINITIONS}
CLASS_RISK = {item["short"]: item["risk_level"] for item in ACTIVE_CLASS_DEFINITIONS}

LOCAL_CLASS_DEFINITIONS = [{**item, "provider": "local_model"} for item in ACTIVE_CLASS_DEFINITIONS]

ALL_CLASS_DEFINITIONS = LOCAL_CLASS_DEFINITIONS


class SkinClassifier:
    """Run the five-class MobileNetV2 model with ONNX Runtime on CPU."""

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = str(model_path or MODEL_PATH)
        self.use_ensemble = model_path is None and LOCAL_ENSEMBLE_AVAILABLE
        self.ensemble_model_path = ENSEMBLE_MODEL_PATH if self.use_ensemble else None
        self.device = "cpu"
        self.model = None
        self.input_name: Optional[str] = None
        self.output_name: Optional[str] = None
        self.ensemble_model = None
        self.ensemble_input_name: Optional[str] = None
        self.ensemble_output_name: Optional[str] = None

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
            if self.use_ensemble:
                try:
                    self.ensemble_model = ort.InferenceSession(
                        str(ENSEMBLE_MODEL_PATH),
                        sess_options=options,
                        providers=["CPUExecutionProvider"],
                    )
                    self.ensemble_input_name = self.ensemble_model.get_inputs()[0].name
                    self.ensemble_output_name = self.ensemble_model.get_outputs()[0].name
                except Exception as exc:
                    logger.warning("Auxiliary ensemble model is unavailable; using primary model only: %s", exc)
                    self.ensemble_model = None
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
            if self.ensemble_model is not None:
                auxiliary_raw = self.ensemble_model.run(
                    [self.ensemble_output_name],
                    {self.ensemble_input_name: tensor},
                )[0]
                auxiliary_probabilities = self._normalize_output(auxiliary_raw[0])
                probabilities = (
                    ENSEMBLE_PRIMARY_WEIGHT * probabilities
                    + (1.0 - ENSEMBLE_PRIMARY_WEIGHT) * auxiliary_probabilities
                )
            safety_topk = min(max(topk, 3), len(CLASS_NAMES))
            indices = np.argsort(probabilities)[::-1][:safety_topk]
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
                        "provider": "local_model",
                    }
                )

            top_probability = predictions[0]["probability"]
            urgent_candidates = [
                item for item in predictions
                if item["risk_level"] == "urgent" and item["probability"] >= 0.10
            ]
            urgent_secondary = any(
                item["risk_level"] == "urgent" and item["probability"] >= 0.20
                for item in predictions[1:]
            )
            high_risk_ambiguity = len(urgent_candidates) >= 2 or urgent_secondary
            uncertain = top_probability < 0.60 or high_risk_ambiguity
            if high_risk_ambiguity:
                notice = "多个高风险病变候选外观相似，图片无法可靠区分，请尽快由皮肤科医生面诊。"
            elif top_probability < 0.60:
                notice = "图片与模型已知类别的匹配度较低，请勿依据本结果自行用药。"
            elif predictions[0]["risk_level"] == "urgent":
                notice = "结果包含高风险病变候选，请尽快由皮肤科医生评估；本结果不构成诊断。"
            else:
                notice = "结果仅表示图像相似度，不构成医疗诊断。"
            return {
                "success": True,
                "predictions": predictions[:topk],
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
