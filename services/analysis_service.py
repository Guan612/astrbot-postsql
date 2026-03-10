from typing import Tuple, Optional, List, Dict, Any
from astrbot.api import logger
from astrbot.api.provider import LLMResponse
from astrbot.api import AstrBotContext


class AnalysisService:
    def __init__(self, context: AstrBotContext, config: dict):
        self.context = context
        self.config = config
        self.ai_provider = config.get("ai_provider", "")

    async def analyze_data(
        self, data: List[Dict[str, Any]], description: str = ""
    ) -> Tuple[str, Optional[str]]:
        """
        使用 AI 分析数据

        Args:
            data: 要分析的数据
            description: 数据描述

        Returns:
            Tuple[str, Optional[str]]: (分析结果, 错误信息)
        """
        if not self.ai_provider:
            return ("", "未配置 AI 提供商，请先在插件配置中选择 AI 模型")

        # 格式化数据
        data_str = self._format_data(data)

        # 构建提示词
        prompt = f"""你是一个数据分析专家。请分析以下数据并给出洞察。

数据描述：{description}

数据：
{data_str}

请提供：
1. 数据概览
2. 关键发现
3. 趋势分析（如果适用）
4. 建议和洞察
"""

        try:
            # 调用 AI 模型
            llm_req = self.context.use_llm_sync(prompt)

            return (llm_req.content, None)
        except Exception as e:
            logger.error(f"数据分析失败: {e}")
            return ("", f"分析失败，请检查日志")

    async def analyze_trends(
        self, data: List[Dict[str, Any]], field: str
    ) -> Tuple[str, Optional[str]]:
        """
        分析数据趋势

        Args:
            data: 要分析的数据
            field: 要分析的字段

        Returns:
            Tuple[str, Optional[str]]: (趋势分析结果, 错误信息)
        """
        if not self.ai_provider:
            return ("", "未配置 AI 提供商，请先在插件配置中选择 AI 模型")

        # 提取字段数据
        values = [str(row.get(field, "")) for row in data if row.get(field) is not None]

        # 构建提示词
        prompt = f"""你是一个数据分析专家。请分析以下数据的趋势。

字段：{field}
数据：
{", ".join(values[:100])}

请提供：
1. 数据趋势分析
2. 峰值和谷值
3. 周期性或模式（如果适用）
4. 预测和建议
"""

        try:
            # 调用 AI 模型
            llm_req = self.context.use_llm_sync(prompt)

            return (llm_req.content, None)
        except Exception as e:
            logger.error(f"趋势分析失败: {e}")
            return ("", f"分析失败，请检查日志")

    async def generate_insights(
        self, table_name: str, sample_data: List[Dict[str, Any]]
    ) -> Tuple[str, Optional[str]]:
        """
        生成数据洞察

        Args:
            table_name: 表名
            sample_data: 示例数据

        Returns:
            Tuple[str, Optional[str]]: (洞察结果, 错误信息)
        """
        if not self.ai_provider:
            return ("", "未配置 AI 提供商，请先在插件配置中选择 AI 模型")

        # 格式化数据
        data_str = self._format_data(sample_data[:20])

        # 构建提示词
        prompt = f"""你是一个数据分析专家。请对以下表的数据进行深入分析。

表名：{table_name}

示例数据：
{data_str}

请提供：
1. 数据质量评估
2. 潜在的数据质量问题
3. 数据特征分析
4. 可能的优化建议
5. 可视化建议（如果适用）
"""

        try:
            # 调用 AI 模型
            llm_req = self.context.use_llm_sync(prompt)

            return (llm_req.content, None)
        except Exception as e:
            logger.error(f"生成洞察失败: {e}")
            return ("", f"生成洞察失败，请检查日志")

    def _format_data(self, data: List[Dict[str, Any]]) -> str:
        """
        格式化数据为字符串
        """
        if not data:
            return "无数据"

        # 获取列名
        columns = list(data[0].keys())

        # 构建表格
        lines = []
        header = " | ".join(columns)
        lines.append(header)
        lines.append("-" * len(header))

        for row in data:
            values = [str(row.get(col, "")) for col in columns]
            lines.append(" | ".join(values))

        return "\n".join(lines)
