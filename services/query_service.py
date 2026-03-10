from typing import Optional, Tuple

from astrbot.api import logger

from ..db.executor import SQLExecutor
from ..utils.formatter import ResultFormatter
from ..utils.permissions import PermissionChecker


class QueryService:
    def __init__(self, executor: SQLExecutor, formatter: ResultFormatter, config: dict):
        self.executor = executor
        self.formatter = formatter
        self.config = config
        self.perm_checker = PermissionChecker(config.get("admin_only_commands", []))

    async def execute_select(
        self, query: str, page: int = 1, is_admin: bool = False
    ) -> Tuple[str, Optional[str]]:
        if not query.strip().upper().startswith("SELECT"):
            return ("", "只允许执行 SELECT 查询")

        _, results, error = await self.executor.execute_query(query)
        if error:
            logger.error(f"查询失败: {error}")
            return ("", "查询失败，请检查日志或联系管理员")
        if not results:
            return ("查询结果为空", None)

        max_rows = self.config.get("max_rows", 1000)
        results = self.formatter.truncate_results(results, max_rows)
        self.formatter.page_size = self.config.get("page_size", 20)
        return (self.formatter.format_table(results, page), None)

    async def execute_write(
        self, command: str, is_admin: bool = False
    ) -> Tuple[str, Optional[str]]:
        if not is_admin and self.perm_checker.is_admin_command("execute"):
            return ("", "此命令需要管理员权限")
        if self.perm_checker.is_dangerous_command(command):
            return ("", "检测到危险操作，请谨慎执行")

        result, error = await self.executor.execute_command(command)
        if error:
            logger.error(f"命令执行失败: {error}")
            return ("", "命令执行失败，请检查日志或联系管理员")
        return (f"执行成功: {result}", None)

    async def get_schema(
        self, table_name: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        schema, error = await self.executor.get_schema(table_name)
        if error:
            logger.error(f"获取表结构失败: {error}")
            return ("", "获取表结构失败，请检查日志")
        return (self.formatter.format_schema(schema, table_name), None)
