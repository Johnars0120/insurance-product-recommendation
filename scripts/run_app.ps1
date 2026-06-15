param(
    [string]$HostName = "127.0.0.1",
    [int]$Port = 8000,
    [switch]$SkipInstall,
    [switch]$NoBrowser,
    [switch]$Reload,
    [switch]$Help
)

if ($Help) {
    Write-Host "保险产品智能推荐系统一键启动脚本"
    Write-Host ""
    Write-Host "用法："
    Write-Host "  powershell -ExecutionPolicy Bypass -File scripts\run_app.ps1"
    Write-Host "  powershell -ExecutionPolicy Bypass -File scripts\run_app.ps1 -Port 8001"
    Write-Host "  powershell -ExecutionPolicy Bypass -File scripts\run_app.ps1 -SkipInstall -NoBrowser"
    Write-Host "  powershell -ExecutionPolicy Bypass -File scripts\run_app.ps1 -Reload"
    Write-Host ""
    Write-Host "参数："
    Write-Host "  -HostName     启动地址，默认 127.0.0.1"
    Write-Host "  -Port         启动端口，默认 8000"
    Write-Host "  -SkipInstall  跳过依赖安装"
    Write-Host "  -NoBrowser    不自动打开浏览器"
    Write-Host "  -Reload       开启开发热重载"
    exit 0
}

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..")
Set-Location $repoRoot

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Get-PythonCommand {
    $commands = @("py", "python")
    foreach ($command in $commands) {
        $found = Get-Command $command -ErrorAction SilentlyContinue
        if ($found) {
            return $command
        }
    }
    throw "未找到 Python。请先安装 Python 3.10 或更高版本，并确认 python 或 py 命令可用。"
}

function Test-PythonModule {
    param(
        [string]$PythonPath,
        [string]$ModuleName
    )
    & $PythonPath -c "import $ModuleName" *> $null
    return $LASTEXITCODE -eq 0
}

Write-Host "保险产品智能推荐系统"
Write-Host "项目目录：$repoRoot"

$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
$venvActivate = Join-Path $repoRoot ".venv\Scripts\Activate.ps1"

if (-not (Test-Path $venvPython)) {
    Write-Step "创建虚拟环境 .venv"
    $pythonCommand = Get-PythonCommand
    if ($pythonCommand -eq "py") {
        & py -3 -m venv .venv
    } else {
        & python -m venv .venv
    }
}

if (-not (Test-Path $venvPython)) {
    throw "虚拟环境创建失败：未找到 $venvPython"
}

Write-Step "使用虚拟环境"
Write-Host $venvPython

if (-not $SkipInstall) {
    Write-Step "安装或更新项目依赖"
    & $venvPython -m pip install -r requirements.txt
} else {
    Write-Step "跳过依赖安装"
}

if (-not (Test-PythonModule -PythonPath $venvPython -ModuleName "uvicorn")) {
    throw "当前虚拟环境缺少 uvicorn。请去掉 -SkipInstall 重新运行脚本，或手动执行：.venv\Scripts\python.exe -m pip install -r requirements.txt"
}

$url = "http://$HostName`:$Port"

if (-not $NoBrowser) {
    Write-Step "打开浏览器"
    Start-Process $url
}

Write-Step "启动 Web 服务"
Write-Host "访问地址：$url"
Write-Host "接口文档：$url/docs"
Write-Host ""
Write-Host "停止服务：在当前窗口按 Ctrl+C"
Write-Host ""

$uvicornArgs = @("-m", "uvicorn", "app.main:app", "--host", $HostName, "--port", "$Port")
if ($Reload) {
    $uvicornArgs += "--reload"
}

& $venvPython @uvicornArgs
