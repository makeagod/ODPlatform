# 7.4 验收用临时 check（verify 脚本会复制到 checks/ 后删除）
from odp_platform.data_validation.registry import CheckContext, CheckResult, CheckSeverity, check


@check("dummy")
def dummy_check(ctx: CheckContext) -> CheckResult:
    return CheckResult("dummy", CheckSeverity.PASS, "dummy ok", {})
