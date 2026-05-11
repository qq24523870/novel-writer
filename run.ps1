$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host "Starting AI Novel Writing Assistant..."
Write-Host ""

$python = Join-Path $scriptDir "venv\Scripts\python.exe"
$mainPy = Join-Path $scriptDir "main.py"

if (-not (Test-Path $python)) {
    Write-Host "Virtual environment not found. Run: .\venv\Scripts\pip install -r requirements.txt"
    pause
    exit 1
}

& $python $mainPy

if ($LASTEXITCODE -ne 0) {
    Write-Host "Start failed, please check dependencies."
    pause
}
