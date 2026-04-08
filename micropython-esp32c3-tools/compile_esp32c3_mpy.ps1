$toolRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $toolRoot

if ($args.Count -lt 1) {
    Write-Host "Usage: .\micropython-esp32c3-tools\compile_esp32c3_mpy.ps1 <script.py>"
    exit 1
}

$inputPath = $args[0]

if (-not (Test-Path $inputPath)) {
    Write-Host "Input file not found: $inputPath"
    exit 1
}

# Keep the compiler self-contained in this repo-local tools folder.
$env:PYTHONPATH = $toolRoot
python -m mpy_cross $inputPath