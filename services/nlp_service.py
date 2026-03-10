from __future__ import annotations

import re
from typing import Optional, Tuple

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent
from astrbot.api.provider import LLMResponse
from astrbot.api.star import Context


class NLPService:
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

    async def text_to_sql(
        self,
        natural_query: str,
        schema_hint: Optional[str] = None,
        event: Optional[AstrMessageEvent] = None,
    ) -> Tuple[str, Optional[str]]:
        provider = self._get_provider(event)
        if not provider:
            return ("", "未找到可用的 AI 提供商，请先在插件配置中选择模型提供商")

        prompt = self._build_nl2sql_prompt(natural_query, schema_hint)
        try:
            response = await provider.text_chat(
                prompt=prompt,
                system_prompt="你是 PostgreSQL 专家，只返回可执行的 SELECT SQL，不要附带解释。",
            )
            sql = self._extract_sql(response)
            if not sql:
                return ("", "AI 未能生成有效的 SQL 语句")
            return (sql, None)
        except Exception as exc:
            logger.error(f"自然语言转 SQL 失败: {exc}")
            return ("", "转换失败，请检查日志")

    def _build_nl2sql_prompt(
        self, natural_query: str, schema_hint: Optional[str] = None
    ) -> str:
        prompt = (
            "请将用户的自然语言请求转换为 PostgreSQL SELECT 语句。\n"
            "要求：\n"
            "1. 只返回 SQL，不要解释。\n"
            "2. 只能生成 SELECT 查询。\n"
            "3. 使用标准 PostgreSQL 语法。\n"
            "4. 优先生成安全、清晰、可直接执行的语句。"
        )
        if schema_hint:
            prompt += f"\n\n数据库表结构：\n{schema_hint}"
        prompt += f"\n\n用户请求：{natural_query}\n\nSQL:"
        return prompt

    def _extract_sql(self, llm_response: LLMResponse) -> str:
        content = llm_response.completion_text if llm_response else ""

        code_block_matches = re.findall(
            r"```sql\s*(.*?)\s*```", content, re.DOTALL | re.IGNORECASE
        )
        if code_block_matches:
            return code_block_matches[0].strip()

        select_matches = re.findall(
            r"SELECT.*?(?:;|$)", content, re.DOTALL | re.IGNORECASE
        )
        if select_matches:
            return select_matches[0].strip().rstrip(";")

        return content.strip().rstrip(";")
