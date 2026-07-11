"""Verify or restore the bundled lightweight ONNX skin classifier."""

import argparse
import hashlib
import shutil
import subprocess
import urllib.request
from pathlib import Path

from .model import MODEL_PATH, MODEL_SHA256


GIT_MODEL_PATH = "backend/app/classifier/weights/skin_disease_mobilenetv2.onnx"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(path: Path) -> bool:
    return path.is_file() and sha256(path) == MODEL_SHA256


def restore_from_git(destination: Path) -> None:
    repository_root = Path(__file__).resolve().parents[3]
    result = subprocess.run(
        ["git", "show", f"HEAD:{GIT_MODEL_PATH}"],
        cwd=repository_root,
        check=True,
        stdout=subprocess.PIPE,
    )
    destination.write_bytes(result.stdout)


def download(url: str, destination: Path) -> None:
    with urllib.request.urlopen(url, timeout=60) as response:
        with destination.open("wb") as target:
            shutil.copyfileobj(response, target)


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify or restore the bundled ONNX model")
    parser.add_argument("--url", help="Optional public ONNX download URL")
    args = parser.parse_args()

    if verify(MODEL_PATH):
        print(f"Model is ready: {MODEL_PATH} ({MODEL_PATH.stat().st_size / 1_000_000:.1f} MB)")
        return

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = MODEL_PATH.with_suffix(".onnx.restore")
    try:
        if args.url:
            print(f"Downloading model: {args.url}")
            download(args.url, temporary)
        else:
            print("Restoring model from the current Git commit...")
            restore_from_git(temporary)
        if not verify(temporary):
            raise RuntimeError("Model SHA-256 verification failed")
        temporary.replace(MODEL_PATH)
        print(f"Model restored: {MODEL_PATH} ({MODEL_PATH.stat().st_size / 1_000_000:.1f} MB)")
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
