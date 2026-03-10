from typing import List


class PermissionChecker:
    def __init__(self, admin_commands: List[str]):
        self.admin_commands = admin_commands

    def is_admin_command(self, command: str) -> bool:
        """
        检查命令是否需要管理员权限

        Args:
            command: 命令名

        Returns:
            True if admin command, False otherwise
        """
        return command in self.admin_commands

    def is_dangerous_command(self, command: str) -> bool:
        """
        检查是否为危险命令

        Args:
            command: SQL 命令

        Returns:
            True if dangerous, False otherwise
        """
        dangerous_keywords = ["DROP", "TRUNCATE", "DELETE", "ALTER"]
        command_upper = command.upper()
        for keyword in dangerous_keywords:
            if keyword in command_upper:
                return True
        return False
