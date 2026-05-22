# scripts/make_disaster_data.ps1
# 为 D2.5 课程造灾难现场数据 (Windows 版, 与 make_disaster_data.sh 等价)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

Write-Host "🎬 准备灾难现场..."

# 1. data/raw/ 假装放了珍贵的标注数据(撞墙③要保护这个)
New-Item -ItemType Directory -Force -Path "data/raw/precious_dataset/images" | Out-Null
New-Item -ItemType Directory -Force -Path "data/raw/precious_dataset/labels" | Out-Null
1..200 | ForEach-Object {
    "fake image $_ bytes" | Set-Content "data/raw/precious_dataset/images/img_$_.jpg"
    "0 0.5 0.5 0.3 0.4" | Set-Content "data/raw/precious_dataset/labels/img_$_.txt"
}
Write-Host "  ✅ data/raw/precious_dataset/ — 400 个文件(模拟珍贵标注)"

# 2. runs/ 里造一个 2GB 的稀疏文件(撞墙④:删除这个会跑文件系统)
New-Item -ItemType Directory -Force -Path "runs/exp_2026_05_10" | Out-Null
fsutil file createnew "runs/exp_2026_05_10/best.pt" 2147483648 | Out-Null
fsutil sparse setflag "runs/exp_2026_05_10/best.pt" | Out-Null
Write-Host "  ✅ runs/exp_2026_05_10/best.pt — 2 GB(稀疏文件,删除时会跑文件系统)"

# 3. runs/ 里造大量小文件(撞墙④:大量 inode 删除是真的慢)
New-Item -ItemType Directory -Force -Path "runs/exp_2026_05_10/tb_logs" | Out-Null
1..5000 | ForEach-Object {
    "step $_ loss 0.$_" | Set-Content "runs/exp_2026_05_10/tb_logs/event.$_"
}
Write-Host "  ✅ runs/exp_2026_05_10/tb_logs/ — 5000 个小文件(大量 inode)"

# 4. apps/platform/logs/ 一些已存在日志(撞墙⑤的舞台)
$platLogs = "apps/platform/logs/training/2026-05-10"
New-Item -ItemType Directory -Force -Path $platLogs | Out-Null
1..50 | ForEach-Object {
    "training run $_ log content" | Set-Content "$platLogs/run-$_.log"
}
Write-Host "  ✅ apps/platform/logs/ — 50 份训练日志"

Write-Host ""
Write-Host "🎬 灾难现场准备就绪。"
Write-Host "   总文件数:约 5650"
Write-Host "   总名义大小:约 2 GB(磁盘实际占用 < 100 MB,得益于稀疏文件)"
Get-ChildItem data/raw, runs, apps/platform/logs -Recurse -ErrorAction SilentlyContinue |
    Measure-Object -Property Length -Sum |
    ForEach-Object { Write-Host ("   当前占用: {0:N2} MB" -f ($_.Sum / 1MB)) }