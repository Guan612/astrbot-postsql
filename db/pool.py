from typing import Any, List, Optional

import asyncpg
from astrbot.api import logger


class PostgresPool:
    def __init__(self, config: dict):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None

    async def initialize(self) -> None:
        if self.pool is not None:
            return
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
        except Exception as exc:
            self.pool = None
            logger.error(f"PostgreSQL 连接池初始化失败: {exc}")
            raise

    async def ensure_initialized(self) -> None:
        if self.pool is None:
            await self.initialize()

    async def close(self) -> None:
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("PostgreSQL 连接池已关闭")

    async def get_connection(self) -> asyncpg.Connection:
        await self.ensure_initialized()
        return await self.pool.acquire()

    async def release_connection(self, conn: Optional[asyncpg.Connection]) -> None:
        if conn is None:
            logger.warning("尝试释放空连接")
            return
        if not self.pool:
            logger.warning("尝试释放连接，但连接池尚未初始化")
            return
        try:
            await self.pool.release(conn)
        except Exception as exc:
            logger.error(f"释放连接失败: {exc}")

    async def execute(self, query: str, *args) -> str:
        await self.ensure_initialized()
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        await self.ensure_initialized()
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        await self.ensure_initialized()
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args) -> Any:
        await self.ensure_initialized()
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)
