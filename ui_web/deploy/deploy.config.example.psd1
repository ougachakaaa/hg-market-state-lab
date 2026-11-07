@{
    # Empty means the parent of this deploy directory.
    ProjectRoot = ''
    PackageManager = 'npm'
    BuildArguments = @('run', 'build')
    BuildOutput = 'dist'
    Distribution = 'Ubuntu-24.04'
    DeployRoot = '~/deployments/nginx-gateway'
    SitePath = 'sites/example'
    BaseUrl = 'http://localhost:8080'
    HealthPath = '/healthz'
    VerifyHttp = $true
    CreateBackup = $true
    BackupRetention = 3
    AllowOverwrite = $true
}
