# 开发环境一键安装 / 刷新 CLI 入口 (odp-init, odp-reset)
# 用法 (项目根目录):
#   .\scripts\setup-dev.ps1
#   .\scripts\setup-dev.ps1 -ReinstallOnly

param(
    [switch]$ReinstallOnly
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if ($ReinstallOnly) {
    Write-Host ">> 仅刷新 platform 包与 CLI 入口 (不装依赖)..."
    pip install -e ./apps/platform --force-reinstall --no-deps
} else {
    Write-Host ">> 安装 platform 包 + 开发依赖..."
    pip install -r requirements-dev.txt
}

Write-Host ""
Write-Host ">> 验证 CLI:"
foreach ($cmd in @("odp-init", "odp-reset")) {
    $found = Get-Command $cmd -ErrorAction SilentlyContinue
    if ($found) { Write-Host "  $cmd -> $($found.Source)" }
    else { Write-Host "  $cmd -> 未找到 (请检查 pip Scripts 是否在 PATH)" }
}
Write-Host ""
Write-Host "完成。常用命令:"
Write-Host "  odp-init"
Write-Host "  odp-reset              # dry-run 预览"
Write-Host "  odp-reset --yes        # 执行删除 (需输入 RESET)"
