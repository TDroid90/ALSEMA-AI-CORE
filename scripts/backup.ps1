param(
    [Parameter(Mandatory = $true)] [string] $Destination
)

$ErrorActionPreference = "Stop"
$target = [System.IO.Path]::GetFullPath($Destination)
New-Item -ItemType Directory -Force -Path $target | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$database = Join-Path $target "alsema-$timestamp.sql"
docker compose exec -T postgres pg_dump -U alsema -d alsema --clean --if-exists | Out-File -FilePath $database -Encoding utf8
if ((Get-Item -LiteralPath $database).Length -eq 0) { throw "El backup de PostgreSQL quedó vacío." }
Write-Output "Backup creado: $database"
