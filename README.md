# AstrBot PostgreSQL Plugin

功能强大的 PostgreSQL 数据库插件，支持 SQL 查询、自然语言查询和 AI 数据分析

## 功能特性

- **SQL 查询执行**: 直接执行 SELECT、INSERT、UPDATE、DELETE 等 SQL 命令
- **自然语言转 SQL**: 使用 AI 将自然语言描述转换为 SQL 查询
- **AI 数据分析**: 自动分析数据趋势、生成数据洞察
- **数据管理**: 创建表、插入数据、更新数据、删除数据
- **数据导出**: 将查询结果导出为 CSV 格式
- **权限控制**: 支持管理员权限控制，保护敏感操作
- **连接池管理**: 高效的连接池管理，支持并发查询
- **结果分页**: 支持查询结果分页，避免返回过多数据

## 安装

### 前置要求

- Python 3.10 或更高版本
- PostgreSQL 数据库
- [AstrBot](https://github.com/AstrBotDevs/AstrBot)

### 安装步骤

1. 创建虚拟环境:
   ```bash
   python -m venv .venv
   ```

2. 激活虚拟环境:

   **Windows:**
   ```bash
   .venv\Scripts\activate
   ```

   **Linux/Mac:**
   ```bash
   source .venv/bin/activate
   ```

3. 安装依赖:
   ```bash
   pip install -r requirements.txt
   ```

4. 将插件放置到 AstrBot 的插件目录中

## 配置

在 AstrBot 的插件配置页面中配置以下参数:

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| db_host | string | localhost | 数据库主机地址 |
| db_port | int | 5432 | 数据库端口 |
| db_name | string | postgres | 数据库名称 |
| db_user | string | postgres | 数据库用户名 |
| db_password | string | - | 数据库密码 |
| pool_min_size | int | 2 | 连接池最小连接数 (建议 2-5) |
| pool_max_size | int | 10 | 连接池最大连接数 (根据负载调整) |
| pool_timeout | int | 30 | 连接超时时间（秒） |
| page_size | int | 20 | 单页结果行数 |
| max_rows | int | 1000 | 最大返回行数 |
| ai_provider | string | - | AI 提供商 (用于自然语言转 SQL 和数据分析) |
| admin_only_commands | list | - | 需要管理员权限的命令 |

## 使用指南

### SQL 查询

执行 SELECT 查询:
```
/sql query SELECT * FROM users WHERE age > 18
```

查看数据库表结构:
```
/sql schema users
```

查看所有表结构:
```
/sql schema
```

### 数据库操作

创建表:
```
/db create_table CREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT, age INTEGER)
```

删除表:
```
/db drop_table users
```

列出所有表:
```
/db list_tables
```

插入数据:
```
/db insert users {"name": "张三", "age": 25}
```

更新数据:
```
/db update users "age > 20" {"name": "李四"}
```

删除数据:
```
/db delete users "name = '张三'"
```

导出数据为 CSV:
```
/db export users
```

### 自然语言查询

使用自然语言描述查询:
```
/sql ask 查询所有年龄大于 18 的用户
```

```
/sql ask 统计每个部门的员工数量
```

### AI 数据分析

分析数据趋势:
```
/analyze trends users age
```

生成数据洞察:
```
/analyze insights users
```

## 权限控制

以下命令默认需要管理员权限:
- execute: 执行 INSERT/UPDATE/DELETE 命令
- create_table: 创建表
- drop_table: 删除表
- insert: 插入数据
- update: 更新数据
- delete: 删除数据

管理员角色: admin, owner, superuser

## 架构

```
astrbot-pgsql/
├── main.py                 # 插件主入口
├── metadata.yaml           # 插件元数据
├── requirements.txt        # Python 依赖
├── _conf_schema.json       # 配置模式
├── db/                     # 数据库层
│   ├── pool.py            # 连接池管理
│   └── executor.py        # SQL 执行器
├── services/              # 服务层
│   ├── query_service.py   # 查询服务
│   ├── nlp_service.py     # 自然语言处理服务
│   ├── analysis_service.py # 数据分析服务
│   └── data_service.py    # 数据管理服务
└── utils/                 # 工具类
    ├── permissions.py     # 权限检查
    └── formatter.py      # 结果格式化
```

## 已知限制

### MSYS2/MinGW64 Python 环境

如果您在 Windows 上使用 MSYS2/MinGW64 Python，在安装 `asyncpg` 时可能会遇到编译错误。这是因为 asyncpg 需要编译，而 MSYS2/MinGW64 构建版本没有预编译的二进制包。

**解决方案:** 使用标准的 Windows Python 安装（来自 python.org 或 Microsoft Store），而不是 MSYS2/MinGW64 Python。标准 Windows Python 提供 asyncpg 的预编译二进制包，可以无需编译直接安装。

### MSYS2/MinGW64 用户的替代方案

如果必须使用 MSYS2/MinGW64 Python，您需要:
1. 安装 PostgreSQL 开发头文件
2. 安装 C 编译工具（gcc, make 等）
3. 安装 Cython
4. 从源代码编译 asyncpg

不推荐大多数用户使用此方法。

## 支持

- [AstrBot 仓库](https://github.com/AstrBotDevs/AstrBot)
- [AstrBot 插件开发文档 (中文)](https://docs.astrbot.app/dev/star/plugin-new.html)
- [AstrBot 插件开发文档 (英文)](https://docs.astrbot.app/en/dev/star/plugin-new.html)

## 许可证

本插件遵循 AstrBot 的许可证。

## 作者

opencode & guan612

## 版本

v1.0.0
