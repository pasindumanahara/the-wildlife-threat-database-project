<#
.SYNOPSIS
Install PostgreSQL if needed and prepare the Django database.

.EXAMPLE
.\scripts\setup-database.ps1

.EXAMPLE
.\scripts\setup-database.ps1 -DatabaseName wildlife_threat_db -DatabaseUser postgres
#>
[CmdletBinding()]
param(
    [ValidatePattern('^[A-Za-z_][A-Za-z0-9_]{0,62}$')]
    [string]$DatabaseName = 'wildlife_threat_db',
    [string]$DatabaseUser = 'postgres',
    [string]$DatabaseHost = '127.0.0.1',
    [ValidateRange(1, 65535)]
    [int]$Port = 5432,
    [switch]$SkipPostgresInstall
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$serverPath = Join-Path $projectRoot 'server'
$pythonPath = Join-Path $serverPath '.venv\Scripts\python.exe'
$previousPgPassword = $env:PGPASSWORD
$previousDbPassword = $env:DB_PASSWORD
$previousDbName = $env:DB_NAME
$previousDbUser = $env:DB_USER
$previousDbHost = $env:DB_HOST
$previousDbPort = $env:DB_PORT

function Find-Psql {
    $command = Get-Command psql.exe -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }

    $installRoot = Join-Path $env:ProgramFiles 'PostgreSQL'
    if (Test-Path -LiteralPath $installRoot -PathType Container) {
        $versions = Get-ChildItem -LiteralPath $installRoot -Directory |
            Sort-Object { if ($_.Name -match '^\d+$') { [int]$_.Name } else { 0 } } -Descending
        foreach ($version in $versions) {
            $candidate = Join-Path $version.FullName 'bin\psql.exe'
            if (Test-Path -LiteralPath $candidate -PathType Leaf) { return $candidate }
        }
    }
    return $null
}

function Require-Success {
    param([string]$Step)
    if ($LASTEXITCODE -ne 0) { throw "$Step failed with exit code $LASTEXITCODE." }
}

function Restore-Environment {
    param([string]$Name, [string]$Value)
    if ($null -eq $Value) {
        Remove-Item -Path "Env:$Name" -ErrorAction SilentlyContinue
    } else {
        Set-Item -Path "Env:$Name" -Value $Value
    }
}

try {
    $psqlPath = Find-Psql
    if (-not $psqlPath) {
        if ($SkipPostgresInstall) { throw 'psql.exe was not found. Install PostgreSQL or omit -SkipPostgresInstall.' }
        $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
        if (-not $winget) { throw 'WinGet is required to install PostgreSQL. See https://www.postgresql.org/download/windows/.' }
        Write-Host 'Installing PostgreSQL 18 through WinGet. Complete the installer, including its postgres password and port prompts.'
        & $winget.Source install --id PostgreSQL.PostgreSQL.18 --exact --source winget --interactive
        Require-Success 'PostgreSQL installation'
        $psqlPath = Find-Psql
        if (-not $psqlPath) { throw 'PostgreSQL was installed, but psql.exe could not be found. Reopen PowerShell and rerun this script.' }
    }

    if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
        $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
        if ($launcher) {
            & $launcher.Source -3 -m venv (Join-Path $serverPath '.venv')
        } else {
            $python = Get-Command python.exe -ErrorAction SilentlyContinue
            if (-not $python) { throw 'Python 3 is required. Install Python and rerun this script.' }
            & $python.Source -m venv (Join-Path $serverPath '.venv')
        }
        Require-Success 'Python virtual environment creation'
    }

    & $pythonPath -m pip install -r (Join-Path $serverPath 'requirements.txt')
    Require-Success 'Backend dependency installation'

    if (-not $env:PGPASSWORD) {
        $securePassword = Read-Host 'PostgreSQL password for the database user' -AsSecureString
        $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
        try { $env:PGPASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) }
        finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
    }
    $env:DB_PASSWORD = $env:PGPASSWORD
    $env:DB_NAME = $DatabaseName
    $env:DB_USER = $DatabaseUser
    $env:DB_HOST = $DatabaseHost
    $env:DB_PORT = [string]$Port

    $psqlArgs = @('--no-psqlrc', '--no-password', '-v', 'ON_ERROR_STOP=1',
                  '-h', $DatabaseHost, '-p', [string]$Port, '-U', $DatabaseUser)
    $exists = & $psqlPath @psqlArgs -d postgres -At -c "SELECT 1 FROM pg_database WHERE datname = '$DatabaseName'"
    Require-Success 'PostgreSQL connection'
    if ($exists -ne '1') {
        Write-Host "Creating database $DatabaseName..."
        & $psqlPath @psqlArgs -d postgres -c "CREATE DATABASE $DatabaseName"
        Require-Success 'Database creation'
    } else {
        Write-Host "Database $DatabaseName already exists."
    }

    Push-Location $serverPath
    try {
        & $pythonPath manage.py migrate
        Require-Success 'Django migrations'
    } finally { Pop-Location }
    Write-Host "Database $DatabaseName is ready. Run .\scripts\run-project.ps1 to start the app."
} finally {
    Restore-Environment 'PGPASSWORD' $previousPgPassword
    Restore-Environment 'DB_PASSWORD' $previousDbPassword
    Restore-Environment 'DB_NAME' $previousDbName
    Restore-Environment 'DB_USER' $previousDbUser
    Restore-Environment 'DB_HOST' $previousDbHost
    Restore-Environment 'DB_PORT' $previousDbPort
}
