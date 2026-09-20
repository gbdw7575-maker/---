import base64
import io
import unittest

import numpy as np
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

from app.routers.classify import router
from app.classifier.model import CLASS_SHORT, SkinClassifier
from app.classifier.quality import assess_skin_image_quality


class ClassifierApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = FastAPI()
        app.include_router(router)
        cls.client = TestClient(app)

    def test_status_and_classes(self):
        status = self.client.get("/api/classify/status")
        classes = self.client.get("/api/classify/classes")

        self.assertEqual(status.status_code, 200)
        self.assertTrue(status.json()["runtime_available"])
        self.assertTrue(status.json()["model_file_exists"])
        self.assertEqual(status.json()["local_class_count"], len(classes.json()))
        self.assertGreaterEqual(status.json()["local_class_count"], 5)
        self.assertEqual(status.json()["inference_mode"], "local_only")

    def test_rejects_flat_low_detail_image(self):
        buffer = io.BytesIO()
        Image.new("RGB", (224, 224), (180, 120, 100)).save(buffer, format="JPEG")
        payload = base64.b64encode(buffer.getvalue()).decode("ascii")

        response = self.client.post(
            "/api/classify/skin?topk=3",
            json={"image_base64": payload},
        )

        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(body["success"])
        self.assertEqual(body["error"], "图片质量不足，暂不进行识别")
        self.assertTrue(body["uncertain"])

    def test_rejects_invalid_base64(self):
        response = self.client.post(
            "/api/classify/skin",
            json={"image_base64": "this-is-not-valid-base64"},
        )
        self.assertEqual(response.status_code, 400)

    def test_quality_check_accepts_detailed_image(self):
        pixels = np.indices((224, 224)).sum(axis=0) % 2 * 120 + 60
        image = Image.fromarray(pixels.astype("uint8"), mode="L").convert("RGB")
        self.assertTrue(assess_skin_image_quality(image)["acceptable"])

    def test_top1_request_still_checks_high_risk_ambiguity(self):
        probabilities = np.zeros(len(CLASS_SHORT), dtype=np.float32)
        probabilities[CLASS_SHORT.index("BCC")] = 0.65
        probabilities[CLASS_SHORT.index("SCC")] = 0.20
        probabilities[CLASS_SHORT.index("AD")] = 0.15

        class FakeSession:
            def run(self, *_args, **_kwargs):
                return [np.expand_dims(probabilities, axis=0)]

        classifier = SkinClassifier("unused.onnx")
        classifier.model = FakeSession()
        classifier.input_name = "images"
        classifier.output_name = "probabilities"
        result = classifier.predict(Image.new("RGB", (224, 224), "white"), topk=1)

        self.assertEqual(len(result["predictions"]), 1)
        self.assertTrue(result["uncertain"])
        self.assertIn("多个高风险病变候选", result["notice"])


if __name__ == "__main__":
    unittest.main()
