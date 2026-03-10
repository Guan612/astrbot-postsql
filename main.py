from __future__ import annotations

import json
from typing import Any, Optional

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register

from .db.executor import SQLExecutor
from .db.pool import PostgresPool
from .services.analysis_service import AnalysisService
from .services.data_service import DataService
from .services.nlp_service import NLPService
from .services.query_service import QueryService
from .utils.formatter import ResultFormatter


@register(
    "astrbot_postsql",
    "opencode",
    "功能强大的 PostgreSQL 数据库插件，支持 SQL 查询、自然语言转 SQL 和 AI 数据分析",
    "1.0.1",
)
class PostgreSQLPlugin(Star):
    def __init__(self, context: Context, config: Optional[dict[str, Any]] = None):
        super().__init__(context)
        self.config = config or context.get_config()
        self.pool: Optional[PostgresPool] = None
        self.executor: Optional[SQLExecutor] = None
        self.query_service: Optional[QueryService] = None
        self.nlp_service: Optional[NLPService] = None
        self.analysis_service: Optional[AnalysisService] = None
        self.data_service: Optional[DataService] = None

    async def initialize(self):
        logger.info("正在初始化 PostgreSQL 插件")
        self.pool = PostgresPool(self.config)
        await self.pool.initialize()

        self.executor = SQLExecutor(self.pool)
        formatter = ResultFormatter(
            page_size=self.config.get("page_size", 20),
            max_col_width=self.config.get("max_col_width", 50),
        )

        self.query_service = QueryService(self.executor, formatter, self.config)
        self.nlp_service = NLPService(self.context, self.config)
        self.analysis_service = AnalysisService(self.context, self.config)
        self.data_service = DataService(
            self.executor, self.pool, formatter, self.config
        )
        logger.info("PostgreSQL 插件初始化完成")

    async def terminate(self):
        logger.info("正在关闭 PostgreSQL 插件")
        if self.pool:
            await self.pool.close()
        logger.info("PostgreSQL 插件已关闭")

    def _is_admin(self, event: AstrMessageEvent) -> bool:
        try:
            role = event.get_sender_info().role
        except Exception:
            return False
        return role in {"admin", "owner", "superuser"}

    def _services_ready(self) -> bool:
        return all(
            [
                self.executor,
                self.query_service,
                self.nlp_service,
                self.analysis_service,
                self.data_service,
            ]
        )

    @filter.command("sql query", "执行 SELECT 查询")
    async def sql_query(self, event: AstrMessageEvent):
        if not self._services_ready():
            yield event.plain_result("插件尚未初始化完成")
            return
        message = event.message_str
        query = message.split("query", 1)[1].strip() if "query" in message else ""
        if not query:
            yield event.plain_result("请提供查询语句。用法: /sql query SELECT * FROM table_name")
            return
        result, error = await self.query_service.execute_select(
            query, is_admin=self._is_admin(event)
        )
        yield event.plain_result(f"错误: {error}" if error else result)

    @filter.command("sql execute", "执行 INSERT/UPDATE/DELETE 命令")
    async def sql_execute(self, event: AstrMessageEvent):
        if not self._services_ready():
            yield event.plain_result("插件尚未初始化完成")
            return
        message = event.message_str
        command = (
            message.split("execute", 1)[1].strip() if "execute" in message else ""
        )
        if not command:
            yield event.plain_result(
                "请提供命令。用法: /sql execute INSERT INTO table_name (column) VALUES (value)"
            )
            return
        result, error = await self.query_service.execute_write(
            command, is_admin=self._is_admin(event)
        )
        yield event.plain_result(f"错误: {error}" if error else result)

    @filter.command("sql schema", "查看数据库表结构")
    async def sql_schema(self, event: AstrMessageEvent):
        if not self._services_ready():
            yield event.plain_result("插件尚未初始化完成")
            return
        parts = event.message_str.split()
        table_name = parts[2] if len(parts) > 2 else None
        result, error = await self.query_service.get_schema(table_name)
        yield event.plain_result(f"错误: {error}" if error else result)

    @filter.command("sql ask", "自然语言转 SQL")
    async def sql_ask(self, event: AstrMessageEvent):
        if not self._services_ready():
            yield event.plain_result("插件尚未初始化完成")
            return
        message = event.message_str
        natural_query = message.split("ask", 1)[1].strip() if "ask" in message else ""
        if not natural_query:
            yield event.plain_result("请提供查询描述。用法: /sql ask 查询所有用户")
            return
        sql, error = await self.nlp_service.text_to_sql(natural_query, event=event)
        if error:
            yield event.plain_result(f"错误: {error}")
            return
        yield event.plain_result(f"生成的 SQL:\n{sql}")
        result, error = await self.query_service.execute_select(sql)
        yield event.plain_result(f"执行失败: {error}" if error else result)

    @filter.command("db create_table", "创建表")
    async def db_create_table(self, event: AstrMessageEvent):
        if not self._services_ready():
            yield event.plain_result("插件尚未初始化完成")
            return
        message = event.message_str
        table_def = (
            message.split("create_table", 1)[1].strip()
            if "create_table" in message
            else ""
        )
        if not table_def:
            yield event.plain_result(
                "请提供表定义。用法: /db create_table CREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT)"
            )
            return
        result, error = await self.data_service.create_table(
            table_def, is_admin=self._is_admin(event)
        )
        yield event.plain_result(f"错误: {error}" if error else result)

    @filter.command("db drop_table", "删除表")
    async def db_drop_table(self, event: AstrMessageEvent):
        if not self._services_ready():
            yield event.plain_result("插件尚未初始化完成")
            return
        parts = event.message_str.split()
        if len(parts) < 3:
            yield event.plain_result("请提供表名。用法: /db drop_table table_name")
            return
        result, error = await self.data_service.drop_table(
            parts[2], is_admin=self._is_admin(event)
        )
        yield event.plain_result(f"错误: {error}" if error else result)

    @filter.command("db list_tables", "列出所有表")
    async def db_list_tables(self, event: AstrMessageEvent):
        if not self._services_ready():
            yield event.plain_result("插件尚未初始化完成")
            return
        result, error = await self.data_service.list_tables()
        yield event.plain_result(f"错误: {error}" if error else result)

    @filter.command("db insert", "插入数据")
    async def db_insert(self, event: AstrMessageEvent):
        if not self._services_ready():
            yield event.plain_result("插件尚未初始化完成")
            return
        parts = event.message_str.split()
        if len(parts) < 4:
            yield event.plain_result(
                "请提供表名和 JSON 数据。用法: /db insert table_name {\"column1\": \"value1\"}"
            )
            return
        try:
            data = json.loads(" ".join(parts[3:]))
        except json.JSONDecodeError:
            yield event.plain_result("数据格式错误，请使用合法 JSON")
            return
        result, error = await self.data_service.insert_data(
            parts[2], data, is_admin=self._is_admin(event)
        )
        yield event.plain_result(f"错误: {error}" if error else result)

    @filter.command("db update", "更新数据")
    async def db_update(self, event: AstrMessageEvent):
        if not self._services_ready():
            yield event.plain_result("插件尚未初始化完成")
            return
        parts = event.message_str.split()
        if len(parts) < 5:
            yield event.plain_result(
                "请提供表名、条件和 JSON 数据。用法: /db update table_name \"condition\" {\"column1\": \"new_value\"}"
            )
            return
        try:
            data = json.loads(" ".join(parts[4:]))
        except json.JSONDecodeError:
            yield event.plain_result("数据格式错误，请使用合法 JSON")
            return
        result, error = await self.data_service.update_data(
            parts[2], parts[3].strip("\"'"), data, is_admin=self._is_admin(event)
        )
        yield event.plain_result(f"错误: {error}" if error else result)

    @filter.command("db delete", "删除数据")
    async def db_delete(self, event: AstrMessageEvent):
        if not self._services_ready():
            yield event.plain_result("插件尚未初始化完成")
            return
        parts = event.message_str.split()
        if len(parts) < 4:
            yield event.plain_result(
                "请提供表名和条件。用法: /db delete table_name \"condition\""
            )
            return
        result, error = await self.data_service.delete_data(
            parts[2], parts[3].strip("\"'"), is_admin=self._is_admin(event)
        )
        yield event.plain_result(f"错误: {error}" if error else result)

    @filter.command("db export", "导出表数据为 CSV")
    async def db_export(self, event: AstrMessageEvent):
        if not self._services_ready():
            yield event.plain_result("插件尚未初始化完成")
            return
        parts = event.message_str.split()
        if len(parts) < 3:
            yield event.plain_result("请提供表名。用法: /db export table_name")
            return
        result, error = await self.data_service.export_to_csv(parts[2])
        yield event.plain_result(f"错误: {error}" if error else f"数据已导出到: {result}")

    @filter.command("analyze", "AI 数据分析说明")
    async def analyze(self, event: AstrMessageEvent):
        yield event.plain_result(
            "请使用 /analyze trends <table_name> <field> 分析趋势，或使用 /analyze insights <table_name> 生成洞察。"
        )

    @filter.command("analyze trends", "分析数据趋势")
    async def analyze_trends(self, event: AstrMessageEvent):
        if not self._services_ready():
            yield event.plain_result("插件尚未初始化完成")
            return
        parts = event.message_str.split()
        if len(parts) < 4:
            yield event.plain_result(
                "请提供表名和字段。用法: /analyze trends table_name field"
            )
            return
        _, results, error = await self.executor.execute_query(f"SELECT * FROM {parts[2]}")
        if error:
            yield event.plain_result(f"查询失败: {error}")
            return
        if not results:
            yield event.plain_result("表中没有数据")
            return
        result, error = await self.analysis_service.analyze_trends(
            results, parts[3], event=event
        )
        yield event.plain_result(f"分析失败: {error}" if error else result)

    @filter.command("analyze insights", "生成数据洞察")
    async def analyze_insights(self, event: AstrMessageEvent):
        if not self._services_ready():
            yield event.plain_result("插件尚未初始化完成")
            return
        parts = event.message_str.split()
        if len(parts) < 3:
            yield event.plain_result("请提供表名。用法: /analyze insights table_name")
            return
        table_name = parts[2]
        _, results, error = await self.executor.execute_query(
            f"SELECT * FROM {table_name} LIMIT 100"
        )
        if error:
            yield event.plain_result(f"查询失败: {error}")
            return
        if not results:
            yield event.plain_result("表中没有数据")
            return
        result, error = await self.analysis_service.generate_insights(
            table_name, results, event=event
        )
        yield event.plain_result(f"生成洞察失败: {error}" if error else result)
