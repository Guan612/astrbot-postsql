import time
from typing import Any, Dict, List, Optional, Tuple

from astrbot.api import logger

from .pool import PostgresPool


class SQLExecutor:
    def __init__(self, pool: PostgresPool):
        self.pool = pool

    async def execute_query(
        self, query: str, params: Optional[tuple] = None
    ) -> Tuple[int, List[Dict[str, Any]], Optional[str]]:
        start_time = time.time()
        try:
            rows = (
                await self.pool.fetch(query, *params)
                if params
                else await self.pool.fetch(query)
            )
            elapsed = time.time() - start_time
            results = [dict(row) for row in rows]
            logger.info(f"查询执行成功: {query[:80]}... 耗时: {elapsed:.2f}s")
            return (len(results), results, None)
        except Exception as exc:
            elapsed = time.time() - start_time
            logger.error(f"查询执行失败: {exc} 耗时: {elapsed:.2f}s")
            return (0, [], str(exc))

    async def execute_command(
        self, command: str, params: Optional[tuple] = None
    ) -> Tuple[str, Optional[str]]:
        start_time = time.time()
        try:
            result = (
                await self.pool.execute(command, *params)
                if params
                else await self.pool.execute(command)
            )
            elapsed = time.time() - start_time
            logger.info(f"命令执行成功: {command[:80]}... 耗时: {elapsed:.2f}s")
            return (result, None)
        except Exception as exc:
            elapsed = time.time() - start_time
            logger.error(f"命令执行失败: {exc} 耗时: {elapsed:.2f}s")
            return ("", str(exc))

    async def get_schema(
        self, table_name: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        try:
            if table_name:
                query = """
                    SELECT table_name, column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = $1
                    ORDER BY ordinal_position
                """
                columns = await self.pool.fetch(query, table_name)
                return ([dict(col) for col in columns], None)

            table_query = """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """
            tables = await self.pool.fetch(table_query)

            all_columns: List[Dict[str, Any]] = []
            column_query = """
                SELECT table_name, column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = $1
                ORDER BY ordinal_position
            """
            for table in tables:
                columns = await self.pool.fetch(column_query, table["table_name"])
                all_columns.extend(dict(col) for col in columns)

            return (all_columns, None)
        except Exception as exc:
            logger.error(f"获取表结构失败: {exc}")
            return ([], str(exc))
