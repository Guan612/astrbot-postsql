from typing import Tuple, List, Dict, Any, Optional
from astrbot.api import logger

try:
    from ..db.executor import SQLExecutor
    from ..utils.formatter import ResultFormatter
    from ..utils.permissions import PermissionChecker
except ImportError:
    from db.executor import SQLExecutor
    from utils.formatter import ResultFormatter
    from utils.permissions import PermissionChecker


class QueryService:
    def __init__(self, executor: SQLExecutor, formatter: ResultFormatter, config: dict):
        self.executor = executor
        self.formatter = formatter
        self.config = config
        self.perm_checker = PermissionChecker(config.get("admin_only_commands", []))

    async def execute_select(
        self, query: str, page: int = 1, is_admin: bool = False
    ) -> Tuple[str, Optional[str]]:
        """
        执行 SELECT 查询

        Args:
            query: SQL 查询语句
            page: 页码
            is_admin: 是否为管理员

        Returns:
            Tuple[str, Optional[str]]: (结果字符串, 错误信息)
        """
        # 检查是否为 SELECT 查询
        if not query.strip().upper().startswith("SELECT"):
            return ("", "只允许执行 SELECT 查询")

        # 执行查询
        total_rows, results, error = await self.executor.execute_query(query)

        if error:
            logger.error(f"查询失败: {error}")
            return ("", f"查询失败，请检查日志或联系管理员")

        if not results:
            return ("查询结果为空", None)

        # 限制最大行数
        max_rows = self.config.get("max_rows", 1000)
        results = self.formatter.truncate_results(results, max_rows)

        # 格式化结果
        page_size = self.config.get("page_size", 20)
        self.formatter.page_size = page_size
        result_str = self.formatter.format_table(results, page)

        return (result_str, None)

    async def execute_write(
        self, command: str, is_admin: bool = False
    ) -> Tuple[str, Optional[str]]:
        """
        执行写入命令（INSERT/UPDATE/DELETE）

        Args:
            command: SQL 命令
            is_admin: 是否为管理员

        Returns:
            Tuple[str, Optional[str]]: (结果字符串, 错误信息)
        """
        # 检查权限
        if not is_admin and self.perm_checker.is_admin_command("execute"):
            return ("", "此命令需要管理员权限")

        # 检查危险命令
        if self.perm_checker.is_dangerous_command(command):
            return ("", "检测到危险操作，请谨慎执行")

        # 执行命令
        result, error = await self.executor.execute_command(command)

        if error:
            logger.error(f"命令执行失败: {error}")
            return ("", f"命令执行失败，请检查日志或联系管理员")

        return (f"执行成功: {result}", None)

    async def get_schema(
        self, table_name: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """
        获取表结构

        Args:
            table_name: 可选，指定表名

        Returns:
            Tuple[str, Optional[str]]: (表结构字符串, 错误信息)
        """
        schema, error = await self.executor.get_schema(table_name)

        if error:
            logger.error(f"获取表结构失败: {error}")
            return ("", f"获取表结构失败，请检查日志")

        result_str = self.formatter.format_schema(schema, table_name)
        return (result_str, None)
