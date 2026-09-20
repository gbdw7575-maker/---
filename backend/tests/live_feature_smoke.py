"""Run an opt-in smoke test against a running local backend.

This script calls configured external AI services and creates temporary local
database records. It removes those records before exiting.
"""

import base64
import io
import json
import time
from pathlib import Path

import httpx
from PIL import Image, ImageDraw, ImageFont


BASE_URL = "http://127.0.0.1:8000"


def image_payload() -> str:
    image = Image.new("RGB", (1200, 600), "white")
    draw = ImageDraw.Draw(image)
    font_path = Path("C:/Windows/Fonts/arial.ttf")
    font = ImageFont.truetype(str(font_path), 42) if font_path.is_file() else None
    draw.text((60, 60), "HEALTH EXAMINATION REPORT", fill="black", font=font)
    draw.text((60, 180), "Fasting Glucose: 5.6 mmol/L", fill="black", font=font)
    draw.text((60, 280), "Total Cholesterol: 4.8 mmol/L", fill="black", font=font)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=95)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def main() -> None:
    results = {}
    indicator_id = None
    session_id = None
    with httpx.Client(base_url=BASE_URL, timeout=150, trust_env=False) as client:
        def request(name, method, path, **kwargs):
            started = time.perf_counter()
            response = client.request(method, path, **kwargs)
            elapsed = round(time.perf_counter() - started, 2)
            response.raise_for_status()
            results[name] = {"status": response.status_code, "seconds": elapsed}
            return response.json()

        try:
            request("health", "GET", "/api/health")
            user = request("user_profile", "GET", "/api/users/default")
            user_id = user["id"]

            request("indicator_list", "GET", "/api/health/indicators")
            request("categories", "GET", "/api/health/categories")
            created = request(
                "indicator_create",
                "POST",
                "/api/health/indicators",
                json={
                    "user_id": user_id,
                    "category": "blood_sugar",
                    "name": "空腹血糖",
                    "value": "5.6",
                    "unit": "mmol/L",
                    "source": "smoke_test",
                },
            )
            indicator_id = created["id"]
            request("indicator_detail", "GET", f"/api/health/indicators/{indicator_id}")
            request(
                "indicator_update",
                "PUT",
                f"/api/health/indicators/{indicator_id}",
                json={"value": "6.2"},
            )
            request("risk_summary", "GET", f"/api/health/risk-summary?user_id={user_id}")
            request("suggestions", "GET", f"/api/health/suggestions?user_id={user_id}")
            analysis = request("ai_analysis", "POST", f"/api/health/ai-analyze?user_id={user_id}")
            results["ai_analysis"]["source"] = analysis.get("source")

            session = request(
                "chat_session_create",
                "POST",
                "/api/chat/sessions",
                json={"user_id": user_id, "title": "自动测试"},
            )
            session_id = session["id"]
            chat = request(
                "ai_chat",
                "POST",
                "/api/chat/send",
                json={"session_id": session_id, "message": "请只回复：测试成功"},
            )
            results["ai_chat"]["reply_received"] = bool(chat.get("reply"))
            request("chat_messages", "GET", f"/api/chat/sessions/{session_id}/messages")

            payload = image_payload()
            ocr = request(
                "ocr",
                "POST",
                "/api/ocr/recognize?auto_save=false",
                json={"image_base64": payload},
            )
            results["ocr"]["raw_text_received"] = bool(ocr.get("raw_text"))
            results["ocr"]["indicator_count"] = len(ocr.get("indicators", []))

            request("classifier_status", "GET", "/api/classify/status")
            request("classifier_classes", "GET", "/api/classify/classes")
            classified = request(
                "classifier_predict",
                "POST",
                "/api/classify/skin?topk=3",
                json={"image_base64": payload},
            )
            results["classifier_predict"]["success"] = classified.get("success")
        finally:
            if indicator_id is not None:
                request("indicator_cleanup", "DELETE", f"/api/health/indicators/{indicator_id}")
            if session_id is not None:
                request("chat_cleanup", "DELETE", f"/api/chat/sessions/{session_id}")

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
