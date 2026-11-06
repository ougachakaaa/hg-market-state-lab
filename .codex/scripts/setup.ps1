$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$snapshotDir = Join-Path $repoRoot 'data_snapshot'
$frontendDir = Join-Path $repoRoot 'ui_web'

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

$poetry = Get-Command poetry -ErrorAction SilentlyContinue
$node = Get-Command node -ErrorAction SilentlyContinue
$npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
if (-not $npm) {
    $npm = Get-Command npm -ErrorAction SilentlyContinue
}
if (-not $poetry -or -not $node -or -not $npm) {
    throw 'Poetry, Node, and npm must be installed and available on PATH.'
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

foreach ($required in @(
    (Join-Path $repoRoot 'pyproject.toml'),
    (Join-Path $repoRoot 'poetry.lock'),
    (Join-Path $repoRoot 'poetry.toml'),
    (Join-Path $snapshotDir '.env.example'),
    (Join-Path $frontendDir 'package.json'),
    (Join-Path $frontendDir 'package-lock.json')
)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required repository file is missing: $required"
    }
}

$localEnv = Join-Path $snapshotDir '.env'
if (-not (Test-Path -LiteralPath $localEnv)) {
    Copy-Item -LiteralPath (Join-Path $snapshotDir '.env.example') -Destination $localEnv
    Write-Host 'Created data_snapshot/.env from .env.example.'
} else {
    Write-Host 'Using existing data_snapshot/.env.'
}

Push-Location $repoRoot
try {
    $env:POETRY_VIRTUALENVS_IN_PROJECT = 'true'
    Write-Host 'Installing repository Python dependencies into .venv...'
    & $poetry.Source env use $pythonExe
    if ($LASTEXITCODE -ne 0) { throw 'Poetry could not select Python 3.13.' }
    & $poetry.Source install --sync --no-interaction
    if ($LASTEXITCODE -ne 0) { throw 'Poetry install failed.' }

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

    Write-Host 'Installing frontend dependencies into ui_web/node_modules...'
    Push-Location $frontendDir
    try {
        & $npm.Source ci
        if ($LASTEXITCODE -ne 0) { throw 'npm ci failed.' }
    } finally {
        Pop-Location
    }

    Write-Host 'Verifying development environment readiness...'
    & $poetry.Source run lab doctor
    if ($LASTEXITCODE -ne 0) { throw 'lab doctor reported missing prerequisites.' }
} finally {
    Pop-Location
}
