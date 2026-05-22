# -*- coding: utf-8 -*-
"""日志子系统常量。"""

# 项目根 logger 名 = 顶层 Python 包名；业务模块 getLogger(__name__) 会冒泡到此树
ROOT_LOGGER_NAME: str = "odp_platform"

# reset 等元工具使用独立子树，避免与业务日志混写同一 handler
AUDIT_LOGGER_NAME: str = "odp_platform.audit"
