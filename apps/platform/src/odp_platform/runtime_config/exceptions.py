# -*- coding: utf-8 -*-
"""运行配置子系统异常。"""


class ConfigError(Exception):
    """配置错误基类。"""


class ConfigFileNotFoundError(ConfigError):
    """YAML 配置文件不存在 (FR-06)。"""


class ConfigParseError(ConfigError):
    """YAML 解析或结构错误。"""


class UnknownFieldError(ConfigError):
    """未知字段 (FR-14)。"""


class ConfigValidationError(ConfigError):
    """字段值或跨字段验证失败 (FR-12/13)。"""
