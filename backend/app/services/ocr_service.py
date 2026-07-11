"""
OCR 服务 — 对接 Kimi 视觉大模型

负责体检报告图片的文字识别。
"""

from typing import Optional
from openai import OpenAI

from config import settings


# Kimi 的 OCR 系统提示词
KIMI_OCR_PROMPT = """请仔细识别这张体检报告图片中的所有文字内容。
要求：
1. 完整识别所有可见文字，包括表格、数字、单位
2. 保留原始格式和排版
3. 不要遗漏任何数字和指标名称
4. 不要添加原文中没有的内容
5. 如果图片不清晰，请如实说明"""


def _get_kimi_client() -> Optional[OpenAI]:
    """获取 Kimi 客户端"""
    if not settings.KIMI_API_KEY:
        return None
    return OpenAI(
        api_key=settings.KIMI_API_KEY,
        base_url=settings.KIMI_BASE_URL,
    )


async def ocr_recognize(image_base64: str) -> Optional[str]:
    """
    对体检报告图片进行 OCR 识别。

    Args:
        image_base64: 图片的 Base64 编码

    Returns:
        识别出的文本内容，或 None（API 不可用 / 识别失败）
    """
    client = _get_kimi_client()
    if not client:
        return None

    try:
        response = client.chat.completions.create(
            model=settings.KIMI_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                            },
                        },
                        {
                            "type": "text",
                            "text": KIMI_OCR_PROMPT,
                        },
                    ],
                }
            ],
            temperature=0.1,
            max_tokens=4096,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[OCR Service] Kimi API 调用失败: {e}")
        return None
