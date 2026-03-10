from typing import Tuple, Optional
from astrbot.api import logger
from astrbot.api.provider import LLMResponse
from astrbot.api import AstrBotContext


class NLPService:
    def __init__(self, context: AstrBotContext, config: dict):
        self.context = context
        self.config = config
        self.ai_provider = config.get('ai_provider', '')

    async def text_to_sql(self, natural_query: str, schema_hint: Optional[str] = None) -> Tuple[str, Optional[str]]:
        """
        将自然语言转换为 SQL

        Args:
            natural_query: 自然语言查询
            schema_hint: 可选，表结构提示

        Returns:
            Tuple[str, Optional[str]]: (SQL语句, 错误信息)
        """
        if not self.ai_provider:
            return ("", "未配置 AI 提供商，请先在插件配置中选择 AI 模型")

        # 构建提示词
        prompt = self._build_nl2sql_prompt(natural_query, schema_hint)

        try:
            # 调用 AI 模型
            llm_req = self.context.use_llm_sync(prompt)

            # 提取 SQL 语句
            sql = self._extract_sql(llm_req)

            if not sql:
                return ("", "AI 未能生成有效的 SQL 语句")

            return (sql, None)
        except Exception as e:
            logger.error(f"自然语言转 SQL 失败: {e}")
            return ("", f"转换失败，请检查日志")

    def _build_nl2sql_prompt(self, natural_query: str, schema_hint: Optional[str] = None) -> str:
        """
        构建自然语言转 SQL 的提示词
        """
        prompt = """你是一个 SQL 专家，需要将用户的自然语言查询转换为 PostgreSQL SQL 语句。

请遵循以下规则：
1. 只返回 SQL 语句，不要包含任何解释或其他文字
2. 使用标准的 PostgreSQL 语法
3. 确保生成的 SQL 语句安全，避免 SQL 注入
4. 如果查询需要多个表，请使用适当的 JOIN
5. 只生成 SELECT 查询，不要生成 INSERT/UPDATE/DELETE
"""

        if schema_hint:
            prompt += f"\n\n数据库表结构：\n{schema_hint}\n"

        prompt += f"\n\n用户查询：{natural_query}\n\nSQL："

        return prompt

    def _extract_sql(self, llm_response: LLMResponse) -> str:
        """
        从 AI 响应中提取 SQL 语句
        """
        content = llm_response.content if llm_response else ""

        # 尝试提取 SQL 语句
        import re

        # 查找 SQL 代码块
        sql_pattern = r'```sql\s*(.*?)\s*```'
        matches = re.findall(sql_pattern, content, re.DOTALL | re.IGNORECASE)

        if matches:
            return matches[0].strip()

        # 如果没有代码块，尝试提取 SELECT 语句
        select_pattern = r'SELECT.*?(?=\n\n|$)'
        matches = re.findall(select_pattern, content, re.DOTALL | re.IGNORECASE)

        if matches:
            return matches[0].strip()

        return content.strip()
