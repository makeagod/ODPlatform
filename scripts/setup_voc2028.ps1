# VOC2028 full pipeline: extract -> link -> transform -> validate
# Run from repo root: .\scripts\setup_voc2028.ps1

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Zip = "D:\VOC2028.zip"
$VocRoot = "D:\VOC2028"
$RawLink = Join-Path $Root "data\raw\voc2028"
$ProcessedYaml = Join-Path $Root "data\processed\voc2028.yaml"

Set-Location $Root

function Step($msg) { Write-Host ""; Write-Host "=== $msg ===" -ForegroundColor Cyan }

Step "1/6 Extract ZIP"
if (-not (Test-Path $Zip)) {
    Write-Host "Missing: $Zip" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path (Join-Path $VocRoot "JPEGImages"))) {
    Write-Host "Extracting to $VocRoot ..."
    if (-not (Test-Path $VocRoot)) { New-Item -ItemType Directory -Path $VocRoot | Out-Null }
    Expand-Archive -Path $Zip -DestinationPath $VocRoot -Force
} else {
    Write-Host "Already extracted, skip"
}

Step "2/6 Link data/raw/voc2028"
if (-not (Test-Path (Join-Path $Root "data\raw"))) {
    New-Item -ItemType Directory -Path (Join-Path $Root "data\raw") -Force | Out-Null
}
if (-not (Test-Path $RawLink)) {
    cmd /c mklink /J "$RawLink" "$VocRoot"
} else {
    Write-Host "Link exists: $RawLink"
}

Step "3/6 Install deps"
pip install colorlog scikit-learn pydantic "ultralytics>=8,<9" opencv-python pyyaml -q
pip install -e .\apps\platform -q

Step "4/6 odp-transform"
if (-not (Test-Path $ProcessedYaml)) {
    odp-transform --dataset voc2028 --format pascal_voc --train-rate 0.8 --val-rate 0.1
} else {
    Write-Host "Skip transform, yaml exists"
}

Step "5/6 odp-validate"
odp-validate --dataset voc2028 --task detect
if ($LASTEXITCODE -ne 0) {
    Write-Host "Validate failed exit=$LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Step "6/6 Done"
Write-Host "All VOC2028 tasks completed." -ForegroundColor Green
Write-Host "Train CPU: odp-train --yaml configs/runtime/train_voc2028.yaml --epochs 3 --batch 8 --device cpu"
Write-Host "Train GPU: odp-train --yaml configs/runtime/train_voc2028.yaml --device 0"
