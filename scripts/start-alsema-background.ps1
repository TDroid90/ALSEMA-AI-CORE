$ErrorActionPreference = "Stop"

$ProjectDirectory = Split-Path -Parent $PSScriptRoot
$DockerDesktop = Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"
$StateDirectory = Join-Path $env:LOCALAPPDATA "ALSEMA-AI-CORE"
$LogDirectory = Join-Path $StateDirectory "logs"
$LogPath = Join-Path $LogDirectory "startup.log"

New-Item -ItemType Directory -Force -Path $LogDirectory | Out-Null

function Write-StartupLog {
    param([string]$Message)

    "$(Get-Date -Format o) $Message" | Add-Content -LiteralPath $LogPath -Encoding UTF8
}

function Test-DockerEngine {
    $PreviousErrorPreference = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    try {
        & docker info *> $null
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
    finally {
        $ErrorActionPreference = $PreviousErrorPreference
    }
}

try {
    Write-StartupLog "Inicio automatico solicitado."

    if (-not (Test-DockerEngine)) {
        if (-not (Test-Path -LiteralPath $DockerDesktop)) {
            throw "Docker Desktop no esta instalado en la ruta esperada: $DockerDesktop"
        }

        if (-not (Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue)) {
            Write-StartupLog "Iniciando Docker Desktop en segundo plano."
            Start-Process -FilePath $DockerDesktop -ArgumentList "-Autostart" -WindowStyle Hidden
        }

        $DockerDeadline = (Get-Date).AddMinutes(5)
        while ((Get-Date) -lt $DockerDeadline) {
            Start-Sleep -Seconds 5
            if (Test-DockerEngine) {
                break
            }
        }
    }

    if (-not (Test-DockerEngine)) {
        throw "El motor de Docker no respondio dentro de los cinco minutos permitidos."
    }

    Write-StartupLog "Docker esta disponible. Levantando ALSEMA AI CORE."
    Push-Location $ProjectDirectory
    try {
        $PreviousErrorPreference = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            $ComposeOutput = & docker compose up -d 2>&1
            $ComposeExitCode = $LASTEXITCODE
        }
        finally {
            $ErrorActionPreference = $PreviousErrorPreference
        }
        $ComposeOutput | ForEach-Object { Write-StartupLog $_ }
        if ($ComposeExitCode -ne 0) {
            throw "docker compose up termino con codigo $ComposeExitCode."
        }
    }
    finally {
        Pop-Location
    }

    $HealthDeadline = (Get-Date).AddMinutes(3)
    while ((Get-Date) -lt $HealthDeadline) {
        try {
            $Health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health/ready" -TimeoutSec 5
            if ($Health.status -eq "ready") {
                Write-StartupLog "ALSEMA AI CORE esta listo."
                exit 0
            }
        }
        catch {
            # El backend todavía está iniciando; se vuelve a comprobar.
        }
        Start-Sleep -Seconds 5
    }

    throw "ALSEMA no alcanzo el estado ready dentro de los tres minutos permitidos."
}
catch {
    Write-StartupLog "ERROR: $($_.Exception.Message)"
    exit 1
}
