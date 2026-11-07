[CmdletBinding()]
param([string]$ConfigPath)

$ErrorActionPreference = 'Stop'
try {
    if (-not $ConfigPath) { $ConfigPath = Join-Path $PSScriptRoot 'deploy.config.psd1' }
    if (-not (Test-Path -LiteralPath $ConfigPath -PathType Leaf)) { throw "Configuration file not found: $ConfigPath" }
    $config = Import-PowerShellDataFile -LiteralPath $ConfigPath
    $required = @('ProjectRoot','PackageManager','BuildArguments','BuildOutput','Distribution','DeployRoot','SitePath','BaseUrl','HealthPath','VerifyHttp','CreateBackup','BackupRetention','AllowOverwrite')
    foreach ($key in $required) { if (-not $config.ContainsKey($key)) { throw "Missing configuration: $key" } }
    foreach ($key in @('PackageManager','BuildOutput','Distribution','DeployRoot','SitePath','BaseUrl','HealthPath')) {
        if ($config[$key] -isnot [string] -or [string]::IsNullOrWhiteSpace($config[$key])) { throw "Configuration $key must be a nonempty string." }
    }
    if ($config.ProjectRoot -isnot [string]) { throw 'ProjectRoot must be a string.' }
    foreach ($key in @('VerifyHttp','CreateBackup','AllowOverwrite')) { if ($config[$key] -isnot [bool]) { throw "Configuration $key must be a boolean." } }
    if ($config.BackupRetention -isnot [int] -or $config.BackupRetention -lt 0 -or ($config.CreateBackup -and $config.BackupRetention -lt 1)) { throw 'BackupRetention must be a nonnegative integer, and at least 1 when backups are enabled.' }
    if ($config.BuildArguments -isnot [array] -or $config.BuildArguments.Count -eq 0 -or @($config.BuildArguments | Where-Object { $_ -isnot [string] -or [string]::IsNullOrWhiteSpace($_) }).Count -gt 0) { throw 'BuildArguments must be a nonempty array of strings.' }
    if ($config.PackageManager -ne 'npm') { throw 'This project uses npm and package-lock.json; PackageManager must be npm.' }
    if (-not [Uri]::IsWellFormedUriString($config.BaseUrl, [UriKind]::Absolute) -or ([Uri]$config.BaseUrl).Scheme -notin @('http','https') -or -not $config.HealthPath.StartsWith('/')) { throw 'BaseUrl must be an HTTP(S) URL and HealthPath must begin with /.' }
    $root = if ($config.ProjectRoot) { $config.ProjectRoot } else { Join-Path $PSScriptRoot '..' }
    $root = (Resolve-Path -LiteralPath $root).Path
    $packageFile = Join-Path $root 'package.json'
    if (-not (Test-Path -LiteralPath $packageFile -PathType Leaf) -or -not (Test-Path -LiteralPath (Join-Path $root 'package-lock.json') -PathType Leaf)) { throw 'Expected package.json and package-lock.json in ProjectRoot.' }
    $package = Get-Content -LiteralPath $packageFile -Raw | ConvertFrom-Json
    if (-not $package.scripts.build) { throw 'package.json has no build script.' }
    if ($package.dependencies.next -or $package.dependencies.nuxt -or $package.scripts.build -match '(?i)\b(next|nuxt)\s+build\b|--ssr') { throw 'SSR or server-side builds are not supported by this static deployment.' }
    foreach ($command in @('node.exe','npm.cmd','wsl.exe')) { if (-not (Get-Command $command -ErrorAction SilentlyContinue)) { throw "Required command unavailable: $command" } }
    $output = [IO.Path]::GetFullPath((Join-Path $root $config.BuildOutput))
    $rootPrefix = $root.TrimEnd('\','/') + [IO.Path]::DirectorySeparatorChar
    if (-not $output.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) { throw 'BuildOutput must be inside ProjectRoot.' }
    Write-Host '[BUILD] Checking WSL distribution and building on Windows'
    & wsl.exe --distribution $config.Distribution --exec true
    if ($LASTEXITCODE -ne 0) { throw 'Cannot access the configured WSL distribution.' }
    Push-Location $root
    try { & npm.cmd @($config.BuildArguments); if ($LASTEXITCODE -ne 0) { throw "Build failed with exit code $LASTEXITCODE." } } finally { Pop-Location }
    if (-not (Test-Path -LiteralPath (Join-Path $output 'index.html') -PathType Leaf)) { throw 'Build output is missing index.html.' }
    $payload = @{
        output = $output; root = $config.DeployRoot; site = $config.SitePath
        base_url = $config.BaseUrl; health = $config.HealthPath; verify = $config.VerifyHttp
        backup = $config.CreateBackup; retention = $config.BackupRetention; overwrite = $config.AllowOverwrite
    } | ConvertTo-Json -Compress
    $payload64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($payload))
    $helper64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes((Join-Path $PSScriptRoot 'publish.py')))
    $launcher = "import base64;exec(compile(base64.b64decode('$helper64'),'<publisher>','exec'))"
    & wsl.exe --distribution $config.Distribution --exec python3 -c $launcher $payload64
    if ($LASTEXITCODE -ne 0) { throw "WSL publication failed with exit code $LASTEXITCODE." }
    Write-Host '[RESULT] Deployment completed successfully.'
    exit 0
} catch {
    Write-Error "[RESULT] Deployment failed: $_" -ErrorAction Continue
    exit 1
}
