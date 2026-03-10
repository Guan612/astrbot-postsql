from typing import Any, Dict, Optional, Tuple

from astrbot.api import logger

from ..db.executor import SQLExecutor
from ..db.pool import PostgresPool
from ..utils.formatter import ResultFormatter
from ..utils.permissions import PermissionChecker


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
        if not is_admin and self.perm_checker.is_admin_command("create_table"):
            return ("", "此命令需要管理员权限")
        if not table_definition.strip().upper().startswith("CREATE TABLE"):
            return ("", "请提供有效的 CREATE TABLE 语句")

        _, error = await self.executor.execute_command(table_definition)
        if error:
            logger.error(f"创建表失败: {error}")
            return ("", "创建表失败，请检查日志")
        return ("表创建成功", None)

    async def drop_table(
        self, table_name: str, is_admin: bool = False
    ) -> Tuple[str, Optional[str]]:
        if not is_admin and self.perm_checker.is_admin_command("drop_table"):
            return ("", "此命令需要管理员权限")
        if not table_name.strip():
            return ("", "请提供有效的表名")

        _, error = await self.executor.execute_command(
            f"DROP TABLE IF EXISTS {table_name}"
        )
        if error:
            logger.error(f"删除表失败: {error}")
            return ("", "删除表失败，请检查日志")
        return (f"表 {table_name} 删除成功", None)

    async def list_tables(self) -> Tuple[str, Optional[str]]:
        schema, error = await self.executor.get_schema()
        if error:
            logger.error(f"获取表列表失败: {error}")
            return ("", "获取表列表失败，请检查日志")

        tables = sorted({col.get("table_name", "unknown") for col in schema})
        if not tables:
            return ("数据库中没有表", None)
        return ("数据库表列表:\n" + "\n".join(f"- {table}" for table in tables), None)

    async def insert_data(
        self, table_name: str, data: Dict[str, Any], is_admin: bool = False
    ) -> Tuple[str, Optional[str]]:
        if not is_admin and self.perm_checker.is_admin_command("insert"):
            return ("", "此命令需要管理员权限")

        columns = list(data.keys())
        values = list(data.values())
        placeholders = ", ".join(f"${i + 1}" for i in range(len(values)))
        query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"

        _, error = await self.executor.execute_command(query, tuple(values))
        if error:
            logger.error(f"插入数据失败: {error}")
            return ("", "插入数据失败，请检查日志")
        return ("数据插入成功", None)

    async def update_data(
        self,
        table_name: str,
        condition: str,
        data: Dict[str, Any],
        is_admin: bool = False,
    ) -> Tuple[str, Optional[str]]:
        if not is_admin and self.perm_checker.is_admin_command("update"):
            return ("", "此命令需要管理员权限")

        set_clause = ", ".join(f"{key} = ${i + 1}" for i, key in enumerate(data.keys()))
        query = f"UPDATE {table_name} SET {set_clause} WHERE {condition}"

        _, error = await self.executor.execute_command(query, tuple(data.values()))
        if error:
            logger.error(f"更新数据失败: {error}")
            return ("", "更新数据失败，请检查日志")
        return ("数据更新成功", None)

    async def delete_data(
        self, table_name: str, condition: str, is_admin: bool = False
    ) -> Tuple[str, Optional[str]]:
        if not is_admin and self.perm_checker.is_admin_command("delete"):
            return ("", "此命令需要管理员权限")

        _, error = await self.executor.execute_command(
            f"DELETE FROM {table_name} WHERE {condition}"
        )
        if error:
            logger.error(f"删除数据失败: {error}")
            return ("", "删除数据失败，请检查日志")
        return ("数据删除成功", None)

    async def export_to_csv(self, table_name: str) -> Tuple[str, Optional[str]]:
        _, results, error = await self.executor.execute_query(f"SELECT * FROM {table_name}")
        if error:
            logger.error(f"导出数据失败: {error}")
            return ("", "导出数据失败，请检查日志")
        if not results:
            return ("", "表中没有数据")

        import csv
        from astrbot.core.utils.astrbot_path import get_astrbot_data_path

        plugin_data_path = get_astrbot_data_path() / "plugin_data" / "astrbot_postsql"
        plugin_data_path.mkdir(parents=True, exist_ok=True)
        csv_file = plugin_data_path / f"{table_name}_export.csv"

        try:
            with open(csv_file, "w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)
            return (str(csv_file), None)
        except Exception as exc:
            logger.error(f"写入 CSV 文件失败: {exc}")
            return ("", "导出失败，请检查日志")
