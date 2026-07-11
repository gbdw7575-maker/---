"""Convert the development Keras checkpoint to the runtime ONNX model."""

from pathlib import Path
import hashlib
import urllib.request

import tensorflow as tf
import tf2onnx


WEIGHTS_DIR = Path(__file__).resolve().parent / "weights"
SOURCE_PATH = WEIGHTS_DIR / "skin_disease_mobilenetv2.h5"
OUTPUT_PATH = WEIGHTS_DIR / "skin_disease_mobilenetv2.onnx"
SOURCE_URL = (
    "https://huggingface.co/Zeynepcklc/skin-mobilenetv2/resolve/main/"
    "model/skin_disease_model.h5"
)
SOURCE_SHA256 = "cd1887eb90ad4af2f79f08ff62fa2d21f6aa7826b6d848abf67473747a12cf27"


def ensure_source() -> None:
    if not SOURCE_PATH.is_file():
        WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Downloading source checkpoint: {SOURCE_URL}")
        urllib.request.urlretrieve(SOURCE_URL, SOURCE_PATH)
    actual = hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest()
    if actual != SOURCE_SHA256:
        raise RuntimeError(f"Source SHA-256 mismatch: {actual}")


def main() -> None:
    ensure_source()
    model = tf.keras.models.load_model(SOURCE_PATH, compile=False)

    @tf.function(
        input_signature=[
            tf.TensorSpec([None, 224, 224, 3], tf.float32, name="images")
        ]
    )
    def inference(images):
        return {"probabilities": model(images, training=False)}

    tf2onnx.convert.from_function(
        inference,
        input_signature=inference.input_signature,
        opset=13,
        output_path=str(OUTPUT_PATH),
    )
    print(f"ONNX model written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
