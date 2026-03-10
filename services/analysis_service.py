from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent
from astrbot.api.star import Context


class AnalysisService:
    def __init__(self, context: Context, config: dict):
        self.context = context
        self.config = config
        self.ai_provider = config.get("ai_provider", "")

    def _get_provider(self, event: Optional[AstrMessageEvent] = None):
        if self.ai_provider:
            return self.context.get_provider_by_id(provider_id=self.ai_provider)
        if event is not None:
            return self.context.get_using_provider(umo=event.unified_msg_origin)
        return self.context.get_using_provider()

    async def analyze_data(
        self,
        data: List[Dict[str, Any]],
        description: str = "",
        event: Optional[AstrMessageEvent] = None,
    ) -> Tuple[str, Optional[str]]:
        provider = self._get_provider(event)
        if not provider:
            return ("", "未找到可用的 AI 提供商，请先在插件配置中选择模型提供商")

        prompt = (
            "请分析下面的数据，并输出简洁的中文结论。\n"
            "请包含：数据概览、关键发现、潜在异常、建议。\n\n"
            f"数据说明：{description or '未提供'}\n\n"
            f"数据内容：\n{self._format_data(data)}"
        )
        try:
            response = await provider.text_chat(
                prompt=prompt,
                system_prompt="你是一名数据分析师，请输出结构清晰、可执行的中文分析。",
            )
            return (response.completion_text, None)
        except Exception as exc:
            logger.error(f"数据分析失败: {exc}")
            return ("", "分析失败，请检查日志")

    async def analyze_trends(
        self,
        data: List[Dict[str, Any]],
        field: str,
        event: Optional[AstrMessageEvent] = None,
    ) -> Tuple[str, Optional[str]]:
        values = [str(row.get(field, "")) for row in data if row.get(field) is not None]
        if not values:
            return ("", f"字段 {field} 没有可分析的数据")

        provider = self._get_provider(event)
        if not provider:
            return ("", "未找到可用的 AI 提供商，请先在插件配置中选择模型提供商")

        prompt = (
            f"请分析字段 {field} 的趋势、异常点和可能原因。\n"
            "请用中文输出，并尽量简洁。\n\n"
            f"样本值（最多 100 个）：\n{', '.join(values[:100])}"
        )
        try:
            response = await provider.text_chat(
                prompt=prompt,
                system_prompt="你是一名数据分析师，请输出趋势分析结论。",
            )
            return (response.completion_text, None)
        except Exception as exc:
            logger.error(f"趋势分析失败: {exc}")
            return ("", "分析失败，请检查日志")

    async def generate_insights(
        self,
        table_name: str,
        sample_data: List[Dict[str, Any]],
        event: Optional[AstrMessageEvent] = None,
    ) -> Tuple[str, Optional[str]]:
        provider = self._get_provider(event)
        if not provider:
            return ("", "未找到可用的 AI 提供商，请先在插件配置中选择模型提供商")

        prompt = (
            f"请基于表 {table_name} 的样本数据生成洞察。\n"
            "请包含：数据质量、主要特征、潜在问题、建议行动。\n\n"
            f"样本数据：\n{self._format_data(sample_data[:20])}"
        )
        try:
            response = await provider.text_chat(
                prompt=prompt,
                system_prompt="你是一名数据分析顾问，请输出结构化中文洞察。",
            )
            return (response.completion_text, None)
        except Exception as exc:
            logger.error(f"生成数据洞察失败: {exc}")
            return ("", "生成洞察失败，请检查日志")

    def _format_data(self, data: List[Dict[str, Any]]) -> str:
        if not data:
            return "无数据"
        columns = list(data[0].keys())
        lines = [" | ".join(columns), "-" * max(3, len(" | ".join(columns)))]
        for row in data:
            lines.append(" | ".join(str(row.get(col, "")) for col in columns))
        return "\n".join(lines)
