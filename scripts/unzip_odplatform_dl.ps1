# ODPlatform_dl.zip 解压（Windows PowerShell，无需 unzip 命令）
# 用法:
#   .\scripts\unzip_odplatform_dl.ps1
#   .\scripts\unzip_odplatform_dl.ps1 -ZipPath "D:\Downloads\ODPlatform_dl.zip"
#   .\scripts\unzip_odplatform_dl.ps1 -ZipPath ".\ODPlatform_dl.zip" -Dest ".\ODPlatform_dl"

param(
    [string]$ZipPath = "",
    [string]$Dest = ""
)

$ErrorActionPreference = "Stop"

function Find-Zip {
    param([string]$Name)
    $candidates = @(
        (Join-Path $PSScriptRoot "..\$Name"),
        (Join-Path $PSScriptRoot "..\..$Name"),
        (Join-Path $env:USERPROFILE "Downloads\$Name"),
        (Join-Path $env:USERPROFILE "Desktop\$Name"),
        "D:\$Name",
        "C:\$Name"
    )
    foreach ($p in $candidates) {
        $resolved = (Resolve-Path $p -ErrorAction SilentlyContinue)
        if ($resolved) { return $resolved.Path }
    }
    return $null
}

if (-not $ZipPath) {
    $ZipPath = Find-Zip "ODPlatform_dl.zip"
}
if (-not $ZipPath -or -not (Test-Path $ZipPath)) {
    Write-Host "未找到 ODPlatform_dl.zip。请指定路径:" -ForegroundColor Red
    Write-Host '  .\scripts\unzip_odplatform_dl.ps1 -ZipPath "完整路径\ODPlatform_dl.zip"'
    exit 1
}

$ZipPath = (Resolve-Path $ZipPath).Path
if (-not $Dest) {
    $Dest = Join-Path (Split-Path $ZipPath -Parent) "ODPlatform_dl"
}

Write-Host "ZIP:  $ZipPath"
Write-Host "解压到: $Dest"

if (-not (Test-Path $Dest)) {
    New-Item -ItemType Directory -Path $Dest -Force | Out-Null
}

Expand-Archive -Path $ZipPath -DestinationPath $Dest -Force
Write-Host "解压完成。" -ForegroundColor Green
Get-ChildItem $Dest | Select-Object -First 15 Name
