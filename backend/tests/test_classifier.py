import base64
import io
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

from app.routers.classify import router


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
        self.assertEqual(len(classes.json()), 5)

    def test_predict_marks_ambiguous_synthetic_image(self):
        buffer = io.BytesIO()
        Image.new("RGB", (224, 224), (180, 120, 100)).save(buffer, format="JPEG")
        payload = base64.b64encode(buffer.getvalue()).decode("ascii")

        response = self.client.post(
            "/api/classify/skin?topk=3",
            json={"image_base64": payload},
        )

        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(body["success"])
        self.assertEqual(len(body["predictions"]), 3)
        self.assertTrue(body["uncertain"])

    def test_rejects_invalid_base64(self):
        response = self.client.post(
            "/api/classify/skin",
            json={"image_base64": "this-is-not-valid-base64"},
        )
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
