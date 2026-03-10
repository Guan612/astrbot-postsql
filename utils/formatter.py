from typing import Any, Dict, List, Optional


class ResultFormatter:
    def __init__(self, page_size: int = 20, max_col_width: int = 50):
        self.page_size = page_size
        self.max_col_width = max_col_width

    def format_table(self, results: List[Dict[str, Any]], page: int = 1) -> str:
        if not results:
            return "查询结果为空"

        total_rows = len(results)
        total_pages = (total_rows + self.page_size - 1) // self.page_size
        page = max(1, min(page, total_pages))
        start_idx = (page - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, total_rows)
        page_results = results[start_idx:end_idx]

        columns = list(page_results[0].keys())
        col_widths: Dict[str, int] = {}
        for col in columns:
            max_len = len(str(col))
            for row in page_results:
                value = "NULL" if row.get(col) is None else str(row.get(col))
                max_len = max(max_len, len(value))
            col_widths[col] = min(max_len, self.max_col_width)

        header = " | ".join(str(col).ljust(col_widths[col]) for col in columns)
        separator = "-+-".join("-" * col_widths[col] for col in columns)
        lines = [header, separator]

        for row in page_results:
            cells = []
            for col in columns:
                value = "NULL" if row.get(col) is None else str(row.get(col))
                cells.append(value[: col_widths[col]].ljust(col_widths[col]))
            lines.append(" | ".join(cells))

        lines.append(f"\n第 {page}/{total_pages} 页，共 {total_rows} 行")
        return "\n".join(lines)

    def format_schema(
        self, schema: List[Dict[str, Any]], table_name: Optional[str] = None
    ) -> str:
        if not schema:
            return "未找到表结构信息"

        if table_name:
            lines = [f"表名: {table_name}"]
            for col in schema:
                lines.append(
                    f"- {col.get('column_name', '')}: {col.get('data_type', '')}, "
                    f"可空={col.get('is_nullable', '')}, 默认值={col.get('column_default', '')}"
                )
            return "\n".join(lines)

        tables: Dict[str, List[Dict[str, Any]]] = {}
        for col in schema:
            tables.setdefault(col.get("table_name", "unknown"), []).append(col)

        lines: List[str] = []
        for current_table, columns in sorted(tables.items()):
            lines.append(f"表名: {current_table}")
            for col in columns:
                lines.append(
                    f"- {col.get('column_name', '')}: {col.get('data_type', '')}, "
                    f"可空={col.get('is_nullable', '')}, 默认值={col.get('column_default', '')}"
                )
            lines.append("")
        return "\n".join(lines).strip()

    def truncate_results(
        self, results: List[Dict[str, Any]], max_rows: int
    ) -> List[Dict[str, Any]]:
        return results if len(results) <= max_rows else results[:max_rows]
