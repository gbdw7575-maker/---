"""
OCR 服务 — 对接 DeepSeek 视觉模型

负责体检报告图片的文字识别。
"""

from typing import Optional
import logging

from openai import AsyncOpenAI

from config import settings

logger = logging.getLogger(__name__)


# OCR 系统提示词（防御式，引导式列举易诱导幻觉）
OCR_PROMPT = """请从图片中识别体检报告里**实际可见**的健康数据，仅输出以下类型指标——
不存在的指标必须跳过，不得根据常识、清单或常见体检项目猜测或补全。

指标类型与常见别名/代号（识别到别名时统一使用标准中文名输出）：
- 血糖：空腹血糖（别名：葡萄糖、GLU）、餐后2小时血糖、糖化血红蛋白（别名：HbA1c）、随机血糖
- 血压：收缩压、舒张压
- 血脂：总胆固醇（别名：CHOL、TC）、甘油三酯（别名：TG）、高密度脂蛋白（别名：HDLC、HDL、高密度脂蛋白胆固醇）、低密度脂蛋白（别名：LDLC、LDL、低密度脂蛋白胆固醇）、载脂蛋白A1（别名：ApoA1）、载脂蛋白B（别名：ApoB）、脂蛋白a（别名：Lp(a)）
- 肝功能：谷丙转氨酶（别名：ALT）、谷草转氨酶（别名：AST）、总胆红素（别名：TBIL、TB）、直接胆红素（别名：DBIL）、碱性磷酸酶（别名：ALP、AKP）、总蛋白（别名：TP）、白蛋白（别名：ALB）、总胆汁酸（别名：TBA）
- 肾功能：肌酐（别名：Cr、CRE）、尿素氮（别名：BUN）、尿酸（别名：UA）
- 血常规：白细胞（别名：WBC）、红细胞（别名：RBC）、血红蛋白（别名：HGB、Hb）、血小板（别名：PLT）
- 甲状腺功能：促甲状腺激素（别名：TSH）、游离三碘甲状腺原氨酸（别名：FT3）、游离甲状腺素（别名：FT4）、总三碘甲状腺原氨酸（别名：TT3）、总甲状腺素（别名：TT4）
- 电解质：钾（别名：K）、钠（别名：Na）、氯（别名：Cl）、钙（别名：Ca）、磷（别名：P）、镁（别名：Mg）
- 心血管/心肌酶：肌酸激酶（别名：CK）、肌酸激酶同工酶（别名：CK-MB）、乳酸脱氢酶（别名：LDH）、超敏C反应蛋白（别名：hs-CRP）
- 肿瘤标志物：甲胎蛋白（别名：AFP）、癌胚抗原（别名：CEA）、糖类抗原125（别名：CA125）、糖类抗原19-9（别名：CA19-9）

要求：
1. 每行只写一个关键字段，保留检测值、单位和对应参考范围
2. 同一指标的最小值、最大值、平均值必须分别识别并标明，不能只返回最大值
3. 忽略医院名称、科室、地址、条码、页码、医生签名、参考说明和广告
4. 图片里没有的指标不要输出（例如报告只做了肝功能，就不要补写不存在的血糖、血常规）
5. 图片写的是什么名字就输出什么名字（例如图上写"葡萄糖"就输出"葡萄糖"，不要私自改成"空腹血糖"）
6. 不要猜测看不清的数字；图片不清晰时请明确说明"""


def _get_client() -> Optional[AsyncOpenAI]:
    """获取 DeepSeek 视觉客户端"""
    if not _vision_available():
        return None
    return AsyncOpenAI(
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
        timeout=90.0,
        max_retries=1,
    )


def _vision_available() -> bool:
    """仅在配置了真实 DeepSeek API Key 时启用视觉服务。"""
    key = settings.DEEPSEEK_API_KEY.strip()
    return bool(key and not key.lower().startswith(("your_", "replace_", "example")))


async def ocr_recognize(image_base64: str) -> Optional[str]:
    """
    对体检报告图片进行 OCR 识别。

    Args:
        image_base64: 图片的 Base64 编码

    Returns:
        识别出的文本内容，或 None（API 不可用 / 识别失败）
    """
    client = _get_client()
    if not client:
        return None

    try:
        response = await client.chat.completions.create(
            model=settings.DEEPSEEK_VISION_MODEL,
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
                            "text": OCR_PROMPT,
                        },
                    ],
                }
            ],
            temperature=0.1,
            # thinking 默认开启，推理 token 计入预算；长报告需充足额度避免 content 被截断
            max_tokens=16384,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.exception("DeepSeek OCR request failed: %s", e)
        return None
