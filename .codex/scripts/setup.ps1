param(
    [ValidateSet('all', 'python', 'frontend')]
    [string]$Dependencies = 'all'
)

$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$snapshotDir = Join-Path $repoRoot 'data_snapshot'
$frontendDir = Join-Path $repoRoot 'ui_web'
$runtimeDir = Join-Path $repoRoot 'ui_http/data/one-click'
$installPython = $Dependencies -ne 'frontend'
$installFrontend = $Dependencies -ne 'python'

function Invoke-LoggedCommand {
    param(
        [string]$Command,
        [string[]]$Arguments,
        [string]$Label,
        [string]$WorkingDirectory
    )

    Write-Host $Label
    $lines = New-Object System.Collections.Generic.List[string]
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    Push-Location -LiteralPath $WorkingDirectory
    try {
        & $Command @Arguments 2>&1 | ForEach-Object {
            $line = [string]$_
            [void]$lines.Add($line)
            Write-Host $line
        }
        $exitCode = $LASTEXITCODE
    } finally {
        Pop-Location
        $ErrorActionPreference = $previous
    }
    return [pscustomobject]@{ ExitCode = $exitCode; Lines = $lines }
}

function Save-InstallLog {
    param([string]$Name, $Lines)

    New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null
    $path = Join-Path $runtimeDir ('{0}-{1}.log' -f $Name, (Get-Date -Format 'yyyyMMdd-HHmmss'))
    [System.IO.File]::WriteAllLines($path, [string[]]$Lines)
    return $path
}

function Get-OutputTail {
    param($Lines, [int]$Count = 12)

    $selected = @($Lines | Where-Object { $_.Trim() } | Select-Object -Last $Count)
    if ($selected.Count -eq 0) { return 'no output' }
    return ($selected -join [Environment]::NewLine)
}

function Test-PoetrySyncCommand {
    param([string]$Poetry)

    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & $Poetry sync --help *> $null
        return ($LASTEXITCODE -eq 0)
    } finally {
        $ErrorActionPreference = $previous
    }
}

function Get-NodeModulesHolders {
    $root = Join-Path $frontendDir 'node_modules'
    $holders = @()
    foreach ($process in @(Get-Process -ErrorAction SilentlyContinue)) {
        if ($process.ProcessName -notmatch '^(node|nodejs|esbuild|code|cursor)$') { continue }
        try {
            foreach ($module in $process.Modules) {
                if ($module.FileName -and $module.FileName.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
                    $holders += [pscustomobject]@{
                        Id = $process.Id
                        Name = $process.ProcessName
                        Module = $module.FileName
                    }
                    break
                }
            }
        } catch { }
    }
    return $holders
}

function Format-DependencyHolders {
    param($Holders)

    $lines = @()
    foreach ($holder in $Holders) {
        $process = Get-CimInstance Win32_Process -Filter "ProcessId=$($holder.Id)" -ErrorAction SilentlyContinue
        $command = if ($process -and $process.CommandLine) { $process.CommandLine } else { '(command line unavailable)' }
        $module = [System.IO.Path]::GetFileName($holder.Module)
        $lines += ('  PID {0} {1}: {2} [{3}]' -f $holder.Id, $holder.Name, $command, $module)
    }
    return ($lines -join [Environment]::NewLine)
}

function Assert-NoNodeModulesHolders {
    $holders = @(Get-NodeModulesHolders)
    if ($holders.Count -eq 0) { return }
    throw ("Windows file lock: these processes currently use files under $frontendDir\node_modules:" +
        [Environment]::NewLine + (Format-DependencyHolders $holders) + [Environment]::NewLine +
        'Stop those repository-owned processes before retrying (for example run .\market-lab.cmd stop and close terminals running Vite or the Demo preview). The bootstrap never terminates other processes automatically.')
}

