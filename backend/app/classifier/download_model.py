"""Download and verify the lightweight ONNX skin classifier."""

import hashlib
import shutil
import urllib.request
from pathlib import Path

from .model import MODEL_PATH, MODEL_SHA256


MODEL_URL = (
    "https://github.com/gbdw7575-maker/---/raw/main/"
    "backend/app/classifier/weights/skin_disease_mobilenetv2.onnx"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = MODEL_PATH.with_suffix(".onnx.download")
    print(f"Downloading {MODEL_URL}")
    try:
        with urllib.request.urlopen(MODEL_URL, timeout=60) as response:
            with temporary.open("wb") as target:
                shutil.copyfileobj(response, target)
        actual = sha256(temporary)
        if actual != MODEL_SHA256:
            raise RuntimeError(f"SHA-256 mismatch: expected {MODEL_SHA256}, got {actual}")
        temporary.replace(MODEL_PATH)
        print(f"Model ready: {MODEL_PATH} ({MODEL_PATH.stat().st_size / 1024 / 1024:.1f} MB)")
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
