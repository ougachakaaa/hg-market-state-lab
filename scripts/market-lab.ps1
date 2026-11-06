param(
    [Parameter(Position = 0)]
    [ValidateSet('start', 'stop', 'status')]
    [string]$Action = 'start'
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$runtimeDir = Join-Path $repoRoot 'ui_http\data\one-click'
$ports = @(8011, 5173)

function Test-NativeCommand([string]$Command, [string[]]$Arguments) {
    $ErrorActionPreference = 'Continue'
    & $Command @Arguments *> $null
    return ($LASTEXITCODE -eq 0)
}

function Get-Listeners([int]$Port) {
    @(Get-NetTCPConnection -State Listen -ErrorAction Stop | Where-Object { $_.LocalPort -eq $Port })
}

function Assert-FreePorts {
    foreach ($port in $ports) {
        if (@(Get-Listeners $port).Count -gt 0) {
            throw "Port occupied: $port. Stop the program using it and retry; it was not terminated."
        }
    }
}

function Test-OwnedListener([int]$Port, [int]$RootId) {
    $listeners = @(Get-Listeners $Port)
    if ($listeners.Count -eq 0) { return $false }
    $processes = @(Get-CimInstance Win32_Process)
    foreach ($listener in $listeners) {
        $idToCheck = [int]$listener.OwningProcess
        $owned = $false
        $visited = @{}
        while ($idToCheck -gt 0 -and -not $visited.ContainsKey($idToCheck)) {
            if ($idToCheck -eq $RootId) { $owned = $true; break }
            $visited[$idToCheck] = $true
            $process = $processes | Where-Object { $_.ProcessId -eq $idToCheck } | Select-Object -First 1
            if (-not $process) { break }
            $idToCheck = [int]$process.ParentProcessId
        }
        if (-not $owned) { throw "Port occupied during startup: $Port. The other program was not terminated." }
    }
    return $true
}

function Test-Http([string]$Url, [bool]$Protected) {
    try {
        $request = [System.Net.HttpWebRequest]::Create($Url)
        $request.Proxy = $null
        $request.Timeout = 2000
        $response = $request.GetResponse()
        try { return (-not $Protected -and [int]$response.StatusCode -eq 200) }
        finally { $response.Dispose() }
    } catch [System.Net.WebException] {
        $response = $_.Exception.Response
        if (-not $response) { return $false }
        try {
            if ($Protected -and [int]$response.StatusCode -eq 401) {
                $reader = New-Object System.IO.StreamReader($response.GetResponseStream())
                try { $body = $reader.ReadToEnd() | ConvertFrom-Json }
                finally { $reader.Dispose() }
                return ($body.error.kind -eq 'authentication_required' -and
                    $body.error.detail -eq 'Authentication required.' -and $null -eq $body.error.param)
            }
        } catch { return $false }
        finally { $response.Dispose() }
        return $false
    }
}

function Start-ServiceProcess([string]$Name, [string]$RunId) {
    $stdout = Join-Path $runtimeDir "$RunId-$Name.stdout.log"
    $stderr = Join-Path $runtimeDir "$RunId-$Name.stderr.log"
    $command = "& poetry run lab serve $Name; exit `$LASTEXITCODE"
    $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($command))
    $process = Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoLogo', '-NoProfile', '-EncodedCommand', $encoded) `
        -WorkingDirectory $repoRoot -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru -WindowStyle Hidden
    $streams = @()
    foreach ($path in @($stdout, $stderr)) {
        $file = [System.IO.File]::Open($path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
        $streams += [System.IO.StreamReader]::new($file)
    }
    return @{ Process = $process; Readers = $streams; Name = $Name }
}

function Show-Logs($Service) {
    if (-not $Service) { return }
    foreach ($reader in $Service.Readers) {
        while ($null -ne ($line = $reader.ReadLine())) { Write-Host "[$($Service.Name)] $line" }
    }
}

function Stop-ServiceTree($Service) {
    if ($Service -and -not $Service.Process.HasExited) {
        $ErrorActionPreference = 'Continue'
        & taskkill.exe /PID $Service.Process.Id /T /F 2>&1 | Out-Null
    }
}

function Get-ExitStatus($Process) {
    if (-not $Process -or -not $Process.HasExited) { return $null }
    try {
        $Process.WaitForExit()
        return $Process.ExitCode
    } catch {
        return $null
    }
}

function Get-ExitLabel($Process) {
    $code = Get-ExitStatus $Process
    if ($null -eq $code) { return 'unknown' }
    return [string]$code
}

function Test-MarketLabProcess($Process, [int]$Port) {
    $command = [string]$Process.CommandLine
    if (-not $command) { return $false }
    $inRepo = $command.IndexOf($repoRoot, [StringComparison]::OrdinalIgnoreCase) -ge 0
    if ($Port -eq 8011) {
        return $inRepo -and ($command -match 'ui_http[\\/]scripts[\\/]api\.py')
    }
    return $inRepo -and ($command.IndexOf('vite', [StringComparison]::OrdinalIgnoreCase) -ge 0)
}

function Start-MarketLab {
    $backend = $null
    $frontend = $null
    $failed = $false

    try {
        Set-Location -LiteralPath $repoRoot
        Write-Host 'Checking Windows development prerequisites...'
        foreach ($name in @('poetry', 'node', 'npm', 'powershell.exe', 'taskkill.exe')) {
            if (-not (Get-Command $name -ErrorAction SilentlyContinue)) { throw "Environment missing: $name is not available on PATH." }
        }
        $ErrorActionPreference = 'Continue'
        $python = Get-Command py -ErrorAction SilentlyContinue
        if ($python) { $version = & $python.Source -3.13 -c 'import sys; print(sys.version_info.major, sys.version_info.minor, sep=chr(46))' 2>$null }
        else {
            $python = Get-Command python3.13 -ErrorAction SilentlyContinue
            if ($python) { $version = & $python.Source -c 'import sys; print(sys.version_info.major, sys.version_info.minor, sep=chr(46))' 2>$null }
        }
        $ErrorActionPreference = 'Stop'
        if (-not $python -or $LASTEXITCODE -ne 0 -or $version -ne '3.13') { throw 'Environment missing: Python 3.13 is required (py -3.13 or python3.13).' }
        foreach ($tool in @('poetry', 'node', 'npm')) {
            if (-not (Test-NativeCommand $tool @('--version'))) { throw "Environment error: $tool could not be executed." }
        }
        & node -e 'const [major, minor] = process.versions.node.split(\".\").map(Number); process.exit((major === 20 && minor >= 19) || (major === 22 && minor >= 12) || major > 22 ? 0 : 1)'
        if ($LASTEXITCODE -ne 0) { throw 'Environment error: Node.js must be 20.19+ or 22.12+.' }
        Assert-FreePorts

        $env:POETRY_VIRTUALENVS_IN_PROJECT = 'true'
        $needsSetup = -not (Test-Path -LiteralPath (Join-Path $repoRoot '.venv\Scripts\python.exe')) -or
            -not (Test-Path -LiteralPath (Join-Path $repoRoot 'ui_web\node_modules'))
        if (-not $needsSetup) {
            if (-not (Test-NativeCommand 'poetry' @('run', 'python', '-c', 'import sys, fastapi, uvicorn, jwt, argon2; assert sys.version_info[:2] == (3, 13)'))) { $needsSetup = $true }
            if (-not (Test-NativeCommand 'poetry' @('run', 'lab', '--help'))) { $needsSetup = $true }
            Push-Location (Join-Path $repoRoot 'ui_web')
            try { if (-not (Test-NativeCommand 'npm' @('ls', '--depth=0'))) { $needsSetup = $true } }
            finally { Pop-Location }
        }
        if ($needsSetup) {
            Write-Host 'Project dependencies missing or incomplete; running existing Windows bootstrap...'
            try { & (Join-Path $repoRoot '.codex\scripts\setup.ps1') }
            catch { throw "Project dependency installation failed: $($_.Exception.Message)" }
        }
        $env:POETRY_VIRTUALENVS_IN_PROJECT = 'true'
        $poetryEnv = & poetry env info --path
        if ($LASTEXITCODE -ne 0 -or -not $poetryEnv -or
            (Resolve-Path -LiteralPath $poetryEnv.Trim()).Path -ne (Resolve-Path -LiteralPath (Join-Path $repoRoot '.venv')).Path) {
            throw 'Project dependency error: Poetry must use the repository root .venv. Run .codex\scripts\setup.ps1.'
        }

        if ($null -eq $env:LAB_AUTH_MODE) { $env:LAB_AUTH_MODE = 'loopback-http' }
        if ($null -eq $env:LAB_AUTH_ORIGIN) { $env:LAB_AUTH_ORIGIN = 'http://127.0.0.1:5173' }
        New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null
        if ($null -eq $env:LAB_AUTH_JWT_SECRET) {
            $secretPath = Join-Path $runtimeDir 'jwt-secret'
            if (-not (Test-Path -LiteralPath $secretPath)) {
                $bytes = New-Object byte[] 32
                $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
                try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
                $secret = [Convert]::ToBase64String($bytes).TrimEnd('=').Replace('+', '-').Replace('/', '_')
                try {
                    $file = [System.IO.File]::Open($secretPath, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
                    try { $writer = [System.IO.StreamWriter]::new($file); try { $writer.Write($secret) } finally { $writer.Dispose() } }
                    finally { $file.Dispose() }
                } catch [System.IO.IOException] { if (-not (Test-Path -LiteralPath $secretPath)) { throw } }
            }
            $env:LAB_AUTH_JWT_SECRET = [System.IO.File]::ReadAllText($secretPath)
        }
        $authCheck = 'from ui_http.auth._session import AuthConfig; c = AuthConfig.from_environment(); c.validate_listener(\"127.0.0.1\"); assert not c.secure and c.browser_origin == (\"http\", \"127.0.0.1\", 5173)'
        if (-not (Test-NativeCommand 'poetry' @('run', 'python', '-c', $authCheck))) { throw 'Auth configuration error: invalid JWT secret or local settings; existing values were not changed.' }

        Write-Host 'Checking backend imports...'
        $ErrorActionPreference = 'Continue'
        $probe = & poetry run python -c "import ui_http.app" 2>&1 | Out-String
        $probeCode = $LASTEXITCODE
        $ErrorActionPreference = 'Stop'
        if ($probeCode -ne 0) {
            $detail = if ($probe) { $probe.Trim() } else { 'no output' }
            throw "Backend import preflight failed:`n$detail"
        }

        Assert-FreePorts
        $runId = [Guid]::NewGuid().ToString('N')
        Write-Host "Starting services. Logs: $runtimeDir"
        $backend = Start-ServiceProcess 'backend' $runId
        $frontend = Start-ServiceProcess 'frontend' $runId
        $deadline = [DateTime]::UtcNow.AddSeconds(90)
        $ready = $false
        while ([DateTime]::UtcNow -lt $deadline) {
            Show-Logs $backend; Show-Logs $frontend
            if ($backend.Process.HasExited) { throw "Backend startup failed (exit $(Get-ExitLabel $backend.Process)); see logs above and in $runtimeDir." }
            if ($frontend.Process.HasExited) { throw "Frontend startup failed (exit $(Get-ExitLabel $frontend.Process)); see logs above and in $runtimeDir." }
            $backendOwned = Test-OwnedListener 8011 $backend.Process.Id
            $frontendOwned = Test-OwnedListener 5173 $frontend.Process.Id
            if ($backendOwned -and $frontendOwned -and (Test-Http 'http://127.0.0.1:8011/openapi.json' $true) -and
                (Test-Http 'http://127.0.0.1:5173/' $false)) {
                $ready = $true; break
            }
            Start-Sleep -Milliseconds 500
        }
        if (-not $ready) { throw "Service startup timeout: backend or frontend did not become ready within 90 seconds. See logs in $runtimeDir." }
        Write-Host 'Both services are ready. Opening http://127.0.0.1:5173/'
        Start-Process 'http://127.0.0.1:5173/'
        Write-Host 'Keep this window open. Press any key to stop both services, or run "market-lab.cmd stop" from another terminal.'
        while (-not [Console]::KeyAvailable) {
            Show-Logs $backend; Show-Logs $frontend
            if ($backend.Process.HasExited) { throw "Backend exited unexpectedly (exit $(Get-ExitLabel $backend.Process))." }
            if ($frontend.Process.HasExited) { throw "Frontend exited unexpectedly (exit $(Get-ExitLabel $frontend.Process))." }
            Start-Sleep -Milliseconds 500
        }
        [void][Console]::ReadKey($true)
    } catch {
        Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
        $failed = $true
    } finally {
        Stop-ServiceTree $frontend
        Stop-ServiceTree $backend
        Show-Logs $backend; Show-Logs $frontend
        foreach ($service in @($backend, $frontend)) { if ($service) { foreach ($reader in $service.Readers) { $reader.Dispose() } } }
    }

    if ($failed) { return 1 }
    return 0
}

function Stop-MarketLab {
    $failed = $false
    $targets = @()

    foreach ($port in $ports) {
        foreach ($listener in Get-Listeners $port) {
            $process = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)" -ErrorAction SilentlyContinue
            if (-not $process) { continue }
            if (-not (Test-MarketLabProcess $process $port)) {
                Write-Host "Port $port is used by another program (PID $($process.ProcessId), $($process.Name)); not stopping it." -ForegroundColor Yellow
                $failed = $true
                continue
            }
            if (@($targets | Where-Object { $_.ProcessId -eq $process.ProcessId }).Count -eq 0) {
                $targets += [pscustomobject]@{
                    ProcessId = $process.ProcessId
                    Port = $port
                    Name = $process.Name
                }
            }
        }
    }

    if ($targets.Count -eq 0) {
        if (-not $failed) {
            Write-Host 'Market Lab services are not running (ports 8011 and 5173 are free).'
        }
        if ($failed) { return 1 }
        return 0
    }

    foreach ($target in $targets) {
        Write-Host "Stopping $($target.Name) on port $($target.Port) (PID $($target.ProcessId))..."
        & taskkill.exe /PID $target.ProcessId /T /F 2>&1 | Out-Host
        if ($LASTEXITCODE -ne 0) { $failed = $true }
    }

    $deadline = [DateTime]::UtcNow.AddSeconds(10)
    $remaining = @()
    do {
        Start-Sleep -Milliseconds 500
        $remaining = @()
        foreach ($port in $ports) {
            $remaining += @(Get-Listeners $port)
        }
    } while ($remaining.Count -gt 0 -and [DateTime]::UtcNow -lt $deadline)

    if ($remaining.Count -gt 0) {
        foreach ($listener in $remaining) {
            Write-Host "Port $($listener.LocalPort) is still in use by PID $($listener.OwningProcess); stop it manually." -ForegroundColor Yellow
        }
        $failed = $true
    }

    if ($failed) {
        Write-Host 'Market Lab shutdown was incomplete; see the messages above.' -ForegroundColor Yellow
        return 1
    }
    Write-Host 'Market Lab services stopped.'
    return 0
}

function Show-MarketLabStatus {
    $found = $false
    foreach ($port in $ports) {
        $listeners = @(Get-Listeners $port)
        if ($listeners.Count -eq 0) {
            Write-Host "Port ${port}: stopped"
            continue
        }
        foreach ($listener in $listeners) {
            $found = $true
            $process = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)" -ErrorAction SilentlyContinue
            if (-not $process) {
                Write-Host "Port ${port}: PID $($listener.OwningProcess) (process unavailable)"
                continue
            }
            $label = if (Test-MarketLabProcess $process $port) { 'Market Lab' } else { 'other program' }
            Write-Host "Port ${port}: PID $($process.ProcessId) $($process.Name) [$label]"
        }
    }
    if (-not $found) {
        Write-Host 'Market Lab services are not running.'
    }
    return 0
}

try {
    switch ($Action) {
        'start' { exit (Start-MarketLab) }
        'stop' { exit (Stop-MarketLab) }
        'status' { exit (Show-MarketLabStatus) }
    }
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
