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
$serverJob = $null

function Restore-Environment {
    param([string]$Name, [string]$Value)
    if ($null -eq $Value) {
        Remove-Item -Path "Env:$Name" -ErrorAction SilentlyContinue
    } else {
        Set-Item -Path "Env:$Name" -Value $Value
    }
}

try {
    if (-not ('ServerJob' -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;

public sealed class ServerJob : IDisposable {
    [StructLayout(LayoutKind.Sequential)]
    private struct BasicLimits {
        public long PerProcessUserTimeLimit;
        public long PerJobUserTimeLimit;
        public uint LimitFlags;
        public UIntPtr MinimumWorkingSetSize;
        public UIntPtr MaximumWorkingSetSize;
        public uint ActiveProcessLimit;
        public UIntPtr Affinity;
        public uint PriorityClass;
        public uint SchedulingClass;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct IoCounters {
        public ulong ReadOperationCount;
        public ulong WriteOperationCount;
        public ulong OtherOperationCount;
        public ulong ReadTransferCount;
        public ulong WriteTransferCount;
        public ulong OtherTransferCount;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct ExtendedLimits {
        public BasicLimits BasicLimitInformation;
        public IoCounters IoInfo;
        public UIntPtr ProcessMemoryLimit;
        public UIntPtr JobMemoryLimit;
        public UIntPtr PeakProcessMemoryUsed;
        public UIntPtr PeakJobMemoryUsed;
    }

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern SafeFileHandle CreateJobObject(IntPtr attributes, string name);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool SetInformationJobObject(SafeFileHandle job, int infoClass,
        ref ExtendedLimits info, uint length);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool AssignProcessToJobObject(SafeFileHandle job, IntPtr process);

    private readonly SafeFileHandle handle;

    public ServerJob() {
        handle = CreateJobObject(IntPtr.Zero, null);
        if (handle.IsInvalid) throw new Win32Exception(Marshal.GetLastWin32Error());
        var limits = new ExtendedLimits();
        limits.BasicLimitInformation.LimitFlags = 0x2000; // Kill processes when the launcher closes.
        if (!SetInformationJobObject(handle, 9, ref limits, (uint)Marshal.SizeOf<ExtendedLimits>())) {
            int error = Marshal.GetLastWin32Error();
            handle.Dispose();
            throw new Win32Exception(error);
        }
    }

    public void Add(Process process) {
        if (!AssignProcessToJobObject(handle, process.Handle))
            throw new Win32Exception(Marshal.GetLastWin32Error());
    }

    public void Dispose() { handle.Dispose(); }
}
'@
    }
    $serverJob = [ServerJob]::new()

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
    $serverJob.Add($backend)
    Remove-Item Env:DB_PASSWORD -ErrorAction SilentlyContinue

    $frontend = Start-Process -FilePath $npm.Source -ArgumentList @('run', 'dev', '--', '--host', '127.0.0.1', '--port', '5173') `
        -WorkingDirectory $clientPath -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $logPath 'vite.out.log') `
        -RedirectStandardError (Join-Path $logPath 'vite.err.log')
    $serverJob.Add($frontend)

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
    if ($serverJob) { $serverJob.Dispose() }
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
