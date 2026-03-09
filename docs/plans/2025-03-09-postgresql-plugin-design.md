# AstrBot PostgreSQL 插件设计文档

**日期**: 2025-03-09
**作者**: opencode
**状态**: 已批准

## 1. 概述

开发一个功能丰富的 AstrBot PostgreSQL 驱动插件，提供多种数据库操作功能。

### 1.1 核心功能

- 多种用途（数据存储 + SQL 查询 + 数据分析）
- 配置文件方式管理数据库连接
- 支持命令式 SQL 查询和自然语言查询
- 独立的数据管理功能
- AI 辅助数据分析
- 命令级权限控制
- 连接池管理
- 分页显示查询结果
- 详细错误日志

## 2. 架构设计

### 2.1 分层架构

```
┌─────────────────────────────────┐
│       命令层 (Commands)          │
├─────────────────────────────────┤
│       权限层 (Permissions)       │
├─────────────────────────────────┤
│       服务层 (Services)          │
├─────────────────────────────────┤
│       连接层 (Connection)        │
├─────────────────────────────────┤
│       配置层 (Config)             │
└─────────────────────────────────┘
```

### 2.2 核心组件

#### 2.2.1 配置管理

使用 `_conf_schema.json` 定义配置 schema：

- 数据库连接信息
  - `db_host`: 数据库主机地址
  - `db_port`: 数据库端口
  - `db_name`: 数据库名称
  - `db_user`: 数据库用户名
  - `db_password`: 数据库密码
- 连接池配置
  - `pool_min_size`: 最小连接数（默认：2）
  - `pool_max_size`: 最大连接数（默认：10）
  - `pool_timeout`: 连接超时时间（默认：30秒）
- 查询限制
  - `page_size`: 单页结果数（默认：20）
  - `max_rows`: 最大返回行数（默认：1000）
- AI 配置
  - `ai_provider`: AI 提供商（使用 `_special: select_provider`）
- 权限配置
  - `admin_only_commands`: 需要管理员权限的命令列表

#### 2.2.2 数据库连接池

使用 `asyncpg` 异步驱动：

- 初始化时创建连接池
- 提供获取/释放连接的方法
- 支持连接健康检查
- 自动重连机制

#### 2.2.3 SQL 查询服务

**命令式查询**：
- `/sql query <SQL语句>` - 执行 SELECT 查询
- `/sql execute <SQL语句>` - 执行 INSERT/UPDATE/DELETE
- `/sql schema [表名]` - 查看数据库表结构

**自然语言查询**：
- `/sql ask <自然语言描述>` - 通过 AI 转换为 SQL
- 结合 AstrBot 的 AI 能力

#### 2.2.4 数据管理服务

**表管理**：
- `/db create_table <表定义>` - 创建表
- `/db drop_table <表名>` - 删除表
- `/db list_tables` - 列出所有表

**数据管理**：
- `/db insert <表名> <数据>` - 插入数据
- `/db update <表名> <条件> <数据>` - 更新数据
- `/db delete <表名> <条件>` - 删除数据

**数据导出**：
- `/db export <表名>` - 导出表数据为 CSV

#### 2.2.5 AI 数据分析服务

- `/analyze <数据描述>` - 对查询结果进行 AI 分析
- `/analyze trends <表名> <字段>` - 分析数据趋势
- `/analyze insights <表名>` - 提供 AI 洞察和建议
- 生成图表（使用文转图功能）

#### 2.2.6 权限控制

命令级权限配置：
- 只读命令：普通用户可用
- 写入命令：需要管理员权限
- 危险命令（如 DROP）：需要额外确认

#### 2.2.7 结果展示

- 分页显示：
  - 每页默认 20 行
  - 支持翻页命令（上一页/下一页/跳转页）
- 结果格式化：
  - 表格形式展示
  - 显示查询耗时和总行数
- 文件导出：
  - 超过页面限制的结果导出为 CSV

## 3. 文件结构

```
astrbot-pgsql/
├── main.py                 # 插件主文件
├── metadata.yaml           # 插件元数据
├── _conf_schema.json        # 配置 schema
├── requirements.txt        # 依赖项
├── db/                     # 数据库相关模块
│   ├── __init__.py
│   ├── pool.py            # 连接池管理
│   ├── executor.py        # SQL 执行器
│   └── models.py          # 数据模型
├── services/              # 服务层
│   ├── __init__.py
│   ├── query_service.py   # 查询服务
│   ├── nlp_service.py     # 自然语言处理服务
│   ├── analysis_service.py # 数据分析服务
│   └── data_service.py    # 数据管理服务
└── utils/                 # 工具函数
    ├── __init__.py
    ├── formatter.py       # 结果格式化
    ├── permissions.py     # 权限检查
    └── logger.py          # 日志管理
```

## 4. 依赖项

```
asyncpg>=0.29.0
```

## 5. 开发环境

- Python 3.10+
- 虚拟环境（venv）
- AstrBot >= 4.9.2

## 6. 错误处理

- 详细错误日志记录
- 用户友好的错误消息
- 不暴露敏感数据库信息
- 可恢复错误自动重试

## 7. 安全考虑

- 密码不在日志中明文显示
- 命令级权限控制
- SQL 注入防护（使用参数化查询）
- 敏感操作需要确认
