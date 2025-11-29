# restores the unet_final folder into mediverse/backend, installs deps and starts the uvicorn server
param(
    [string]$Source = "C:\Users\MOHIT MATHANGI\OneDrive\Desktop\unet_final",
    [int]$Port = 8050
)
# Ensure running from mediverse root
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $repoRoot

$dest = Join-Path $repoRoot "backend"
if (-Not (Test-Path $Source)) {
    Write-Error "Source path '$Source' not found. Please ensure you provided the correct path or upload the files into the workspace."
    exit 1
}

if (-Not (Test-Path $dest)) {
    New-Item -ItemType Directory -Path $dest -Force | Out-Null
}

Write-Output "Copying files from '$Source' -> '$dest' (overwrites existing files)"
Copy-Item -Path (Join-Path $Source "*") -Destination $dest -Recurse -Force

# If a requirements.txt exists, create venv, install deps
Set-Location $dest
if (Test-Path requirements.txt) {
    Write-Output "Found requirements.txt — creating virtual environment and installing dependencies..."
    if (-Not (Test-Path ".venv")) {
        python -m venv .venv
    }
    Write-Output "Activating virtual environment and installing requirements"
    .\.venv\Scripts\Activate.ps1
    pip install --upgrade pip
    pip install -r requirements.txt
} else {
    Write-Output "No requirements.txt found in backend. Please manually install dependencies if needed."
}

# Start uvicorn in a new PowerShell window (non-blocking)
$entryCandidates = @('main:app','app:app','backend.main:app')
$entry = $null
foreach ($c in $entryCandidates) {
    # very simple heuristic: if main.py or app.py exists, choose main:app or app:app
    if (Test-Path "main.py") { $entry = 'main:app'; break }
    if (Test-Path "app.py") { $entry = 'app:app'; break }
}
if (-Not $entry) { $entry = 'main:app' }

$uvicornCmd = "python -m uvicorn $entry --host 0.0.0.0 --port $Port"
Write-Output "Starting backend with: $uvicornCmd"
Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$dest'; $uvicornCmd"

Write-Output "Backend started in a new PowerShell window (or will start after dependency install)."
Write-Output "Visit http://localhost:$Port/docs to validate the API (once server is running)."
