from typing import List, Dict, Any, Optional


class ResultFormatter:
    def __init__(self, page_size: int = 20, max_col_width: int = 50):
        self.page_size = page_size
        self.max_col_width = max_col_width

    def format_table(self, results: List[Dict[str, Any]], page: int = 1) -> str:
        """
        格式化查询结果为表格

        Args:
            results: 查询结果列表
            page: 页码（从 1 开始）

        Returns:
            格式化的表格字符串
        """
        if not results:
            return "查询结果为空"

        # 计算分页
        total_rows = len(results)
        total_pages = (total_rows + self.page_size - 1) // self.page_size
        page = max(1, min(page, total_pages))
        start_idx = (page - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, total_rows)
        page_results = results[start_idx:end_idx]

        if not page_results:
            return "当前页无数据"

        # 获取列名
        columns = list(page_results[0].keys())

        # 计算每列的最大宽度
        col_widths = {}
        for col in columns:
            max_len = len(col)
            for row in page_results:
                val = str(row[col]) if row[col] is not None else "NULL"
                max_len = max(max_len, len(val))
            col_widths[col] = min(max_len, self.max_col_width)

        # 构建表格
        lines = []

        # 表头
        header = "│ " + " │ ".join(col.ljust(col_widths[col]) for col in columns) + " │"
        separator = "├─" + "─┼─".join("─" * col_widths[col] for col in columns) + "─┤"

        lines.append("┌─" + "─┬─".join("─" * col_widths[col] for col in columns) + "─┐")
        lines.append(header)
        lines.append(separator)

        # 数据行
        for row in page_results:
            cells = []
            for col in columns:
                val = str(row[col]) if row[col] is not None else "NULL"
                cells.append(val.ljust(col_widths[col])[: col_widths[col]])
            lines.append("│ " + " │ ".join(cells) + " │")

        lines.append("└─" + "─┴─".join("─" * col_widths[col] for col in columns) + "─┘")

        # 分页信息
        lines.append(f"\n第 {page}/{total_pages} 页，共 {total_rows} 行")

        return "\n".join(lines)

    def format_schema(
        self, schema: List[Dict[str, Any]], table_name: Optional[str] = None
    ) -> str:
        """
        格式化表结构

        Args:
            schema: 表结构列表
            table_name: 可选，指定表名

        Returns:
            格式化的表结构字符串
        """
        if not schema:
            return "未找到表结构信息"

        if table_name:
            lines = [f"表名: {table_name}"]
            lines.append(
                "┌────────────────────┬──────────────────┬──────────────┬──────────────────┐"
            )
            lines.append(
                "│ 字段名             │ 数据类型         │ 可为空      │ 默认值           │"
            )
            lines.append(
                "├────────────────────┼──────────────────┼──────────────┼──────────────────┤"
            )

            for col in schema:
                col_name = col.get("column_name", "").ljust(18)
                data_type = col.get("data_type", "").ljust(16)
                is_nullable = col.get("is_nullable", "").ljust(12)
                default_val = str(col.get("column_default", "")).ljust(16)
                lines.append(
                    f"│ {col_name}│ {data_type}│ {is_nullable}│ {default_val}│"
                )

            lines.append(
                "└────────────────────┴──────────────────┴──────────────┴──────────────────┘"
            )
        else:
            # 按表名分组
            tables = {}
            for col in schema:
                table = col.get("table_name", "unknown")
                if table not in tables:
                    tables[table] = []
                tables[table].append(col)

            lines = []
            for table_name, columns in sorted(tables.items()):
                lines.append(f"\n表名: {table_name}")
                lines.append(
                    "┌────────────────────┬──────────────────┬──────────────┬──────────────────┐"
                )
                lines.append(
                    "│ 字段名             │ 数据类型         │ 可为空      │ 默认值           │"
                )
                lines.append(
                    "├────────────────────┼──────────────────┼──────────────┼──────────────────┤"
                )

                for col in columns:
                    col_name = col.get("column_name", "").ljust(18)
                    data_type = col.get("data_type", "").ljust(16)
                    is_nullable = col.get("is_nullable", "").ljust(12)
                    default_val = str(col.get("column_default", "")).ljust(16)
                    lines.append(
                        f"│ {col_name}│ {data_type}│ {is_nullable}│ {default_val}│"
                    )

                lines.append(
                    "└────────────────────┴──────────────────┴──────────────┴──────────────────┘"
                )

        return "\n".join(lines)

    def truncate_results(
        self, results: List[Dict[str, Any]], max_rows: int
    ) -> List[Dict[str, Any]]:
        """
        截断结果集

        Args:
            results: 原始结果
            max_rows: 最大行数

        Returns:
            截断后的结果
        """
        if len(results) <= max_rows:
            return results

        return results[:max_rows]
