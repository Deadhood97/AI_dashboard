param(
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$FrontendDir = Join-Path $ProjectRoot "frontend"
$LogDir = Join-Path $ProjectRoot "artifacts\logs"
$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Test-Port {
    param([int]$Port)

    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $async = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
        if (-not $async.AsyncWaitHandle.WaitOne(500, $false)) {
            return $false
        }
        $client.EndConnect($async)
        return $true
    }
    catch {
        return $false
    }
    finally {
        $client.Close()
    }
}

function Wait-ForPort {
    param(
        [int]$Port,
        [int]$TimeoutSeconds = 60
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-Port -Port $Port) {
            return $true
        }
        Start-Sleep -Milliseconds 750
    }
    return $false
}

if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python"
}

if (-not (Test-Port -Port 8000)) {
    Start-Process `
        -FilePath $PythonExe `
        -ArgumentList @("-m", "uvicorn", "api:app", "--host", "127.0.0.1", "--port", "8000") `
        -WorkingDirectory $ProjectRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $LogDir "shortcut-api.out.log") `
        -RedirectStandardError (Join-Path $LogDir "shortcut-api.err.log")
}

if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
    Start-Process `
        -FilePath "npm.cmd" `
        -ArgumentList @("install") `
        -WorkingDirectory $FrontendDir `
        -Wait `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $LogDir "shortcut-npm-install.out.log") `
        -RedirectStandardError (Join-Path $LogDir "shortcut-npm-install.err.log")
}

if (-not (Test-Port -Port 3000)) {
    Start-Process `
        -FilePath "npm.cmd" `
        -ArgumentList @("run", "dev", "--", "--hostname", "127.0.0.1", "--port", "3000") `
        -WorkingDirectory $FrontendDir `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $LogDir "shortcut-frontend.out.log") `
        -RedirectStandardError (Join-Path $LogDir "shortcut-frontend.err.log")
}

$frontendReady = Wait-ForPort -Port 3000 -TimeoutSeconds 75
if (-not $frontendReady) {
    throw "Dashboard Studio frontend did not become ready on http://127.0.0.1:3000. Check artifacts\logs\shortcut-frontend.err.log."
}

if (-not $NoBrowser) {
    Start-Process "http://127.0.0.1:3000"
}

Write-Host "Dashboard Studio is running at http://127.0.0.1:3000"
