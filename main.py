from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
from typing import Optional

from db.pool import PostgresPool
from db.executor import SQLExecutor
from utils.formatter import ResultFormatter
from utils.permissions import PermissionChecker
from services.query_service import QueryService
from services.nlp_service import NLPService
from services.analysis_service import AnalysisService
from services.data_service import DataService


@register("astrbot_plugin_pgsql", "opencode", "功能强大的 PostgreSQL 数据库插件，支持 SQL 查询、自然语言查询和 AI 数据分析", "1.0.0")
class PostgreSQLPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.pool: Optional[PostgresPool] = None
        self.query_service: Optional[QueryService] = None
        self.nlp_service: Optional[NLPService] = None
        self.analysis_service: Optional[AnalysisService] = None
        self.data_service: Optional[DataService] = None

    async def initialize(self):
        """初始化插件"""
        logger.info("正在初始化 PostgreSQL 插件...")

        try:
            # 初始化连接池
            self.pool = PostgresPool(self.config)
            await self.pool.initialize()

            # 初始化 SQL 执行器
            executor = SQLExecutor(self.pool)

            # 初始化结果格式化器
            formatter = ResultFormatter(self.config.get('page_size', 20))

            # 初始化权限检查器
            perm_checker = PermissionChecker(self.config.get('admin_only_commands', []))

            # 初始化服务
            self.query_service = QueryService(executor, formatter, self.config)
            self.nlp_service = NLPService(self.context, self.config)
            self.analysis_service = AnalysisService(self.context, self.config)
            self.data_service = DataService(executor, self.pool, formatter, self.config)

            logger.info("PostgreSQL 插件初始化成功")
        except Exception as e:
            logger.error(f"PostgreSQL 插件初始化失败: {e}")
            raise

    async def terminate(self):
        """插件销毁"""
        logger.info("正在关闭 PostgreSQL 插件...")
        if self.pool:
            await self.pool.close()
        logger.info("PostgreSQL 插件已关闭")

    def _is_admin(self, event: AstrMessageEvent) -> bool:
        """检查用户是否为管理员"""
        try:
            return event.get_sender_info().role in ['admin', 'owner', 'superuser']
        except:
            return False

    @filter.command("sql query", "执行 SELECT 查询")
    async def sql_query(self, event: AstrMessageEvent):
        """
        执行 SELECT 查询
        用法: /sql query SELECT * FROM table_name
        """
        message_str = event.message_str
        # 提取查询语句
        if "query" in message_str:
            query = message_str.split("query", 1)[1].strip()
        else:
            yield event.plain_result("请提供查询语句。用法: /sql query SELECT * FROM table_name")
            return

        if not query:
            yield event.plain_result("查询语句不能为空")
            return

        is_admin = self._is_admin(event)

        result, error = await self.query_service.execute_select(query, is_admin=is_admin)

        if error:
            yield event.plain_result(f"错误: {error}")
        else:
            yield event.plain_result(result)

    @filter.command("sql execute", "执行 INSERT/UPDATE/DELETE 命令")
    async def sql_execute(self, event: AstrMessageEvent):
        """
        执行写入命令
        用法: /sql execute INSERT INTO table_name (column) VALUES (value)
        """
        message_str = event.message_str
        # 提取命令
        if "execute" in message_str:
            command = message_str.split("execute", 1)[1].strip()
        else:
            yield event.plain_result("请提供命令。用法: /sql execute INSERT INTO table_name (column) VALUES (value)")
            return

        if not command:
            yield event.plain_result("命令不能为空")
            return

        is_admin = self._is_admin(event)

        result, error = await self.query_service.execute_write(command, is_admin=is_admin)

        if error:
            yield event.plain_result(f"错误: {error}")
        else:
            yield event.plain_result(result)

    @filter.command("sql schema", "查看数据库表结构")
    async def sql_schema(self, event: AstrMessageEvent):
        """
        查看表结构
        用法: /sql schema [table_name]
        """
        message_str = event.message_str
        parts = message_str.split()

        table_name = None
        if len(parts) > 2:
            table_name = parts[2]

        result, error = await self.query_service.get_schema(table_name)

        if error:
            yield event.plain_result(f"错误: {error}")
        else:
            yield event.plain_result(result)

    @filter.command("sql ask", "自然语言转 SQL")
    async def sql_ask(self, event: AstrMessageEvent):
        """
        将自然语言转换为 SQL 并执行
        用法: /sql ask 查询所有用户
        """
        message_str = event.message_str
        # 提取自然语言查询
        if "ask" in message_str:
            natural_query = message_str.split("ask", 1)[1].strip()
        else:
            yield event.plain_result("请提供查询描述。用法: /sql ask 查询所有用户")
            return

        if not natural_query:
            yield event.plain_result("查询描述不能为空")
            return

        # 转换为 SQL
        sql, error = await self.nlp_service.text_to_sql(natural_query)

        if error:
            yield event.plain_result(f"错误: {error}")
            return

        yield event.plain_result(f"生成的 SQL: {sql}")

        # 执行 SQL
        result, error = await self.query_service.execute_select(sql)

        if error:
            yield event.plain_result(f"执行失败: {error}")
        else:
            yield event.plain_result(result)

    @filter.command("db create_table", "创建表")
    async def db_create_table(self, event: AstrMessageEvent):
        """
        创建表
        用法: /db create_table CREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT)
        """
        message_str = event.message_str
        # 提取表定义
        if "create_table" in message_str:
            table_def = message_str.split("create_table", 1)[1].strip()
        else:
            yield event.plain_result("请提供表定义。用法: /db create_table CREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT)")
            return

        if not table_def:
            yield event.plain_result("表定义不能为空")
            return

        is_admin = self._is_admin(event)

        result, error = await self.data_service.create_table(table_def, is_admin=is_admin)

        if error:
            yield event.plain_result(f"错误: {error}")
        else:
            yield event.plain_result(result)

    @filter.command("db drop_table", "删除表")
    async def db_drop_table(self, event: AstrMessageEvent):
        """
        删除表
        用法: /db drop_table table_name
        """
        message_str = event.message_str
        parts = message_str.split()

        if len(parts) < 3:
            yield event.plain_result("请提供表名。用法: /db drop_table table_name")
            return

        table_name = parts[2]
        is_admin = self._is_admin(event)

        result, error = await self.data_service.drop_table(table_name, is_admin=is_admin)

        if error:
            yield event.plain_result(f"错误: {error}")
        else:
            yield event.plain_result(result)

    @filter.command("db list_tables", "列出所有表")
    async def db_list_tables(self, event: AstrMessageEvent):
        """
        列出所有表
        用法: /db list_tables
        """
        result, error = await self.data_service.list_tables()

        if error:
            yield event.plain_result(f"错误: {error}")
        else:
            yield event.plain_result(result)

    @filter.command("db insert", "插入数据")
    async def db_insert(self, event: AstrMessageEvent):
        """
        插入数据
        用法: /db insert table_name {"column1": "value1", "column2": "value2"}
        """
        message_str = event.message_str
        parts = message_str.split()

        if len(parts) < 4:
            yield event.plain_result("请提供表名和数据。用法: /db insert table_name {'column1': 'value1', 'column2': 'value2'}")
            return

        table_name = parts[2]
        try:
            import json
            data_json = ' '.join(parts[3:])
            data = json.loads(data_json)
        except:
            yield event.plain_result("数据格式错误，请使用 JSON 格式")
            return

        is_admin = self._is_admin(event)

        result, error = await self.data_service.insert_data(table_name, data, is_admin=is_admin)

        if error:
            yield event.plain_result(f"错误: {error}")
        else:
            yield event.plain_result(result)

    @filter.command("db update", "更新数据")
    async def db_update(self, event: AstrMessageEvent):
        """
        更新数据
        用法: /db update table_name "condition" {"column1": "new_value"}
        """
        message_str = event.message_str
        parts = message_str.split()

        if len(parts) < 5:
            yield event.plain_result("请提供表名、条件和数据。用法: /db update table_name \"condition\" {'column1': 'new_value'}")
            return

        table_name = parts[2]
        condition = parts[3].strip('"\'')
        try:
            import json
            data_json = ' '.join(parts[4:])
            data = json.loads(data_json)
        except:
            yield event.plain_result("数据格式错误，请使用 JSON 格式")
            return

        is_admin = self._is_admin(event)

        result, error = await self.data_service.update_data(table_name, condition, data, is_admin=is_admin)

        if error:
            yield event.plain_result(f"错误: {error}")
        else:
            yield event.plain_result(result)

    @filter.command("db delete", "删除数据")
    async def db_delete(self, event: AstrMessageEvent):
        """
        删除数据
        用法: /db delete table_name "condition"
        """
        message_str = event.message_str
        parts = message_str.split()

        if len(parts) < 4:
            yield event.plain_result("请提供表名和条件。用法: /db delete table_name \"condition\"")
            return

        table_name = parts[2]
        condition = parts[3].strip('"\'')
        is_admin = self._is_admin(event)

        result, error = await self.data_service.delete_data(table_name, condition, is_admin=is_admin)

        if error:
            yield event.plain_result(f"错误: {error}")
        else:
            yield event.plain_result(result)

    @filter.command("db export", "导出表数据为 CSV")
    async def db_export(self, event: AstrMessageEvent):
        """
        导出表数据为 CSV
        用法: /db export table_name
        """
        message_str = event.message_str
        parts = message_str.split()

        if len(parts) < 3:
            yield event.plain_result("请提供表名。用法: /db export table_name")
            return

        table_name = parts[2]

        result, error = await self.data_service.export_to_csv(table_name)

        if error:
            yield event.plain_result(f"错误: {error}")
        else:
            yield event.plain_result(f"数据已导出到: {result}")

    @filter.command("analyze", "AI 数据分析")
    async def analyze(self, event: AstrMessageEvent):
        """
        对查询结果进行 AI 分析
        用法: /analyze <自然语言描述>
        """
        yield event.plain_result("此功能需要先执行查询，然后对结果进行分析。请使用 /sql query 先查询数据，然后提供数据描述。")

    @filter.command("analyze trends", "分析数据趋势")
    async def analyze_trends(self, event: AstrMessageEvent):
        """
        分析数据趋势
        用法: /analyze trends <table_name> <field>
        """
        message_str = event.message_str
        parts = message_str.split()

        if len(parts) < 4:
            yield event.plain_result("请提供表名和字段。用法: /analyze trends table_name field")
            return

        table_name = parts[2]
        field = parts[3]

        # 查询数据
        query = f"SELECT * FROM {table_name}"
        total_rows, results, error = await self.query_service.execute_select(query)

        if error:
            yield event.plain_result(f"查询失败: {error}")
            return

        if not results:
            yield event.plain_result("表中没有数据")
            return

        # 分析趋势
        result, error = await self.analysis_service.analyze_trends(results, field)

        if error:
            yield event.plain_result(f"分析失败: {error}")
        else:
            yield event.plain_result(result)

    @filter.command("analyze insights", "生成数据洞察")
    async def analyze_insights(self, event: AstrMessageEvent):
        """
        生成数据洞察
        用法: /analyze insights <table_name>
        """
        message_str = event.message_str
        parts = message_str.split()

        if len(parts) < 3:
            yield event.plain_result("请提供表名。用法: /analyze insights table_name")
            return

        table_name = parts[2]

        # 查询数据
        query = f"SELECT * FROM {table_name} LIMIT 100"
        total_rows, results, error = await self.query_service.execute_select(query)

        if error:
            yield event.plain_result(f"查询失败: {error}")
            return

        if not results:
            yield event.plain_result("表中没有数据")
            return

        # 生成洞察
        result, error = await self.analysis_service.generate_insights(table_name, results)

        if error:
            yield event.plain_result(f"生成洞察失败: {error}")
        else:
            yield event.plain_result(result)
