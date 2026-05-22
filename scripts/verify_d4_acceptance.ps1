# D4 acceptance (7.1 - 7.5)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

function Assert-ExitCode([int]$code, [int]$expected, [string]$label) {
    if ($code -ne $expected) {
        throw "${label}: expected exit ${expected}, got ${code}"
    }
    Write-Host "  OK ${label} (exit=${code})"
}

Write-Host "=== 7.1 rsod ==="
odp-validate --dataset rsod --task detect | Out-Null
Assert-ExitCode $LASTEXITCODE 0 "7.1"

Write-Host "`n=== 7.2 leak detection ==="
$trainDir = "data\processed\rsod\train\images"
$valDir = "data\processed\rsod\val\images"
$img = Get-ChildItem $trainDir -Filter *.jpg | Select-Object -First 1
if (-not $img) { throw "no rsod train images" }
$dup = Join-Path $valDir $img.Name
Copy-Item $img.FullName $dup -Force
try {
    odp-validate --dataset rsod --task detect | Out-Null
    Assert-ExitCode $LASTEXITCODE 2 "7.2"
} finally {
    if (Test-Path $dup) { Remove-Item $dup -Force }
}

Write-Host "`n=== 7.4 dummy check ==="
$dst = "apps\platform\src\odp_platform\data_validation\checks\dummy_check.py"
Copy-Item "scripts\dummy_check_template.py" $dst -Force
try {
    $out = odp-validate --dataset rsod --task detect 2>&1 | Out-String
    if ($out -notmatch "dummy") { throw "7.4: dummy check not in output" }
    Assert-ExitCode $LASTEXITCODE 0 "7.4"
} finally {
    if (Test-Path $dst) { Remove-Item $dst -Force }
}

Write-Host "`n=== 7.3 / 7.5 pytest ==="
python -m pytest tests/data_validation -q
if ($LASTEXITCODE -ne 0) { throw "pytest failed" }

Write-Host "`n=== safety_helmet pipeline ==="
if (-not (Test-Path "data\raw\safety_helmet\JPEGImages")) {
    python scripts/make_safety_helmet_sample.py
}
odp-transform --dataset safety_helmet --format pascal_voc | Out-Null
if ($LASTEXITCODE -ne 0) { throw "odp-transform failed" }
odp-validate --dataset safety_helmet --task detect | Out-Null
Assert-ExitCode $LASTEXITCODE 0 "safety_helmet"

Write-Host "`n=== ALL D4 ACCEPTANCE PASSED ==="
