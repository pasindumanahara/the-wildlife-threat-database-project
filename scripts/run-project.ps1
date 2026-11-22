<#
.SYNOPSIS
Start Django and the Vite client for local development.

.DESCRIPTION
Prompts for the PostgreSQL password each run. It is passed to Django only in
the child process environment and is not written to a file. Press Ctrl+C to
stop both servers.

.EXAMPLE
.\scripts\run-project.ps1
#>
[CmdletBinding()]
param(
    [string]$DatabaseName = 'wildlife_threat_db',
    [string]$DatabaseUser = 'postgres',
    [string]$DatabaseHost = '127.0.0.1',
    [ValidateRange(1, 65535)]
    [int]$Port = 5432
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$serverPath = Join-Path $projectRoot 'server'
$clientPath = Join-Path $projectRoot 'client'
$pythonPath = Join-Path $serverPath '.venv\Scripts\python.exe'
$logPath = Join-Path $projectRoot 'logs'
$previousDbPassword = $env:DB_PASSWORD
$previousDbName = $env:DB_NAME
$previousDbUser = $env:DB_USER
$previousDbHost = $env:DB_HOST
$previousDbPort = $env:DB_PORT
$backend = $null
$frontend = $null

function Restore-Environment {
    param([string]$Name, [string]$Value)
    if ($null -eq $Value) {
        Remove-Item -Path "Env:$Name" -ErrorAction SilentlyContinue
    } else {
        Set-Item -Path "Env:$Name" -Value $Value
    }
}

try {
    if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
        throw 'Backend virtual environment is missing. Run .\scripts\setup-database.ps1 first.'
    }
    $npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if (-not $npm) { throw 'Node.js and npm are required to start the frontend.' }
    if (-not (Test-Path -LiteralPath (Join-Path $clientPath 'node_modules') -PathType Container)) {
        Push-Location $clientPath
        try {
            & $npm.Source ci
            if ($LASTEXITCODE -ne 0) { throw 'npm ci failed.' }
        } finally { Pop-Location }
    }

    if (-not $env:DB_PASSWORD) {
        $securePassword = Read-Host 'PostgreSQL password for the database user' -AsSecureString
        $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
        try { $env:DB_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) }
        finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
    }
    $env:DB_NAME = $DatabaseName
    $env:DB_USER = $DatabaseUser
    $env:DB_HOST = $DatabaseHost
    $env:DB_PORT = [string]$Port

    New-Item -ItemType Directory -Path $logPath -Force | Out-Null
    $backend = Start-Process -FilePath $pythonPath -ArgumentList @('manage.py', 'runserver', '127.0.0.1:8000', '--noreload') `
        -WorkingDirectory $serverPath -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $logPath 'django.out.log') `
        -RedirectStandardError (Join-Path $logPath 'django.err.log')
    Remove-Item Env:DB_PASSWORD -ErrorAction SilentlyContinue

    $frontend = Start-Process -FilePath $npm.Source -ArgumentList @('run', 'dev', '--', '--host', '127.0.0.1', '--port', '5173') `
        -WorkingDirectory $clientPath -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $logPath 'vite.out.log') `
        -RedirectStandardError (Join-Path $logPath 'vite.err.log')

    Start-Sleep -Seconds 2
    if ($backend.HasExited -or $frontend.HasExited) {
        throw "A server stopped during startup. Check $logPath for details."
    }
    Write-Host 'Django: http://127.0.0.1:8000/'
    Write-Host 'Frontend: http://127.0.0.1:5173/'
    Write-Host "Logs: $logPath"
    Write-Host 'Press Ctrl+C to stop both servers.'
    while (-not $backend.HasExited -and -not $frontend.HasExited) {
        Start-Sleep -Seconds 1
    }
    throw "A server stopped. Check $logPath for details."
} finally {
    foreach ($process in @($backend, $frontend)) {
        if ($process -and -not $process.HasExited) {
            & taskkill.exe /PID $process.Id /T /F | Out-Null
        }
    }
    Restore-Environment 'DB_PASSWORD' $previousDbPassword
    Restore-Environment 'DB_NAME' $previousDbName
    Restore-Environment 'DB_USER' $previousDbUser
    Restore-Environment 'DB_HOST' $previousDbHost
    Restore-Environment 'DB_PORT' $previousDbPort
}
