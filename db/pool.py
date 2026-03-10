import asyncpg
from typing import Optional, List, Any
from astrbot.api import logger


class PostgresPool:
    def __init__(self, config: dict):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None

    async def initialize(self) -> None:
        """初始化连接池"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.get("db_host", "localhost"),
                port=self.config.get("db_port", 5432),
                database=self.config.get("db_name", "postgres"),
                user=self.config.get("db_user", "postgres"),
                password=self.config.get("db_password", ""),
                min_size=self.config.get("pool_min_size", 2),
                max_size=self.config.get("pool_max_size", 10),
                command_timeout=self.config.get("pool_timeout", 30),
            )
            logger.info("PostgreSQL 连接池初始化成功")
        except Exception as e:
            logger.error(f"PostgreSQL 连接池初始化失败: {e}")
            raise

    async def close(self) -> None:
        """关闭连接池"""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("PostgreSQL 连接池已关闭")

    async def get_connection(self) -> asyncpg.Connection:
        """获取数据库连接"""
        if not self.pool:
            raise RuntimeError("连接池未初始化")
        return await self.pool.acquire()

    async def release_connection(self, conn: Optional[asyncpg.Connection]) -> None:
        """释放数据库连接"""
        if conn is None:
            logger.warning("尝试释放空连接")
            return
        if not self.pool:
            logger.warning("尝试释放连接但连接池未初始化")
            return
        try:
            await self.pool.release(conn)
        except Exception as e:
            logger.error(f"释放连接失败: {e}")

    async def execute(self, query: str, *args) -> str:
        """执行 SQL 命令"""
        if not self.pool:
            raise RuntimeError("连接池未初始化")
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        """执行查询并返回所有结果"""
        if not self.pool:
            raise RuntimeError("连接池未初始化")
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """执行查询并返回单行结果"""
        if not self.pool:
            raise RuntimeError("连接池未初始化")
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args) -> Any:
        """执行查询并返回单个值"""
        if not self.pool:
            raise RuntimeError("连接池未初始化")
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)
