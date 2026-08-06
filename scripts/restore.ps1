param(
    [Parameter(Mandatory = $true)] [string] $BackupFile
)

$ErrorActionPreference = "Stop"
$source = [System.IO.Path]::GetFullPath($BackupFile)
if (-not (Test-Path -LiteralPath $source)) { throw "No existe el archivo de backup." }
Get-Content -LiteralPath $source -Raw | docker compose exec -T postgres psql -U alsema -d alsema -v ON_ERROR_STOP=1
Write-Output "Restore completado: $source"
