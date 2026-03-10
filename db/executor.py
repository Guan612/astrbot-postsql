import time
from typing import Tuple, Optional, List, Dict, Any
from astrbot.api import logger
from .pool import PostgresPool


class SQLExecutor:
    def __init__(self, pool: PostgresPool):
        self.pool = pool

    async def execute_query(
        self, query: str, params: Optional[tuple] = None
    ) -> Tuple[int, List[Dict[str, Any]], Optional[str]]:
        """
        执行 SELECT 查询

        Returns:
            Tuple[int, List[Dict], Optional[str]]: (总行数, 结果列表, 错误信息)
        """
        start_time = time.time()

        try:
            rows = (
                await self.pool.fetch(query, *params)
                if params
                else await self.pool.fetch(query)
            )
            elapsed = time.time() - start_time

            results = [dict(row) for row in rows]
            logger.info(f"查询执行成功: {query[:50]}... 耗时: {elapsed:.2f}s")

            return (len(results), results, None)
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"查询执行失败: {e} 耗时: {elapsed:.2f}s")
            return (0, [], str(e))

    async def execute_command(
        self, command: str, params: Optional[tuple] = None
    ) -> Tuple[str, Optional[str]]:
        """
        执行 INSERT/UPDATE/DELETE 命令

        Returns:
            Tuple[str, Optional[str]]: (执行结果/影响行数, 错误信息)
        """
        start_time = time.time()

        try:
            result = (
                await self.pool.execute(command, *params)
                if params
                else await self.pool.execute(command)
            )
            elapsed = time.time() - start_time
            logger.info(f"命令执行成功: {command[:50]}... 耗时: {elapsed:.2f}s")
            return (result, None)
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"命令执行失败: {e} 耗时: {elapsed:.2f}s")
            return ("", str(e))

    async def get_schema(
        self, table_name: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        获取数据库表结构

        Args:
            table_name: 可选，指定表名

        Returns:
            Tuple[List[Dict], Optional[str]]: (表结构列表, 错误信息)
        """
        try:
            if table_name:
                query = """
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = $1
                    ORDER BY ordinal_position
                """
                columns = await self.pool.fetch(query, table_name)
            else:
                query = """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """
                tables = await self.pool.fetch(query)

                columns = []
                for table in tables:
                    column_query = """
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns
                        WHERE table_name = $1
                        ORDER BY ordinal_position
                    """
                    cols = await self.pool.fetch(column_query, table["table_name"])
                    columns.extend([dict(col) for col in cols])

            return ([dict(col) for col in columns], None)
        except Exception as e:
            logger.error(f"获取表结构失败: {e}")
            return ([], str(e))
