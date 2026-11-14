param(
    [int]$Port = 8080
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $ScriptDir ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    $PythonExe = $VenvPython
} elseif (Test-Path "C:\Users\shant\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\python.exe") {
    $PythonExe = "C:\Users\shant\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\python.exe"
} else {
    $PythonExe = "python.exe"
}
$ServerScript = Join-Path $ScriptDir "backend\server.py"

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host " Starting SPHEREx 'Planet X' Discovery Engine Server on Port $Port..." -ForegroundColor Green
Write-Host " Interactive GUI: http://localhost:$Port/" -ForegroundColor Yellow
Write-Host "=================================================================" -ForegroundColor Cyan

& $PythonExe $ServerScript $Port