function Get-FrontendInstallFailure {
    param($Result, [string]$LogPath)

    $errorLines = @($Result.Lines | Where-Object { $_ -match 'npm (error|ERR!)' })
    $blockedPath = $null
    $lockCode = $null
    foreach ($line in $errorLines) {
        $pathMatch = [regex]::Match($line, 'npm (?:error|ERR!)\s+path\s+(.+)$')
        if (-not $blockedPath -and $pathMatch.Success) { $blockedPath = $pathMatch.Groups[1].Value.Trim() }
        $codeMatch = [regex]::Match($line, 'npm (?:error|ERR!)\s+code\s+(EPERM|EBUSY|ENOTEMPTY|EEXIST|EACCES)\b')
        if (-not $lockCode -and $codeMatch.Success) { $lockCode = $codeMatch.Groups[1].Value }
    }

    $message = "npm ci failed (exit $($Result.ExitCode)). Full npm output: $LogPath"
    if ($lockCode) {
        $message += [Environment]::NewLine + "Windows reported $lockCode while npm was replacing installed packages."
        if ($blockedPath) { $message += [Environment]::NewLine + "Blocked path: $blockedPath" }
        $holders = @(Get-NodeModulesHolders)
        if ($holders.Count -gt 0) {
            $message += [Environment]::NewLine + 'Processes currently using files in ui_web\node_modules:' +
                [Environment]::NewLine + (Format-DependencyHolders $holders)
            $message += [Environment]::NewLine + 'Stop those repository-owned processes and retry. The bootstrap never terminates them automatically.'
        } else {
            $message += [Environment]::NewLine +
                'No repository process is holding these files right now; a security scanner or indexer may be accessing them. Wait for it to finish and retry. Do not disable Windows security features.'
        }
    } else {
        $message += [Environment]::NewLine + 'Original npm errors:' + [Environment]::NewLine + (Get-OutputTail $errorLines 12)
        $message += [Environment]::NewLine + 'Run "npm ci" in ui_web to see the complete output, fix the reported problem, and retry.'
    }
    return $message
}

if ($installPython) {
    $pythonLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pythonLauncher) {
        $pythonCommand = $pythonLauncher.Source
        $pythonArgs = @('-3.13')
    } else {
        $pythonLauncher = Get-Command python3.13 -ErrorAction SilentlyContinue
        if (-not $pythonLauncher) {
            throw 'Python 3.13 is required (py -3.13 or python3.13).'
        }
        $pythonCommand = $pythonLauncher.Source
        $pythonArgs = @()
    }

    $pythonVersion = & $pythonCommand @pythonArgs -c 'import sys; print(sys.version_info.major, sys.version_info.minor, sep=chr(46))'
    if ($LASTEXITCODE -ne 0 -or -not $pythonVersion) {
        throw 'Python 3.13 is required and could not be executed.'
    }
    $pythonVersion = $pythonVersion.Trim()
    if ($pythonVersion -ne '3.13') {
        throw "Python 3.13 is required; found $pythonVersion."
    }
    $pythonExe = & $pythonCommand @pythonArgs -c 'import sys; print(sys.executable)'
    if ($LASTEXITCODE -ne 0 -or -not $pythonExe) {
        throw 'Unable to locate the Python 3.13 executable.'
    }
    $pythonExe = $pythonExe.Trim()
    if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) {
        throw 'Unable to locate the Python 3.13 executable.'
    }

    $poetry = Get-Command poetry -ErrorAction SilentlyContinue
    if (-not $poetry) {
        throw 'Poetry must be installed and available on PATH.'
    }
}

if ($installFrontend) {
    $node = Get-Command node -ErrorAction SilentlyContinue
    $npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if (-not $npm) {
        $npm = Get-Command npm -ErrorAction SilentlyContinue
    }
    if (-not $node -or -not $npm) {
        throw 'Node.js and npm must be installed and available on PATH.'
    }
}

$required = @((Join-Path $repoRoot '.env.example'))
if ($installPython) {
    $required += @(
        (Join-Path $repoRoot 'pyproject.toml'),
        (Join-Path $repoRoot 'poetry.lock'),
        (Join-Path $repoRoot 'poetry.toml')
    )
}
if ($installFrontend) {
    $required += @(
        (Join-Path $frontendDir 'package.json'),
        (Join-Path $frontendDir 'package-lock.json')
    )
}
foreach ($path in $required) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required repository file is missing: $path"
    }
}

