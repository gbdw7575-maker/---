"""Lightweight input-quality checks for skin screening images."""

from __future__ import annotations

import numpy as np
from PIL import Image


MIN_SIDE = 160
MIN_CONTRAST = 10.0
MIN_SHARPNESS = 1.5
MIN_BRIGHTNESS = 25.0
MAX_BRIGHTNESS = 235.0


def assess_skin_image_quality(image: Image.Image) -> dict:
    """Return deterministic image-quality metrics and actionable issues."""
    width, height = image.size
    gray = image.convert("L")
    gray.thumbnail((384, 384), Image.Resampling.BILINEAR)
    array = np.asarray(gray, dtype=np.float32)
    brightness = float(array.mean())
    contrast = float(array.std())
    horizontal = float(np.abs(np.diff(array, axis=1)).mean()) if array.shape[1] > 1 else 0.0
    vertical = float(np.abs(np.diff(array, axis=0)).mean()) if array.shape[0] > 1 else 0.0
    sharpness = (horizontal + vertical) / 2

    issues = []
    if min(width, height) < MIN_SIDE:
        issues.append("图片尺寸过小，请靠近病变并重新拍摄")
    if brightness < MIN_BRIGHTNESS:
        issues.append("图片过暗，请在光线充足处重新拍摄")
    elif brightness > MAX_BRIGHTNESS:
        issues.append("图片过曝，请避免闪光灯直射")
    if contrast < MIN_CONTRAST:
        issues.append("图片对比度过低，未能看清皮肤细节")
    if sharpness < MIN_SHARPNESS:
        issues.append("图片可能模糊，请保持相机稳定并重新对焦")

    return {
        "acceptable": not issues,
        "issues": issues,
        "metrics": {
            "width": width,
            "height": height,
            "brightness": round(brightness, 2),
            "contrast": round(contrast, 2),
            "sharpness": round(sharpness, 2),
        },
    }
