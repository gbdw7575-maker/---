"""
AI 服务 — 对接 DeepSeek API

负责健康分析、智能咨询、指标提取等 AI 相关功能。
"""

from typing import Optional, List, Dict, Any
from openai import OpenAI

from config import settings

# ── 系统提示词 ──

HEALTH_ANALYSIS_SYSTEM_PROMPT = """你是一个专业的健康管理助手，名叫「康康」。你的职责是：

## 核心原则
1. 你不得给出明确疾病诊断，以"建议就医"代替
2. 你不得开具医疗处方
3. 你不得替代医生结论
4. 所有分析仅供参考，不构成医疗建议

## 输出要求
- 使用口语化中文，带适当表情符号
- 可以用 Markdown 排版（标题、列表、加粗）
- 分析包含：指标解读、风险提示、饮食/运动/作息/就医四维度建议
- 语气温和专业，鼓励用户重视健康"""

HEALTH_CHAT_SYSTEM_PROMPT = """你是一个贴心的健康管理助手「康康」。你可以：
- 回答健康相关的日常问题
- 解读体检报告指标
- 提供健康生活方式建议
- 识别皮肤图片（初步分类，不诊断）

请记住：你的回答仅供参考，不构成医疗诊断。对于疑似严重问题，请提醒用户及时就医。"""


def _get_client() -> Optional[OpenAI]:
    """获取 DeepSeek 客户端"""
    if not settings.DEEPSEEK_API_KEY:
        return None
    return OpenAI(
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
    )


async def chat_completion(
    messages: List[Dict[str, str]],
    system_prompt: str = HEALTH_CHAT_SYSTEM_PROMPT,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> Optional[str]:
    """
    调用 DeepSeek 进行对话补全。

    Args:
        messages: 历史消息列表 [{"role": "user"/"assistant", "content": "..."}]
        system_prompt: 系统提示词
        temperature: 温度参数
        max_tokens: 最大输出 token 数

    Returns:
        AI 回复文本，或 None（API 不可用时）
    """
    client = _get_client()
    if not client:
        return None

    try:
        response = client.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                *messages,
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[AI Service] DeepSeek API 调用失败: {e}")
        return None


async def analyze_health_indicators(
    indicators_text: str,
    user_info: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    对一组健康指标进行 AI 综合分析。

    Args:
        indicators_text: 指标文本，如 "空腹血糖 6.3mmol/L\n总胆固醇 5.8mmol/L"
        user_info: 用户信息（年龄、性别、病史等）

    Returns:
        AI 分析结果
    """
    user_context = ""
    if user_info:
        parts = []
        for k, v in user_info.items():
            if v:
                parts.append(f"{k}: {v}")
        user_context = "用户信息：" + "，".join(parts) + "\n\n"

    prompt = f"""{user_context}请对以下健康指标进行综合评估分析：

{indicators_text}

请从以下维度分析：
1. **总体评估**：哪些指标正常，哪些异常，整体健康状态如何
2. **异常指标解读**：逐项说明异常指标的含义和潜在风险
3. **饮食建议**：基于异常指标给出针对性饮食调整方案
4. **运动建议**：适合当前健康状况的运动建议
5. **作息建议**：睡眠、压力管理等方面
6. **就医建议**：哪些情况需要及时就医

请用口语化中文回复，适当使用表情符号。"""

    return await chat_completion(
        messages=[{"role": "user", "content": prompt}],
        system_prompt=HEALTH_ANALYSIS_SYSTEM_PROMPT,
        temperature=0.5,
        max_tokens=4096,
    )


async def chat_with_ai(
    message: str,
    history: Optional[List[Dict[str, str]]] = None,
    image_base64: Optional[str] = None,
) -> Optional[str]:
    """
    AI 健康咨询对话。

    Args:
        message: 用户消息
        history: 历史消息列表
        image_base64: 附带图片的 Base64 编码

    Returns:
        AI 回复
    """
    messages = list(history or [])

    if image_base64:
        # 带图片的多模态消息
        user_content = [
            {"type": "text", "text": message},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_base64}",
                    "detail": "high",
                },
            },
        ]
        # 对于不支持多模态的模型，改用文本描述
        messages.append({
            "role": "user",
            "content": f"{message}\n\n[用户同时上传了一张图片，请根据上下文回复]",
        })
    else:
        messages.append({"role": "user", "content": message})

    return await chat_completion(
        messages=messages,
        system_prompt=HEALTH_CHAT_SYSTEM_PROMPT,
        temperature=0.7,
    )


async def extract_indicators_from_text(raw_text: str) -> Optional[str]:
    """
    使用 AI 从 OCR 文本中提取关键健康指标。

    Args:
        raw_text: OCR 识别的原始文本

    Returns:
        格式化后的指标文本（行格式），或 None
    """
    prompt = f"""请从以下体检报告文本中提取所有关键健康指标。
以行格式输出，每行一个指标：
INDICATOR|指标名称|检测值|单位

只提取有临床意义的指标，忽略统计汇总数据、二维码、页码等无关信息。

文本内容：
{raw_text}"""

    return await chat_completion(
        messages=[{"role": "user", "content": prompt}],
        system_prompt="你是一个专业的体检报告解析助手。只输出指标行，不要多余解释。",
        temperature=0.1,
        max_tokens=2048,
    )