$localEnv = Join-Path $repoRoot '.env'
$legacyEnv = Join-Path $snapshotDir '.env'
if (-not (Test-Path -LiteralPath $localEnv)) {
    Copy-Item -LiteralPath (Join-Path $repoRoot '.env.example') -Destination $localEnv
    Write-Host 'Created .env from .env.example.'
} else {
    Write-Host 'Using existing repository-root .env.'
}
if (Test-Path -LiteralPath $legacyEnv) {
    Write-Warning 'data_snapshot/.env is no longer read; move its contents to root .env and remove the legacy file.'
}

Push-Location $repoRoot
try {
    $env:POETRY_VIRTUALENVS_IN_PROJECT = 'true'
    if ($installPython) {
        Write-Host 'Installing repository Python dependencies into .venv...'
        $environment = Invoke-LoggedCommand -Command $poetry.Source -Arguments @('env', 'use', $pythonExe) `
            -Label "Selecting Python: $pythonExe" -WorkingDirectory $repoRoot
        if ($environment.ExitCode -ne 0) {
            $logPath = Save-InstallLog 'poetry-env' $environment.Lines
            throw ("Poetry could not select Python 3.13 (exit $($environment.ExitCode))." +
                [Environment]::NewLine + (Get-OutputTail $environment.Lines) + [Environment]::NewLine +
                "Full output: $logPath" + [Environment]::NewLine +
                'Fix the reported Python/Poetry problem and retry.')
        }

        $sync = Test-PoetrySyncCommand -Poetry $poetry.Source
        $installArguments = if ($sync) { @('sync', '--no-interaction') } else { @('install', '--sync', '--no-interaction') }
        $installLabel = if ($sync) { 'Running poetry sync...' } else { 'Running poetry install --sync...' }
        $install = Invoke-LoggedCommand -Command $poetry.Source -Arguments $installArguments `
            -Label $installLabel -WorkingDirectory $repoRoot
        if ($install.ExitCode -ne 0) {
            $logPath = Save-InstallLog 'poetry-install' $install.Lines
            throw ("Poetry dependency installation failed (exit $($install.ExitCode))." +
                [Environment]::NewLine + 'Original Poetry output:' + [Environment]::NewLine + (Get-OutputTail $install.Lines) +
                [Environment]::NewLine + "Full output: $logPath" + [Environment]::NewLine +
                'Check network access and the Poetry environment, then retry. The launcher did not change your .env or data directories.')
        }

        $poetryEnv = & $poetry.Source env info --path
        if ($LASTEXITCODE -ne 0 -or -not $poetryEnv) { throw 'Poetry environment is unavailable.' }
        $poetryEnv = $poetryEnv.Trim()
        $expectedEnv = Join-Path $repoRoot '.venv'
        if (-not (Test-Path -LiteralPath $expectedEnv -PathType Container)) {
            throw "Poetry did not create the worktree-local environment: $expectedEnv"
        }
        $actualEnv = (Resolve-Path -LiteralPath $poetryEnv).Path
        if ($actualEnv -ne (Resolve-Path -LiteralPath $expectedEnv).Path) {
            throw "Poetry environment is not worktree-local: $actualEnv"
        }
    }

    if ($installFrontend) {
        Assert-NoNodeModulesHolders
        Write-Host 'Installing frontend dependencies into ui_web/node_modules...'
        $npmInstall = Invoke-LoggedCommand -Command $npm.Source -Arguments @('ci') `
            -Label 'Running npm ci...' -WorkingDirectory $frontendDir
        if ($npmInstall.ExitCode -ne 0) {
            $logPath = Save-InstallLog 'npm-ci' $npmInstall.Lines
            throw (Get-FrontendInstallFailure -Result $npmInstall -LogPath $logPath)
        }
    }

    if ($Dependencies -eq 'all') {
        Write-Host 'Verifying development environment readiness...'
        & $poetry.Source run lab doctor
        if ($LASTEXITCODE -ne 0) { throw 'lab doctor reported missing prerequisites.' }
    }
} finally {
    Pop-Location
}
