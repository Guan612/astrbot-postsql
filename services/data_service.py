from typing import Tuple, Optional, List, Dict, Any
from astrbot.api import logger
from db.executor import SQLExecutor
from db.pool import PostgresPool
from utils.permissions import PermissionChecker
from utils.formatter import ResultFormatter


class DataService:
    def __init__(
        self,
        executor: SQLExecutor,
        pool: PostgresPool,
        formatter: ResultFormatter,
        config: dict,
    ):
        self.executor = executor
        self.pool = pool
        self.formatter = formatter
        self.config = config
        self.perm_checker = PermissionChecker(config.get("admin_only_commands", []))

    async def create_table(
        self, table_definition: str, is_admin: bool = False
    ) -> Tuple[str, Optional[str]]:
        """
        创建表

        Args:
            table_definition: 表定义（CREATE TABLE 语句）
            is_admin: 是否为管理员

        Returns:
            Tuple[str, Optional[str]]: (结果字符串, 错误信息)
        """
        # 检查权限
        if not is_admin and self.perm_checker.is_admin_command("create_table"):
            return ("", "此命令需要管理员权限")

        # 验证是否为 CREATE TABLE 语句
        if not table_definition.strip().upper().startswith("CREATE TABLE"):
            return ("", "请提供有效的 CREATE TABLE 语句")

        # 执行命令
        result, error = await self.executor.execute_command(table_definition)

        if error:
            logger.error(f"创建表失败: {error}")
            return ("", f"创建表失败，请检查日志")

        return ("表创建成功", None)

    async def drop_table(
        self, table_name: str, is_admin: bool = False
    ) -> Tuple[str, Optional[str]]:
        """
        删除表

        Args:
            table_name: 表名
            is_admin: 是否为管理员

        Returns:
            Tuple[str, Optional[str]]: (结果字符串, 错误信息)
        """
        # 检查权限
        if not is_admin and self.perm_checker.is_admin_command("drop_table"):
            return ("", "此命令需要管理员权限")

        # 验证表名
        if not table_name or not table_name.strip():
            return ("", "请提供有效的表名")

        # 执行命令
        command = f"DROP TABLE IF EXISTS {table_name}"
        result, error = await self.executor.execute_command(command)

        if error:
            logger.error(f"删除表失败: {error}")
            return ("", f"删除表失败，请检查日志")

        return (f"表 {table_name} 删除成功", None)

    async def list_tables(self) -> Tuple[str, Optional[str]]:
        """
        列出所有表

        Returns:
            Tuple[str, Optional[str]]: (表列表字符串, 错误信息)
        """
        schema, error = await self.executor.get_schema()

        if error:
            logger.error(f"获取表列表失败: {error}")
            return ("", f"获取表列表失败，请检查日志")

        # 提取表名
        tables = {}
        for col in schema:
            table = col.get("table_name", "unknown")
            if table not in tables:
                tables[table] = []

        if not tables:
            return ("数据库中没有表", None)

        # 格式化结果
        lines = ["数据库表列表："]
        for table in sorted(tables.keys()):
            lines.append(f"  - {table}")

        return ("\n".join(lines), None)

    async def insert_data(
        self, table_name: str, data: Dict[str, Any], is_admin: bool = False
    ) -> Tuple[str, Optional[str]]:
        """
        插入数据

        Args:
            table_name: 表名
            data: 要插入的数据（字典格式）
            is_admin: 是否为管理员

        Returns:
            Tuple[str, Optional[str]]: (结果字符串, 错误信息)
        """
        # 检查权限
        if not is_admin and self.perm_checker.is_admin_command("insert"):
            return ("", "此命令需要管理员权限")

        # 构建插入语句
        columns = list(data.keys())
        values = list(data.values())
        placeholders = ", ".join(["$" + str(i + 1) for i in range(len(values))])
        columns_str = ", ".join(columns)

        query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"

        # 执行命令
        result, error = await self.executor.execute_command(query, tuple(values))

        if error:
            logger.error(f"插入数据失败: {error}")
            return ("", f"插入数据失败，请检查日志")

        return ("数据插入成功", None)

    async def update_data(
        self,
        table_name: str,
        condition: str,
        data: Dict[str, Any],
        is_admin: bool = False,
    ) -> Tuple[str, Optional[str]]:
        """
        更新数据

        Args:
            table_name: 表名
            condition: WHERE 条件
            data: 要更新的数据（字典格式）
            is_admin: 是否为管理员

        Returns:
            Tuple[str, Optional[str]]: (结果字符串, 错误信息)
        """
        # 检查权限
        if not is_admin and self.perm_checker.is_admin_command("update"):
            return ("", "此命令需要管理员权限")

        # 构建更新语句
        set_clause = ", ".join(
            [f"{key} = ${i + 1}" for i, key in enumerate(data.keys())]
        )
        query = f"UPDATE {table_name} SET {set_clause} WHERE {condition}"

        # 执行命令
        values = list(data.values())
        result, error = await self.executor.execute_command(query, tuple(values))

        if error:
            logger.error(f"更新数据失败: {error}")
            return ("", f"更新数据失败，请检查日志")

        return ("数据更新成功", None)

    async def delete_data(
        self, table_name: str, condition: str, is_admin: bool = False
    ) -> Tuple[str, Optional[str]]:
        """
        删除数据

        Args:
            table_name: 表名
            condition: WHERE 条件
            is_admin: 是否为管理员

        Returns:
            Tuple[str, Optional[str]]: (结果字符串, 错误信息)
        """
        # 检查权限
        if not is_admin and self.perm_checker.is_admin_command("delete"):
            return ("", "此命令需要管理员权限")

        # 构建删除语句
        query = f"DELETE FROM {table_name} WHERE {condition}"

        # 执行命令
        result, error = await self.executor.execute_command(query)

        if error:
            logger.error(f"删除数据失败: {error}")
            return ("", f"删除数据失败，请检查日志")

        return ("数据删除成功", None)

    async def export_to_csv(self, table_name: str) -> Tuple[str, Optional[str]]:
        """
        导出表数据为 CSV

        Args:
            table_name: 表名

        Returns:
            Tuple[str, Optional[str]]: (CSV 文件路径, 错误信息)
        """
        # 查询表数据
        query = f"SELECT * FROM {table_name}"
        total_rows, results, error = await self.executor.execute_query(query)

        if error:
            logger.error(f"导出数据失败: {error}")
            return ("", f"导出数据失败，请检查日志")

        if not results:
            return ("", "表中没有数据")

        # 生成 CSV 内容
        import csv
        import io
        from astrbot.core.utils.astrbot_path import get_astrbot_data_path

        # 获取插件数据目录
        plugin_data_path = (
            get_astrbot_data_path() / "plugin_data" / "astrbot_plugin_pgsql"
        )
        plugin_data_path.mkdir(parents=True, exist_ok=True)

        # 创建 CSV 文件
        csv_file = plugin_data_path / f"{table_name}_export.csv"

        try:
            with open(csv_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)

            return (str(csv_file), None)
        except Exception as e:
            logger.error(f"写入 CSV 文件失败: {e}")
            return ("", f"导出失败，请检查日志")
